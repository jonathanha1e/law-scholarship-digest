import os
from datetime import date, datetime, timezone

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from digest import build_digest
from mailer import send_digest_email
from scrape import fetch_scholarships
from state import load_sent, mark_sent
from validate import filter_candidates

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def render_email(featured: list[dict]) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("email.html.j2")
    return template.render(
        featured=featured,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


def main() -> None:
    load_dotenv()
    dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"

    sent = load_sent()
    scholarships = fetch_scholarships()
    print(f"Scraped {len(scholarships)} scholarships from AccessLex.")

    candidates = filter_candidates(scholarships, set(sent.keys()))
    print(f"{len(candidates)} candidates after dedup/validation.")

    featured = build_digest(candidates)
    print(f"Claude selected {len(featured)} scholarships to feature.")

    if not featured:
        print("Nothing new to send this week.")
        return

    html = render_email(featured)

    if dry_run:
        out_path = os.path.join(os.path.dirname(__file__), "..", "preview.local.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"DRY_RUN set -- wrote preview to {out_path}. No email sent, no state written.")
        return

    subject = f"Law Scholarship Digest -- {date.today().isoformat()}"
    send_digest_email(html, subject)
    print("Email sent.")

    mark_sent(sent, featured)
    print("Updated data/sent.json.")


if __name__ == "__main__":
    main()
