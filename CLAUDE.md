# CLAUDE.md — Email Pipeline: Replayable Email Thread Analysis

This file specifies how to build a replayable, auditable email thread analysis pipeline
that deterministically parses messy email chains, extracts facts/decisions/actions/risks/conflicts
via separate LLM calls, and generates follow-up communications grounded in extracted data.

---

## What kind of project this is

You are building a **replayable, staged email analysis pipeline** that:

- Reads raw, messy email threads from disk (`thread.txt`)
- Deterministically parses and reconstructs conversation structure
- Makes targeted LLM calls at defined stages to extract facts, decisions, actions, risks, and conflicts
- Saves every intermediate artifact to disk
- Logs every LLM call to `llm_calls.jsonl`
- Can be fully re-run from a clean state by an evaluator

The evaluator will:
1. Delete all generated artifacts
2. Optionally replace `thread.txt` with an equivalent messy email chain
3. Run `python run_pipeline.py`
4. Run `python validate.py`
5. Inspect artifacts for correctness, determinism, and stage separation

Static precomputed outputs will fail. Everything must regenerate from the pipeline.

---

## Project file structure

```
project-root/
├── run_pipeline.py              # single entry point, enforces stage order
├── validate.py                  # evaluator runs this — check ALL artifacts
├── requirements.txt             # minimal deps, pin versions
├── CLAUDE.md                    # this file
│
├── data/                        # input files (read-only during pipeline)
│   └── thread.txt              # raw email thread (messy, multi-threaded)
│
├── stages/
│   ├── 01_load_thread.py       # load + validate thread format
│   ├── 02_parse_emails.py      # deterministic email parsing → email records
│   ├── 03_build_graph.py       # conversation graph + sub-threads (deterministic)
│   ├── 04_extract_facts.py     # LLM Stage 1: extract facts, decisions, risks
│   ├── 05_extract_actions.py   # LLM Stage 2: extract action items with status taxonomy
│   ├── 06_identify_conflicts.py # LLM Stage 3: identify tensions and blockers
│   ├── 07_generate_summary.py   # Executive summary (deterministic, from extracted data)
│   ├── 08_draft_followups.py    # LLM Stage 4: draft follow-up communications
│   ├── 09_optional_analyses.py  # LLM optional: decision log, health score, stakeholders
│   └── 10_audit.py             # validation checks
│
├── artifacts/                   # all generated outputs land here
│   ├── parsed_thread.json       # email records + conversation graph
│   ├── facts_decisions.json     # Stage 1 output: facts, decisions, risks
│   ├── action_items.json        # Stage 2 output: actions with status taxonomy
│   ├── conflicts.json           # Stage 3 output: conflicts + tensions
│   ├── extraction_report.json   # combined Stage 1-2 summary
│   ├── executive_summary.md     # generated from extracted data (deterministic)
│   ├── follow_up_drafts.md      # Stage 4 output: drafted communications
│   ├── decision_log.json        # optional: all decisions with basis
│   ├── thread_health_score.json # optional: quality metrics with evidence
│   └── missing_stakeholders.md  # optional: identified gaps + briefings
│
├── llm_calls.jsonl              # append one line per LLM call
└── email_analysis_model.md      # document every extraction rule and validation
```

---

## Stage enforcement — implement this in every project

```python
# run_pipeline.py

STAGES = [
    "INIT",
    "THREAD_LOADED",
    "EMAILS_PARSED",
    "CONVERSATION_GRAPH_BUILT",
    "SUBTHREADS_IDENTIFIED",
    "FACTS_AND_DECISIONS_EXTRACTED",    # LLM Stage 1
    "ACTION_ITEMS_EXTRACTED",           # LLM Stage 2
    "CONFLICTS_IDENTIFIED",             # LLM Stage 3
    "SUMMARY_GENERATED",                # deterministic
    "FOLLOW_UPS_DRAFTED",               # LLM Stage 4
    "OPTIONAL_ANALYSES_GENERATED",      # LLM (optional)
    "VALIDATION_COMPLETE",
    "RESULTS_FINALISED",
]

current_stage = "INIT"

def advance(expected_current: str, next_stage: str):
    global current_stage
    assert current_stage == expected_current, (
        f"Stage violation: expected {expected_current}, got {current_stage}"
    )
    current_stage = next_stage
    print(f"[STAGE] {current_stage}")

# Usage
advance("INIT", "THREAD_LOADED")
load_thread()

advance("THREAD_LOADED", "EMAILS_PARSED")
parse_emails()  # deterministic

advance("EMAILS_PARSED", "CONVERSATION_GRAPH_BUILT")
build_conversation_graph()  # deterministic

advance("CONVERSATION_GRAPH_BUILT", "SUBTHREADS_IDENTIFIED")
identify_subthreads()  # deterministic

advance("SUBTHREADS_IDENTIFIED", "FACTS_AND_DECISIONS_EXTRACTED")
extract_facts_and_decisions()  # LLM Stage 1

advance("FACTS_AND_DECISIONS_EXTRACTED", "ACTION_ITEMS_EXTRACTED")
extract_action_items()  # LLM Stage 2

advance("ACTION_ITEMS_EXTRACTED", "CONFLICTS_IDENTIFIED")
identify_conflicts()  # LLM Stage 3

advance("CONFLICTS_IDENTIFIED", "SUMMARY_GENERATED")
generate_executive_summary()  # deterministic, from extracted data

advance("SUMMARY_GENERATED", "FOLLOW_UPS_DRAFTED")
draft_follow_ups()  # LLM Stage 4

advance("FOLLOW_UPS_DRAFTED", "OPTIONAL_ANALYSES_GENERATED")
generate_optional_analyses()  # LLM (optional)

advance("OPTIONAL_ANALYSES_GENERATED", "VALIDATION_COMPLETE")
validate_all_artifacts()

advance("VALIDATION_COMPLETE", "RESULTS_FINALISED")
print("[PIPELINE COMPLETE]")
```

**CRITICAL**: Stage order and names must match Problem.md exactly. Never skip or reorder stages.

---

## Deterministic vs LLM — the core rule

| Task | Method | Rule |
|---|---|---|
| Email parsing | Code only | Regex/text processing, no LLM |
| Conversation graph building | Code only | Infer reply-to deterministically |
| Sub-thread identification | Code only | Cluster by topic + participants |
| Executive summary generation | Code only | Deterministic template from extracted data |
| Facts & decisions extraction | LLM | Stage 1 — controlled vocabulary (confirmed/implied/assumed) |
| Action item extraction | LLM | Stage 2 — must use action status taxonomy |
| Conflict identification | LLM | Stage 3 — conflict type + severity vocabulary |
| Follow-up drafting | LLM | Stage 4 — tone/recipient constraints, grounded in facts |
| Optional analyses | LLM | Decision log, health scores, stakeholder gaps |

**CRITICAL CONSTRAINT**: Facts, actions, and conflicts must be extracted in **SEPARATE LLM calls** (not one combined call). Each call gets its own log entry in `llm_calls.jsonl`.

If the prompt says "do not ask an LLM to compute this value", treat that as a hard constraint. Validate all constraints in `validate.py`.

---

## LLM call pattern — use this for every call

```python
import hashlib, json, datetime
from anthropic import Anthropic

client = Anthropic()

def llm_call(
    stage: str,
    system: str,
    user_content: str,
    input_artifacts: list[str],
    output_artifact: str,
    entity_id: str | None = None,
) -> str:
    """Make an LLM call and log it to llm_calls.jsonl."""
    prompt_hash = hashlib.sha256(
        (system + user_content).encode()
    ).hexdigest()[:16]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    )

    result = response.content[0].text

    # Log the call (required for auditing)
    log_entry = {
        "stage": stage,
        "entity_id": entity_id,      # null for whole-thread calls
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "prompt_hash": prompt_hash,
        "input_artifacts": input_artifacts,
        "output_artifact": output_artifact,
    }
    with open("llm_calls.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result


def parse_json_response(text: str) -> dict | list:
    """Strip markdown fences and parse JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
```

---

## Controlled vocabularies — enforce after EVERY LLM call

```python
# Fact & Decision Vocabulary
ALLOWED_CONFIDENCE = {"confirmed", "implied", "assumed"}
ALLOWED_RISK_SEVERITY = {"critical", "high", "medium", "low"}

# Action Status Taxonomy (CRITICAL — use ONLY these)
ALLOWED_ACTION_STATUS = {
    "confirmed",   # owner explicitly accepted/acknowledged
    "requested",   # someone asked, but no acknowledgement
    "implied",     # suggested or logically required
    "completed",   # action finished within thread
    "pending",     # unresolved at end of thread
}

# Conflict Vocabulary
ALLOWED_CONFLICT_TYPES = {
    "interpersonal_tension",
    "unresolved_dependency",
    "decision_reversal",
    "unaddressed_risk",
    "blocked_action",
}
ALLOWED_CONFLICT_SEVERITY = {"critical", "high", "medium", "low"}


def enforce_vocabulary(value: str | list, allowed: set, field: str):
    """Validate extracted values against allowed vocabulary."""
    values = [value] if isinstance(value, str) else value
    invalid = [v for v in values if v not in allowed]
    if invalid:
        raise ValueError(
            f"{field}: invalid values {invalid}. Allowed: {allowed}"
        )


# Usage: After Stage 1 LLM call
for decision in extracted_decisions:
    enforce_vocabulary(
        decision["confidence"], ALLOWED_CONFIDENCE, "decision.confidence"
    )

for risk in extracted_risks:
    enforce_vocabulary(
        risk["severity"], ALLOWED_RISK_SEVERITY, "risk.severity"
    )

# After Stage 2 LLM call
for action in extracted_actions:
    enforce_vocabulary(
        action["status"], ALLOWED_ACTION_STATUS, "action.status"
    )

# After Stage 3 LLM call
for conflict in extracted_conflicts:
    enforce_vocabulary(
        conflict["type"], ALLOWED_CONFLICT_TYPES, "conflict.type"
    )
    enforce_vocabulary(
        conflict["severity"], ALLOWED_CONFLICT_SEVERITY, "conflict.severity"
    )
```

**Include all vocabularies in system prompts so the LLM knows them upfront.**
**Validate after every LLM call — never trust raw LLM output directly.**

---

## System Prompt: Stage 1 — Facts & Decisions Extraction

```python
SYSTEM_EXTRACT_FACTS = """
You are an email thread analysis engine. Your job is to extract facts, decisions, 
risks, and open questions from a parsed email thread.

You will receive a JSON array of parsed emails. Each email has:
- email_id: unique identifier (EMAIL_1, EMAIL_2, etc.)
- from: sender address
- to: recipient list
- date: date string
- subject: subject line
- body: email body text

Extract:

1. **Decisions made**: Who decided what, when, and what was the basis?
2. **Open questions**: What is still unresolved?
3. **Blockers**: What is preventing progress?
4. **Risks flagged**: What concerns were raised about project success, SLA, legal risk, budget?

Confidence levels:
- confirmed: explicit statement or clear agreement
- implied: logically follows from the thread but not stated directly
- assumed: reasonable interpretation but uncertain

For each extracted item, cite the email_id(s) that support it.

Output valid JSON only. No markdown fences.

Output schema:
{
  "decisions": [{"decision_id": "D1", "decision_text": "...", "made_by": "...", 
    "date": "...", "confidence": "confirmed|implied|assumed", "email_id_sources": [...]}],
  "risks": [{"risk_id": "R1", "risk_text": "...", "raised_by": "...", 
    "severity": "critical|high|medium|low", "email_id_sources": [...]}],
  "open_questions": [...],
  "blockers": [...]
}
"""
```

## System Prompt: Stage 2 — Action Items Extraction

```python
SYSTEM_EXTRACT_ACTIONS = """
You are analyzing an email thread to extract action items.

Action Status Taxonomy (use ONLY these values):
- confirmed: assigned person explicitly acknowledged or accepted the task
- requested: someone asked another person to do something, but no acknowledgement
- implied: action is suggested or logically required, but not directly assigned
- completed: the action was completed within the thread
- pending: the action remains unresolved by the final email

Rules:
- Every action must have an owner (person or role).
- If no deadline stated, set deadline_if_stated to null.
- If action completed, cite the email_id where completion happened.
- Cite all email_id_sources that led to this action identification.

Output valid JSON only.

Output schema:
{
  "action_items": [{"action_id": "A1", "owner": "...", "action": "...", 
    "deadline_if_stated": "string | null", "status": "confirmed|requested|implied|completed|pending", 
    "email_id_sources": [...], "completion_email_id": "EMAIL_X | null"}]
}
"""
```

## System Prompt: Stage 3 — Conflict & Tension Identification

```python
SYSTEM_IDENTIFY_CONFLICTS = """
You are analyzing an email thread to identify conflicts, tensions, and blockers.

Conflict Types:
- interpersonal_tension: disagreement between individuals or teams
- unresolved_dependency: one team waiting on another, dependency not met
- decision_reversal: earlier decision contradicted or overridden later
- unaddressed_risk: risk was flagged but not actively addressed
- blocked_action: action cannot proceed due to external block

For each conflict, explain why it matters and cite the email sources.

Output valid JSON only.

Output schema:
{
  "conflicts": [{"conflict_id": "C1", "type": "interpersonal_tension|unresolved_dependency|decision_reversal|unaddressed_risk|blocked_action",
    "description": "...", "severity": "critical|high|medium|low", "email_id_sources": [...], "why_it_matters": "..."}]
}
"""
```

## System Prompt: Stage 4 — Follow-Up Drafting

```python
SYSTEM_DRAFT_FOLLOWUPS = """
You are drafting follow-up communications based on extracted email thread data.

You will receive:
- Parsed emails from the thread
- Extracted facts, decisions, actions, and conflicts
- Context about who is communicating to whom

Draft three communications:
1. Priya's message to Client A's technical contact (address SLA complication)
2. Sarah's end-of-Tuesday update to the full team
3. James's rate-limiting policy document section header and 3-bullet scope

Rules:
- Every draft must cite extracted facts or email_ids it relies on.
- Ground all drafts in extracted data (no hallucination).
- Priya's draft MUST explicitly address the 5k req/min SLA complication.
- Acknowledge risks and blockers where relevant.
- Tone: professional, empathetic, action-oriented.

Output valid JSON only.
"""
```

---

## Email parsing — deterministic extraction from thread.txt

```python
import re, json
from datetime import datetime

def parse_emails_from_thread(thread_text: str) -> list:
    """
    Parse raw email thread into structured records.
    Deterministic — regex only, no LLM, no hallucination.
    """
    emails = []
    email_id = 1
    
    # Pattern to identify email boundaries (From: line signals new email)
    EMAIL_PATTERN = re.compile(
        r'^From:\s*(.+?)$\n'
        r'^To:\s*(.+?)$\n'
        r'^Date:\s*(.+?)$\n'
        r'^Subject:\s*(.+?)$\n'
        r'^$\n'
        r'(.*?)(?=^From:|$)',
        re.MULTILINE | re.DOTALL
    )
    
    for match in EMAIL_PATTERN.finditer(thread_text):
        from_addr = match.group(1).strip()
        to_addrs = [e.strip() for e in match.group(2).split(',')]
        date_str = match.group(3).strip()
        subject = match.group(4).strip()
        body = match.group(5).strip()
        
        emails.append({
            "email_id": f"EMAIL_{email_id}",
            "from": from_addr,
            "to": to_addrs,
            "date": date_str,
            "subject": subject,
            "body": body,
            "reply_to_inferred": None,  # filled in next stage
        })
        email_id += 1
    
    return emails


def infer_reply_relationships(emails: list) -> list:
    """
    Infer reply-to relationships by matching subjects and participants.
    Pure deterministic logic — no LLM.
    """
    for i, email in enumerate(emails):
        # Strip "RE:" for comparison
        current_subject = email["subject"].replace("RE: ", "").strip()
        
        # Search backwards for matching subject + participant
        for j in range(i - 1, -1, -1):
            prev_subject = emails[j]["subject"].replace("RE: ", "").strip()
            
            # Match if subject same AND sender in previous recipients
            if (current_subject == prev_subject and 
                email["from"] in emails[j]["to"]):
                email["reply_to_inferred"] = emails[j]["email_id"]
                break
    
    return emails
```

Always seed random data for reproducibility.

---

## Conversation graph & sub-thread identification — deterministic

```python
def build_conversation_graph(emails: list) -> dict:
    """
    Build a graph showing reply relationships and thread structure.
    Deterministic — no LLM.
    """
    graph = {
        "emails": emails,
        "reply_chains": [],  # list of linear chains
        "branches": {},      # email_id -> list of replies
        "participants": set(),
    }
    
    # Build branches (email_id -> list of direct replies)
    branches = {}
    for email in emails:
        parent_id = email.get("reply_to_inferred")
        if parent_id:
            if parent_id not in branches:
                branches[parent_id] = []
            branches[parent_id].append(email["email_id"])
    
    # Collect participants
    for email in emails:
        graph["participants"].add(email["from"])
        graph["participants"].extend(email["to"])
    
    graph["branches"] = branches
    return graph


def identify_subthreads(emails: list, graph: dict) -> list:
    """
    Identify distinct sub-threads by clustering similar subjects + participants.
    Deterministic — no LLM.
    """
    subthreads = []
    processed = set()
    
    for email in emails:
        if email["email_id"] in processed:
            continue
        
        # Base subject (strip RE:)
        base_subject = email["subject"].replace("RE: ", "").strip()
        
        # Gather all emails with same base subject
        subthread = {
            "subject": base_subject,
            "emails": [],
            "participants": set(),
        }
        
        for other in emails:
            other_subject = other["subject"].replace("RE: ", "").strip()
            if other_subject == base_subject and other["email_id"] not in processed:
                subthread["emails"].append(other["email_id"])
                subthread["participants"].add(other["from"])
                subthread["participants"].update(other["to"])
                processed.add(other["email_id"])
        
        subthreads.append(subthread)
    
    return subthreads
```

---

## Executive Summary Generation — deterministic from extracted data

```python
def generate_executive_summary(
    facts: dict,
    actions: dict,
    conflicts: dict,
) -> str:
    """
    Generate ~200 word summary from extracted data.
    Deterministic — no LLM, template-based.
    """
    lines = []
    
    # Current situation
    decisions = facts.get("decisions", [])
    lines.append("## Current Situation")
    if decisions:
        decision_texts = [d["decision_text"] for d in decisions[:2]]
        lines.append(f"Key decisions made: {'; '.join(decision_texts)}")
    
    # Key blockers
    blockers = facts.get("blockers", [])
    if blockers:
        lines.append("\n## Key Blockers")
        for blocker in blockers[:3]:
            lines.append(f"- {blocker['blocker']} ({blocker['impact']})")
    
    # Immediate next actions
    pending_actions = [
        a for a in actions.get("action_items", [])
        if a["status"] in ["confirmed", "pending"]
    ]
    if pending_actions:
        lines.append("\n## Immediate Next Actions")
        for action in pending_actions[:3]:
            deadline = action.get("deadline_if_stated") or "no deadline stated"
            lines.append(f"- {action['action']} (owner: {action['owner']}, {deadline})")
    
    # Unresolved risks
    risks = facts.get("risks", [])
    critical_risks = [r for r in risks if r["severity"] in ["critical", "high"]]
    if critical_risks:
        lines.append("\n## Unresolved Risks")
        for risk in critical_risks[:2]:
            lines.append(f"- {risk['risk_text']} (severity: {risk['severity']})")
    
    # Tensions
    critical_conflicts = [
        c for c in conflicts.get("conflicts", [])
        if c["severity"] in ["critical", "high"]
    ]
    if critical_conflicts:
        lines.append("\n## Unresolved Tensions")
        for conflict in critical_conflicts[:2]:
            lines.append(f"- {conflict['type']}: {conflict['description']}")
    
    return "\n".join(lines)
```

---

## Validate.py — what to check

Write validate.py so the evaluator can run it independently. It must exit with code 0 on success and non-zero on failure.

```python
#!/usr/bin/env python3
"""Validation script. Run after the pipeline to verify all artifacts."""

import json, os, sys

errors = []

def check(condition: bool, message: str):
    if not condition:
        errors.append(message)
        print(f"  FAIL  {message}")
    else:
        print(f"  OK    {message}")


# ── 1. Required files exist ──────────────────────────────────────────────────
REQUIRED = [
    "artifacts/parsed_thread.json",
    "artifacts/facts_decisions.json",
    "artifacts/action_items.json",
    "artifacts/conflicts.json",
    "artifacts/executive_summary.md",
    "artifacts/follow_up_drafts.md",
    "llm_calls.jsonl",
]
for path in REQUIRED:
    check(os.path.exists(path), f"File exists: {path}")

# ── 2. JSON files are valid ──────────────────────────────────────────────────
json_files = [p for p in REQUIRED if p.endswith(".json")]
for path in json_files:
    if os.path.exists(path):
        try:
            with open(path) as f:
                json.load(f)
            check(True, f"Valid JSON: {path}")
        except Exception as e:
            check(False, f"Invalid JSON {path}: {e}")

# ── 3. All emails have required fields ───────────────────────────────────────
with open("artifacts/parsed_thread.json") as f:
    parsed = json.load(f)
    emails = parsed.get("emails", [])

for email in emails:
    check(
        all(k in email for k in {"email_id", "from", "to", "date", "subject", "body"}),
        f"Email {email.get('email_id')} has all required fields"
    )

# ── 4. Conversation graph exists ─────────────────────────────────────────────
check("conversation_graph" in parsed, "Conversation graph created")

# ── 5. Sub-threads identified ────────────────────────────────────────────────
check("subthreads" in parsed, "Sub-threads identified (at least 2 expected)")

# ── 6. Action status taxonomy enforced ───────────────────────────────────────
with open("artifacts/action_items.json") as f:
    actions = json.load(f)

ALLOWED_STATUS = {"confirmed", "requested", "implied", "completed", "pending"}
for action in actions.get("action_items", []):
    status = action.get("status")
    check(
        status in ALLOWED_STATUS,
        f"Action {action.get('action_id')} has valid status: {status}"
    )

# ── 7. All extracted items cite valid email_ids ──────────────────────────────
valid_email_ids = {e["email_id"] for e in emails}

with open("artifacts/facts_decisions.json") as f:
    facts = json.load(f)
    for decision in facts.get("decisions", []):
        for eid in decision.get("email_id_sources", []):
            check(
                eid in valid_email_ids,
                f"Decision {decision.get('decision_id')} cites valid email_id: {eid}"
            )

with open("artifacts/conflicts.json") as f:
    conflicts = json.load(f)
    for conflict in conflicts.get("conflicts", []):
        for eid in conflict.get("email_id_sources", []):
            check(
                eid in valid_email_ids,
                f"Conflict {conflict.get('conflict_id')} cites valid email_id: {eid}"
            )

# ── 8. Facts, actions, conflicts extracted in separate LLM calls ────────────
with open("llm_calls.jsonl") as f:
    llm_logs = [json.loads(line) for line in f if line.strip()]

stages_present = {log["stage"] for log in llm_logs}
check("facts_and_decisions_extraction" in stages_present, "Stage 1 logged")
check("action_items_extraction" in stages_present, "Stage 2 logged")
check("conflict_identification" in stages_present, "Stage 3 logged")

# ── 9. Priya's draft addresses SLA complication ──────────────────────────────
with open("artifacts/follow_up_drafts.md") as f:
    drafts_content = f.read().lower()

check(
    "sla" in drafts_content or "contractual" in drafts_content or "5k" in drafts_content,
    "Priya's draft addresses SLA/contractual complication"
)

# ── Result ───────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"VALIDATION FAILED — {len(errors)} error(s)")
    for err in errors:
        print(f"  - {err}")
    sys.exit(1)
else:
    print("VALIDATION PASSED ✓")
    sys.exit(0)
```

---

## email_analysis_model.md template

Always create this file. It documents all extraction rules and validation.

```markdown
# Email Analysis Model — Extraction Rules & Validation

Version: v1.0.0

## Email Parsing & Thread Reconstruction

### Thread Format
Raw email thread assumed to be multi-threaded, messy, with potential forwarding
and reply chains. Parser uses regex to split on "From:" lines and extract headers.

### Email Record Schema
\`\`\`json
{
  "email_id": "EMAIL_1",
  "from": "name@company.com",
  "to": ["recipient1@company.com", "recipient2@company.com"],
  "date": "Monday 9:02 AM",
  "subject": "RE: Project status",
  "body": "full text",
  "reply_to_inferred": "EMAIL_5 | null"
}
\`\`\`

## Extraction Stages & Vocabularies

### Stage 1: Facts & Decisions
Extracts explicit and implied decisions, risks, blockers, open questions.

**Confidence Levels**: confirmed, implied, assumed
**Risk Severity**: critical, high, medium, low

Every item must cite email_id sources.

### Stage 2: Action Items
Extracts tasks assigned or requested, with ownership and status.

**Status Taxonomy** (CRITICAL):
- confirmed: owner explicitly accepted/acknowledged
- requested: someone asked, but no acknowledgement
- implied: suggested or logically required, not directly assigned
- completed: action finished within thread
- pending: unresolved at end of thread

### Stage 3: Conflict Identification
Identifies interpersonal tensions, unresolved dependencies, blockers.

**Conflict Types**: interpersonal_tension, unresolved_dependency, decision_reversal, unaddressed_risk, blocked_action
**Severity**: critical, high, medium, low

### Stage 4: Follow-Up Drafting
Drafts communications grounded in extracted facts/actions/conflicts.

**Constraints**: Priya's draft must address 5k req/min SLA complication

## Validation Rules

- All email_ids cited must exist in parsed_thread.json
- All action statuses must be in allowed taxonomy
- All risk/conflict severities must be in allowed vocabulary
- Facts, actions, conflicts extracted in SEPARATE LLM calls
- Executive summary generated deterministically from extracted data
- Follow-up drafts grounded in email_ids, no hallucination
- Thread parsing is 100% deterministic (regex/code only)
- Reply-to relationships inferred by subject + participant matching

## Notes

- Every extracted fact/action/risk/conflict MUST cite source email_ids.
- Separate LLM calls enforce auditability.
- Sub-threads should cluster by topic and participant overlap.
```

---

## requirements.txt

```
anthropic>=0.25.0
python-dateutil>=2.8.2
```

Pin versions. Add domain-specific deps as needed.

---

## Common mistakes to avoid

| Mistake | Fix |
|---|---|
| Using LLM to parse raw emails | Parse with regex/code only, deterministic |
| Combining facts+actions+conflicts into one LLM call | Make three separate calls, three log entries |
| Missing email_id sources in extracted items | Always cite which email(s) led to extraction |
| Hardcoding action statuses instead of enforcing taxonomy | Validate after every extraction |
| Priya's draft ignoring SLA detail | Explicitly call out 5k req/min contractual guarantee |
| Static precomputed artifacts | Delete and regenerate from pipeline |
| Conversation graph missing sub-threads | Identify at least two distinct sub-threads |
| "RE:" subject matching too strict | Normalize subjects, match on base text |
| Follow-ups mentioning context not in thread | Ground every statement in email_ids or facts |
| Executive summary not using extracted data | Build from decisions/actions/risks deterministically |
| LLM receives raw email thread | Pass parsed_thread.json with extracted data |
| Vocabulary not validated after extraction | Check status/severity/type immediately after LLM call |

---

## Checklist before submitting

- [ ] `python run_pipeline.py` completes without errors from a clean state
- [ ] `python validate.py` exits 0
- [ ] `llm_calls.jsonl` has separate lines for Stage 1, 2, 3, 4 LLM calls
- [ ] `email_analysis_model.md` documents all extraction rules
- [ ] All emails parsed with email_id, from, to, date, subject, body
- [ ] Conversation graph includes inferred reply-to relationships
- [ ] Sub-threads identified (at least 2 expected in fixture)
- [ ] All decisions include confidence level (confirmed/implied/assumed)
- [ ] All actions include status from taxonomy (5 values only)
- [ ] All conflicts include type and severity from vocabularies
- [ ] All facts, actions, conflicts cite valid email_ids
- [ ] Executive summary generated from extracted data, not LLM
- [ ] Follow-up drafts cite email_ids and grounded in facts
- [ ] Priya's draft explicitly addresses 5k req/min SLA complication
- [ ] No LLM call inside any deterministic stage file
- [ ] Thread parsing deterministic (same output every run)
- [ ] All vocabularies validated immediately after LLM calls
- [ ] README or inline comments explain how to run the project
