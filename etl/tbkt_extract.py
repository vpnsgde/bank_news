import requests
from lxml import html
import json
import os

BASE_URLS = [
    {
        "url": "https://thoibaotaichinhvietnam.vn/tai-chinh&s_cond=&BRSR={count}",
        "category": "tai-chinh-ngan-hang"
    },
    {
        "url": "https://thoibaotaichinhvietnam.vn/ngan-hang&s_cond=&BRSR={count}",
        "category": "tai-chinh-ngan-hang"
    },
    {
        "url": "https://thoibaotaichinhvietnam.vn/chung-khoan&s_cond=&BRSR={count}",
        "category": "chung-khoan"
    },
    {
        "url": "https://thoibaotaichinhvietnam.vn/bat-dong-san&s_cond=&BRSR={count}",
        "category": "bat-dong-san"
    },
    {
        "url": "https://thoibaotaichinhvietnam.vn/kinh-te&s_cond=&BRSR={count}",
        "category": "vi-mo"
    }
]

COUNTS = [0, 15, 30, 45, 60]

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

    tree = html.fromstring(resp.content)
    records = []

    articles = tree.xpath("//article[@class='article']")
    print(f"[INFO] Found {len(articles)} articles")

    if not articles:
        print(f"[WARN] No articles found at {url}")

    for idx, article in enumerate(articles, start=1):
        # title & href
        title_nodes = article.xpath(".//h3[@class='article-title']/a/text()")
        link_nodes = article.xpath(".//h3[@class='article-title']/a/@href")

        # publish date
        time_nodes = article.xpath(".//span[@class='article-publish-time']//span[@class='format_time']/text()")
        date_nodes = article.xpath(".//span[@class='article-publish-time']//span[@class='format_date']/text()")

        if not (title_nodes and link_nodes and time_nodes and date_nodes):
            print(f"[WARN] Skip article #{idx} (missing field)")
            continue

        title = title_nodes[0].strip()
        href = link_nodes[0].strip()
        publish_date = f"{time_nodes[0].strip()} {date_nodes[0].strip()}"

        records.append({
            "title": title,
            "href": href,
            "category": category,
            "publish_date": publish_date
        })

    print(f"[INFO] Extracted {len(records)} records\n")
    return records


def main():
    print("[START] TBKT extract job\n")
    grouped_data = {}

    for src in BASE_URLS:
        category = src["category"]
        print(f"[CATEGORY] {category}")

        for count in COUNTS:
            url = src["url"].format(count=count)
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
            f"tbkt_{category}.json"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        print(f"[OK] Saved {len(items)} records -> {file_path}")

    print("\n[DONE] TBKT extract completed")


if __name__ == "__main__":
    main()
