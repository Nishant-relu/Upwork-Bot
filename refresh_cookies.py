"""Manually refresh cookies.

    python refresh_cookies.py            # every account except the worker
    python refresh_cookies.py muktesh    # just one account
"""
import asyncio, sys
from patchright.async_api import async_playwright
from browser.context import ContextHandler
from config import bot_settings, paths, constants

SKIP = {"shubham"}

if len(sys.argv) > 1:
    names = sys.argv[1:]
    unknown = [n for n in names if n not in bot_settings.USER_CONFIG]
    if unknown:
        print(f"Not found: {unknown}. Loaded users: {list(bot_settings.USER_CONFIG)}")
        sys.exit(1)
else:
    names = [n for n in bot_settings.USER_CONFIG if n not in SKIP]


async def refresh(pw, name: str) -> None:
    user = bot_settings.USER_CONFIG[name]
    browser = await pw.chromium.launch(channel="chrome", headless=False)
    try:
        handler = ContextHandler(browser, paths.COOKIES_DIR / f"{name}_cookies.json")
        page = await (await handler.create()).new_page()
        await page.goto(constants.UPWORK_LOGIN_URL)

        print(f"\n[{name}] Log in as {user.email} in the browser window.")
        answer = await asyncio.to_thread(
            input, "Once the dashboard loads, press Enter to save cookies (or 's' + Enter to skip): "
        )
        if answer.strip().lower() == "s":
            print(f"[{name}] Skipped — cookies not saved.")
            return

        await handler.destroy()  # writes storage_state to the cookies file
        print(f"[{name}] Cookies saved.")
    finally:
        await browser.close()


async def main():
    print(f"Refreshing cookies for: {', '.join(names)}")
    async with async_playwright() as pw:
        for name in names:
            try:
                await refresh(pw, name)
            except Exception as e:
                print(f"[{name}] FAILED: {e}")
    print("\nDone.")


asyncio.run(main())
