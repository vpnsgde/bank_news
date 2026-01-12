import os
import requests
from lxml import html
import json
import re
import time

# --- Cấu hình ---
START_URL = "https://nguoiquansat.vn/tin-moi-nhat"
CHANNEL_IDS = [302, 310, 315, 372]  # chỉ xử lý các channel này
API_TEMPLATE = "https://nguoiquansat.vn/api/getMoreArticle/channel_empty_{PublisherId}_{ChannelId}_0"
OUTPUT_FOLDER = ".tmp"
HTML_FILE = os.path.join(OUTPUT_FOLDER, "page.html")
LOOP_COUNT = 10

# Tạo folder nếu chưa có
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# --- Bước 1: Lấy HTML lần đầu ---
response = requests.get(START_URL)
response.raise_for_status()
with open(HTML_FILE, "w", encoding="utf-8") as f:
    f.write(response.text)
print(f"HTML saved to {HTML_FILE}")

# --- Bước 2: Lấy link từ XPath ---
tree = html.fromstring(response.content)
link_elem = tree.xpath('/html/body/div[3]/div/div/div[1]/div[2]/div[1]/div/div/div[1]/a')
if not link_elem:
    raise ValueError("Không tìm thấy link tại XPath đã cho")
link_href = link_elem[0].get("href")
print(f"Found link: {link_href}")

# --- Bước 3: Lấy PublisherId 6 số cuối ---
match = re.search(r'(\d{6})\.html$', link_href)
if not match:
    raise ValueError("Không tìm thấy PublisherId trong link")
publisher_id = match.group(1)
print(f"Initial PublisherId: {publisher_id}")

# Xóa file HTML sau khi lấy PublisherId
os.remove(HTML_FILE)
print(f"Deleted temporary HTML file: {HTML_FILE}")

# --- Bước 4: Duyệt qua từng ChannelId ---
for channel_id in CHANNEL_IDS:
    print(f"\n--- Crawling ChannelId: {channel_id} ---")
    current_publisher_id = publisher_id  # reset cho mỗi channel
    output_file = os.path.join(OUTPUT_FOLDER, f"nqs_{channel_id}.json")
    
    # Nếu file tổng đã tồn tại, load dữ liệu cũ để append
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            all_articles = json.load(f)
    else:
        all_articles = []

    for i in range(LOOP_COUNT):
        api_url = API_TEMPLATE.format(PublisherId=current_publisher_id, ChannelId=channel_id)
        print(f"[{i+1}/{LOOP_COUNT}] Fetching API: {api_url}")
        try:
            resp = requests.get(api_url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"API không truy cập được hoặc lỗi: {e}. Dừng crawl channel này.")
            break

        # Kiểm tra data có phải list và có dữ liệu không
        if not isinstance(data, list) or not data:
            print("API trả về rỗng hoặc không phải list. Dừng crawl channel này.")
            break

        # --- Ép tất cả object ChannelId = channel đang xử lý ---
        for item in data:
            item['ChannelId'] = channel_id

        # --- Sắp xếp PublisherId giảm dần ---
        sorted_data = sorted(data, key=lambda x: int(x.get("PublisherId", 0)), reverse=True)

        # --- Lấy PublisherId nhỏ nhất làm last PublisherId ---
        last_publisher_id = str(min(int(item.get("PublisherId", 0)) for item in sorted_data))
        current_publisher_id = last_publisher_id

        # --- Append vào file tổng ---
        all_articles.extend(sorted_data)

        # Lưu file tổng ChannelId
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        print(f"Updated total JSON for channel {channel_id} ({len(all_articles)} articles)")

        time.sleep(0.1)  # delay nhẹ tránh spam server
