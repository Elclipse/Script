import asyncio
import os
import yt_dlp
from playwright.async_api import async_playwright

# --- HÀM TẢI VIDEO ---
def download_with_ytdlp_lib(m3u8_url, output_path):
    ydl_opts = {
        'final_ext': 'mp4',
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_path,
        'referer': 'https://animehay02.site/',
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'concurrent_fragment_downloads': 5,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([m3u8_url])

async def main():
    info_url = input("Link phim: ").strip()
    folder_name = input("Tên thư mục lưu: ").strip()

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # ĐƯỜNG DẪN BRAVE MẶC ĐỊNH TRÊN WINDOWS
    # Thử đường dẫn phổ biến nhất:
    brave_path = os.path.expandvars(r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe")
    if not os.path.exists(brave_path):
        # Nếu không thấy, thử đường dẫn trong Local AppData
        brave_path = os.path.expandvars(r"%LocalAppData%\BraveSoftware\Brave-Browser\Application\brave.exe")

    async with async_playwright() as p:
        print(f"[*] Đang khởi chạy Brave tại: {brave_path}")
        
        try:
            browser = await p.chromium.launch(
                executable_path=brave_path,
                headless=False # Hiện trình duyệt để vượt Cloudflare nếu cần
            )
        except Exception as e:
            print(f"[!] Không tìm thấy Brave. Lỗi: {e}")
            print("Hãy kiểm tra lại đường dẫn cài đặt Brave của bạn.")
            return

        context = await browser.new_context()
        page = await context.new_page()
        
        print("[*] Đang quét danh sách tập...")
        await page.goto(info_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        
        # Selector lấy link tập
        ep_links = await page.locator("a[href*='xem-phim']").evaluate_all("nodes => nodes.map(n => n.href)")
        ep_links = list(dict.fromkeys(ep_links))

        print(f"[+] Tìm thấy {len(ep_links)} tập.")

        for i, link in enumerate(ep_links):
            ep_num = i + 1
            file_path = os.path.join(folder_name, f"Tap_{ep_num:02d}.mp4")

            if os.path.exists(file_path):
                continue

            print(f"\n>>> Đang lấy link m3u8 tập {ep_num}...")
            
            temp_page = await context.new_page()
            m3u8_url = None
            
            def handle_request(request):
                nonlocal m3u8_url
                if ".m3u8" in request.url and not m3u8_url:
                    m3u8_url = request.url
            
            temp_page.on("request", handle_request)
            try:
                await temp_page.goto(link, wait_until="networkidle", timeout=60000)
                await temp_page.wait_for_timeout(5000)
            except: pass
            
            await temp_page.close()

            if m3u8_url:
                download_with_ytdlp_lib(m3u8_url, file_path)
            else:
                print(f"[!] Không tìm thấy link cho tập {ep_num}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
