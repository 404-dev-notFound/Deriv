```python?code_reference&code_event_index=2
content = """## BUILD

Build a replayable pipeline that ingests a messy multi-threaded email chain, reconstructs the conversation structure, extracts facts, decisions, actions, risks, conflicts, and drafts follow-up communications.

This is not a one-shot email summary task. The evaluator will run your pipeline from a clean checkout, may replace the thread with an equivalent fixture, and will verify that deterministic parsing happens before LLM interpretation and that facts, actions, and conflicts are extracted in separate stages.

The pipeline must preserve source citations, enforce action-status taxonomy, and ensure follow-up drafts are grounded in extracted thread state.

---

## INPUT FILES

Your pipeline must read the email thread from disk:

- `thread.txt`

The sample thread is provided for local testing. The evaluator may replace it with another messy email chain using a similar text format. Your implementation must not depend on exact names, dates, or hardcoded extracted items.

---

## PIPELINE STAGES

Your implementation must enforce these stages in code:

```
```text?code_stdout&code_event_index=2
File created successfully at email_pipeline_specification.md

```text
INIT
 -> THREAD_LOADED
 -> EMAILS_PARSED
 -> CONVERSATION_GRAPH_BUILT
 -> SUBTHREADS_IDENTIFIED
 -> FACTS_AND_DECISIONS_EXTRACTED
 -> ACTION_ITEMS_EXTRACTED
 -> CONFLICTS_IDENTIFIED
 -> SUMMARY_GENERATED
 -> FOLLOW_UPS_DRAFTED
 -> OPTIONAL_ANALYSES_GENERATED
 -> VALIDATION_COMPLETE
 -> RESULTS_FINALISED
```

Follow-up drafts must not be generated until facts, actions, risks, and conflicts have been extracted.

---

## MUST COMPLETE

### 1. Thread Reconstruction

Parse `thread.txt` deterministically before any LLM call.

Extract each email into:

```json
{
  "email_id": "EMAIL_1",
  "from": "sarah.chen@company.com",
  "to": ["dev-team@company.com"],
  "date": "Monday 9:02 AM",
  "subject": "RE: API rate limiting — urgent",
  "body": "string",
  "reply_to_inferred": "EMAIL_ID | null"
}
```

Build a conversation graph showing:

- inferred reply relationships
- participants
- branching points
- distinct sub-threads

Save output to `parsed_thread.json`.

The public fixture contains at least two sub-threads:

- rate-limit increase / queueing / infra dependency
- Client A webhook / SLA / legal-risk thread

---

### 2. Fact and Decision Extraction

Make one Stage 1 LLM call using `parsed_thread.json`.

Extract:

- decisions made
- open questions
- blockers
- risks flagged

Every item must cite one or more `email_id` values.

Each decision must include:

```json
{
  "decision_id": "D1",
  "decision_text": "string",
  "made_by": "string",
  "date": "string",
  "confidence": "confirmed | implied | assumed",
  "email_id_sources": ["EMAIL_4"]
}
```

Each risk must include:

```json
{
  "risk_id": "R1",
  "risk_text": "string",
  "raised_by": "string",
  "severity": "critical | high | medium | low",
  "email_id_sources": ["EMAIL_5"]
}
```

Save Stage 1 output to `facts_decisions.json`.

---

### 3. Action Item Extraction

Make a separate Stage 2 LLM call.

The prompt must define this action status taxonomy:

```text
confirmed: assigned person explicitly acknowledged or accepted the task
requested: someone asked another person to do something, but no acknowledgement is present
implied: action is suggested or logically required, but not directly assigned
completed: the action was completed within the thread
pending: the action remains unresolved by the final email
```

Each action item must include:

```json
{
  "action_id": "A1",
  "owner": "string",
  "action": "string",
  "deadline_if_stated": "string | null",
  "status": "confirmed | requested | implied | completed | pending",
  "email_id_sources": ["EMAIL_4"],
  "completion_email_id": "EMAIL_9 | null"
}
```

Save output to `action_items.json`.

For the public fixture, James's rate-limiting policy document suggestion must be captured as an implied or pending action, even though it is tabled for next sprint planning.

---

### 4. Conflict and Tension Identification

Make a separate Stage 3 LLM call.

Identify:

- interpersonal tensions
- unresolved dependencies
- decision reversals
- risks flagged but not addressed
- blocked actions

Each conflict must include:

```json
{
  "conflict_id": "C1",
  "type": "interpersonal_tension | unresolved_dependency | decision_reversal | unaddressed_risk | blocked_action",
  "description": "string",
  "severity": "critical | high | medium | low",
  "email_id_sources": ["EMAIL_5", "EMAIL_8"],
  "why_it_matters": "string"
}
```

Save output to `conflicts.json`.

---

### 5. Executive Summary

Generate `executive_summary.md`.

The summary must be approximately 200 words and include:

- current situation
- key blockers
- immediate next actions
- unresolved risks
- current owner or next responsible party, where known

The summary must be grounded in extracted Stage 1-3 data.

Do not invent context not present in the thread.

---

### 6. Follow-Up Drafts

Generate `follow_up_drafts.md` using extracted context from Stages 1-3.

Produce three communications:

1. Priya's message to Client A's technical contact
2. Sarah's end-of-Tuesday update to the full team
3. James's rate-limiting policy document section header and 3-bullet scope

Priya's draft must explicitly account for the SLA complication from Email 5.

It must not ask Client A to migrate to webhooks in a way that ignores their possible 5k req/min contractual guarantee.

Each draft must cite the extracted facts or email IDs it relies on.

---

## SHOULD ATTEMPT

### 7. Decision Log

Create `decision_log.json`.

Include all confirmed and implied decisions:

```json
{
  "decision_id": "D1",
  "date": "string",
  "decision_text": "string",t
  "made_by": "string",
  "basis": "string",
  "open_question_if_any": "string | null",
  "email_id_sources": ["EMAIL_8"]
}
```

---

### 8. Thread Health Score

Create `thread_health_score.json`.

Score the thread from 1-5 on:

- clarity of ownership
- decision velocity
- risk acknowledgement
- communication quality

Each score must include a specific email reference as evidence.

---

## STRETCH

### 9. Missing Stakeholder Identification

Identify roles that should have been included but were not, based on topics in the thread.

Possible stakeholder domains include:

- Legal
- Infra
- Client success or account management
- Product owner
- Commercial or contracts owner

For each missing stakeholder, draft a short briefing explaining what is relevant to their domain.

Save output to `missing_stakeholders.md`.

---

### 10. Thread Simulation

Simulate the most likely next 3 emails.

Each simulated email must include:

- sender
- recipients
- likely content
- new information introduced
- why it is consistent with that person's communication style

Save output to `thread_simulation.md`.

---

## REQUIRED ARTIFACTS

Your repository must produce:

- `thread.txt`
- `parsed_thread.json`
- `facts_decisions.json`
- `action_items.json`
- `extraction_report.json`
- `conflicts.json`
- `executive_summary.md`
- `follow_up_drafts.md`
- `decision_log.json`, if attempted
- `thread_health_score.json`, if attempted
- `missing_stakeholders.md`, if attempted
- `thread_simulation.md`, if attempted
- `llm_calls.jsonl`

`extraction_report.json` may combine Stage 1 and Stage 2 outputs, but the LLM calls must remain separate.

---

## `llm_calls.jsonl` REQUIREMENTS

Log one JSON object per LLM call.

Each record must include:

```json
{
  "stage": "string",
  "timestamp": "ISO-8601 timestamp",
  "provider": "string",
  "model": "string",
  "prompt_hash": "string",
  "input_artifacts": ["path"],
  "output_artifact": "path"
}
```

There must be separate records for:

- Stage 1 fact and decision extraction
- Stage 2 action item extraction
- Stage 3 conflict identification
- follow-up drafting
- optional analyses, if attempted

---

## VALIDATION REQUIREMENTS

The repository must include a validation command, for example:

```bash
make validate
```

or:

```bash
python validate.py
```

The validation command must check that:

- required artifacts exist
- JSON files are valid
- thread parsing happened before any LLM call
- all emails have IDs, sender, recipients, date, subject, and body
- conversation graph exists
- sub-threads are identified
- extracted facts, decisions, risks, actions, and conflicts cite valid email IDs
- action statuses use only the allowed taxonomy
- facts, actions, and conflicts were extracted in separate LLM calls
- Priya's follow-up draft addresses the SLA complication from Email 5
- executive summary is generated from extracted data
- LLM call logs contain separate records for required stages

---

## EXECUTION REQUIREMENTS

The evaluator will run the pipeline from a clean checkout.

Generated artifacts may be deleted before evaluation.

The evaluator may replace `thread.txt` with an equivalent messy email thread.

Static precomputed outputs are not sufficient.

The solution must actually run the staged pipeline and regenerate required artifacts.

---

## TOOLS

Any programming language may be used.

Any LLM provider or AI tooling may be used.

---

## TECHNICAL CONSTRAINTS

- Thread parsing must be deterministic code.
- Do not use the LLM to parse raw emails into records.
- Facts, actions, and conflicts must be extracted in separate LLM calls.
- Every extracted item must cite valid `email_id` sources.
- Action status taxonomy must distinguish confirmed, requested, implied, completed, and pending.
- Follow-up drafts must use extracted context.
- Priya's draft must address the SLA complication.
- Do not invent context outside the email thread.
- Static precomputed outputs are not sufficient.
"""

file_path = "email_pipeline_specification.md"
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print(f"File created successfully at {file_path}")


```
Your Markdown file is ready
[file-tag: code-generated-file-0-1777964971478530306]

The provided specification has been successfully formatted and saved into the `.md` file. Let me know if you need any adjustments or further assistance!