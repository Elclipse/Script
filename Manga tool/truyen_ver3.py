import os
import cloudscraper
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
import re

# --- CẤU HÌNH ---
MAX_WORKERS = 3 # Giảm xuống 3 để tránh bị web nghi ngờ
MAX_SLICE_HEIGHT = 1500 
# Khởi tạo scraper thay cho requests
scraper = cloudscraper.create_scraper() 

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3",
    "Referer": "https://truyenqqko.com/"
}

def download_and_process_chapter(chapter_url, chapter_name, main_folder):
    chapter_name = re.sub(r'[\\/*?:"<>|]', "", chapter_name).strip()
    chapter_path = os.path.join(main_folder, chapter_name)
    
    if not os.path.exists(chapter_path):
        os.makedirs(chapter_path)
    else:
        print(f"[*] {chapter_name} đã tồn tại.")
        return

    try:
        # Sử dụng scraper thay vì requests
        response = scraper.get(chapter_url, headers=BASE_HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm tất cả ảnh trong nội dung chương
        images = soup.select(".chapter_content img") or soup.select(".story-see-content img")

        if not images:
            print(f"[!] Không thấy ảnh ở {chapter_name}. (Có thể bị Cloudflare chặn)")
            return

        print(f"[>] Đang tải {chapter_name}...")
        img_counter = 1
        
        for i, img in enumerate(images):
            img_url = img.get('data-original') or img.get('data-src') or img.get('src')
            if not img_url or "logo" in img_url.lower(): continue
            if img_url.startswith('//'): img_url = 'https:' + img_url

            try:
                img_res = scraper.get(img_url, headers=BASE_HEADERS, timeout=20)
                img_data = Image.open(BytesIO(img_res.content))
                if img_data.mode in ("RGBA", "P"):
                    img_data = img_data.convert("RGB")
                
                width, height = img_data.size

                if height > MAX_SLICE_HEIGHT:
                    for top in range(0, height, MAX_SLICE_HEIGHT):
                        bottom = min(top + MAX_SLICE_HEIGHT, height)
                        if (bottom - top) < 250 and top != 0: break
                        slice_img = img_data.crop((0, top, width, bottom))
                        slice_img.save(os.path.join(chapter_path, f"trang_{img_counter:03d}.jpg"), "JPEG", quality=85)
                        img_counter += 1
                else:
                    img_data.save(os.path.join(chapter_path, f"trang_{img_counter:03d}.jpg"), "JPEG", quality=85)
                    img_counter += 1
            except: continue
                
        print(f"[OK] Xong: {chapter_name}")

    except Exception as e:
        print(f"[Lỗi] {chapter_name}: {e}")

def get_all_chapters(main_url):
    try:
        response = scraper.get(main_url, headers=BASE_HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Selector mới nhất cho truyenqqko
        # Danh sách chương nằm trong class 'works-chapter-item' hoặc 'list-chapters'
        chapter_links = soup.select(".works-chapter-item a") or soup.select(".list-chapters a")
        
        title_node = soup.select_one("h1")
        comic_title = title_node.text.strip() if title_node else "Truyen_Tai_Ve"
        comic_title = re.sub(r'[\\/*?:"<>|]', "", comic_title).strip()
        
        chapters = []
        for a in chapter_links:
            href = a['href']
            if href.startswith('/'):
                href = f"https://truyenqqko.com{href}"
            chapters.append({"url": href, "name": a.text.strip()})
        
        return chapters[::-1], comic_title
    except Exception as e:
        print(f"Lỗi khi quét danh sách: {e}")
        return [], ""

def main():
    print("--- TRUYENQQ BATCH DOWNLOADER (CLOUDFLARE BYPASS) ---")
    url = input("Nhập link truyện: ").strip()
    
    chapters, folder_name = get_all_chapters(url)
    
    if not chapters:
        print("Vẫn không tìm thấy chương. Trang web có thể đang dùng bảo mật quá cao.")
        return

    print(f"Tìm thấy {len(chapters)} chương. Bắt đầu tải vào thư mục: {folder_name}")
    
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for chap in chapters:
            executor.submit(download_and_process_chapter, chap['url'], chap['name'], folder_name)

if __name__ == "__main__":
    main()