"""
Stage 4: Follow-Up Communications Drafting
Drafts follow-up emails grounded in extracted data.
Produces three communications: Priya to Client A, Sarah's team update, James's policy doc.
"""

import json
import hashlib
import datetime
from anthropic import Anthropic

client = Anthropic()


def llm_call(stage: str, system: str, user_content: str, input_artifacts: list, output_artifact: str) -> str:
    """Make an LLM call and log it to llm_calls.jsonl."""
    prompt_hash = hashlib.sha256((system + user_content).encode()).hexdigest()[:16]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )

    result = response.content[0].text

    # Log the call
    log_entry = {
        "stage": stage,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "prompt_hash": prompt_hash,
        "input_artifacts": input_artifacts,
        "output_artifact": output_artifact,
    }
    with open("llm_calls.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result


def parse_json_response(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


SYSTEM_DRAFT_FOLLOWUPS = """
You are drafting follow-up communications based on extracted email thread data.

You will receive:
- Parsed emails from the thread
- Extracted facts, decisions, actions, and conflicts

Draft three communications grounded in extracted data:
1. **Priya's message to Client A's technical contact**:
   - Address the SLA complication (5k req/min contractual guarantee)
   - Must explicitly account for their contractual obligations
   - Professional, empathetic tone

2. **Sarah's end-of-Tuesday update to the full team**:
   - Summary of decisions made today
   - Action items assigned
   - Timeline and next steps
   - Acknowledge risks and blockers

3. **James's rate-limiting policy document**:
   - Section header
   - 3-bullet scope defining what the policy covers

CRITICAL RULES:
- Ground ALL drafts ONLY in facts, decisions, and actions from the extracted data.
- DO NOT hallucinate commitments, timelines, or details not in the thread.
- DO NOT make promises on behalf of teams unless explicitly discussed.
- DO NOT invent implementation details, technical decisions, or solutions not mentioned.
- Every claim in drafts must be traceable to specific emails.
- Do not add false reassurances or implied guarantees.
- Stick to facts: decisions made, actions assigned, risks identified, next steps discussed.
- Priya MUST explicitly address the 5k req/min SLA - do not minimize or omit it.

Rules:
- Every draft must cite the extracted facts or email_ids it relies on.
- Ground all drafts in extracted data (no hallucination).
- Priya's draft MUST explicitly address the 5k req/min SLA complication.
- Do not promise outcomes not in the thread.
- Tone: professional, empathetic, action-oriented.

Output valid JSON only. No markdown fences.

Output schema:
{
  "follow_up_drafts": [
    {
      "draft_id": "DRAFT_1",
      "recipient": "string (Client A technical contact)",
      "from": "Priya",
      "subject": "string",
      "body": "string (full draft)",
      "grounded_in_email_ids": ["EMAIL_1", "EMAIL_2"],
      "key_constraints_addressed": ["SLA 5k req/min guarantee", "...]
    },
    {
      "draft_id": "DRAFT_2",
      "recipient": "full team",
      "from": "Sarah",
      "subject": "Tuesday end-of-day update",
      "body": "string",
      "grounded_in_email_ids": ["EMAIL_3"],
      "key_constraints_addressed": ["decisions made", "action items", "risks acknowledged"]
    },
    {
      "draft_id": "DRAFT_3",
      "recipient": "internal",
      "from": "James",
      "subject": "Rate-limiting policy - scope outline",
      "body": "string (header + 3 bullets)",
      "grounded_in_email_ids": ["EMAIL_4"],
      "key_constraints_addressed": ["policy scope", "rate-limiting rules"]
    }
  ]
}
"""


def validate_priya_draft(drafts: list):
    """Ensure Priya's draft addresses the 5k req/min SLA complication."""
    priya_draft = next((d for d in drafts if d.get("from") == "Priya"), None)
    if not priya_draft:
        raise ValueError("Priya's draft not found")

    body = priya_draft.get("body", "").lower()
    sla_mentioned = (
        "sla" in body or
        "contractual" in body or
        "5k" in body or
        "req/min" in body or
        "guarantee" in body
    )

    if not sla_mentioned:
        raise ValueError(
            "Priya's draft must explicitly address the 5k req/min SLA complication. "
            "Mention SLA, contractual guarantee, or 5k req/min."
        )


def validate_email_ids(extracted_data: dict, valid_email_ids: set):
    """Ensure all cited email_ids exist in parsed thread."""
    for draft in extracted_data.get("follow_up_drafts", []):
        for eid in draft.get("grounded_in_email_ids", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Draft {draft.get('draft_id')} cites invalid email_id: {eid}"
                )


def draft_follow_ups():
    """Stage 4: Draft follow-up communications grounded in extracted data."""
    # Load all artifacts from previous stages
    with open("ARTIFACTS/parsed_thread.json") as f:
        parsed = json.load(f)

    with open("ARTIFACTS/facts_decisions.json") as f:
        facts_decisions = json.load(f)

    with open("ARTIFACTS/action_items.json") as f:
        action_items = json.load(f)

    with open("ARTIFACTS/conflicts.json") as f:
        conflicts = json.load(f)

    emails = parsed.get("emails", [])
    valid_email_ids = {e["email_id"] for e in emails}

    # Build user prompt
    user_content = json.dumps({
        "emails": emails,
        "facts_decisions": facts_decisions,
        "action_items": action_items,
        "conflicts": conflicts
    })

    # Make LLM call
    result = llm_call(
        stage="follow_ups_drafted",
        system=SYSTEM_DRAFT_FOLLOWUPS,
        user_content=user_content,
        input_artifacts=[
            "ARTIFACTS/parsed_thread.json",
            "ARTIFACTS/facts_decisions.json",
            "ARTIFACTS/action_items.json",
            "ARTIFACTS/conflicts.json"
        ],
        output_artifact="ARTIFACTS/follow_up_drafts.json",
    )

    # Parse response
    extracted_data = parse_json_response(result)

    # Validate Priya's draft addresses SLA
    drafts = extracted_data.get("follow_up_drafts", [])
    validate_priya_draft(drafts)

    # Validate email_id citations
    validate_email_ids(extracted_data, valid_email_ids)

    # Save output with exact Problem.md schema
    output = {
        "follow_up_drafts": drafts
    }

    with open("ARTIFACTS/follow_up_drafts.json", "w") as f:
        json.dump(output, f, indent=2)

    # Also save as markdown for readability
    with open("ARTIFACTS/follow_up_drafts.md", "w") as f:
        f.write("# Follow-Up Drafts\n\n")
        for draft in drafts:
            f.write(f"## {draft.get('draft_id')}: {draft.get('subject')}\n")
            f.write(f"**From:** {draft.get('from')}\n")
            f.write(f"**To:** {draft.get('recipient')}\n\n")
            f.write(f"{draft.get('body')}\n\n")
            f.write(f"**Grounded in:** {', '.join(draft.get('grounded_in_email_ids', []))}\n")
            f.write(f"**Constraints addressed:** {', '.join(draft.get('key_constraints_addressed', []))}\n\n")
            f.write("---\n\n")

    print("[STAGE] Follow-up drafts created and saved to ARTIFACTS/follow_up_drafts.json")
    return output


if __name__ == "__main__":
    draft_follow_ups()
