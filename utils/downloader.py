import logging
import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from curl_cffi import requests

from config.paths import paths


logger = logging.getLogger(__name__)


def download_file(url:str, directory:Path|str|None=None) -> Path:
    """
    Downloads a file from the given URL and saves it with its original filename.
    """

    logger.info(f"Starting download from URL: {url}")
    try:
        if not url or not url.strip():
            logger.error("Empty URL provided")
            raise ValueError("URL cannot be empty")
        
        if directory is None:
            directory = paths.ATTACHMENTS_DIR
        
        if isinstance(directory, str):
            directory = Path(directory)
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Using directory: {directory}")
        
        response = requests.get(url, stream=True, impersonate="chrome")
        response.raise_for_status()
        logger.info(f"Response received with status code: {response.status_code}")

        filename = None
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            logger.info(f"Found Content-Disposition header: {content_disposition}")

            parts = content_disposition.split(';')
            for part in parts:
                if 'filename=' in part:
                    filename = part.split('filename=')[1].strip(' "\'')
                    logger.info(f"Filename from Content-Disposition: {filename}")
                    break
        
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(unquote(parsed_url.path))
            logger.info(f"Filename from URL: {filename}")
        
        if not filename:
            filename = 'downloaded_file.pdf'
            logger.info(f"Default Filename: {filename}")
        
        file_path = directory / filename
        
        # Save the file
        with open(file_path, 'wb') as f:
            logger.info(f"Saving to file path: {file_path}")
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info(f"File successfully downloaded: {file_path}")      
        return file_path
    
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"Error downloading file: {str(e)}")
    except IOError as e:
        raise IOError(f"Error saving file: {str(e)}")
    except Exception as e:
        raise Exception(f"Unexpected error: {str(e)}")


if __name__ == '__main__':
    url = ""

    filepath = download_file(url=url)

    print(f"File saved at {filepath}")
