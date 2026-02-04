from bs4 import BeautifulSoup
from upwork.selectors.proposals_page_selectors import ProposalSelectors
import logging


logger = logging.getLogger(__name__)


class ProposalsParser:

    @staticmethod
    def parse(html: str) -> list[dict[str, str|bool|None]]:
        """
        Extracts active proposals data from HTML.
        """

        proposals = []
        try:
            soup = BeautifulSoup(html, 'lxml')
            table_rows = soup.find_all(*ProposalSelectors.PROPOSAL_ROW_TAG)

            if not table_rows:
                logger.info("No submitted proposal rows found.")
                return proposals

            for row in table_rows:
                try:
                    job_cell = row.find(*ProposalSelectors.JOB_INFO_CELL_TAG)
                    link = job_cell.find(*ProposalSelectors.JOB_LINK_TAG) if job_cell else None

                    if not link:
                        logger.warning("No job link found.")
                        continue

                    job_title = link.text.strip()
                    url = link.get('href').strip()
                    job_id = url.split("/")[-1].strip()
                    job_url = f"https://www.upwork.com{url}".strip()

                    viewed_mark = row.find(*ProposalSelectors.VIEWED_MARK_TAG)
                    viewed_by_client = bool(viewed_mark)

                    proposals.append({
                        "job_id": job_id,
                        "job_title": job_title,
                        "job_url": job_url,
                        "viewed_by_client": viewed_by_client
                    })

                except Exception as e:
                    logger.warning(f"Failed parsing submitted proposal row: {e}", exc_info=True)

            logger.info(f"Extracted proposal data: {proposals}")
        except Exception as e:
            logger.error(f"Error parsing proposal section: {e}", exc_info=True)
        
        return proposals
