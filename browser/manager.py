from config.paths import paths
from patchright.async_api import async_playwright


class PatchrightBrowser:
    def __init__(self, profile_name: str, proxy: dict|None = None):

        self.profile_dir = paths.USER_PROFILE_DIR / profile_name
        self.proxy = proxy
        self.context = None
        self.playwright = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        user_data_dir = self.profile_dir

        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=False,
            proxy=self.proxy,
            no_viewport=True
        )
        return self.context

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()

if __name__ == '__main__':

    import asyncio
    from utils.proxy import get_proxy

    url = "https://www.upwork.com/nx/search/jobs/?from_recent_search=true&per_page=20&q=scraping"
    ip_url = "https://ip.smartproxy.com/ip"

    async def main():
        name = "subham"
        proxy_dict = get_proxy(name)

        async with PatchrightBrowser(profile_name=name, proxy=proxy_dict) as context:
            page = context.pages[0]

            await page.goto(ip_url, wait_until="domcontentloaded")
            ip = await page.locator("body").text_content()
            print("IP: ", ip)

            await page.wait_for_timeout(300)

            await page.goto(url, wait_until="domcontentloaded")
            print("Page Title: ", await page.title())

            await page.wait_for_timeout(6000)
    
    asyncio.run(main())
