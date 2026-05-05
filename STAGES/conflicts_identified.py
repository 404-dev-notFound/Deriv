"""
Stage 3: Conflict and Tension Identification
Identifies interpersonal tensions, unresolved dependencies, decision reversals, etc.
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


SYSTEM_IDENTIFY_CONFLICTS = """
You are analyzing an email thread to identify conflicts, tensions, and blockers.

You will receive a JSON object with:
- emails: parsed emails array
- facts_decisions: extracted facts and decisions from Stage 1
- action_items: extracted actions from Stage 2

Identify:
- interpersonal tensions: disagreement between individuals or teams
- unresolved dependencies: one team waiting on another, dependency not met
- decision reversals: earlier decision contradicted or overridden later
- unaddressed risks: risk was flagged but not actively addressed
- blocked actions: action cannot proceed due to external block

CRITICAL RULES:
- Identify ONLY conflicts explicitly present or clearly evident in the thread.
- DO NOT hallucinate or invent tensions, reversals, or dependencies not in the emails.
- Every conflict MUST cite email_id_sources showing evidence.
- "why_it_matters" must explain actual consequences described in the thread.
- Do not speculate about potential conflicts or future issues.
- Do not infer conflicts not directly stated or strongly implied.
- Each conflict must be grounded in specific email statements or exchanges.

For each conflict, explain why it matters and cite the email sources.

Output valid JSON only. No markdown fences.

Output schema:
{
  "conflicts": [
    {
      "conflict_id": "C1",
      "type": "interpersonal_tension | unresolved_dependency | decision_reversal | unaddressed_risk | blocked_action",
      "description": "string",
      "severity": "critical | high | medium | low",
      "email_id_sources": ["EMAIL_1", "EMAIL_2"],
      "why_it_matters": "string"
    }
  ]
}
"""


def enforce_vocabulary_conflicts(conflicts: list):
    """Validate conflict types and severities against allowed vocabulary."""
    ALLOWED_TYPES = {
        "interpersonal_tension",
        "unresolved_dependency",
        "decision_reversal",
        "unaddressed_risk",
        "blocked_action",
    }
    ALLOWED_SEVERITY = {"critical", "high", "medium", "low"}

    for conflict in conflicts:
        conflict_type = conflict.get("type")
        if conflict_type not in ALLOWED_TYPES:
            raise ValueError(
                f"Conflict {conflict.get('conflict_id')}: invalid type '{conflict_type}'. "
                f"Must be one of: {ALLOWED_TYPES}"
            )

        severity = conflict.get("severity")
        if severity not in ALLOWED_SEVERITY:
            raise ValueError(
                f"Conflict {conflict.get('conflict_id')}: invalid severity '{severity}'. "
                f"Must be one of: {ALLOWED_SEVERITY}"
            )


def validate_email_ids(extracted_data: dict, valid_email_ids: set):
    """Ensure all cited email_ids exist in parsed thread."""
    for conflict in extracted_data.get("conflicts", []):
        for eid in conflict.get("email_id_sources", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Conflict {conflict.get('conflict_id')} cites invalid email_id: {eid}"
                )


def identify_conflicts():
    """Stage 3: Identify conflicts, tensions, and blockers."""
    # Load all artifacts from previous stages
    with open("ARTIFACTS/parsed_thread.json") as f:
        parsed = json.load(f)

    with open("ARTIFACTS/facts_decisions.json") as f:
        facts_decisions = json.load(f)

    with open("ARTIFACTS/action_items.json") as f:
        action_items = json.load(f)

    emails = parsed.get("emails", [])
    valid_email_ids = {e["email_id"] for e in emails}

    # Build user prompt
    user_content = json.dumps({
        "emails": emails,
        "facts_decisions": facts_decisions,
        "action_items": action_items
    })

    # Make LLM call
    result = llm_call(
        stage="conflict_identification",
        system=SYSTEM_IDENTIFY_CONFLICTS,
        user_content=user_content,
        input_artifacts=[
            "ARTIFACTS/parsed_thread.json",
            "ARTIFACTS/facts_decisions.json",
            "ARTIFACTS/action_items.json"
        ],
        output_artifact="ARTIFACTS/conflicts.json",
    )

    # Parse response
    extracted_data = parse_json_response(result)

    # Validate conflict types and severities
    enforce_vocabulary_conflicts(extracted_data.get("conflicts", []))

    # Validate email_id citations
    validate_email_ids(extracted_data, valid_email_ids)

    # Save output with exact Problem.md schema
    output = {
        "conflicts": extracted_data.get("conflicts", [])
    }

    with open("ARTIFACTS/conflicts.json", "w") as f:
        json.dump(output, f, indent=2)

    print("[STAGE] Conflicts identified and saved to ARTIFACTS/conflicts.json")
    return output


if __name__ == "__main__":
    identify_conflicts()
