from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError
from bs4 import BeautifulSoup

class AntiBot:
    def __init__(self) -> None:
        self.rss_content: str | None = None
        
    def get_rss_content(self, url: str) -> str | None:
        self.rss_content = None
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, 
                args=[
                    "--disable-blink-features=AutomationControlled", 
                    "--no-sandbox"
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = context.new_page()

            page.on("response", self.handle_response(url))
            
            page.goto(url)
            
            try:
                robot_btn = page.get_by_text("robot")
                robot_btn.wait_for(state="visible", timeout=3000)
                robot_btn.click()
            except TimeoutError:
                pass
            
            try:
                page.wait_for_function("document.body.innerText.includes('<rss') || document.body.innerText.includes('<?xml')", timeout=3000)
            except Exception:
                print("RSS not found")
                return None
                
            page.wait_for_load_state("networkidle")
            
            browser.close()

            return self.rss_content
        
    def get_page(self, target_url) -> str:
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True, 
                args=[
                    "--disable-blink-features=AutomationControlled", 
                    "--no-sandbox"
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            page = context.new_page()

            page.goto(target_url)
            
            try:
                robot_btn = page.get_by_text("robot")
                robot_btn.wait_for(state="visible", timeout=3000)
                robot_btn.click()
            except Exception:
                pass
            
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            
            html_content = page.content()
            body_visible_text = page.inner_text("body")
            
            browser.close()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            def get_meta(tag_name, attrs_dict):
                found = soup.find(tag_name, attrs=attrs_dict)
                return found["content"] if found and "content" in found.attrs else ""

            meta_data = {
                "title": soup.title.string if soup.title else "",
                "og_title": get_meta("meta", {"property": "og:title"}),
                "og_description": get_meta("meta", {"property": "og:description"}),
                "twitter_card": get_meta("meta", {"name": "twitter:card"}),
                "twitter_description": get_meta("meta", {"name": "twitter:description"}),
            }

            return str(meta_data) + body_visible_text
        
            
    def handle_response(self, target_url):
        def handle_response(response):
            if target_url in response.url and response.status == 200:
                ctype = response.headers.get("content-type", "").lower()
                if "xml" in ctype: 
                    self.rss_content = response.text()
        
        return handle_response
