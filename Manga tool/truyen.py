import os
import cloudscraper
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm  # Thư viện làm thanh tiến trình
import re

# --- CẤU HÌNH ---
MAX_WORKERS = 3 
MAX_SLICE_HEIGHT = 1500 
IMG_QUALITY = 85
SCRAPER = cloudscraper.create_scraper()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://truyenqqko.com/"
}

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def download_and_process_chapter(chapter_url, chapter_name, main_folder, pbar):
    chapter_folder = clean_filename(chapter_name)
    chapter_path = os.path.join(main_folder, chapter_folder)
    
    if not os.path.exists(chapter_path):
        os.makedirs(chapter_path)
    else:
        if len(os.listdir(chapter_path)) > 0:
            pbar.update(1)
            return

    try:
        response = SCRAPER.get(chapter_url, headers=HEADERS, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.select(".chapter_content img") or soup.select(".story-see-content img")

        if images:
            img_counter = 1
            for img in images:
                img_url = img.get('data-original') or img.get('data-src') or img.get('src')
                if not img_url or "logo" in img_url.lower(): continue
                if img_url.startswith('//'): img_url = 'https:' + img_url

                try:
                    img_res = SCRAPER.get(img_url, headers=HEADERS, timeout=20)
                    img_data = Image.open(BytesIO(img_res.content))
                    if img_data.mode in ("RGBA", "P"): img_data = img_data.convert("RGB")
                    
                    width, height = img_data.size
                    if height > MAX_SLICE_HEIGHT:
                        for top in range(0, height, MAX_SLICE_HEIGHT):
                            bottom = min(top + MAX_SLICE_HEIGHT, height)
                            if (bottom - top) < 250 and top != 0: break
                            slice_img = img_data.crop((0, top, width, bottom))
                            slice_img.save(os.path.join(chapter_path, f"trang_{img_counter:03d}.jpg"), "JPEG", quality=IMG_QUALITY)
                            img_counter += 1
                    else:
                        img_data.save(os.path.join(chapter_path, f"trang_{img_counter:03d}.jpg"), "JPEG", quality=IMG_QUALITY)
                        img_counter += 1
                except: continue
        
        # Cập nhật thanh tiến trình sau khi xong 1 chương
        pbar.set_description(f"Done: {chapter_name[:20]}...")
        pbar.update(1)

    except Exception:
        pbar.update(1)

def get_comic_info(main_url):
    try:
        response = SCRAPER.get(main_url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        chapter_elements = soup.select(".works-chapter-item a") or soup.select(".list-chapters a")
        title_node = soup.select_one("h1")
        comic_title = clean_filename(title_node.text) if title_node else "Manga_Download"
        chapters = [{"url": f"https://truyenqqko.com{a['href']}" if a['href'].startswith('/') else a['href'], "name": a.text.strip()} for a in chapter_elements]
        return chapters[::-1], comic_title
    except: return [], ""

def main():
    print("\033[92m" + "=== TRUYENQQ ULTIMATE DOWNLOADER ===" + "\033[0m")
    url = input("Dán link truyện: ").strip()
    chapters, folder_name = get_comic_info(url)
    
    if not chapters:
        print("Lỗi link hoặc cấu trúc web!")
        return

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    print(f"\033[94mTruyện: {folder_name}\033[0m")
    print(f"\033[94mTổng số chương: {len(chapters)}\033[0m\n")

    # Khởi tạo thanh tiến trình chính
    with tqdm(total=len(chapters), unit="chap", bar_format="{l_bar}{bar:30}{r_bar}{bar:-10b}") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for chap in chapters:
                executor.submit(download_and_process_chapter, chap['url'], chap['name'], folder_name, pbar)

    print("\n\033[92m" + "--- TẢI HOÀN TẤT! ---" + "\033[0m")

if __name__ == "__main__":
    main()