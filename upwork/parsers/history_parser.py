import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup


class ClientHistoryParser:
    """Parses the "Client's recent history" panel on a job detail page, and the
    title/description/skills/activity of an individual history job's own page."""

    HISTORY_SECTION = 'section[data-cy="jobs"]'
    HISTORY_ITEM = 'div[data-cy="job"]'

    _FREELANCER_ID_RE = re.compile(r"~[0-9a-z]+", re.I)

    @staticmethod
    def _row_freelancer(item) -> dict:
        """Freelancer name + id off a history row's "To freelancer: <a>Name</a>" line.
        Blank fields (not the missing-freelancer default) when the row has no such line."""
        freelancer = {"freelancer_name": None, "freelancer_id": None}
        link = item.select_one('div.text-body-sm a.up-n-link[href*="/freelancers/"]')
        if not link:
            return freelancer
        freelancer["freelancer_name"] = link.get_text(strip=True) or None
        id_match = ClientHistoryParser._FREELANCER_ID_RE.search(link.get("href", ""))
        freelancer["freelancer_id"] = id_match.group(0) if id_match else None
        return freelancer

    @staticmethod
    def list_history_links(html: str, page_url: str, limit: int = 10) -> list[dict]:
        """Rows out of the currently loaded "Client's recent history" panel, most-
        recent first, capped at `limit`. Each row is {link, freelancer_name,
        freelancer_id}. Relative hrefs are resolved against `page_url` since the
        history panel only has partial links."""
        if not html:
            return []

        section = BeautifulSoup(html, "html.parser").select_one(
            ClientHistoryParser.HISTORY_SECTION
        )
        if not section:
            return []

        rows = []
        seen = set()
        for item in section.select(ClientHistoryParser.HISTORY_ITEM):
            title_el = item.select_one('[data-cy="job-title"]')
            href = title_el.get("href") if title_el else None
            if not href or href.startswith("javascript:"):
                continue
            url = urljoin(page_url, href).split("?")[0]
            if url in seen:
                continue
            seen.add(url)
            rows.append({"link": url, **ClientHistoryParser._row_freelancer(item)})
            if len(rows) >= limit:
                break

        return rows

    @staticmethod
    def _extract_keywords(soup: BeautifulSoup) -> str:
        keywords = []
        seen = set()

        def _add(text: str) -> None:
            keyword = re.sub(r"\s+", " ", text or "").strip()
            if keyword and keyword not in seen:
                seen.add(keyword)
                keywords.append(keyword)

        skill_links = soup.select("div.skills-list a")
        if skill_links:
            for a in skill_links:
                _add(a.get_text(strip=True))
        else:
            for skill_span in soup.find_all("span", {"data-test": "skill"}):
                tag_div = skill_span.find("div", {"data-test": "tag"})
                if tag_div:
                    _add(tag_div.get_text(strip=True))

        return ", ".join(keywords)

    @staticmethod
    def extract_summary(html: str) -> dict:
        """title / description / skills only, for a history job we don't need the
        full record for."""
        summary = {"job_title": "", "job_description": None, "keywords": ""}
        if not html:
            return summary

        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find(attrs={"data-test": "job-title"}) or soup.select_one("h4 span.flex-1")
        summary["job_title"] = title_tag.get_text(strip=True) if title_tag else ""

        desc_div = soup.find("div", {"data-test": "Description"}) or soup.find(
            "div", class_="job-description-content"
        )
        summary["job_description"] = (
            desc_div.get_text(separator="\n", strip=True) if desc_div else None
        )

        summary["keywords"] = ClientHistoryParser._extract_keywords(soup)

        return summary

    @staticmethod
    def _parse_activity_value(title: str, value: str):
        """Proposals come as a range ("5 to 10", "Less than 5", "50+") -> {min, max};
        everything else is kept as the raw string."""
        if "Proposals" not in title:
            return value
        try:
            if " to " in value:
                lo, hi = value.split(" to ")
                return {"min": int(lo.strip()), "max": int(hi.strip())}
            if "Less than" in value:
                return {"min": 1, "max": int(value.split()[-1])}
            if "+" in value:
                return {"min": int(value.replace("+", "").strip()), "max": 1000}
            v = int(value.strip())
            return {"min": v, "max": v}
        except (ValueError, IndexError):
            return {"min": 0, "max": 0}

    @staticmethod
    def extract_activity(html: str) -> dict:
        """"Activity on this job" data off a history job's own page."""
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")
        activity_data = {}

        # New layout: <section> with <h5>Activity on this job</h5> and
        # <li class="ca-item"> rows, each a <span class="title"> + a .value element.
        section = None
        for sec in soup.find_all("section"):
            h5 = sec.find("h5")
            if h5 and "activity on this job" in h5.get_text(strip=True).lower():
                section = sec
                break

        if section:
            for li_tag in section.select("li.ca-item"):
                title_el = li_tag.find("span", class_="title")
                value_el = li_tag.find(class_="value")
                if not title_el or not value_el:
                    continue
                title = title_el.get_text(strip=True).rstrip(":")
                value = value_el.get_text(strip=True)
                activity_data[title] = ClientHistoryParser._parse_activity_value(title, value)
            return activity_data

        # Legacy layout
        activity_section = soup.find("section", {"data-test": "client-activity"})
        activity_items = activity_section.find_all("li", {"data-test": True}) if activity_section else []

        for li_tag in activity_items:
            try:
                title_el = li_tag.find("span", {"class": "secondary-text-color"})
                value_el = li_tag.find("span", {"class": "client-activity-value"})
                if not title_el or not value_el:
                    continue
                title = title_el.get_text(strip=True).rstrip(":")
                value = value_el.get_text(strip=True)
                activity_data[title] = ClientHistoryParser._parse_activity_value(title, value)
            except Exception:
                continue

        return activity_data
