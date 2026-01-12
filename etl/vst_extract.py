import requests
import xml.etree.ElementTree as ET
import json
import os

RSS_SOURCES = [
    # --- Tài chính - Ngân hàng ---
    {
        "url": "https://vietstock.vn/757/tai-chinh/ngan-hang.rss",
        "category": "tai-chinh-ngan-hang"
    },
    {
        "url": "https://vietstock.vn/758/tai-chinh/thue-va-ngan-sach.rss",
        "category": "tai-chinh-ngan-hang"
    },
    {
        "url": "https://vietstock.vn/3113/tai-chinh/bao-hiem.rss",
        "category": "tai-chinh-ngan-hang"
    },

    # --- Bất động sản ---
    {
        "url": "https://vietstock.vn/4220/bat-dong-san/thi-truong-nha-dat.rss",
        "category": "bat-dong-san"
    },
    {
        "url": "https://vietstock.vn/42221/bat-dong-san/quy-hoach-ha-tang.rss",
        "category": "bat-dong-san"
    },

    # --- Vĩ mô ---
    {
        "url": "https://vietstock.vn/761/kinh-te/vi-mo.rss",
        "category": "vi-mo"
    },
    {
        "url": "https://vietstock.vn/768/kinh-te/kinh-te-dau-tu.rss",
        "category": "vi-mo"
    },

    # --- Chứng khoán ---
    {
        "url": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
        "category": "chung-khoan"
    },
    {
        "url": "https://vietstock.vn/143/chung-khoan/chinh-sach.rss",
        "category": "chung-khoan"
    },
    {
        "url": "https://vietstock.vn/738/doanh-nghiep/co-tuc.rss",
        "category": "chung-khoan"
    },
    {
        "url": "http://vietstock.vn/737/doanh-nghiep/hoat-dong-kinh-doanh.rss",
        "category": "chung-khoan"
    },
    {
        "url": "https://vietstock.vn/764/doanh-nghiep/tang-von-m-a.rss",
        "category": "chung-khoan"
    },
    {
        "url": "https://vietstock.vn/746/doanh-nghiep/ipo-co-phan-hoa.rss",
        "category": "chung-khoan"
    }
]

OUTPUT_DIR = ".tmp"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🔑 Header để tránh 403 (bắt buộc với Vietstock)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
}


def parse_rss(url: str, category: str):
    resp = requests.get(url, headers=HEADERS, timeout=15)
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
            f"vst_{category}.json"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

        print(f"Saved {len(items)} records -> {file_path}")


if __name__ == "__main__":
    main()
