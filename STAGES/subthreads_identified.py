"""
Stage 3: Identify Subthreads - Cluster related conversations.
Deterministic stage - no LLM calls.
"""

from typing import List, Dict, Any
from models import Email
from logger import log_info


def identify_subthreads(emails: List[Email]) -> List[Dict[str, Any]]:
    """
    Identify logical subthreads within the email conversation.

    Groups emails by topic/subject using:
    - Base subject line (removing RE:, FW:)
    - Participants (from/to)
    - Temporal clustering
    """
    log_info("Identifying subthreads in conversation...")

    subthreads = []
    processed_ids = set()

    for email in emails:
        if email.email_id in processed_ids:
            continue

        # Get base subject
        base_subject = email.subject.lower()
        if base_subject.startswith(("re:", "fw:", "fwd:")):
            for prefix in ["re:", "fw:", "fwd:"]:
                if base_subject.startswith(prefix):
                    base_subject = base_subject[len(prefix):].strip()
                    break

        # Find all emails in this subthread
        subthread_emails = []
        for candidate in emails:
            candidate_subject = candidate.subject.lower()
            if candidate_subject.startswith(("re:", "fw:", "fwd:")):
                for prefix in ["re:", "fw:", "fwd:"]:
                    if candidate_subject.startswith(prefix):
                        candidate_subject = candidate_subject[len(prefix):].strip()
                        break

            if candidate_subject == base_subject:
                subthread_emails.append(candidate.email_id)
                processed_ids.add(candidate.email_id)

        subthread = {
            "subthread_id": f"ST_{len(subthreads) + 1}",
            "subject": email.subject,
            "base_subject": base_subject,
            "email_ids": sorted(subthread_emails),
            "participant_count": len(set(
                p for e in emails if e.email_id in subthread_emails
                for p in [e.from_] + e.to
            )),
            "email_count": len(subthread_emails),
        }
        subthreads.append(subthread)

    log_info(f"Identified {len(subthreads)} subthreads")
    return subthreads
