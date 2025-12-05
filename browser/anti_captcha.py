import asyncio
import math
import random
import time

from patchright.async_api import Page, TimeoutError
from pynput.mouse import Button, Controller


class AntiCloudflare:
    def __init__(self, page:Page):
        self.page = page
        self.mouse = Controller()
    
    async def check(self):
        # challenge = await self.page.query_selector('input[name="cf-turnstile-response"]')
        try:
            challenge = self.page.locator('input[name="cf-turnstile-response"]')
            await challenge.wait_for(state="attached")
        except TimeoutError:
            print("Captcha does not attach to dom.")
        
        if challenge:
            await asyncio.sleep(random.uniform(7.157, 9.97))
            challenge = await self.page.query_selector('input[name="cf-turnstile-response"]')
            if challenge:
                return True
        
        return False

    async def human_like_move(
        self, 
        x1:float, 
        y1:float, 
        x2:float, 
        y2:float, 
        duration:float=1.0, 
        steps:int=100
    ):
        """Moves mouse from (x1, y1) to (x2, y2) using sinusoidal easing"""
        for i in range(steps + 1):
            t = i / steps
            ease = 0.5 - 0.5 * math.cos(math.pi * t)  # Sinusoidal easing
            x = x1 + (x2 - x1) * ease
            y = y1 + (y2 - y1) * ease
            self.mouse.position = (int(x), int(y))
            time.sleep(duration / steps)
    
    async def bypass(self):

        try:
            elem = self.page.locator('input[name="cf-turnstile-response"]').locator('xpath=ancestor::div[@style]').first
            await elem.wait_for(state="attached")
        except TimeoutError:
            print("Captcha box element not prsent.")
        
        await elem.scroll_into_view_if_needed()
        rect = await elem.bounding_box()

        if not rect:
            print("Element not visible.")
            return

        # Get browser window position on the screen
        screen_x = await self.page.evaluate("() => window.screenX")
        screen_y = await self.page.evaluate("() => window.screenY")

        # Calculate screen-level coordinates
        target_x = screen_x + rect['x'] + 40 + random.randint(3, 7)
        target_y = screen_y + rect['y'] + 125 + random.randint(3, 7)

        # target_x, target_y = screen_coord_x, screen_coord_y
        start_x, start_y = self.mouse.position
        await self.human_like_move(start_x, start_y, target_x, target_y, duration=1.5)

        self.mouse.click(Button.left)
