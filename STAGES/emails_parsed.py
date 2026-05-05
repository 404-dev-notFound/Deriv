"""
Stage 1: Parse Emails - Extract structured email records from thread text.
Deterministic stage - no LLM calls.
"""

import re
from typing import List
from models import Email
from logger import log_info, log_error


def parse_emails(thread_content: str) -> List[Email]:
    """
    Parse raw email thread text into structured Email objects.

    Expected format (email boundaries marked by "---" or similar):
    From: sender@example.com
    To: recipient@example.com
    Date: 2025-05-05T10:00:00Z
    Subject: Email subject

    Email body text here.
    """
    log_info("Parsing email thread into structured records...")

    # Split by common email delimiters
    email_blocks = re.split(
        r'\n---+\n|\n=+\n|\n\*+\n',
        thread_content,
        flags=re.MULTILINE
    )

    emails = []
    email_counter = 1

    for block in email_blocks:
        if not block.strip():
            continue

        try:
            # Extract email components
            from_match = re.search(r'From:\s*(.+?)(?:\n|$)', block)
            to_match = re.search(r'To:\s*(.+?)(?:\n|$)', block)
            date_match = re.search(r'Date:\s*(.+?)(?:\n|$)', block)
            subject_match = re.search(r'Subject:\s*(.+?)(?:\n|$)', block)

            # Extract body (everything after the headers)
            header_end = max(
                m.end() if m else 0
                for m in [from_match, to_match, date_match, subject_match]
            )
            body = block[header_end:].strip()

            if not from_match or not to_match:
                continue

            from_addr = from_match.group(1).strip()
            to_addrs = [a.strip() for a in to_match.group(1).split(',')]
            date_str = date_match.group(1).strip() if date_match else "2025-05-05T00:00:00Z"
            subject = subject_match.group(1).strip() if subject_match else "(no subject)"

            email = Email(
                email_id=f"EMAIL_{email_counter}",
                from_=from_addr,
                to=to_addrs,
                date=date_str,
                subject=subject,
                body=body,
            )
            emails.append(email)
            email_counter += 1

        except Exception as e:
            log_error(f"Failed to parse email block: {str(e)}")
            continue

    log_info(f"Parsed {len(emails)} emails from thread")
    return emails
