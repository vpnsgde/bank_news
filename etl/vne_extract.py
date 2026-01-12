import requests
import xml.etree.ElementTree as ET
import json
import os

RSS_SOURCES = [
    {
        "url": "https://vneconomy.vn/chung-khoan.rss",
        "category": "chung-khoan"
    },
    {
        "url": "https://vneconomy.vn/tai-chinh.rss",
        "category": "tai-chinh-ngan-hang"
    },
    {
        "url": "https://vneconomy.vn/dau-tu.rss",
        "category": "tai-chinh-ngan-hang"
    },
    {
        "url": "https://vneconomy.vn/dia-oc.rss",
        "category": "bat-dong-san"
    }
]

OUTPUT_DIR = ".tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_rss(url: str, category: str):
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel = root.find("channel")
    if channel is None:
        return []

    records = []

    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()

        # chỉ lấy record đủ 4 field
        if not (title and link and pub_date and category):
            continue

        records.append({
            "title": title,
            "href": link,
            "category": category,
            "publish_date": pub_date
        })

    return records


def main():
    grouped_data = {}

    for src in RSS_SOURCES:
        category = src["category"]
        records = parse_rss(src["url"], category)

        if category not in grouped_data:
            grouped_data[category] = []

        grouped_data[category].extend(records)

    # ghi file theo category
    for category, items in grouped_data.items():
        if not items:
            continue

        file_path = os.path.join(
            OUTPUT_DIR,
            f"vne_{category}.json"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(items)} records -> {file_path}")


if __name__ == "__main__":
    main()
