"""
Stage 2: Action Items Extraction
Extracts action items with status taxonomy: confirmed, requested, implied, completed, pending.
"""

import json
import hashlib
import datetime
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm_client, get_llm_model_name, LLM_PROVIDER, MAX_TOKENS


def llm_call(stage: str, system: str, user_content: str, input_artifacts: list, output_artifact: str) -> str:
    """Make an LLM call using configured provider and log it to llm_calls.jsonl."""
    prompt_hash = hashlib.sha256((system + user_content).encode()).hexdigest()[:16]
    client = get_llm_client()
    model = get_llm_model_name()

    if LLM_PROVIDER == "anthropic":
        response = client.messages.create(
            model=model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user_content}],
        )
        result = response.content[0].text
    else:  # openrouter uses OpenAI-compatible API
        response = client.chat.completions.create(
            model=f"anthropic/{model}" if not model.startswith("anthropic/") and "gpt" not in model else model,
            max_tokens=MAX_TOKENS,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
        )
        result = response.choices[0].message.content

    # Log the call
    log_entry = {
        "stage": stage,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "provider": LLM_PROVIDER,
        "model": model,
        "prompt_hash": prompt_hash,
        "input_artifacts": input_artifacts,
        "output_artifact": output_artifact,
    }
    with open("llm_calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return result


def parse_json_response(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


SYSTEM_EXTRACT_ACTIONS = """
You are analyzing an email thread to extract action items.

You will receive a JSON object with:
- emails: parsed emails array
- facts_decisions: extracted facts and decisions from Stage 1

Action Status Taxonomy (use ONLY these values):
- confirmed: assigned person explicitly acknowledged or accepted the task
- requested: someone asked another person to do something, but no acknowledgement is present
- implied: action is suggested or logically required, but not directly assigned
- completed: the action was completed within the thread
- pending: the action remains unresolved by the final email

CRITICAL RULES:
- Extract ONLY actions explicitly mentioned or clearly implied in the emails.
- DO NOT hallucinate or invent actions not discussed in the thread.
- Every action MUST cite email_id_sources where it was identified.
- Do not assume future actions or goals not stated in the emails.
- Only include deadlines explicitly mentioned in the thread.
- Do not add implied deadlines - use null if not stated.
- Owners must be actual people/roles mentioned in the thread.
- Do not invent ownership or assignments not present in the emails.

Rules:
- Every action must have an owner (person or role).
- If no deadline stated, set deadline_if_stated to null.
- If action completed, cite the email_id where completion happened.
- Cite all email_id_sources that led to this action identification.

Output valid JSON only. No markdown fences.

Output schema:
{
  "action_items": [
    {
      "action_id": "A1",
      "owner": "string (name or role)",
      "action": "string",
      "deadline_if_stated": "string | null",
      "status": "confirmed | requested | implied | completed | pending",
      "email_id_sources": ["EMAIL_1"],
      "completion_email_id": "EMAIL_5 | null"
    }
  ]
}
"""


def enforce_vocabulary_actions(action_items: list):
    """Validate action statuses against allowed taxonomy."""
    ALLOWED_STATUS = {"confirmed", "requested", "implied", "completed", "pending"}

    for action in action_items:
        status = action.get("status")
        if status not in ALLOWED_STATUS:
            raise ValueError(
                f"Action {action.get('action_id')}: invalid status '{status}'. "
                f"Must be one of: {ALLOWED_STATUS}"
            )


def validate_email_ids(extracted_data: dict, valid_email_ids: set):
    """Ensure all cited email_ids exist in parsed thread."""
    for action in extracted_data.get("action_items", []):
        for eid in action.get("email_id_sources", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Action {action.get('action_id')} cites invalid email_id: {eid}"
                )
        if action.get("completion_email_id") and action.get("completion_email_id") not in valid_email_ids:
            raise ValueError(
                f"Action {action.get('action_id')} cites invalid completion_email_id: {action.get('completion_email_id')}"
            )


def extract_action_items():
    """Stage 2: Extract action items with status taxonomy."""
    # Load parsed thread and facts
    with open("ARTIFACTS/parsed_thread.json") as f:
        parsed = json.load(f)

    with open("ARTIFACTS/facts_decisions.json") as f:
        facts_decisions = json.load(f)

    emails = parsed.get("emails", [])
    valid_email_ids = {e["email_id"] for e in emails}

    # Build user prompt
    user_content = json.dumps({
        "emails": emails,
        "facts_decisions": facts_decisions
    })

    # Make LLM call
    result = llm_call(
        stage="action_items_extraction",
        system=SYSTEM_EXTRACT_ACTIONS,
        user_content=user_content,
        input_artifacts=["ARTIFACTS/parsed_thread.json", "ARTIFACTS/facts_decisions.json"],
        output_artifact="ARTIFACTS/action_items.json",
    )

    # Parse response
    extracted_data = parse_json_response(result)

    # Validate action statuses (strict taxonomy)
    enforce_vocabulary_actions(extracted_data.get("action_items", []))

    # Validate email_id citations
    validate_email_ids(extracted_data, valid_email_ids)

    # Save output with exact Problem.md schema
    output = {
        "action_items": extracted_data.get("action_items", [])
    }

    with open("ARTIFACTS/action_items.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("[STAGE] Action items extracted and saved to ARTIFACTS/action_items.json")
    return output


if __name__ == "__main__":
    extract_action_items()
