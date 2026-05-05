#!/usr/bin/env python3
"""Validation script - Verify all pipeline artifacts are valid and complete."""

import json
import os
import sys
from pathlib import Path
from logger import log_info, log_success, log_error, log_validation_pass, log_validation_fail


def validate_parsed_thread() -> bool:
    """Validate parsed_thread.json contains all expected sections."""
    filepath = "ARTIFACTS/parsed_thread.json"

    if not os.path.exists(filepath):
        log_validation_fail("parsed_thread.json", "File not found")
        return False

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        checks = [
            ("emails" in data, "Contains emails key"),
            ("conversation_graph" in data, "Contains conversation_graph key"),
            ("subthreads" in data, "Contains subthreads key"),
            (len(data.get("emails", [])) > 0, "Has at least one email"),
        ]

        passed = sum(1 for check, _ in checks if check)
        log_validation_pass("parsed_thread.json", passed)
        return all(check for check, _ in checks)

    except Exception as e:
        log_validation_fail("parsed_thread.json", str(e))
        return False


def validate_facts_and_decisions() -> bool:
    """Validate facts_and_decisions.json has required structure."""
    filepath = "ARTIFACTS/facts_and_decisions.json"

    if not os.path.exists(filepath):
        return True

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        checks = [
            ("decisions" in data, "Has decisions"),
            ("risks" in data, "Has risks"),
        ]

        passed = sum(1 for check, _ in checks if check)
        log_validation_pass("facts_and_decisions.json", passed)
        return all(check for check, _ in checks)

    except Exception as e:
        log_validation_fail("facts_and_decisions.json", str(e))
        return False


def validate_action_items() -> bool:
    """Validate action_items.json has required structure."""
    filepath = "ARTIFACTS/action_items.json"

    if not os.path.exists(filepath):
        return True

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        valid_statuses = {"confirmed", "requested", "implied", "completed", "pending"}

        for item in data.get("action_items", []):
            status = item.get("status", "")
            if status not in valid_statuses:
                log_validation_fail("action_items.json", f"Invalid status: {status}")
                return False

        log_validation_pass("action_items.json", len(data.get("action_items", [])))
        return True

    except Exception as e:
        log_validation_fail("action_items.json", str(e))
        return False


def validate_conflicts() -> bool:
    """Validate conflicts.json has required structure."""
    filepath = "ARTIFACTS/conflicts.json"

    if not os.path.exists(filepath):
        return True

    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        valid_types = {
            "interpersonal_tension",
            "unresolved_dependency",
            "decision_reversal",
            "unaddressed_risk",
            "blocked_action",
        }

        for conflict in data.get("conflicts", []):
            conflict_type = conflict.get("type", "")
            if conflict_type not in valid_types:
                log_validation_fail("conflicts.json", f"Invalid type: {conflict_type}")
                return False

        log_validation_pass("conflicts.json", len(data.get("conflicts", [])))
        return True

    except Exception as e:
        log_validation_fail("conflicts.json", str(e))
        return False


def validate_llm_calls_log() -> bool:
    """Validate llm_calls.jsonl has proper format."""
    filepath = "llm_calls.jsonl"

    if not os.path.exists(filepath):
        log_validation_fail("llm_calls.jsonl", "File not found")
        return False

    try:
        call_count = 0
        with open(filepath, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                call_count += 1

        log_validation_pass("llm_calls.jsonl", call_count)
        return True

    except Exception as e:
        log_validation_fail("llm_calls.jsonl", str(e))
        return False


def run_validation() -> dict:
    """Run all validation checks."""
    log_info("Running validation checks...")

    checks = [
        ("parsed_thread.json", validate_parsed_thread),
        ("facts_and_decisions.json", validate_facts_and_decisions),
        ("action_items.json", validate_action_items),
        ("conflicts.json", validate_conflicts),
        ("llm_calls.jsonl", validate_llm_calls_log),
    ]

    passed = 0
    failed = 0

    for name, check_fn in checks:
        try:
            if check_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            log_error(f"Validation error for {name}: {str(e)}")
            failed += 1

    return {
        "passed": passed,
        "failed": failed,
        "total": len(checks),
    }


if __name__ == "__main__":
    try:
        results = run_validation()
        log_success(f"Validation complete: {results['passed']}/{results['total']} checks passed")

        if results["failed"] > 0:
            sys.exit(1)
        sys.exit(0)

    except Exception as e:
        log_error(f"Validation failed: {str(e)}")
        sys.exit(1)
