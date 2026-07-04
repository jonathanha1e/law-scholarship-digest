import time
from datetime import date, datetime

import requests
from dateutil import parser as dateparser

from scrape import session

REQUEST_TIMEOUT = 10
LINK_CHECK_DELAY_SECONDS = 2

# Status codes that mean "this page genuinely doesn't exist" -- drop the
# scholarship. Everything else (429 rate-limited, 5xx, network hiccups) is
# treated as inconclusive rather than broken, since AccessLex's Cloudflare
# protection can throttle automated requests without the link actually
# being dead.
DEFINITELY_BROKEN = {404, 410}


def classify_deadline(deadline_str: str) -> dict:
    """Returns {'type': 'date'|'non_date', 'date': date|None, 'expired': bool}.

    Non-date deadline text (e.g. "Rolling", "Varies", "N/A") is always kept,
    never dropped -- only a confidently-parsed past date counts as expired.
    """
    if not deadline_str or deadline_str == "N/A":
        return {"type": "non_date", "date": None, "expired": False}

    try:
        parsed = dateparser.parse(deadline_str, fuzzy=True)
        if not isinstance(parsed, datetime):
            raise ValueError("unparseable")
        parsed_date = parsed.date()
        current_year = date.today().year
        if not (current_year - 1 <= parsed_date.year <= current_year + 2):
            raise ValueError("implausible year")
        return {
            "type": "date",
            "date": parsed_date,
            "expired": parsed_date < date.today(),
        }
    except (ValueError, OverflowError, TypeError):
        return {"type": "non_date", "date": None, "expired": False}


def is_link_broken(url: str | None) -> bool:
    if not url:
        return True
    try:
        response = session.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
        if response.status_code in (405, 403):
            response = session.get(
                url, allow_redirects=True, timeout=REQUEST_TIMEOUT, stream=True
            )
        return response.status_code in DEFINITELY_BROKEN
    except requests.RequestException:
        return False


def filter_candidates(scholarships: list[dict], already_sent: set[str]) -> list[dict]:
    candidates = []
    for scholarship in scholarships:
        if scholarship["id"] in already_sent:
            continue

        deadline_info = classify_deadline(scholarship["deadline"])
        if deadline_info["expired"]:
            continue

        broken = is_link_broken(scholarship["link"])
        time.sleep(LINK_CHECK_DELAY_SECONDS)
        if broken:
            continue

        candidate = dict(scholarship)
        candidate["deadline_info"] = deadline_info
        candidates.append(candidate)

    return candidates
