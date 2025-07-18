import json
import logging
import mimetypes
import traceback
from pathlib import Path

import requests

from config import constants

logger = logging.getLogger(__name__)


def prepare_payload(job_data: dict) -> dict:
    """Prepare the payload for the proposal generation API."""
    return {
        "job_description": job_data.get("description", ""),
        "custom_questions": json.dumps(job_data.get("questions", [])) 
    }


def prepare_file_upload(attachment_path: Path):
    """
    Prepares the file upload data for a multipart/form-data request.
    """
    try:
        
        if not isinstance(attachment_path, Path):
            attachment_path = Path(attachment_path)
        
        mime_type, _ = mimetypes.guess_type(attachment_path)
        mime_type = mime_type or 'application/octet-stream'
        file_data = open(attachment_path, 'rb')
        files = {
            'file': (attachment_path.name, file_data, mime_type)
        }
        logger.info(f"Including file in request: {attachment_path.name}")
        logger.info(f"File : {files}")
        return files, file_data

    except FileNotFoundError:
        logger.error(f"File not found: {attachment_path}")
    except Exception as e:
        logger.error(f"Error preparing file: {e}")
        logger.info(traceback.format_exc())

    return None, None


def generate_proposal(job_data:dict, attachment_path:Path|None=None, url:str|None = None) -> dict|None:

    target_url = url or constants.PROPOSAL_API_URL
    payload = prepare_payload(job_data)
    logger.info(f"Payload generated for API: {payload}")

    files = None
    file_data = None

    if attachment_path:
        files, file_data = prepare_file_upload(attachment_path)
        if files is None:
            return None

    try:    
        logger.info(f"Sending POST request to {target_url}")
        response = requests.post(target_url, data=payload, files=files)
        
        response.raise_for_status()
        logger.info(f"Response received with status code: {response.status_code}")
        
        if response.ok:
            logger.info("Proposal generated successfully.")
        
            logger.info(f"API Response: {response.json()}")
            return response.json()
        else:
            logger.info("Failed to generte proposal.")
            return None

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        logger.info(traceback.format_exc())
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request failed: {req_err}")
        logger.info(traceback.format_exc())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.info(traceback.format_exc())
    finally:
        if file_data:
            file_data.close()
    
    return None


if __name__ == '__main__':
    from config import configure_logging

    configure_logging()
    
    data = {'title': 'We are looking for a developer or team to build an AI-powered solution that parses vehicle listings from dealership websites and engages customers through SMS and a website chatbot. The tool should extract key vehicle details like price, mileage, and model from frequently updated inventory pages. An AI assistant will naturally handle customer queries, gather lead information, schedule test drives via Google Calendar, and assist with financing. The solution must support both SMS and web chatbot interfaces, follow up with non-responsive leads, and be powered by flexible LLM backends. The project will follow a milestone-based delivery with a fast-tracked MVP timeline.\n\n\nTimeline:\no Project start: ASAP\no MVP completion: Within 1–2 weeks from start\no Full deployment: 2–3 weeks\n\nExpectations and Requirements:\no YOU MUST HAVE PRIOR EXPERIENCE developing similar applications that include:\no Website data scraping (especially for automotive or listing-style sites)\no AI-powered chatbot or conversational agents and SMS-based interaction flows\n\no In your application:\no You must provide examples of similar projects you’ve completed\no Be ready to demonstrate such applications during the interview/call (demo links, screen share, etc.)\n\no You must show a working demo of similar projects you have already done.\no The project will be strictly milestone-based as outlined above. Each milestone will be approved before moving on to the next.\n\n\nSee the attached document for the full scope.', 
            'questions': ["Have you previously built an AI-powered chatbot or SMS interaction tool? Please describe the project and share any relevant links or screenshots.","Have you worked on web scraping for vehicle listings or other similar dynamically updated websites? Share details and technologies used.","Which AI tools did you use in the past that provide multiple LLMs?","What technologies, languages, and frameworks do you plan to use for this project?","Can you commit to our timeline of 1–2 weeks for MVP delivery and 2–3 weeks for full deployment?"]}
    # filepath = Path('downloads/AI_Vehicle_Chatbot_Job_Posting.docx')
    print(generate_proposal(data))