#!/usr/bin/env python3
"""Quick setup verification script."""

import sys
import os
from pathlib import Path

def check(description: str, func) -> bool:
    """Run check and report result."""
    try:
        result = func()
        status = "✓" if result else "✗"
        print(f"{status} {description}")
        return result
    except Exception as e:
        print(f"✗ {description}: {str(e)}")
        return False

def main():
    print("Email Analysis Pipeline - Setup Verification\n")

    checks = [
        ("Python version", lambda: sys.version_info >= (3, 8)),
        ("requirements.txt exists", lambda: os.path.exists("requirements.txt")),
        ("config.py exists", lambda: os.path.exists("config.py")),
        ("logger.py exists", lambda: os.path.exists("logger.py")),
        ("models.py exists", lambda: os.path.exists("models.py")),
        ("run_pipeline.py exists", lambda: os.path.exists("run_pipeline.py")),
        ("validate.py exists", lambda: os.path.exists("validate.py")),
        ("data/thread.txt exists", lambda: os.path.exists("data/thread.txt")),
        ("STAGES/ directory exists", lambda: os.path.isdir("STAGES")),
        ("Dockerfile exists", lambda: os.path.exists("Dockerfile")),
        ("docker-compose.yml exists", lambda: os.path.exists("docker-compose.yml")),
        (".env file exists", lambda: os.path.exists(".env")),
        ("STAGES/llm_helper.py exists", lambda: os.path.exists("STAGES/llm_helper.py")),
        ("STAGES/emails_parsed.py exists", lambda: os.path.exists("STAGES/emails_parsed.py")),
    ]

    passed = sum(1 for desc, check_fn in checks if check(desc, check_fn))
    total = len(checks)

    print(f"\n{passed}/{total} checks passed", end="")

    if passed == total:
        print(" ✓")
        print("\nSetup complete! Run: python run_pipeline.py")
        return 0
    else:
        print(" ✗")
        print(f"\nSetup incomplete: {total - passed} check(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
