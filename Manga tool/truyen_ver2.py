import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

def download_and_process(url, folder_name="Manga_Out"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://truyenqqko.com/"
    }

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    try:
        print(f"Đang kết nối đến: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Tìm các thẻ ảnh trong nội dung chương truyện
        # TruyệnQQ thường dùng class 'lazy' hoặc nằm trong div 'chapter_content'
        images = soup.find_all('img', class_='lazy') or soup.select(".chapter_content img")

        if not images:
            print("Không tìm thấy ảnh. Hãy kiểm tra lại đường dẫn!")
            return

        print(f"Tìm thấy {len(images)} dải ảnh. Đang xử lý...")

        img_counter = 1
        for i, img in enumerate(images, start=1):
            # Ưu tiên lấy link ảnh chất lượng cao nhất
            img_url = img.get('data-original') or img.get('data-src') or img.get('src')
            
            if not img_url or "logo" in img_url.lower():
                continue

            if img_url.startswith('//'):
                img_url = 'https:' + img_url

            # Tải dữ liệu ảnh vào bộ nhớ
            img_res = requests.get(img_url, headers=headers)
            img_data = Image.open(BytesIO(img_res.content))
            
            width, height = img_data.size
            
            # KIỂM TRA: Nếu ảnh quá dài (ví dụ cao > 2000px), tiến hành cắt nhỏ
            # Bạn có thể điều chỉnh con số 1500 tùy theo màn hình điện thoại của bạn
            max_slice_height = 1500 

            if height > max_slice_height:
                print(f"Dải ảnh {i} quá dài ({height}px), đang cắt nhỏ...")
                for top in range(0, height, max_slice_height):
                    bottom = min(top + max_slice_height, height)
                    
                    # Bỏ qua nếu mảnh cuối quá ngắn (dưới 200px)
                    if (bottom - top) < 200 and top != 0:
                        break
                        
                    box = (0, top, width, bottom)
                    slice_img = img_data.crop(box)
                    
                    file_name = f"trang_{img_counter:03d}.jpg"
                    slice_img.save(os.path.join(folder_name, file_name), "JPEG", quality=90)
                    img_counter += 1
            else:
                # Nếu ảnh ngắn sẵn thì lưu luôn
                file_name = f"trang_{img_counter:03d}.jpg"
                img_data.convert("RGB").save(os.path.join(folder_name, file_name), "JPEG", quality=90)
                img_counter += 1

            print(f"Đã xử lý xong cụm ảnh thứ {i}")

        print(f"\n--- THÀNH CÔNG ---")
        print(f"Ảnh đã được lưu vào thư mục: {os.path.abspath(folder_name)}")

    except Exception as e:
        print(f"Lỗi: {e}")

# Chỗ này dán link chương truyện bạn muốn tải
url_target = "https://truyenqqko.com/truyen-tranh/onii-chan-wa-oshimai-4029-chap-60"
download_and_process(url_target, folder_name="Truyen_Da_Tai")