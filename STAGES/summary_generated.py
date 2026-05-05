"""
Stage 5: Executive Summary Generation
Deterministic summary from extracted data (NO LLM CALL).
"""

import json


def generate_executive_summary():
    """
    Stage 5: Generate executive summary from extracted facts, actions, and conflicts.
    DETERMINISTIC - No LLM call. Template-based from extracted data.
    """
    # Load extracted data from previous stages
    with open("ARTIFACTS/facts_decisions.json") as f:
        facts = json.load(f)

    with open("ARTIFACTS/action_items.json") as f:
        actions = json.load(f)

    with open("ARTIFACTS/conflicts.json") as f:
        conflicts = json.load(f)

    lines = []

    # Current situation
    decisions = facts.get("decisions", [])
    lines.append("# Executive Summary\n")
    lines.append("## Current Situation")
    if decisions:
        decision_texts = [d["decision_text"] for d in decisions[:2]]
        lines.append(f"\nKey decisions made:\n")
        for decision in decisions[:3]:
            lines.append(f"- {decision['decision_text']} (made by {decision['made_by']}, confidence: {decision['confidence']})")
    else:
        lines.append("\nNo decisions documented.")

    # Key blockers
    blockers = facts.get("blockers", [])
    if blockers:
        lines.append("\n## Key Blockers")
        for blocker in blockers[:3]:
            blocker_text = blocker.get('blocker_text') or blocker.get('blocker', 'Unknown blocker')
            lines.append(f"- **{blocker_text}**: {blocker.get('impact', 'No impact described')}")
    else:
        lines.append("\n## Key Blockers\nNone identified.")

    # Immediate next actions
    pending_actions = [
        a for a in actions.get("action_items", [])
        if a["status"] in ["confirmed", "pending"]
    ]
    if pending_actions:
        lines.append("\n## Immediate Next Actions")
        for action in pending_actions[:5]:
            deadline = action.get("deadline_if_stated") or "TBD"
            status_icon = "✓" if action["status"] == "confirmed" else "→"
            lines.append(f"- {status_icon} **{action['action']}** (Owner: {action['owner']}, Deadline: {deadline})")
    else:
        lines.append("\n## Immediate Next Actions\nNone pending.")

    # Unresolved risks
    risks = facts.get("risks", [])
    critical_risks = [r for r in risks if r["severity"] in ["critical", "high"]]
    if critical_risks:
        lines.append("\n## Unresolved Risks")
        for risk in critical_risks[:3]:
            lines.append(f"- **[{risk['severity'].upper()}]** {risk['risk_text']} (raised by {risk['raised_by']})")
    else:
        lines.append("\n## Unresolved Risks\nNone flagged as critical or high.")

    # Unresolved tensions
    critical_conflicts = [
        c for c in conflicts.get("conflicts", [])
        if c["severity"] in ["critical", "high"]
    ]
    if critical_conflicts:
        lines.append("\n## Unresolved Tensions")
        for conflict in critical_conflicts[:3]:
            lines.append(f"- **{conflict['type']}**: {conflict['description']}")
            lines.append(f"  - Why it matters: {conflict['why_it_matters']}")
    else:
        lines.append("\n## Unresolved Tensions\nNone identified.")

    # Questions still pending
    questions = facts.get("open_questions", [])
    if questions:
        lines.append("\n## Open Questions")
        for question in questions[:3]:
            lines.append(f"- {question['question']}")
    else:
        lines.append("\n## Open Questions\nNone documented.")

    summary_text = "\n".join(lines)

    # Save as markdown
    with open("ARTIFACTS/executive_summary.md", "w") as f:
        f.write(summary_text)

    # Also save as JSON for structured access
    summary_json = {
        "summary_type": "executive",
        "generated_deterministically": True,
        "sections": {
            "current_situation": {
                "decisions": decisions[:3],
                "decision_count": len(decisions),
            },
            "blockers": blockers[:3],
            "pending_actions": pending_actions[:5],
            "critical_risks": critical_risks,
            "critical_conflicts": critical_conflicts,
            "open_questions": questions,
        },
    }

    with open("ARTIFACTS/executive_summary.json", "w") as f:
        json.dump(summary_json, f, indent=2)

    print("[STAGE] Executive summary generated and saved to ARTIFACTS/executive_summary.md")
    return summary_text


if __name__ == "__main__":
    generate_executive_summary()
