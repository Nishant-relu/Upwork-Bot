"""Manually refresh cookies for one account:  python refresh_cookies.py muktesh"""
import asyncio, sys
from patchright.async_api import async_playwright
from browser.context import ContextHandler
from config import bot_settings, paths, constants
from utils.proxy import get_proxy

name = sys.argv[1]
user = bot_settings.USER_CONFIG.get(name)
if user is None:
    print(f"'{name}' not found. Loaded users: {list(bot_settings.USER_CONFIG.keys())}")
    sys.exit(1)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel="chrome", headless=False)  # no proxy: local IP is blacklisted on this Bright Data zone
        handler = ContextHandler(browser, paths.COOKIES_DIR / f"{name}_cookies.json")
        page = await (await handler.create()).new_page()
        await page.goto(constants.UPWORK_LOGIN_URL)

        print(f"\nLog in as {user.email} in the browser window.")
        await asyncio.to_thread(input, "Once the dashboard loads, press Enter here to save cookies...")

        await handler.destroy()  # writes storage_state to the cookies file
        await browser.close()
        print("Cookies saved.")


asyncio.run(main())
