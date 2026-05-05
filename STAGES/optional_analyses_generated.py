"""
Stage 6: Optional Analyses Generation
Optional LLM calls for decision log, thread health score, and missing stakeholders.
Failures here don't halt the pipeline.
"""

import json
from STAGES.llm_helper import llm_call, parse_json_response


SYSTEM_DECISION_LOG = """
You are extracting a comprehensive decision log from extracted facts and decisions.

CRITICAL RULES:
- Only document decisions EXPLICITLY present in the extracted facts.
- DO NOT invent, assume, or hallucinate decisions not mentioned.
- "basis" must cite actual reasoning stated in the emails.
- Do not add your own interpretation of why decisions were made.
- "open_question_if_any" can only reference questions actually in the thread.
- Every decision must be grounded in email_id_sources.

For each decision, document:
- decision_id: identifier
- date: when decided
- decision_text: what was decided
- made_by: who made it
- basis: reasoning or evidence (must be from emails)
- open_question_if_any: outstanding questions from the thread
- email_id_sources: supporting emails

Output valid JSON only. Use this schema:
{
  "decisions": [
    {
      "decision_id": "D1",
      "date": "string",
      "decision_text": "string",
      "made_by": "string",
      "basis": "string",
      "open_question_if_any": "string | null",
      "email_id_sources": ["EMAIL_1"]
    }
  ]
}
"""

SYSTEM_HEALTH_SCORE = """
You are scoring the health/quality of this email thread on four dimensions.

CRITICAL RULES:
- Base scores ONLY on what is observable in the provided email summary.
- DO NOT hallucinate or assume behaviors not evidenced.
- "evidence" must reference actual emails, not opinions or assumptions.
- Do not infer hidden problems or implied issues.
- Scores should reflect ACTUAL clarity, velocity, acknowledgement, quality from the thread.
- Do not score generously based on best practices - score based on actual behavior in the thread.

Score each from 1-5 with specific evidence:
1. **Clarity of ownership**: Are decisions and actions clearly assigned? (1=unclear, 5=crystal clear)
2. **Decision velocity**: Are decisions made promptly or stalled? (1=stalled, 5=quick decisions)
3. **Risk acknowledgement**: Are risks flagged and addressed? (1=ignored, 5=explicitly managed)
4. **Communication quality**: Are threads clear, professional, and actionable? (1=confused, 5=excellent)

Output valid JSON only. Use this schema:
{
  "thread_health_score": {
    "clarity_of_ownership": {
      "score": 1-5,
      "evidence": "email_id or specific observation from thread"
    },
    "decision_velocity": {
      "score": 1-5,
      "evidence": "email_id or specific observation from thread"
    },
    "risk_acknowledgement": {
      "score": 1-5,
      "evidence": "email_id or specific observation from thread"
    },
    "communication_quality": {
      "score": 1-5,
      "evidence": "email_id or specific observation from thread"
    },
    "overall_health": 1-5,
    "summary": "brief assessment based only on thread content"
  }
}
"""

SYSTEM_STAKEHOLDERS = """
You are identifying missing stakeholders based on thread topics.

CRITICAL RULES:
- Identify ONLY missing stakeholders based on topics ACTUALLY discussed in the thread.
- DO NOT hallucinate missing roles or invent stakeholders guess might be needed.
- "why_needed" must reference actual topics from the thread that concern that role.
- Only include stakeholders whose expertise is directly relevant to decisions/actions/risks in the thread.
- Do not add every possible stakeholder - only those whose absence creates a genuine gap.
- "briefing" must be based only on facts, decisions, and risks from the extracted data.

Identify roles/teams that SHOULD have been included but weren't:
- Legal, Infra, Client Success, Product, Commercial/Contracts, etc.

For each missing stakeholder, explain what's relevant to their domain based on thread content.

Output valid JSON only. Use this schema:
{
  "missing_stakeholders": [
    {
      "role": "string (e.g., Legal)",
      "why_needed": "string (based on actual thread topics)",
      "relevant_topics": ["topic1", "topic2"],
      "briefing": "string (what they need to know from the thread)"
    }
  ]
}
"""


def generate_decision_log():
    """Generate comprehensive decision log from extracted decisions."""
    try:
        with open("ARTIFACTS/facts_decisions.json") as f:
            facts = json.load(f)

        decisions = facts.get("decisions", [])
        user_content = json.dumps({"decisions": decisions})

        result = llm_call(
            stage="decision_log_generation",
            system=SYSTEM_DECISION_LOG,
            user_content=user_content,
            input_artifacts=["ARTIFACTS/facts_decisions.json"],
            output_artifact="ARTIFACTS/decision_log.json",
        )

        extracted = parse_json_response(result)

        with open("ARTIFACTS/decision_log.json", "w") as f:
            json.dump(extracted, f, indent=2)

        print("[Optional] Decision log generated")
        return True
    except Exception as e:
        print(f"[Optional] Decision log generation failed: {str(e)}")
        return False


def generate_health_score():
    """Generate thread health score based on dimensions."""
    try:
        with open("ARTIFACTS/parsed_thread.json") as f:
            parsed = json.load(f)

        with open("ARTIFACTS/facts_decisions.json") as f:
            facts = json.load(f)

        with open("ARTIFACTS/action_items.json") as f:
            actions = json.load(f)

        with open("ARTIFACTS/conflicts.json") as f:
            conflicts = json.load(f)

        emails = parsed.get("emails", [])
        user_content = json.dumps({
            "email_count": len(emails),
            "decisions": facts.get("decisions", [])[:3],
            "actions": actions.get("action_items", [])[:3],
            "conflicts": conflicts.get("conflicts", [])[:2],
        })

        result = llm_call(
            stage="thread_health_score_generation",
            system=SYSTEM_HEALTH_SCORE,
            user_content=user_content,
            input_artifacts=["ARTIFACTS/facts_decisions.json", "ARTIFACTS/action_items.json"],
            output_artifact="ARTIFACTS/thread_health_score.json",
        )

        extracted = parse_json_response(result)

        with open("ARTIFACTS/thread_health_score.json", "w") as f:
            json.dump(extracted, f, indent=2)

        print("[Optional] Thread health score generated")
        return True
    except Exception as e:
        print(f"[Optional] Thread health score generation failed: {str(e)}")
        return False


def generate_missing_stakeholders():
    """Identify missing stakeholders and generate briefings."""
    try:
        with open("ARTIFACTS/parsed_thread.json") as f:
            parsed = json.load(f)

        with open("ARTIFACTS/facts_decisions.json") as f:
            facts = json.load(f)

        emails = parsed.get("emails", [])
        decisions = facts.get("decisions", [])[:5]
        risks = facts.get("risks", [])[:3]

        user_content = json.dumps({
            "participants": list({e["from"] for e in emails}),
            "topics_discussed": [d["decision_text"] for d in decisions],
            "risks_raised": [r["risk_text"] for r in risks],
        })

        result = llm_call(
            stage="missing_stakeholders_generation",
            system=SYSTEM_STAKEHOLDERS,
            user_content=user_content,
            input_artifacts=["ARTIFACTS/parsed_thread.json", "ARTIFACTS/facts_decisions.json"],
            output_artifact="ARTIFACTS/missing_stakeholders.md",
        )

        extracted = parse_json_response(result)

        # Save as JSON
        with open("ARTIFACTS/missing_stakeholders.json", "w") as f:
            json.dump(extracted, f, indent=2)

        # Save as markdown for readability
        with open("ARTIFACTS/missing_stakeholders.md", "w") as f:
            f.write("# Missing Stakeholders Analysis\n\n")
            for stakeholder in extracted.get("missing_stakeholders", []):
                f.write(f"## {stakeholder['role']}\n\n")
                f.write(f"**Why needed**: {stakeholder['why_needed']}\n\n")
                f.write(f"**Relevant topics**: {', '.join(stakeholder.get('relevant_topics', []))}\n\n")
                f.write(f"**Briefing**:\n{stakeholder['briefing']}\n\n")
                f.write("---\n\n")

        print("[Optional] Missing stakeholders analysis generated")
        return True
    except Exception as e:
        print(f"[Optional] Missing stakeholders analysis failed: {str(e)}")
        return False


def generate_optional_analyses():
    """
    Stage 6: Generate optional analyses.
    Failures here don't halt the pipeline.
    """
    print("[STAGE] Generating optional analyses...")

    results = {
        "decision_log": generate_decision_log(),
        "health_score": generate_health_score(),
        "missing_stakeholders": generate_missing_stakeholders(),
    }

    # Save summary of what was generated
    with open("ARTIFACTS/optional_analyses_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    success_count = sum(1 for v in results.values() if v)
    print(f"[STAGE] Optional analyses: {success_count}/3 completed")

    return results


if __name__ == "__main__":
    generate_optional_analyses()
