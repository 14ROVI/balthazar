from playwright.async_api import async_playwright, Browser
from html_to_markdown import convert
import asyncio


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
                "--start-maximized"
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
        if self.browser is None:
            raise Exception("Browser not initialised. use `async with AntiBot() as antibot:`")
        return self.browser
    
    
        
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


async def main():    
    async with AntiBot() as antibot:
        a = await antibot.get_rss_content("https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=&company=&dateb=&owner=include&start=0&count=40&output=atom")
        print(a)


if __name__ == "__main__":
    asyncio.run(main())