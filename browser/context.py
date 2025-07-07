from patchright.async_api import Browser
from pathlib import Path

class ContextHandler:
    def __init__(self, browser:Browser, cookies_path:str|Path|None=None):
        self._context = None
        self._cookies_path = cookies_path
        self._browser = browser

    async def create(self):
        if not self._context:
            if not self._cookies_path.exists():
                cookies_path = None
            else:
                cookies_path = self._cookies_path
            
            self._context = await self._browser.new_context(storage_state=cookies_path)
        
        return self._context
    
    async def destroy(self):
        if self._context:
            await self._context.storage_state(path=self._cookies_path)
            await self._context.close()