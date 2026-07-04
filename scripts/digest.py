import json

import anthropic

MODEL = "claude-sonnet-4-6"
MAX_FEATURES = 8

SYSTEM_PROMPT = (
    "You write short, friendly, accurate descriptions of law school scholarships "
    "for a personal weekly email digest, and select which of the provided "
    "candidates to feature this week. Never invent facts not present in the "
    "input data -- only rephrase and summarize what's given. Prioritize "
    "scholarships with sooner deadlines and broader eligibility."
)

FEATURED_SCHEMA = {
    "type": "object",
    "properties": {
        "featured": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "friendly_description": {"type": "string"},
                    "eligibility_summary": {"type": "string"},
                    "deadline_display": {"type": "string"},
                    "amount": {"type": "string"},
                    "link": {"type": "string"},
                    "sponsor": {"type": "string"},
                },
                "required": [
                    "id", "name", "friendly_description", "eligibility_summary",
                    "deadline_display", "amount", "link", "sponsor",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["featured"],
    "additionalProperties": False,
}


def build_digest(candidates: list[dict]) -> list[dict]:
    if not candidates:
        return []

    client = anthropic.Anthropic()

    payload = [
        {
            "id": c["id"],
            "name": c["name"],
            "description": c["description"],
            "eligibility": c["eligibility"],
            "sponsor": c["sponsor"],
            "amount": c["amount"],
            "deadline": c["deadline"],
            "link": c["link"],
            "requirements": c["requirements"],
        }
        for c in candidates
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"Select up to {MAX_FEATURES} scholarships to feature this week "
                f"from the candidates below, ranked by priority. For each selected "
                f"scholarship, write a friendlier 2-3 sentence description and a "
                f"one-line eligibility summary, using only facts given. The 'link' "
                f"field is the scholarship's page on accesslex.org -- pass it "
                f"through unchanged, do not invent a different URL.\n\n"
                f"{json.dumps(payload)}"
            ),
        }],
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": FEATURED_SCHEMA},
        },
    )

    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)["featured"]
