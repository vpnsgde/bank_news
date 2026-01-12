import os
import json
import glob
import hashlib
import unicodedata
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, urlunparse

TMP_DIR = ".tmp"
OUT_DIR = "./data"
OUT_FILE = os.path.join(OUT_DIR, "vnfi_news.json")

os.makedirs(OUT_DIR, exist_ok=True)


# ---------- helpers ----------

def strip_accents(text: str) -> str:
    """
    Ép unicode tiếng Việt -> latin không dấu
    """
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text


def normalize_url(url: str) -> str:
    """
    Canonicalize + normalize URL để hash ổn định
    - lowercase scheme + host
    - bỏ fragment
    - strip slash cuối
    """
    parsed = urlparse(url.strip())

    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    normalized = urlunparse((
        scheme,
        netloc,
        path,
        "",     # params
        parsed.query,
        ""      # fragment
    ))
    return normalized


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def parse_pubdate(pub_date_raw: str):
    """
    Input : 12/01/26 13:43 (GMT+7)
    Output:
        - formatted: yyyy/mm/dd hh:mm:ss
        - unix ts (UTC+7)
    """
    # tách phần datetime, bỏ (GMT+7)
    dt_part = pub_date_raw.split("(")[0].strip()

    dt_local = datetime.strptime(dt_part, "%d/%m/%y %H:%M")

    tz = timezone(timedelta(hours=7))
    dt_local = dt_local.replace(tzinfo=tz)

    formatted = dt_local.strftime("%Y/%m/%d %H:%M:%S")
    ts = int(dt_local.timestamp())
    return formatted, ts


# ---------- main transform ----------

def main():
    all_records = []

    files = glob.glob(os.path.join(TMP_DIR, "vnfi_*.json"))
    if not files:
        print("No vnfi_*.json found in .tmp/")
        return

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)

        for r in records:
            title = r.get("title", "").strip()
            href = r.get("href", "").strip()
            pub_date_raw = r.get("publish_date", "").strip()

            if not (title and href and pub_date_raw):
                continue

            # title_latin
            title_latin = strip_accents(title).lower().strip()

            # href_hash
            href_norm = normalize_url(href)
            href_hash = md5_hash(href_norm)

            # publish_date + ts
            pub_date_fmt, pub_ts = parse_pubdate(pub_date_raw)

            out = {
                "title": title,
                "title_latin": title_latin,
                "href": href_norm,
                "href_hash": href_hash,
                "publish_date": pub_date_fmt,
                "publish_ts": pub_ts,
                "category": r.get("category"),
            }
            all_records.append(out)

    # save output
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_records)} records -> {OUT_FILE}")

    # cleanup tmp files
    for file_path in files:
        os.remove(file_path)

    print("Cleanup .tmp/vnfi_*.json done.")


if __name__ == "__main__":
    main()
