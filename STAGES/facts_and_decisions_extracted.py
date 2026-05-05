"""
Stage 1: Facts and Decisions Extraction
Extracts decisions, open questions, blockers, and risks with email_id citations.
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


SYSTEM_EXTRACT_FACTS = """
You are an email thread analysis engine. Your job is to extract facts, decisions,
risks, and blockers from a parsed email thread.

You will receive a JSON object with emails array containing parsed emails.

Extract:

1. **Decisions made**: Who decided what, when, and what was the basis?
2. **Open questions**: What is still unresolved?
3. **Blockers**: What is preventing progress?
4. **Risks flagged**: What concerns were raised about project success, SLA, legal risk, budget?

Confidence levels:
- confirmed: explicit statement or clear agreement
- implied: logically follows from the thread but not stated directly
- assumed: reasonable interpretation but uncertain

Risk severity:
- critical: threatens project success, legal/SLA compliance
- high: significant impact on timeline or quality
- medium: manageable with mitigation
- low: minor concern

CRITICAL RULES:
- Extract ONLY information explicitly stated or directly referenced in the emails.
- DO NOT hallucinate or invent decisions, risks, blockers, or questions not in the thread.
- Every item MUST be grounded in at least one email_id citation.
- If you cannot find clear evidence for something, exclude it.
- Do not assume information not present in the email content.
- Only include decisions explicitly made or clearly implied from email statements.

For each extracted item, cite the email_id(s) that support it.

Output valid JSON only. No markdown fences, no explanation outside JSON.

Output schema:
{
  "decisions": [
    {
      "decision_id": "D1",
      "decision_text": "string",
      "made_by": "string",
      "date": "string",
      "confidence": "confirmed | implied | assumed",
      "email_id_sources": ["EMAIL_1"]
    }
  ],
  "risks": [
    {
      "risk_id": "R1",
      "risk_text": "string",
      "raised_by": "string",
      "severity": "critical | high | medium | low",
      "email_id_sources": ["EMAIL_2"]
    }
  ],
  "open_questions": [
    {
      "question_id": "Q1",
      "question": "string",
      "related_emails": ["EMAIL_3"]
    }
  ],
  "blockers": [
    {
      "blocker_id": "B1",
      "blocker": "string",
      "impact": "string",
      "email_id_sources": ["EMAIL_4"]
    }
  ]
}
"""


def enforce_vocabulary_facts(decisions: list, risks: list):
    """Validate extracted values against allowed vocabulary."""
    ALLOWED_CONFIDENCE = {"confirmed", "implied", "assumed"}
    ALLOWED_SEVERITY = {"critical", "high", "medium", "low"}

    for decision in decisions:
        confidence = decision.get("confidence")
        if confidence not in ALLOWED_CONFIDENCE:
            raise ValueError(
                f"Decision {decision.get('decision_id')}: invalid confidence '{confidence}'. "
                f"Must be one of: {ALLOWED_CONFIDENCE}"
            )

    for risk in risks:
        severity = risk.get("severity")
        if severity not in ALLOWED_SEVERITY:
            raise ValueError(
                f"Risk {risk.get('risk_id')}: invalid severity '{severity}'. "
                f"Must be one of: {ALLOWED_SEVERITY}"
            )


def validate_email_ids(extracted_data: dict, valid_email_ids: set):
    """Ensure all cited email_ids exist in parsed thread."""
    for decision in extracted_data.get("decisions", []):
        for eid in decision.get("email_id_sources", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Decision {decision.get('decision_id')} cites invalid email_id: {eid}"
                )

    for risk in extracted_data.get("risks", []):
        for eid in risk.get("email_id_sources", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Risk {risk.get('risk_id')} cites invalid email_id: {eid}"
                )

    for question in extracted_data.get("open_questions", []):
        for eid in question.get("related_emails", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Question {question.get('question_id')} cites invalid email_id: {eid}"
                )

    for blocker in extracted_data.get("blockers", []):
        for eid in blocker.get("email_id_sources", []):
            if eid not in valid_email_ids:
                raise ValueError(
                    f"Blocker {blocker.get('blocker_id')} cites invalid email_id: {eid}"
                )


def extract_facts_and_decisions():
    """Stage 1: Extract facts, decisions, risks, and blockers."""
    # Load parsed thread
    with open("ARTIFACTS/parsed_thread.json") as f:
        parsed = json.load(f)

    emails = parsed.get("emails", [])
    valid_email_ids = {e["email_id"] for e in emails}

    # Build user prompt with emails
    user_content = json.dumps({"emails": emails})

    # Make LLM call
    result = llm_call(
        stage="facts_and_decisions_extraction",
        system=SYSTEM_EXTRACT_FACTS,
        user_content=user_content,
        input_artifacts=["ARTIFACTS/parsed_thread.json"],
        output_artifact="ARTIFACTS/facts_decisions.json",
    )

    # Parse response
    extracted_data = parse_json_response(result)

    # Validate vocabularies
    enforce_vocabulary_facts(
        extracted_data.get("decisions", []),
        extracted_data.get("risks", []),
    )

    # Validate email_id citations
    validate_email_ids(extracted_data, valid_email_ids)

    # Save output with exact Problem.md schema
    output = {
        "decisions": extracted_data.get("decisions", []),
        "risks": extracted_data.get("risks", []),
        "open_questions": extracted_data.get("open_questions", []),
        "blockers": extracted_data.get("blockers", []),
    }

    with open("ARTIFACTS/facts_decisions.json", "w") as f:
        json.dump(output, f, indent=2)

    print("[STAGE] Facts and decisions extracted and saved to ARTIFACTS/facts_decisions.json")
    return output


if __name__ == "__main__":
    extract_facts_and_decisions()
