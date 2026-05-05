"""
Stage 12: Results Finalised - Final pipeline completion and cleanup.
Finalization stage - no logic, just marks completion.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from logger import log_info, log_success


def finalise_results() -> dict:
    """
    Mark pipeline as complete and generate final summary.

    Returns:
        Dictionary with pipeline summary
    """
    log_info("Finalizing pipeline results...")

    # Count artifacts
    artifacts_dir = Path("ARTIFACTS")
    artifacts = []

    if artifacts_dir.exists():
        for item in artifacts_dir.glob("*"):
            if item.is_file():
                size = item.stat().st_size
                artifacts.append({
                    "name": item.name,
                    "size_bytes": size,
                    "path": str(item),
                })

    # Count LLM calls
    llm_call_count = 0
    if os.path.exists("llm_calls.jsonl"):
        with open("llm_calls.jsonl", 'r') as f:
            llm_call_count = sum(1 for line in f if line.strip())

    # Generate summary
    summary = {
        "status": "complete",
        "timestamp": datetime.now().isoformat(),
        "artifacts_generated": len(artifacts),
        "llm_calls_made": llm_call_count,
        "artifacts": artifacts,
    }

    log_success(f"Pipeline complete: {len(artifacts)} artifacts generated, {llm_call_count} LLM calls logged")

    return summary
