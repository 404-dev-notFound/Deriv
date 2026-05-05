#!/usr/bin/env python3
"""
Email Pipeline Orchestrator
Manages the complete pipeline execution from Stage 0 through Stage 6.
"""

import json
import sys
import time
from pathlib import Path
from logger import (
    log_info,
    log_success,
    log_error,
    log_stage_start,
    log_stage_complete,
    log_summary,
    log_artifact_saved,
)


# Stage management
STAGES = [
    "INIT",
    "THREAD_LOADED",
    "EMAILS_PARSED",
    "CONVERSATION_GRAPH_BUILT",
    "SUBTHREADS_IDENTIFIED",
    "FACTS_AND_DECISIONS_EXTRACTED",
    "ACTION_ITEMS_EXTRACTED",
    "CONFLICTS_IDENTIFIED",
    "SUMMARY_GENERATED",
    "FOLLOW_UPS_DRAFTED",
    "OPTIONAL_ANALYSES_GENERATED",
    "VALIDATION_COMPLETE",
    "RESULTS_FINALISED",
]

current_stage = "INIT"
completed_stages = []
failed_stages = []
stage_timings = {}


def advance(expected_current: str, next_stage: str):
    """Enforce stage progression."""
    global current_stage

    if current_stage != expected_current:
        error_msg = f"Stage violation: expected {expected_current}, got {current_stage}"
        log_error(error_msg)
        raise RuntimeError(error_msg)

    current_stage = next_stage
    log_stage_start(next_stage)


def complete_stage(stage_name: str, duration: float):
    """Mark stage as complete."""
    global current_stage

    completed_stages.append(stage_name)
    stage_timings[stage_name] = duration
    log_stage_complete(stage_name, duration)


def fail_stage(stage_name: str, error: str):
    """Mark stage as failed."""
    global current_stage

    failed_stages.append(stage_name)
    log_error(f"Stage '{stage_name}' failed: {error}")


def run_pipeline():
    """Execute the complete email analysis pipeline."""
    global current_stage

    log_info("🚀 Starting Email Analysis Pipeline...")
    pipeline_start = time.time()

    try:
        # =====================================================================
        # Stage 0: Load Thread
        # =====================================================================
        advance("INIT", "THREAD_LOADED")
        stage_start = time.time()

        try:
            log_info("Loading email thread from data/thread.txt...")
            thread_path = Path("data/thread.txt")

            if not thread_path.exists():
                raise FileNotFoundError("data/thread.txt not found")

            with open(thread_path, "r") as f:
                thread_content = f.read()

            log_success(f"Thread loaded successfully ({len(thread_content)} bytes)")
            complete_stage("THREAD_LOADED", time.time() - stage_start)

        except Exception as e:
            fail_stage("THREAD_LOADED", str(e))
            raise

        # =====================================================================
        # Stage 1: Parse Emails (Deterministic)
        # =====================================================================
        advance("THREAD_LOADED", "EMAILS_PARSED")
        stage_start = time.time()

        try:
            log_info("Parsing emails into structured records...")
            from STAGES.emails_parsed import parse_emails

            emails = parse_emails(thread_content)
            log_success(f"Parsed {len(emails)} emails")
            complete_stage("EMAILS_PARSED", time.time() - stage_start)

        except Exception as e:
            fail_stage("EMAILS_PARSED", str(e))
            raise

        # =====================================================================
        # Stage 2: Build Conversation Graph (Deterministic)
        # =====================================================================
        advance("EMAILS_PARSED", "CONVERSATION_GRAPH_BUILT")
        stage_start = time.time()

        try:
            log_info("Building conversation graph...")
            from STAGES.conversation_graph_built import build_graph

            graph = build_graph(emails)
            log_success("Conversation graph built")
            complete_stage("CONVERSATION_GRAPH_BUILT", time.time() - stage_start)

        except Exception as e:
            fail_stage("CONVERSATION_GRAPH_BUILT", str(e))
            raise

        # =====================================================================
        # Stage 3: Identify Subthreads (Deterministic)
        # =====================================================================
        advance("CONVERSATION_GRAPH_BUILT", "SUBTHREADS_IDENTIFIED")
        stage_start = time.time()

        try:
            log_info("Identifying subthreads...")
            from STAGES.subthreads_identified import identify_subthreads

            subthreads = identify_subthreads(emails)
            log_success(f"Identified {len(subthreads)} subthreads")
            complete_stage("SUBTHREADS_IDENTIFIED", time.time() - stage_start)

        except Exception as e:
            fail_stage("SUBTHREADS_IDENTIFIED", str(e))
            raise

        # Save parsed thread
        parsed_thread = {
            "emails": [e.dict(by_alias=True) for e in emails],
            "conversation_graph": graph,
            "subthreads": subthreads,
        }

        Path("ARTIFACTS").mkdir(exist_ok=True)
        with open("ARTIFACTS/parsed_thread.json", "w") as f:
            json.dump(parsed_thread, f, indent=2)
        log_artifact_saved("ARTIFACTS/parsed_thread.json", len(emails))

        # =====================================================================
        # Stage 4: Extract Facts & Decisions (LLM - Stage 1)
        # =====================================================================
        advance("SUBTHREADS_IDENTIFIED", "FACTS_AND_DECISIONS_EXTRACTED")
        stage_start = time.time()

        try:
            log_info("Extracting facts and decisions (LLM)...")
            from STAGES.facts_and_decisions_extracted import extract_facts_and_decisions

            facts = extract_facts_and_decisions()
            log_success(
                f"Extracted {len(facts['decisions'])} decisions, "
                f"{len(facts['risks'])} risks"
            )
            complete_stage("FACTS_AND_DECISIONS_EXTRACTED", time.time() - stage_start)

        except Exception as e:
            fail_stage("FACTS_AND_DECISIONS_EXTRACTED", str(e))
            raise

        # =====================================================================
        # Stage 5: Extract Action Items (LLM - Stage 2)
        # =====================================================================
        advance("FACTS_AND_DECISIONS_EXTRACTED", "ACTION_ITEMS_EXTRACTED")
        stage_start = time.time()

        try:
            log_info("Extracting action items (LLM)...")
            from STAGES.actions_items_extracted import extract_action_items

            actions = extract_action_items()
            log_success(f"Extracted {len(actions['action_items'])} action items")
            complete_stage("ACTION_ITEMS_EXTRACTED", time.time() - stage_start)

        except Exception as e:
            fail_stage("ACTION_ITEMS_EXTRACTED", str(e))
            raise

        # =====================================================================
        # Stage 6: Identify Conflicts (LLM - Stage 3)
        # =====================================================================
        advance("ACTION_ITEMS_EXTRACTED", "CONFLICTS_IDENTIFIED")
        stage_start = time.time()

        try:
            log_info("Identifying conflicts (LLM)...")
            from STAGES.conflicts_identified import identify_conflicts

            conflicts = identify_conflicts()
            log_success(f"Identified {len(conflicts['conflicts'])} conflicts")
            complete_stage("CONFLICTS_IDENTIFIED", time.time() - stage_start)

        except Exception as e:
            fail_stage("CONFLICTS_IDENTIFIED", str(e))
            raise

        # =====================================================================
        # Stage 7: Generate Executive Summary (Deterministic)
        # =====================================================================
        advance("CONFLICTS_IDENTIFIED", "SUMMARY_GENERATED")
        stage_start = time.time()

        try:
            log_info("Generating executive summary (deterministic)...")
            from STAGES.summary_generated import generate_executive_summary

            summary = generate_executive_summary()
            log_success("Executive summary generated")
            log_artifact_saved("ARTIFACTS/executive_summary.md", 1)
            complete_stage("SUMMARY_GENERATED", time.time() - stage_start)

        except Exception as e:
            fail_stage("SUMMARY_GENERATED", str(e))
            raise

        # =====================================================================
        # Stage 8: Draft Follow-ups (LLM - Stage 4)
        # =====================================================================
        advance("SUMMARY_GENERATED", "FOLLOW_UPS_DRAFTED")
        stage_start = time.time()

        try:
            log_info("Drafting follow-up communications (LLM)...")
            from STAGES.follow_ups_drafted import draft_follow_ups

            drafts = draft_follow_ups()
            log_success(f"Drafted {len(drafts['follow_up_drafts'])} follow-up communications")
            complete_stage("FOLLOW_UPS_DRAFTED", time.time() - stage_start)

        except Exception as e:
            fail_stage("FOLLOW_UPS_DRAFTED", str(e))
            raise

        # =====================================================================
        # Stage 9: Optional Analyses (LLM - Optional)
        # =====================================================================
        advance("FOLLOW_UPS_DRAFTED", "OPTIONAL_ANALYSES_GENERATED")
        stage_start = time.time()

        try:
            log_info("Generating optional analyses...")
            from STAGES.optional_analyses_generated import generate_optional_analyses

            optional_results = generate_optional_analyses()
            log_success(
                f"Optional analyses: {sum(1 for v in optional_results.values() if v)}/3 completed"
            )
            complete_stage("OPTIONAL_ANALYSES_GENERATED", time.time() - stage_start)

        except Exception as e:
            fail_stage("OPTIONAL_ANALYSES_GENERATED", str(e))
            # Don't raise - optional stage failures don't halt pipeline

        # =====================================================================
        # Stage 10: Validation
        # =====================================================================
        advance("OPTIONAL_ANALYSES_GENERATED", "VALIDATION_COMPLETE")
        stage_start = time.time()

        try:
            log_info("Running validation checks...")
            from validate import run_validation

            validation_results = run_validation()
            log_success(f"Validation: {validation_results['passed']} checks passed")
            complete_stage("VALIDATION_COMPLETE", time.time() - stage_start)

        except Exception as e:
            fail_stage("VALIDATION_COMPLETE", str(e))
            raise

        # =====================================================================
        # Stage 11: Results Finalized
        # =====================================================================
        advance("VALIDATION_COMPLETE", "RESULTS_FINALISED")

        pipeline_duration = time.time() - pipeline_start

        # Print summary
        log_summary(
            {
                "Total Duration": pipeline_duration,
                "Completed Stages": len(completed_stages),
                "Failed Stages": len(failed_stages),
                "LLM Calls": count_llm_calls(),
                "Artifacts Generated": count_artifacts(),
            }
        )

        log_success("✨ Pipeline execution completed successfully!")
        return 0

    except Exception as e:
        log_error(f"Pipeline failed: {str(e)}")
        log_summary(
            {
                "Completed Stages": len(completed_stages),
                "Failed Stages": len(failed_stages),
                "Failed At": current_stage,
            }
        )
        return 1


def count_llm_calls() -> int:
    """Count LLM calls in log."""
    try:
        with open("llm_calls.jsonl", "r") as f:
            return sum(1 for _ in f)
    except:
        return 0


def count_artifacts() -> int:
    """Count generated artifacts."""
    artifacts_dir = Path("ARTIFACTS")
    if not artifacts_dir.exists():
        return 0
    return len(list(artifacts_dir.glob("*")))


if __name__ == "__main__":
    try:
        exit_code = run_pipeline()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_error("\n\n❌ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"\n\n❌ Pipeline crashed: {str(e)}")
        sys.exit(1)
