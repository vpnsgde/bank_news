import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import unidecode

# ================= CONFIG =================
DB_FILE = "../db/total_news.db"
STATUS_TABLE = "user_article_status"
ARTICLES_TABLE = "articles"
PAGE_SIZE = 100

st.set_page_config(page_title="Bank News", layout="wide")

# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page = 0

# ================= THEME COLORS =================
import subprocess

def is_system_dark():
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True
        )
        theme_name = result.stdout.strip().strip("'").lower()
        return "dark" in theme_name
    except Exception:
        return False

is_dark = is_system_dark()
theme = st.get_option("theme.base")
is_dark = theme == "dark" or is_system_dark()

if is_dark:
    BG = "#000000"
    TEXT = "#ffffff"
    META = "#cfcfcf"
    LINK = "#4da3ff"
else:
    BG = "#ffffff"
    TEXT = "#000000"
    META = "#555555"
    LINK = "#1a73e8"

st.markdown(f"""
<style>
html, body, [data-testid="stApp"] {{
    background-color: {BG};
    color: {TEXT};
}}
.news-row {{ padding: 1px 0px; }}
.title {{ font-size: 18px; font-weight: 400; line-height: 1.2; color: {TEXT}; }}
.channel {{ font-size: 15px; color: {META}; }}
.time {{ font-size: 15px; color: {META}; text-align: right; }}
.stt {{ font-size: 15px; color: {META}; text-align: right; padding-top: 0px; }}
a {{ color: {LINK}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR =================
st.sidebar.header("Filters")

conn = sqlite3.connect(DB_FILE)

# Load categories: tối đa 4
categories_from_db = conn.execute(
    "SELECT DISTINCT category FROM categories ORDER BY category LIMIT 4"
).fetchall()
categories = [row[0] for row in categories_from_db]

# ================= CATEGORY CHECKBOX =================
if "selected_categories" not in st.session_state:
    st.session_state.selected_categories = ["tai-chinh-ngan-hang"] if "tai-chinh-ngan-hang" in categories else [categories[0]]

def toggle_categories():
    if set(st.session_state.selected_categories) == set(categories):
        st.session_state.selected_categories = []
    else:
        st.session_state.selected_categories = categories.copy()

st.sidebar.button("All / None", on_click=toggle_categories)

selected_categories = []
for cat in categories:
    if st.sidebar.checkbox(cat, value=(cat in st.session_state.selected_categories)):
        selected_categories.append(cat)
st.session_state.selected_categories = selected_categories

# ================= KEYWORD =================
keyword = st.sidebar.text_input("Search keyword")

# ================= TIME FILTER =================
time_filter = st.sidebar.selectbox(
    "Time range",
    options=["All", "Today", "Yesterday", "This week", "This month"]
)

# ================= READ/FAVORITE FILTER =================
filter_read = st.sidebar.checkbox("Show Read only", value=False)
filter_fav = st.sidebar.checkbox("Show Favorite only", value=False)

# ================= RESET PAGE ON FILTER CHANGE =================
current_filter = (st.session_state.selected_categories, keyword, time_filter, filter_read, filter_fav)
if "last_filter" not in st.session_state:
    st.session_state.last_filter = current_filter
if st.session_state.last_filter != current_filter:
    st.session_state.page = 0
    st.session_state.last_filter = current_filter

# ================= INIT STATUS TABLE =================
conn.execute(f"""
CREATE TABLE IF NOT EXISTS {STATUS_TABLE} (
    href_hash TEXT PRIMARY KEY,
    is_read INTEGER DEFAULT 0,
    is_favorite INTEGER DEFAULT 0
)
""")
conn.commit()

# ================= BUILD QUERY =================
limit = (st.session_state.page + 1) * PAGE_SIZE
params = []
query = f"""
SELECT a.title, a.title_latin, a.href, a.href_hash, a.publish_date, a.publish_ts, a.category, a.source,
       IFNULL(s.is_read,0) AS is_read, IFNULL(s.is_favorite,0) AS is_favorite
FROM articles a
LEFT JOIN {STATUS_TABLE} s ON a.href_hash = s.href_hash
WHERE 1=1
"""

# Category filter
if selected_categories:
    placeholders = ",".join("?" for _ in selected_categories)
    query += f" AND a.category IN ({placeholders})"
    params.extend(selected_categories)

# Keyword filter: latin không dấu + LIKE
# if keyword:
#     keyword_latin = unidecode.unidecode(keyword.lower())
#     query += " AND lower(a.title_latin) LIKE ?"
#     params.append(f"%{keyword_latin}%")

if keyword:
    # 1. Ép sang latin không dấu
    keyword_latin = unidecode.unidecode(keyword.lower())
    # 2. Tách thành các từ
    words = [w.strip() for w in keyword_latin.split() if w.strip()]
    # 3. Thêm điều kiện LIKE cho từng từ
    for w in words:
        query += " AND lower(a.title_latin) LIKE ?"
        params.append(f"%{w}%")

# Time filter
now = datetime.now()
if time_filter == "Today":
    start_ts = int(datetime(now.year, now.month, now.day).timestamp())
    end_ts = int(now.timestamp())
elif time_filter == "Yesterday":
    yesterday = now - timedelta(days=1)
    start_ts = int(datetime(yesterday.year, yesterday.month, yesterday.day).timestamp())
    end_ts = int(datetime(now.year, now.month, now.day).timestamp())
elif time_filter == "This week":
    start_of_week = now - timedelta(days=now.weekday())
    start_ts = int(datetime(start_of_week.year, start_of_week.month, start_of_week.day).timestamp())
    end_ts = int(now.timestamp())
elif time_filter == "This month":
    start_ts = int(datetime(now.year, now.month, 1).timestamp())
    end_ts = int(now.timestamp())
else:
    start_ts = None
    end_ts = None

if start_ts is not None and end_ts is not None:
    query += " AND a.publish_ts BETWEEN ? AND ?"
    params.extend([start_ts, end_ts])

# Read/fav
if filter_read:
    query += " AND IFNULL(s.is_read,0)=1"
if filter_fav:
    query += " AND IFNULL(s.is_favorite,0)=1"

# Sort & limit
query += " ORDER BY a.publish_ts DESC LIMIT ?"
params.append(limit)

# ================= LOAD DATA =================
df = pd.read_sql(query, conn, params=params)
conn.close()

# ================= DASHBOARD =================
st.title("📰 Bank News")
st.caption(f"Showing {len(df)} news")

# ================= NEWS LIST =================
for idx, row in df.iterrows():
    href_hash = row["href_hash"]
    stt = idx + 1
    col0, col1, col2, col3, col4, col5 = st.columns([0.5,7.0,1.5,1.5,0.8,0.8])

    col0.markdown(f"<div class='stt'>{stt}</div>", unsafe_allow_html=True)
    col1.markdown(f"<div class='title'><a href='{row['href']}' target='_blank'>{row['title']}</a></div>", unsafe_allow_html=True)
    col2.markdown(f"<div class='channel'>{row['category']}</div>", unsafe_allow_html=True)
    col3.markdown(f"<div class='time'>{row['publish_date']}</div>", unsafe_allow_html=True)

    # Read/Favorite checkbox
    is_read = col4.checkbox("Read", value=bool(row["is_read"]), key=f"read_{href_hash}")
    is_fav = col5.checkbox("⭐", value=bool(row["is_favorite"]), key=f"fav_{href_hash}")

    # Update status DB
    conn = sqlite3.connect(DB_FILE)
    conn.execute(f"""
    INSERT INTO {STATUS_TABLE} (href_hash, is_read, is_favorite)
    VALUES (?, ?, ?)
    ON CONFLICT(href_hash) DO UPDATE SET
        is_read=excluded.is_read,
        is_favorite=excluded.is_favorite
    """, (href_hash, int(is_read), int(is_fav)))
    conn.commit()
    conn.close()

# ================= LOAD MORE =================
if len(df) >= limit:
    if st.button("Load more"):
        st.session_state.page += 1
