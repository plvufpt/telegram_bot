import requests
import pandas as pd
import time
from datetime import datetime
import schedule

# 🔹 Thông tin bot Telegram
BOT_TOKEN = "7114959890:AAHq05lnkw_pXZunKvOIZOWQTN4Lcj06Ygw"
CHAT_ID = "5601244174"  # Cập nhật với CHAT_ID đúng

# 🔹 URL API Telegram
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# 🔹 URL API Bloomberg
url = "https://www.bloomberg.com/lineup-next/api/paginate"

# 🔹 Cấu hình request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bloomberg.com/",
    "Origin": "https://www.bloomberg.com",
    "Connection": "keep-alive"
}

# 🔹 Danh sách offset cố định
offsets = [0, 12, 24, 36]

# 🔹 Biến lưu bài viết đã gửi
sent_articles = set()

def fetch_news():
    """Hàm lấy tin tức từ Bloomberg"""
    all_data = []
    
    for offset in offsets:
        params = {
            "id": "archive_story_list",
            "page": "phx-economics-central-banks",
            "offset": offset,
            "variation": "archive",
            "type": "lineup_content"
        }

        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Lỗi khi request tại offset {offset}: {response.status_code}")
            continue

        data = response.json().get('archive_story_list', {}).get('items', [])

        if not data:
            print(f"Offset {offset} không có dữ liệu, dừng lại.")
            break

        all_data.extend(data)

    return all_data

def send_news():
    """Hàm lấy tin tức mới và gửi lên Telegram nếu có"""
    global sent_articles
    
    news_data = fetch_news()
    
    extracted_data = [
        {
            "headline": item.get("headline", ""),
            "publishedAt": item.get("publishedAt", ""),
            "url": f"https://www.bloomberg.com{item.get('url', '')}",
            "image": item.get("thumbnailImage", {}).get("url", "")  # Lấy URL hình ảnh
        }
        for item in news_data
    ]

    df = pd.DataFrame(extracted_data)
    df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce")

    # 🔹 Lọc bài viết trong 30 phút gần nhất
    now = datetime.utcnow()
    df_recent = df[df["publishedAt"] >= now - pd.Timedelta(minutes=30)]

    # 🔹 Chỉ gửi bài mới chưa gửi trước đó
    new_articles = df_recent[~df_recent["headline"].isin(sent_articles)]

    if not new_articles.empty:
        for _, row in new_articles.iterrows():
            message = f"📰 *{row['headline']}*\n🔗 [Xem tại đây]({row['url']})"
            
            response = requests.post(TELEGRAM_URL, data={
                "chat_id": CHAT_ID,
                "photo": row["image"],
                "caption": message,
                "parse_mode": "Markdown"
            })

            if response.status_code == 200:
                print(f"✅ Đã gửi: {row['headline']}")
                sent_articles.add(row["headline"])  # Lưu bài đã gửi
            else:
                print(f"❌ Lỗi khi gửi tin: {response.text}")
    else:
        print("⚠️ Không có tin tức mới trong 30 phút qua.")

# 🔹 Lên lịch chạy mỗi 30 phút
schedule.every(5).minutes.do(send_news)

print("🔄 Bot đang chạy...")

# 🔹 Chạy liên tục
while True:
    schedule.run_pending()
    time.sleep(10)
