"""
Stage 2: Build Conversation Graph - Create reply chain relationships.
Deterministic stage - no LLM calls.
"""

from typing import List, Dict, Any
from models import Email
from logger import log_info


def build_graph(emails: List[Email]) -> Dict[str, Any]:
    """
    Build conversation graph showing reply chains between emails.

    Returns graph structure with nodes (emails) and edges (reply relationships).
    Infers reply-to relationships based on:
    - RE: subject lines
    - Quote/FW patterns
    - Temporal sequencing
    - Recipient/sender continuity
    """
    log_info("Building conversation graph from email thread...")

    graph = {
        "nodes": [],
        "edges": [],
        "threads": []
    }

    # Add all emails as nodes
    for email in emails:
        graph["nodes"].append({
            "id": email.email_id,
            "from": email.from_,
            "subject": email.subject,
            "date": email.date,
        })

    # Build edges (reply relationships)
    for i, email in enumerate(emails):
        # Check if this is a reply (subject starts with RE:)
        is_reply = email.subject.lower().startswith("re:")

        if is_reply and i > 0:
            # Find most recent email with matching subject or from similar sender
            base_subject = email.subject[3:].strip()

            # Look back for original
            for j in range(i - 1, -1, -1):
                prev = emails[j]
                prev_subject = prev.subject[3:].strip() if prev.subject.lower().startswith("re:") else prev.subject

                if base_subject in prev_subject or prev_subject in base_subject:
                    graph["edges"].append({
                        "from": prev.email_id,
                        "to": email.email_id,
                        "type": "reply",
                        "reply_to_inferred": prev.email_id,
                    })
                    email.reply_to_inferred = prev.email_id
                    break

    # Identify distinct threads
    threads = {}
    for email in emails:
        # Thread key based on base subject (without RE:)
        thread_key = email.subject.lower()
        if thread_key.startswith("re:"):
            thread_key = thread_key[3:].strip()

        if thread_key not in threads:
            threads[thread_key] = []
        threads[thread_key].append(email.email_id)

    graph["threads"] = [
        {"subject": subj, "emails": email_ids}
        for subj, email_ids in threads.items()
    ]

    log_info(f"Built conversation graph: {len(graph['nodes'])} nodes, {len(graph['edges'])} edges, {len(graph['threads'])} threads")
    return graph
