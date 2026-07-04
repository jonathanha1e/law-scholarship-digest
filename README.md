# Law Scholarship Digest

A personal tool that scrapes the [AccessLex Databank](https://www.accesslex.org/databank) for current
law school scholarships once a week, uses Claude to pick the most relevant ones and write friendly
descriptions, and emails the result to a single recipient. Runs automatically via GitHub Actions.

This is built for **personal use only** -- it emails one recipient (configured via a secret, not
hardcoded) and is not a public subscription product. AccessLex's `robots.txt` asks AI-related bots not
to crawl `/databank` at scale; this script identifies itself honestly (see the `User-Agent` in
[scripts/scrape.py](scripts/scrape.py)), runs at most once a week, and does not redistribute the data
to a subscriber list.

## How it works

1. `scripts/scrape.py` scrapes the AccessLex databank for scholarship listings.
2. `scripts/validate.py` drops anything already sent before, anything with an expired deadline, and
   anything whose apply link doesn't resolve.
3. `scripts/digest.py` sends the validated candidates to Claude, which picks up to 8 to feature and
   writes a short, friendly description for each -- using only the facts provided, never inventing
   details.
4. `scripts/mailer.py` emails the result via Gmail SMTP.
5. `data/sent.json` is updated (and committed by the GitHub Action) so the same scholarship isn't
   featured twice.

## Setup

1. Create a fresh Python virtual environment and install dependencies:
   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in:
   - `ANTHROPIC_API_KEY` -- from [console.anthropic.com](https://console.anthropic.com)
   - `GMAIL_SENDER_ADDRESS` / `GMAIL_APP_PASSWORD` -- a Gmail address and an
     [app password](https://myaccount.google.com/apppasswords) generated for it
   - `RECIPIENT_EMAIL` -- where the digest should be sent
3. Test locally without sending anything:
   ```
   cd scripts && DRY_RUN=true python main.py
   ```
   This writes a preview to `preview.local.html` instead of sending an email.
4. Add the same four values as **GitHub Actions secrets** on this repo (Settings -> Secrets and
   variables -> Actions): `ANTHROPIC_API_KEY`, `GMAIL_SENDER_ADDRESS`, `GMAIL_APP_PASSWORD`,
   `RECIPIENT_EMAIL`.
5. Trigger the workflow manually from the Actions tab with `dry_run: true` first, then `dry_run: false`
   to confirm a real email arrives correctly, before relying on the weekly schedule.

## Disclaimer

Every email includes a notice that it's AI-compiled and to verify details on the official scholarship
page before applying -- this script does its best to catch stale or broken listings automatically, but
it isn't infallible.
