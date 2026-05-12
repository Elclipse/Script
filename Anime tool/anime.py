import asyncio
import os
import yt_dlp
from playwright.async_api import async_playwright

# --- HÀM TẢI VIDEO DÙNG THƯ VIỆN YT-DLP ---
def download_with_ytdlp_lib(m3u8_url, output_path):
    ydl_opts = {
        'final_ext': 'mp4',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'referer': 'https://animehay02.site/',
        'nocheckcertificate': True,
        'quiet': False, # Để False để thấy tiến trình tải
        'no_warnings': False,
        # Giả lập trình duyệt để tránh bị đơ/chặn
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'http_headers': {
            'Origin': 'https://animehay02.site',
            'Referer': 'https://animehay02.site/',
        },
        'concurrent_fragment_downloads': 5, # Tải đa luồng cho nhanh
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[*] Đang tải xuống...")
            ydl.download([m3u8_url])
    except Exception as e:
        print(f"[!] Lỗi tải: {e}")

async def get_m3u8(browser, ep_url):
    context = await browser.new_context()
    page = await context.new_page()
    m3u8_url = None

    def handle_request(request):
        nonlocal m3u8_url
        if ".m3u8" in request.url and not m3u8_url:
            m3u8_url = request.url

    page.on("request", handle_request)
    try:
        await page.goto(ep_url, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000) 
    except:
        pass
    await context.close()
    return m3u8_url

async def main():
    info_url = input("Link phim: ").strip()
    folder_name = input("Thư mục lưu: ").strip()

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, executable_path='/usr/bin/chromium')
        page = await browser.new_page()
        
        print("[*] Đang lấy danh sách tập...")
        await page.goto(info_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Selector lấy link tập
        ep_links = await page.locator("a[href*='xem-phim']").evaluate_all("nodes => nodes.map(n => n.href)")
        ep_links = list(dict.fromkeys(ep_links)) # Lọc trùng

        print(f"[+] Tìm thấy {len(ep_links)} tập.")

        for i, link in enumerate(ep_links):
            ep_num = i + 1
            file_path = os.path.join(folder_name, f"Tap_{ep_num:02d}.mp4")

            if os.path.exists(file_path):
                continue

            print(f"\n>>> Đang xử lý tập {ep_num}...")
            m3u8 = await get_m3u8(browser, link)
            
            if m3u8:
                # Gọi hàm tải bằng thư viện
                download_with_ytdlp_lib(m3u8, file_path)
            else:
                print(f"[!] Không tìm thấy link m3u8 tập {ep_num}")

        await browser.close()
        print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())