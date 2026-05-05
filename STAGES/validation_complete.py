"""
Stage 11: Validation Complete - Verify all artifacts have been generated correctly.
Validation stage - no LLM calls.
"""

import json
import os
from pathlib import Path
from logger import log_info, log_success, log_error, log_validation_pass, log_validation_fail


def run_pipeline_validation() -> dict:
    """
    Validate that all pipeline stages completed successfully and outputs are valid.

    Returns:
        Dictionary with validation results:
        - passed: Number of checks passed
        - failed: Number of checks failed
        - errors: List of error messages
    """
    log_info("Running pipeline validation checks...")

    errors = []
    checks_passed = 0
    checks_total = 0

    # Check 1: parsed_thread.json exists and is valid
    checks_total += 1
    try:
        if not os.path.exists("ARTIFACTS/parsed_thread.json"):
            raise FileNotFoundError("parsed_thread.json not found")

        with open("ARTIFACTS/parsed_thread.json", 'r') as f:
            parsed = json.load(f)

        if not isinstance(parsed.get("emails"), list) or len(parsed["emails"]) == 0:
            raise ValueError("No emails in parsed_thread.json")

        if "conversation_graph" not in parsed:
            raise ValueError("conversation_graph missing")

        if "subthreads" not in parsed:
            raise ValueError("subthreads missing")

        log_validation_pass("parsed_thread.json", len(parsed["emails"]))
        checks_passed += 1

    except Exception as e:
        log_validation_fail("parsed_thread.json", str(e))
        errors.append(f"parsed_thread.json: {str(e)}")

    # Check 2: facts_and_decisions.json structure
    checks_total += 1
    try:
        if os.path.exists("ARTIFACTS/facts_and_decisions.json"):
            with open("ARTIFACTS/facts_and_decisions.json", 'r') as f:
                facts = json.load(f)

            required_keys = ["decisions", "risks", "open_questions", "blockers"]
            for key in required_keys:
                if key not in facts:
                    raise ValueError(f"Missing key: {key}")

            # Validate email citations
            if os.path.exists("ARTIFACTS/parsed_thread.json"):
                with open("ARTIFACTS/parsed_thread.json", 'r') as f:
                    valid_ids = set(e["email_id"] for e in json.load(f).get("emails", []))

                for decision in facts.get("decisions", []):
                    for email_id in decision.get("email_id_sources", []):
                        if email_id not in valid_ids:
                            raise ValueError(f"Invalid email_id: {email_id}")

            log_validation_pass("facts_and_decisions.json", len(facts.get("decisions", [])))
            checks_passed += 1
        else:
            checks_passed += 1  # Optional

    except Exception as e:
        log_validation_fail("facts_and_decisions.json", str(e))
        errors.append(f"facts_and_decisions.json: {str(e)}")

    # Check 3: action_items.json structure
    checks_total += 1
    try:
        if os.path.exists("ARTIFACTS/action_items.json"):
            with open("ARTIFACTS/action_items.json", 'r') as f:
                actions = json.load(f)

            valid_statuses = {"confirmed", "requested", "implied", "completed", "pending"}

            for action in actions.get("action_items", []):
                status = action.get("status", "")
                if status not in valid_statuses:
                    raise ValueError(f"Invalid status: {status}")

            log_validation_pass("action_items.json", len(actions.get("action_items", [])))
            checks_passed += 1
        else:
            checks_passed += 1  # Optional

    except Exception as e:
        log_validation_fail("action_items.json", str(e))
        errors.append(f"action_items.json: {str(e)}")

    # Check 4: conflicts.json structure
    checks_total += 1
    try:
        if os.path.exists("ARTIFACTS/conflicts.json"):
            with open("ARTIFACTS/conflicts.json", 'r') as f:
                conflicts = json.load(f)

            valid_types = {
                "interpersonal_tension",
                "unresolved_dependency",
                "decision_reversal",
                "unaddressed_risk",
                "blocked_action",
            }

            for conflict in conflicts.get("conflicts", []):
                conflict_type = conflict.get("type", "")
                if conflict_type not in valid_types:
                    raise ValueError(f"Invalid conflict type: {conflict_type}")

            log_validation_pass("conflicts.json", len(conflicts.get("conflicts", [])))
            checks_passed += 1
        else:
            checks_passed += 1  # Optional

    except Exception as e:
        log_validation_fail("conflicts.json", str(e))
        errors.append(f"conflicts.json: {str(e)}")

    # Check 5: llm_calls.jsonl format
    checks_total += 1
    try:
        llm_call_count = 0
        if os.path.exists("llm_calls.jsonl"):
            with open("llm_calls.jsonl", 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    llm_call_count += 1

                    # Validate required fields
                    required = ["stage", "timestamp", "provider", "model", "status"]
                    for field in required:
                        if field not in entry:
                            raise ValueError(f"Missing field in log: {field}")

        log_validation_pass("llm_calls.jsonl", llm_call_count)
        checks_passed += 1

    except Exception as e:
        log_validation_fail("llm_calls.jsonl", str(e))
        errors.append(f"llm_calls.jsonl: {str(e)}")

    log_success(f"Validation complete: {checks_passed}/{checks_total} checks passed")

    return {
        "passed": checks_passed,
        "failed": checks_total - checks_passed,
        "total": checks_total,
        "errors": errors,
    }
