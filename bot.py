import requests
import pandas as pd
from datetime import datetime, timedelta

# 🔹 Thông tin bot Telegram
BOT_TOKEN = "7114959890:AAHq05lnkw_pXZunKvOIZOWQTN4Lcj06Ygw"
CHAT_ID = "5601244174"  # Thay bằng ID của bạn hoặc nhóm

# 🔹 URL API Telegram
TELEGRAM_TEXT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
TELEGRAM_PHOTO_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# 🔹 URL API Bloomberg
url = "https://www.bloomberg.com/lineup-next/api/paginate"

# 🔹 Cấu hình request
headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.bloomberg.com/"
}
offsets = [0, 12, 24, 36]
all_data = []

# 🔹 Lặp để lấy dữ liệu
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

# 🔹 Trích xuất thông tin quan trọng
extracted_data = [
    {
        "headline": item.get("headline", ""),
        "publishedAt": item.get("publishedAt", ""),
        "url": f"https://www.bloomberg.com.{item.get('url', '')}",
        "imageUrl": item.get("thumbnail", {}).get("baseUrl", "")  # Thử lấy ảnh nếu có
    }
    for item in all_data
]

# 🔹 Chuyển thành DataFrame
df = pd.DataFrame(extracted_data)
df["publishedAt"] = pd.to_datetime(df["publishedAt"], errors="coerce")

# 🔹 Lọc tin của ngày hôm qua
yesterday = datetime.today().date() - timedelta(days=1)
df_today = df[df["publishedAt"].dt.date == yesterday]

# 🔹 Gửi từng bài viết riêng lẻ
if not df_today.empty:
    for _, row in df_today.iterrows():
        text_message = f"📰 *{row['headline']}*\n🔗 [Xem tại đây]({row['url']})"

        # Nếu có ảnh, gửi kèm ảnh
        if row["imageUrl"]:
            response = requests.post(TELEGRAM_PHOTO_URL, data={
                "chat_id": CHAT_ID,
                "photo": row["imageUrl"],
                "caption": text_message,
                "parse_mode": "Markdown"
            })
        else:
            # Nếu không có ảnh, gửi tin nhắn bình thường
            response = requests.post(TELEGRAM_TEXT_URL, data={
                "chat_id": CHAT_ID,
                "text": text_message,
                "parse_mode": "Markdown"
            })

        if response.status_code == 200:
            print(f"✅ Gửi thành công: {row['headline']}")
        else:
            print(f"❌ Lỗi khi gửi tin nhắn: {response.text}")
else:
    print("⚠️ Không có tin tức nào được đăng hôm qua.")

