from playwright.async_api import async_playwright, Browser
from bs4 import BeautifulSoup
from html_to_markdown import convert
import pypdf
import io


class AntiBot:
    def __init__(self) -> None:
        self.playwright = None
        self.browser = None
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--headless=new",
                "--disable-blink-features=AutomationControlled", 
                "--no-sandbox",
                "--disable-http2", 
                "--dns-result-order=ipv4first",
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-features=IsolateOrigins,site-per-process"
            ],
            ignore_default_args=["--enable-automation"]
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    def _get_browser(self) -> Browser:
        return self.browser # type: ignore
    
    
        
    async def get_rss_content(self, url: str) -> str | None:
        context = await self._get_browser().new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = await context.new_page()
        
        rss_content = None
        async def handle_response(response):
            nonlocal rss_content
            try:
                if response.status == 200:
                    ctype = response.headers.get("content-type", "").lower()
                    if "xml" in ctype or "rss" in ctype: 
                        rss_content = await response.text()
            except:
                pass
        
        try:
            page.on("response", handle_response)
            await page.goto(url)
            
            try:
                robot_btn = page.get_by_text("robot")
                await robot_btn.wait_for(state="visible", timeout=3000)
                await robot_btn.click()
            except:
                pass
            
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=3000)
            except:
                pass
        finally:
            await page.close()
            await context.close()
            
        return rss_content


    async def get_page(self, url: str) -> str | None:        
        context = await self._get_browser().new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        await context.route("**/*", lambda route: route.abort() 
            if any(x in route.request.url for x in ["doubleclick", "adsystem", "analytics", "facebook", "twitter"]) 
            else route.continue_()
        )
        page = await context.new_page()
        
        try:
            await page.goto(url)
            
            try:
                robot_btn = page.get_by_text("robot")
                await robot_btn.wait_for(state="visible", timeout=3000)
                await robot_btn.click()
            except:
                pass
            
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=3000)
                html_content = await page.content()
                return convert(html_content)
            except:
                pass
        finally:
            await page.close()
            await context.close()
            
        return None
        
    # def get_page(self, target_url) -> str:
        
    #     with sync_playwright() as p:
    #         browser = p.chromium.launch(
    #             headless=True,
    #             args=[
    #                 "--headless=new", # The "new" headless mode (undetectable)
    #             "--disable-blink-features=AutomationControlled", 
    #             "--no-sandbox",
    #             "--disable-http2", 
    #             "--dns-result-order=ipv4first", # Fixes many DNS resolution errors
    #             "--window-size=1920,1080",
    #             "--start-maximized",
    #             "--disable-web-security", # Helps with CORS/Protocol errors
    #             "--disable-features=IsolateOrigins,site-per-process" # Helps with loading subframes
    #         ],
    #         ignore_default_args=["--enable-automation"] # Removes the "Chrome is being controlled by software" flag
    #         )
            
    #         context = browser.new_context(
    #             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    #             ignore_https_errors=True
    #         )
            
    #         context.route("**/*", lambda route: route.abort() 
    #             if any(x in route.request.url for x in ["doubleclick", "adsystem", "analytics", "facebook", "twitter"]) 
    #             else route.continue_()
    #         )
            
    #         context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    #         page = context.new_page()
            
    #         download_captured = None

    #         def on_download(download):
    #             nonlocal download_captured
    #             download_captured = download

    #         page.on("download", on_download)

    #         try:
    #             page.goto(target_url, timeout=5000, wait_until="domcontentloaded")
    #         except Exception as e:
    #             if "ERR_NAME_NOT_RESOLVED" in str(e):
    #                 print(f"Skipping {target_url}: Domain not found.")
    #                 browser.close()
    #                 raise Exception(e)
                
    #             if "Download is starting" not in str(e):
    #                 print(f"Navigation error: {e}")
    #                 raise Exception(e)

    #         if download_captured:
    #             print(f"Processing PDF in memory: {download_captured.suggested_filename}")
                
    #             stream = download_captured.create_read_stream()
    #             pdf_buffer = io.BytesIO()
    #             pdf_buffer.write(stream.read())
    #             pdf_buffer.seek(0)
                
    #             try:
    #                 reader = pypdf.PdfReader(pdf_buffer)
    #                 text_content = []
    #                 for page_num in range(len(reader.pages)):
    #                     text_content.append(reader.pages[page_num].extract_text())
                    
    #                 full_text = "\n".join(text_content)
    #                 meta_data = {"title": download_captured.suggested_filename, "type": "pdf"}
                    
    #                 browser.close()
    #                 return str(meta_data) + "\n" + full_text
    #             except Exception as e:
    #                 browser.close()
    #                 return f"Error reading PDF: {e}"
            
    #         try:
    #             robot_btn = page.get_by_text("robot")
    #             robot_btn.wait_for(state="visible", timeout=3000)
    #             robot_btn.click()
    #         except Exception:
    #             pass
            
    #         try:
    #             html_content = page.content()
    #             body_visible_text = page.inner_text("body")
    #             if not body_visible_text:
    #                 body_visible_text = page.evaluate("document.body.innerText")
    #         except:
    #             body_visible_text = ""
    #             html_content = ""
            
    #         browser.close()
            
    #         soup = BeautifulSoup(html_content, 'html.parser')
            
    #         def get_meta(tag_name, attrs_dict):
    #             found = soup.find(tag_name, attrs=attrs_dict)
    #             return found["content"] if found and "content" in found.attrs else ""

    #         meta_data = {
    #             "title": soup.title.string if soup.title else "",
    #             "og_title": get_meta("meta", {"property": "og:title"}),
    #             "og_description": get_meta("meta", {"property": "og:description"}),
    #             "twitter_card": get_meta("meta", {"name": "twitter:card"}),
    #             "twitter_description": get_meta("meta", {"name": "twitter:description"}),
    #         }

    #         return str(meta_data) + body_visible_text
        
