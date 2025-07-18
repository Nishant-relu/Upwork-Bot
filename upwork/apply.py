import logging
import random
from enum import Enum

from bs4 import BeautifulSoup
from patchright.async_api import Page

from browser import dismiss_cookies_popup, handle_captcha
from config import bot_settings
from utils import download_file, format_price, generate_proposal

logger = logging.getLogger(__name__)


class ProposalTypeXPath(Enum):
    FREELANCER = '//label[contains(., "As a freelancer")]'
    AGENCY = '//label[contains(., "As an agency member")]'


class UpworkJobApplication:
    """
    Automates the process of applying for jobs on Upwork using a Selenium-based browser.
    """
    def __init__(self, page:Page):
        """
        Initialize with a SeleniumBase browser instance.
        """
        self.page = page
    
    async def _fetch_page(self, url: str) -> bool | None:
        """Fetch page from the given URL with retry logic."""

        for attempt in range(1, bot_settings.MAX_RETRY+1):
            try:

                await self.page.goto(url, wait_until="domcontentloaded")

                if await handle_captcha(self.page):
                    await dismiss_cookies_popup(self.page)
                    return True
                
                wait_time = random.uniform(3.7, 5.93) + attempt
                logger.info(f"Retrying in {wait_time} seconds.")
                await self.page.wait_for_timeout(wait_time * 1000)
            
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}: Error fetching page - {e}", exc_info=True)
                await self.page.wait_for_timeout(random.uniform(3.7, 5.93) * 1000)
        
        logger.error("Max retries exceeded while trying to fetch the page.")
        return None
    
    async def extract_job_details(self, html:str) -> dict:
        """
        Extract job title, description, and custom questions from the HTML source.
        """
        try:
            logger.info("Extracting job details...")
            soup = BeautifulSoup(html, 'lxml')
            details = {}

            job_details_section = soup.find('div', class_='fe-job-details')
            if job_details_section:
                title = job_details_section.find('h3')
                description = job_details_section.find('span', {'id': 'air3-truncation-1'})
                details['title'] = title.text if title else ""
                details['description'] = description.text if description else ""
            
            question_section = soup.find('div', class_="fe-proposal-job-questions")
            if question_section:
                forms = question_section.find_all('div', class_='form-group')
                details['questions'] = [form.text.strip() for form in forms if form.text]
            else:
                details['questions'] = []
            
            logger.info(f"Job details extracted: {details}")
            return details
        except Exception as e:
            logger.error(f"Error extracting job details: {e}", exc_info=True)
            return {}
    
    async def get_job_details(self) -> dict:
        """
        Extract job details from the current page.
        """
        try:

            trunc_toggle_xpath = '//button[@data-ev-label="truncation_toggle"]'
            toggle_btn = self.page.locator(trunc_toggle_xpath)

            if await toggle_btn.is_visible(timeout=15000):
                await toggle_btn.scroll_into_view_if_needed()
                await toggle_btn.click(timeout=15000)
                await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

            html = await self.page.content()
            return await self.extract_job_details(html)
        except Exception as e:
            logger.error(f"Failed to get job details: {e}", exc_info=True)
            return {}
    
    async def fill_cover_letter(self, cover_letter:str) -> None:
        """
        Fill out the cover letter on the job application form.
        """
        try:
            logger.info("Filling cover letter....")
            # cover letter
            cover_letter_selector = '//textarea[@aria-labelledby="cover_letter_label"]'
            textarea = self.page.locator(cover_letter_selector)

            await textarea.wait_for(timeout=10000)
            await textarea.scroll_into_view_if_needed()
            await textarea.click(timeout=10000)
            await textarea.fill(cover_letter)
            await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

            logger.info("Filled cover letter Successfully.")
        except Exception as e:
            logger.warning(f"Failed to fill cover letter: {e}", exc_info=True)
    
    async def verify_dropdown_value(self, selector:str, expected_value:str) -> bool:
        """
        Check if dropdown has the expected selected value.
        """
        try:
            logger.info(f"Checking if dropdown is set to '{expected_value}'...")

            await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

            element = self.page.locator(selector)
            await element.wait_for(timeout=15000)

            selected_value = await element.text_content() or ""
            selected_value = selected_value.strip()

            if expected_value.lower() in selected_value.lower():
                logger.info(f'Dropdown value is set to "{expected_value}" successfully.')
                return True
            else:
                logger.info(f'Failed to set dropdown value to "{expected_value}". Found: "{selected_value}".')
                return False
        except Exception as e:
            logger.error(f"Dropdown verification error: {e}", exc_info=True)
            return False
    
    async def handle_consent_form(self) -> None:
        """
        Accept the "Understand and Agree" consent form if present.
        """
        try:
            logger.info("Handling consent form...")

            modal_selector = 'h2.air3-modal-title'
            modal = self.page.locator(modal_selector)

            if not await modal.is_visible(timeout=15000):
                logger.info("Consent form modal not found. Skipping consent form submission.")
                return

            logger.info("Found consent form modal. Proceeding with the submit process.")
            

            checkbox_xpath = '//label[@data-test="understand-and-agree"]//span[@data-test="checkbox-input"]'
            checkbox = self.page.locator(checkbox_xpath)
            await checkbox.click(timeout=10000)

            await self.page.wait_for_timeout(random.uniform(2.7, 3.93)*1000)
            
            continue_button_selector = 'button[data-ev-label="fixed_price_confirmation_continue"]'
            continue_button = self.page.locator(continue_button_selector)
            await continue_button.click(timeout=10000)

            await self.page.wait_for_timeout(random.uniform(7.7, 9.93)*1000)
            logger.info('Clicked "I Understand" checkbox and submitted.')
        except Exception as e:
            logger.error(f"Error handling consent form: {e}", exc_info=True)

    async def set_proposal_type(self) -> None:
        """
        Selects the proposal type (Freelancer or Agency).
        """
        try:
            proposal_type = bot_settings.PROPOSAL_TYPE.value.upper()

            logger.info(f"Setting proposal type to {proposal_type}")
            proposal_type_xpath = ProposalTypeXPath[proposal_type].value
            await self.page.wait_for_timeout(random.uniform(5.7, 8.9)*1000)

            checkbox = self.page.locator(proposal_type_xpath)
            if await checkbox.is_visible(timeout=15000):
                logger.info("Found Check box with proposals.")
                await checkbox.wait_for(timeout=10000)
                await checkbox.click(button="left", timeout=10000)
                await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)
                logger.info(f"Proposal type '{proposal_type}' selected.")
            else:
                logger.info("Proposal type selection checkbox not available.")
        except Exception as e:
            logger.error(f"Error setting proposal type: {e}", exc_info=True)
    
    async def fill_answers(self, answers:dict) -> None:
        """
        Fill out custom job questions with provided answers.
        """
        try:
            logger.info("Started filling answers for questions.")

            textarea_locator = '//div[@class="fe-proposal-job-questions questions-area"]/div[contains(@class, "form-group")]//textarea[contains(@class, "air3-textarea")]'
            textareas = self.page.locator(textarea_locator)
            count = await textareas.count()

            for i in range(count):
                question_index = i + 1
                question_label_selector = f'div.questions-area .form-group:nth-of-type({question_index}) > label'
                question_label = self.page.locator(question_label_selector)

                try:
                    question = await question_label.text_content() or "[Label missing]"
                except:
                    question = "[Label fetch error]"

                answer = answers.get(str(question_index))

                if answer:
                    logger.info(f"Q{question_index} : {question.strip()}")
                    logger.info(f"A{question_index} : {answer.strip()}")

                    textarea = textareas.nth(i)
                    await textarea.scroll_into_view_if_needed()
                    await textarea.click()
                    await textarea.fill(answer)
                    await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)
                else:
                    logger.info(f"Answer missing for Q{question_index}: {question}")

        except Exception as e:
            logger.error(f"Error filling custom question answers: {e}", exc_info=True)
    
    async def handle_questions(self, answers:dict) -> None:
        try:
            questions_selector = '//div[@class="fe-proposal-job-questions questions-area"]/div[contains(@class, "form-group")]'
            questions_locator = self.page.locator(questions_selector)
            
            count = await questions_locator.count()

            if count > 0:
                logger.info("Found custom questions on the page.")
                await self.fill_answers(answers)
            else:
                logger.info("There were no custom questions.")
            
        except Exception as e:
            logger.error(f"Error while handling question sections: {e}", exc_info=True)
    
    async def verify_apply(self) -> bool:
        """
        Verify proposal submission
        """
        try:
            logger.info("Verifying successful submission of form.")

            submit_alert_selector = 'div.air3-alert-positive .air3-alert-content > p'
            edit_proposal_btn_selector = 'button[data-test="edit-proposal"]'

            alert_visible = await self.page.locator(submit_alert_selector).is_visible(timeout=15000)
            edit_btn_visible = await self.page.locator(edit_proposal_btn_selector).is_visible(timeout=15000)

            if alert_visible or edit_btn_visible:
                logger.info("Proposal submitted successfully.")
                return True
            else:
                logger.warning("Failed to submit proposal.")
                return False

        except Exception as e:
            logger.error(f"Failed to verify application successful apply: {e}", exc_info=True)
            return False

    async def handle_hourly_rate_form(self, hourly_rate:float, cover_letter:str, answers:dict) -> bool:
        """
        Fill and submit the hourly-rate-based job application form.
        """

        try:
            logger.info(f"Filling hourly rate form: ${hourly_rate}")

            # find hourly rate input field
            input_selector = '//*[@id="step-rate"]'
            rate_input = self.page.locator(input_selector)
            await rate_input.scroll_into_view_if_needed()
            await rate_input.click()
            await rate_input.fill(str(hourly_rate))
            await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

            dropdown_selector = "//div[contains(@class, 'air3-dropdown-toggle has-title')]"
            for _ in range(1, bot_settings.MAX_RETRY + 1):
                dropdown = self.page.locator(dropdown_selector).first
                await dropdown.scroll_into_view_if_needed()
                await dropdown.click()
                await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

                dropdown_item = self.page.locator('//*[@id="dropdown-menu"]/li[1]/span')
                await dropdown_item.click()

                selected_value_selector = "div.fe-proposal-job-terms div.air3-dropdown-toggle.is-selected span.air3-dropdown-toggle-label"

                if await self.verify_dropdown_value(selected_value_selector, "Never"):
                    break
            
            # cover letter
            await self.fill_cover_letter(cover_letter)

            # fill question answers if available
            await self.handle_questions(answers)
            
            submit_selector = 'div.fe-apply-footer-controls > button:first-of-type'
            submit_button = self.page.locator(submit_selector)
            await submit_button.scroll_into_view_if_needed()
            await submit_button.click()
            await self.page.wait_for_timeout(random.uniform(7.7, 9.93)*1000)

            return await self.verify_apply()
        except Exception as e:
            logger.error(f"Error filling hourly rate form: {e}", exc_info=True)
            return False
    
    async def handle_bid_form(self, cover_letter:str, answers:dict, bid_price:float|None=None) -> bool:
        """
        Fill and submit bid based job application form
        """
        try:
            logger.info("Filling project bid based form...")

            # get fixed price
            if not bid_price:
                price_selector = '//li[.//div[@data-cy="fixed-price"]]/div/strong'
                fixed_price_txt = await self.page.locator(price_selector).text_content()
                if fixed_price_txt:
                    bid_price = await format_price(fixed_price_txt.replace("$", "").strip())
                    logger.info(f"Fixed price extracted: {bid_price}")
                else:
                    bid_price = None
            
            fixed_price = bid_price or 300

            # type fixed price in the input
            amount_input_selector = '//*[@id="charged-amount-id"]'
            input_el = self.page.locator(amount_input_selector)
            await input_el.scroll_into_view_if_needed()
            await input_el.click()
            await input_el.fill(str(fixed_price))
            await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

            dropdown_selector = "//div[contains(@class, 'air3-dropdown-toggle has-title')]"
            for _ in range(1, bot_settings.MAX_RETRY + 1):
                dropdown = self.page.locator(dropdown_selector).first
                await dropdown.scroll_into_view_if_needed()
                await dropdown.click()
                await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

                option_selector = '//ul[@id="dropdown-menu"]//li[.//span[text()[normalize-space()="Less than 1 month"]]]'
                option = self.page.locator(option_selector)
                await option.scroll_into_view_if_needed()
                await option.click()
                await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

                selected_value_selector = 'div[aria-labelledby="duration-label"] span'
                if await self.verify_dropdown_value(selected_value_selector, "Less than 1 month"):
                    break

            # Fill cover letter
            await self.fill_cover_letter(cover_letter)

            # fill question answers if available
            await self.handle_questions(answers)
            
            submit_btn_selector = 'div.fe-apply-footer-controls > button:first-of-type'
            submit_btn = self.page.locator(submit_btn_selector)
            await submit_btn.scroll_into_view_if_needed()
            await submit_btn.click()
            await self.page.wait_for_timeout(random.uniform(7.7, 9.93)*1000)

            await self.handle_consent_form()

            return await self.verify_apply()
        except Exception as e:
            logger.error(f"Error filling milestone form: {e}", exc_info=True)
            return False

    async def handle_project_milestone_form(self, cover_letter:str, answers:dict, bid_price:float|None=None) -> bool:
        """
        Fill and submit the milestone/project-based job application form.
        """
        try:
            logger.info("Filling project milestone form...")

            # click By Project
            milestone_selector = '//*[@id="milestoneMode"]/label[2]/span'
            el = self.page.locator(milestone_selector)
            await el.scroll_into_view_if_needed()
            await el.click()
            await self.page.wait_for_timeout(random.uniform(1.7, 2.93)*1000)

            return await self.handle_bid_form(cover_letter, answers, bid_price)
        except Exception as e:
            logger.error(f"Error filling milestone form: {e}", exc_info=True)
            return False
    
    async def fill_form(self, hourly_rate:float, cover_letter:str, answers:dict, bid_price:int|None=None) -> bool:
        """
        Decide which form is present and fill accordingly.
        """
        try:

            if await self.page.locator("#step-rate").is_visible():
                logger.info("Form with Hourly Rate detected. Proceeding to fill the form.")
                return await self.handle_hourly_rate_form(hourly_rate, cover_letter, answers)

            elif await self.page.locator("#milestoneMode").is_visible():
                logger.info("Form with project milestone detected. Proceeding to fill the form.")
                return await self.handle_project_milestone_form(cover_letter, answers, bid_price)

            elif await self.page.locator("#charged-amount-id").is_visible():
                logger.info("Form with bid detected. Proceeding to fill the form.")
                return await self.handle_bid_form(cover_letter, answers, bid_price)

            else:
                logger.warning("Could not identify job form structure.")
                return False
            
        except Exception as e:
            logger.error(f"Error filling job form: {e}", exc_info=True)
            return False
    
    async def job_apply(
            self, 
            url:str, 
            name:str,  
            attachment_link:str|None=None, 
            project_bid_amount:float|None=None
    ) -> bool:
        """
        Main method to apply for a job.
        """

        try:
            if attachment_link is not None:
                attachment_file_path = download_file(attachment_link)
            else:
                attachment_file_path = None
            
            logger.info(f"Opening Job Link: {url}")
            await self._fetch_page(url)
            
            await self.set_proposal_type()

            job_details = await self.get_job_details()
            if not bool(job_details):
                return False
            
            proposal = generate_proposal(job_details, attachment_file_path)
            if not proposal:
                logger.info("Failed to generate proposal. Exiting apply process.")
                return False

            relevant_job = proposal.get("relevant_job", False)
            if not relevant_job:
                logger.info("Job is not relevant. Exititng apply process.")
                return False
            
            answers = proposal.get("question_answers", {})
            cover_letter = proposal.get("response", "")

            hourly_rate = bot_settings.HOURLY_RATE.get_by_name(name)

            applied_successfully = await self.fill_form(hourly_rate, cover_letter, answers, project_bid_amount)
            await self.page.wait_for_timeout(random.uniform(2.91, 3.53)*1000)

            if applied_successfully:
                logger.info(f"Successfully submitted proposal for {url}")
                return True
            else:
                logger.info(f"Failed to submit proposal for {url}")
                return False
        except Exception as e:
            logger.error(f"Job application failed for {url}: {e}")
            return False


if __name__ == '__main__':

    import asyncio

    from .auth import UpworkLoginManager

    from browser import PatchrightBrowser
    from config import configure_logging
    from utils import get_proxy

    configure_logging()

    name = "naman"
    proxy = get_proxy(name)
    url = "https://www.upwork.com/nx/proposals/job/~021941429189394944676/apply/"

    async def main():
        async with PatchrightBrowser(profile_name=name, proxy=proxy) as context:
            page = context.pages[0]
            manager = UpworkLoginManager(page)
            await manager.validate_or_login(account_name=name)

            applicator = UpworkJobApplication(page)
            await applicator.job_apply(url=url, name=name)
    
    asyncio.run(main())
