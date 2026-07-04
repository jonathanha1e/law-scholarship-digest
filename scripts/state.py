import json
import os
from datetime import date

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sent.json")


def load_sent() -> dict:
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)["sent"]


def mark_sent(sent: dict, featured: list[dict]) -> None:
    today = date.today().isoformat()
    for item in featured:
        entry = sent.setdefault(item["id"], {"name": item["name"], "first_sent": today})
        entry["last_sent"] = today
        entry["name"] = item["name"]

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"sent": sent}, f, indent=2, sort_keys=True)
        f.write("\n")
