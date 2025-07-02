import asyncio
import math
import random
import time

from patchright.async_api import Page
from pynput.mouse import Button, Controller


class AntiCloudflare:
    def __init__(self, page:Page):
        self.page = page
        self.mouse = Controller()
    
    async def check(self):
        challenge = await self.page.query_selector("#MwRA1")
        if challenge:
            await asyncio.sleep(10)
            challenge = await self.page.query_selector("#MwRA1")
            if challenge:
                return True
        
        return False

    def human_like_move(self, x1, y1, x2, y2, duration=1.0, steps=100):
        """Moves mouse from (x1, y1) to (x2, y2) using sinusoidal easing"""
        for i in range(steps + 1):
            t = i / steps
            ease = 0.5 - 0.5 * math.cos(math.pi * t)  # Sinusoidal easing
            x = x1 + (x2 - x1) * ease
            y = y1 + (y2 - y1) * ease
            self.mouse.position = (int(x), int(y))
            time.sleep(duration / steps)
    
    def bypass(self):
        # target_x, target_y = random.randint(525, 545), random.randint(330,350)
        target_x, target_y = random.randint(410, 430), random.randint(320,340)
        start_x, start_y = self.mouse.position
        self.human_like_move(start_x, start_y, target_x, target_y, duration=1.5)
        self.mouse.click(Button.left)
