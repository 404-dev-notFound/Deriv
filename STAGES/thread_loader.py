"""
Stage 0: Load Thread - Read email thread from disk into memory.
Deterministic stage - no LLM calls.
"""

from pathlib import Path
from logger import log_info, log_error


def load_thread(filepath: str = "data/thread.txt") -> str:
    """
    Load email thread from file.

    Args:
        filepath: Path to thread.txt file

    Returns:
        Raw thread content as string

    Raises:
        FileNotFoundError: If thread file not found
        IOError: If file cannot be read
    """
    log_info(f"Loading email thread from {filepath}...")

    try:
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Email thread file not found: {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            raise ValueError("Email thread file is empty")

        size_kb = len(content) / 1024
        log_info(f"Loaded {size_kb:.1f} KB from {filepath}")

        return content

    except FileNotFoundError as e:
        log_error(f"File not found: {str(e)}")
        raise
    except IOError as e:
        log_error(f"Cannot read file: {str(e)}")
        raise
    except Exception as e:
        log_error(f"Error loading thread: {str(e)}")
        raise
