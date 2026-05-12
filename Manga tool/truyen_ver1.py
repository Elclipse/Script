import os
import requests
from bs4 import BeautifulSoup

def download_chapter(url):
    # Giả lập trình duyệt để tránh bị chặn
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Referer": "https://truyenqqko.com/"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm tất cả các thẻ img chứa ảnh của chương truyện
        # Lưu ý: Class name có thể thay đổi tùy theo cấu trúc web tại thời điểm bạn dùng
        images = soup.find_all('img', class_='lazy') 
        
        if not images:
            # Backup nếu không tìm thấy class 'lazy'
            images = soup.select(".chapter_content img")

        if not images:
            print("Không tìm thấy ảnh. Vui lòng kiểm tra lại cấu trúc HTML của trang web.")
            return

        # Tạo thư mục lưu truyện dựa trên tiêu đề (optional)
        folder_name = "Chapter_Download"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        print(f"Bắt đầu tải {len(images)} ảnh...")

        for i, img in enumerate(images, start=1):
            # Lấy link ảnh từ src hoặc data-src (thường web truyện dùng lazy load)
            img_url = img.get('data-src') or img.get('src')
            
            if not img_url:
                continue

            # Xử lý link ảnh nếu là link tương đối
            if img_url.startswith('//'):
                img_url = 'https:' + img_url

            # Tải ảnh
            img_data = requests.get(img_url, headers=headers).content
            
            # Định dạng tên file: "trang x.jpg"
            file_name = f"trang {i}.jpg"
            file_path = os.path.join(folder_name, file_name)

            with open(file_path, 'wb') as f:
                f.write(img_data)
            
            print(f"Đã tải xong: {file_name}")

        print("--- Hoàn thành! ---")

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")

# Thay link chương truyện bạn muốn tải vào đây
url_truyen = "https://truyenqqko.com/truyen-tranh/sekai-saikyou-no-majo-hajimemashita-watashidake-kouryaku-saito-wo-mireru-sekai-de-jiyuu-ni-ikimasu-23041-chap-1"
download_chapter(url_truyen)
