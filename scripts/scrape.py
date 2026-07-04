import hashlib
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

DATABANK_URL = "https://www.accesslex.org/databank"

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "PersonalScholarshipDigest/1.0 "
        "(personal use; contact: jonathan.hale@rocketmail.com)"
    )
})


def _absolute_url(url: str) -> str:
    if url and not url.startswith("http"):
        return f"https://www.accesslex.org{url}"
    return url


def _stable_id(more_link: str | None, name: str, sponsor: str, amount: str) -> str:
    if more_link:
        return more_link
    raw = f"{name}|{sponsor}|{amount}"
    return "hash:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def fetch_scholarships() -> list[dict]:
    """Scrapes the AccessLex databank listing page only -- a single request.

    Deliberately does not follow through to each scholarship's own detail page:
    AccessLex's Cloudflare bot protection challenges/rate-limits that pattern
    (observed directly while building this). `more_link` -- the scholarship's
    own page on accesslex.org -- is used as the "learn more / apply" link
    instead of trying to scrape a separate external apply URL per item.
    """
    response = session.get(DATABANK_URL, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    scholarships = []
    scraped_at = datetime.now(timezone.utc).isoformat()

    for entry in soup.find_all("div", class_="scholarship__field-description"):
        name_tag = entry.find_previous("h3")
        name = name_tag.text.strip() if name_tag else "N/A"

        description_tag = entry.find("p")
        description = description_tag.text.strip() if description_tag else "N/A"

        eligibility_tag = entry.find_next("div", class_="scholarship__type")
        eligibility_items = (
            eligibility_tag.find_all("div", class_="field__item") if eligibility_tag else []
        )
        eligibility = (
            ", ".join(item.text.strip() for item in eligibility_items)
            if eligibility_items
            else "N/A"
        )

        sponsor_tag = entry.find_next("div", class_="scholarship__field-sponsoring-organization")
        sponsor = (
            sponsor_tag.find("span").text.strip()
            if sponsor_tag and sponsor_tag.find("span")
            else "N/A"
        )

        amount_tag = entry.find_next("div", class_="scholarship__field-award-maximum-amount")
        amount = (
            amount_tag.find("div", class_="field__item").text.strip() if amount_tag else "N/A"
        )

        deadline_tag = entry.find_next("div", class_="scholarship__field-application-deadline")
        deadline = (
            deadline_tag.find("div", class_="field__item").text.strip()
            if deadline_tag
            else "N/A"
        )

        requirements_tag = entry.find_next(
            "div", class_="scholarship__field-eligibility-requirements"
        )
        requirements_items = (
            requirements_tag.find_all("div", class_="field__item") if requirements_tag else []
        )
        requirements = (
            "; ".join(item.text.strip() for item in requirements_items)
            if requirements_items
            else "N/A"
        )

        more_link_tag = entry.find_parent("article")
        more_link = None
        if more_link_tag:
            anchor = more_link_tag.find_parent("a", href=True)
            if anchor and anchor.get("href"):
                more_link = _absolute_url(anchor["href"].strip())

        scholarships.append({
            "id": _stable_id(more_link, name, sponsor, amount),
            "name": name,
            "description": description,
            "eligibility": eligibility,
            "sponsor": sponsor,
            "amount": amount,
            "deadline": deadline,
            "link": more_link,
            "requirements": requirements,
            "scraped_at": scraped_at,
        })

    return scholarships
