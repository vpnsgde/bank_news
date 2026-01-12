import json
import sqlite3
from datetime import datetime
from pathlib import Path

# ================== CONFIG ==================
JSON_FILE = "./data/nqs_news.json"
DB_FILE = "../db/nqs.db"
ARTICLE_TABLE = "articles"
CATEGORY_TABLE = "categories"

# ================== LOAD JSON ==================
if not Path(JSON_FILE).exists():
    raise FileNotFoundError(f"Không tìm thấy file {JSON_FILE}")

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise ValueError("JSON phải là list các object")

# ================== CONNECT DB ==================
Path(DB_FILE).parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# ================== CREATE ARTICLES TABLE ==================
cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {ARTICLE_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    title_latin TEXT,
    href TEXT,
    href_hash BLOB,
    publish_date TEXT,
    publish_ts INTEGER,
    category TEXT
)
""")

# ================== CREATE UNIQUE INDEX cho dedup ==================
cursor.execute(f"""
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_hash_title
ON {ARTICLE_TABLE} (href_hash, title_latin)
""")

cursor.execute(f"""
CREATE INDEX IF NOT EXISTS idx_{ARTICLE_TABLE}_publish_ts
ON {ARTICLE_TABLE}(publish_ts)
""")

# ================== CREATE CATEGORIES TABLE ==================
cursor.execute(f"""
CREATE TABLE IF NOT EXISTS {CATEGORY_TABLE} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    created_at TEXT
)
""")

# ================== INSERT ARTICLES (dedup) ==================
insert_sql = f"""
INSERT OR IGNORE INTO {ARTICLE_TABLE} (
    title,
    title_latin,
    href,
    href_hash,
    publish_date,
    publish_ts,
    category
) VALUES (?, ?, ?, ?, ?, ?, ?)
"""

rows = []
for item in data:
    title = item.get("title")
    title_latin = item.get("title_latin")
    href = item.get("href")
    href_hash = bytes.fromhex(item.get("href_hash")) if item.get("href_hash") else None
    publish_date = item.get("publish_date")
    publish_ts = item.get("publish_ts")
    category = item.get("category")

    if not (title and title_latin and href and href_hash):
        continue

    rows.append((
        title,
        title_latin,
        href,
        href_hash,
        publish_date,
        publish_ts,
        category
    ))

# Insert all, SQLite tự ignore các duplicate theo index
cursor.executemany(insert_sql, rows)
conn.commit()

# ================== INSERT CATEGORIES ==================
existing_categories = set()
cursor.execute(f"SELECT name FROM {CATEGORY_TABLE}")
for row in cursor.fetchall():
    existing_categories.add(row[0])

now = datetime.utcnow().isoformat()
new_categories = set(item.get("category") for item in data if item.get("category"))
for cat in new_categories:
    if cat and cat not in existing_categories:
        cursor.execute(f"""
        INSERT INTO {CATEGORY_TABLE} (name, created_at)
        VALUES (?, ?)
        """, (cat, now))

conn.commit()

# ================== REPORT ==================
cursor.execute(f"SELECT COUNT(*) FROM {ARTICLE_TABLE}")
total_articles = cursor.fetchone()[0]

cursor.execute(f"SELECT COUNT(*) FROM {CATEGORY_TABLE}")
total_categories = cursor.fetchone()[0]

print(f"[Articles] Total records: {total_articles}")
print(f"[Categories] Total unique categories: {total_categories}")

conn.close()
