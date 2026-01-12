import requests
from bs4 import BeautifulSoup
import json
import os

# --- 6 link cố định ---
URLS = [
    {"url": "https://vietnamfinance.vn/tai-chinh/", "category": "tai-chinh-ngan-hang"},
    {"url": "https://vietnamfinance.vn/ngan-hang/", "category": "tai-chinh-ngan-hang"},
    {"url": "https://vietnamfinance.vn/chung-khoan/", "category": "chung-khoan"},
    {"url": "https://vietnamfinance.vn/bat-dong-san/", "category": "bat-dong-san"},
    {"url": "https://vietnamfinance.vn/dau-tu/", "category": "vi-mo"},
    {"url": "https://vietnamfinance.vn/ma/", "category": "vi-mo"},
]

OUTPUT_DIR = ".tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}


def parse_page(url: str, category: str):
    print(f"[INFO] Fetching: {url}")
    resp = requests.get(url, headers=HEADERS, timeout=15)
    print(f"[INFO] Status: {resp.status_code}")
    resp.raise_for_status()

    soup = BeautifulSoup(resp.content, "html.parser")
    records = []

    articles_div = soup.find("div", id="load_more_cate_pc")
    if not articles_div:
        print(f"[WARN] No main container found at {url}")
        return records

    articles = articles_div.find_all("div", class_="article")
    print(f"[INFO] Found {len(articles)} articles")

    if not articles:
        print(f"[WARN] No articles found at {url}")

    for idx, article in enumerate(articles, start=1):
        h3_tag = article.find("h3", class_="article__title")
        if not h3_tag:
            print(f"[WARN] Skip article #{idx} (no title)")
            continue

        a_tag = h3_tag.find("a")
        if not a_tag:
            print(f"[WARN] Skip article #{idx} (no link)")
            continue

        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "").strip()

        datetime_div = article.find("div", class_="detail-time-public")
        publish_date = datetime_div.get_text(strip=True) if datetime_div else None

        records.append({
            "title": title,
            "href": href,
            "category": category,
            "publish_date": publish_date
        })

    print(f"[INFO] Extracted {len(records)} records\n")
    return records


def main():
    print("[START] VNFI extract job\n")
    grouped_data = {}

    for src in URLS:
        category = src["category"]
        url = src["url"]
        print(f"[CATEGORY] {category}")

        try:
            records = parse_page(url, category)
        except Exception as e:
            print(f"[ERROR] Failed to fetch {url}: {e}")
            continue

        if category not in grouped_data:
            grouped_data[category] = []

        grouped_data[category].extend(records)

    print("\n[INFO] Writing output files...")

    for category, items in grouped_data.items():
        if not items:
            print(f"[WARN] No data for category {category}")
            continue

        file_path = os.path.join(
            OUTPUT_DIR,
            f"vnfi_{category}.json"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        print(f"[OK] Saved {len(items)} records -> {file_path}")

    print("\n[DONE] VNFI extract completed")


if __name__ == "__main__":
    main()
