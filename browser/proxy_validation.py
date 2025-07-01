import logging
from patchright.async_api import Page
from config.constants import IP_CHECK_URL

logger = logging.getLogger(__name__)


async def get_proxy_ip(page:Page, timeout: int = 15) -> str | None:
    """
    Fetch the current public IP address as seen by the browser.
    """
    try:
        # await page.wait_for_timeout(timeout=timeout*100)
        await page.goto(IP_CHECK_URL, wait_until="domcontentloaded", timeout=timeout * 1000)
        ip: str | None = await page.locator("body").text_content()

        if ip:
            ip = ip.strip()
            if ip.count(".") == 3:
                logger.info(f"Retrieved proxy IP: {ip}")
                return ip
            else:
                logger.warning(f"Malformed IP response: '{ip}'")
        else:
            logger.warning("Empty response from IP check page.")
    except Exception as e:
        logger.warning(f"Failed to retrieve proxy IP from browser: {e}", exc_info=True)
        
    return None


async def validate_proxy_ip(page:Page, expected_ip:str, timeout: int = 15) -> None:
    """
     Validates whether the current IP matches the expected proxy IP.
    """

    actual_ip = await get_proxy_ip(page, timeout=timeout)
    if not actual_ip:
        raise ValueError("Proxy validation failed: No IP address retrieved.")

    actual_ip = actual_ip.strip()
    if actual_ip != expected_ip:
        raise ValueError(
            f"Proxy validation failed:\n"
            f"  Expected IP: {expected_ip}\n"
            f"  Actual IP:   {actual_ip}"
        )
    
    logger.info(f"Proxy IP validated successfully: {actual_ip}")
