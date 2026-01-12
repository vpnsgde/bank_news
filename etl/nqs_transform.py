import json
import os
import hashlib
import unicodedata
from datetime import datetime
from urllib.parse import urlparse, urlunparse

DATA_DIR = ".tmp"
OUTPUT_FILE = "./data/nqs_news.json"

CATEGORY_MAP = {
    302: "chung-khoan",
    310: "bat-dong-san",
    315: "tai-chinh-ngan-hang",
    372: "vi-mo",
}

# =========================
# Helpers
# =========================

def normalize_title_latin(text: str) -> str:
    """
    Bỏ dấu, chuyển latin, lowercase, strip
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def canonicalize_url(url: str) -> str:
    """
    Chuẩn hoá URL:
    - lowercase scheme + host
    - remove fragment
    - strip trailing slash
    """
    if not url:
        return ""

    parsed = urlparse(url.strip())
    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        fragment=""
    )
    canon = urlunparse(normalized)
    return canon.rstrip("/")


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def parse_publish_time(timex1: str):
    """
    Input:  "12/01/2026 - 09:57"
    Output: ("2026/01/12 09:57:00", unix_ts)
    """
    if not timex1:
        return None, None

    try:
        dt = datetime.strptime(timex1, "%d/%m/%Y - %H:%M")
        publish_date = dt.strftime("%Y/%m/%d %H:%M:%S")
        publish_ts = int(dt.timestamp())
        return publish_date, publish_ts
    except ValueError:
        return None, None


# =========================
# Load old data (for dedup)
# =========================

all_items = []
seen_href_hash = set()

if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        try:
            old_items = json.load(f)
            if isinstance(old_items, list):
                all_items.extend(old_items)
                seen_href_hash.update(
                    item.get("href_hash")
                    for item in old_items
                    if item.get("href_hash")
                )
        except json.JSONDecodeError:
            print(f"Warning: {OUTPUT_FILE} JSON error, skip old data")

# =========================
# Load all nqs_*.json files
# =========================

raw_records = []

for filename in os.listdir(DATA_DIR):
    if filename.startswith("nqs_") and filename.endswith(".json"):
        path = os.path.join(DATA_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    raw_records.extend(data)
                else:
                    print(f"Skip non-list file: {filename}")
            except json.JSONDecodeError:
                print(f"Skip JSON error file: {filename}")

# =========================
# Transform records
# =========================

for item in raw_records:
    title = item.get("Title", "").strip()
    href_raw = item.get("LinktoMe2", "").strip()
    channel_id = item.get("ChannelId")

    if not title or not href_raw:
        continue

    href = canonicalize_url(href_raw)
    href_hash = md5_hash(href)

    if href_hash in seen_href_hash:
        continue

    publish_date, publish_ts = parse_publish_time(item.get("TimeX1"))

    category = CATEGORY_MAP.get(channel_id)

    transformed = {
        "title": title,
        "title_latin": normalize_title_latin(title),
        "href": href,
        "href_hash": href_hash,
        "publish_date": publish_date,
        "publish_ts": publish_ts,
        "category": category,
    }

    seen_href_hash.add(href_hash)
    all_items.append(transformed)

# =========================
# Sort & Save
# =========================

all_items.sort(
    key=lambda x: x.get("publish_ts") or 0,
    reverse=True
)

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_items, f, ensure_ascii=False, indent=2)

# =========================
# Cleanup temp files
# =========================

for filename in os.listdir(DATA_DIR):
    if filename.startswith("nqs_") and filename.endswith(".json"):
        os.remove(os.path.join(DATA_DIR, filename))

print(f"Done! Total records after transform & dedup: {len(all_items)}")
