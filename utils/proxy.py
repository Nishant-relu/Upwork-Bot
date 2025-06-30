import logging
import traceback

import requests

from config.settings import settings
from utils.env import get_env

logger = logging.getLogger(__name__)


def get_proxy(name:str) -> dict|None:
    """
    Get proxy settings based on the user's name.
    """
    try:

        host = settings.PROXY_HOST
        port = settings.PROXY_PORT
        password = settings.PROXY_PASSWORD
        user = settings.PROXY_USER
        ip_env_var = f"{name.upper()}_IP"

        if not all([host, port, password, user]):
            raise ValueError("Missing essential proxy environment variables.")

        user_ip = get_env(ip_env_var)

        if not user_ip:
            raise ValueError(f"Missing IP environment variable for {name}.")

        proxy_user_with_ip = f"{user}-ip-{user_ip}"

        proxy = {
            "server": f"http://{host}:{port}",
            "username": proxy_user_with_ip,
            "password": password
        }

        logger.info(f"Generated proxy for {name}: {proxy}")

        return proxy
    except Exception as e:
        logger.error(f"Error getting proxy: {e}")
        logging.info(traceback.format_exc())
        return None


def check_proxy(proxy:str) -> bool:
    """Tests whether the given proxy is working by sending a request."""
    
    proxies = {
        'http': f"http://{proxy}",
        'https': f"https://{proxy}"
    }

    test_url = "https://ifconfig.me/"

    try:
        response = requests.get(test_url, proxies=proxies, timeout=10)
        print("Status code: ", response.status_code)
        if response.status_code == 200:
            logger.info(f"Proxy is working. Response: {response.text.strip()}")
            return True
        else:
            logger.warning(f"Proxy test failed with status code: {response.status_code}")
    except requests.exceptions.ProxyError as pe:
        logger.error(f"ProxyError: Failed to connect using proxy - {pe}")
        logging.info(traceback.format_exc())
    except requests.exceptions.ConnectTimeout:
        logger.error("Proxy connection timed out.")
        logging.info(traceback.format_exc())
    except requests.exceptions.RequestException as re:
        logger.error(f"RequestException during proxy test: {re}")
        logging.info(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error during proxy check: {e}")
        logging.info(traceback.format_exc())
    return False


if __name__ == "__main__":
    
    proxy_dict = get_proxy("muktesh")
    print(proxy_dict)
    server = proxy_dict.get("server").replace("http://", "")
    proxy = f"{proxy_dict["username"]}:{proxy_dict["password"]}@{server}"
    print("proxy: ", proxy)
    print(check_proxy(proxy))
