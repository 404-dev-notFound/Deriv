# Plan: Email Thread Analysis Pipeline

## Summary

Build a replayable, auditable email thread analysis pipeline that deterministically parses messy email chains, extracts facts/decisions/actions/risks/conflicts via separate structured LLM calls, and generates follow-up communications grounded in extracted data. The pipeline must enforce stage progression, validate all vocabulary, log every LLM call with prompt hashing, and remain fully reproducible when evaluator replaces input fixtures.

## User Story

As an evaluator, I want to run a deterministic pipeline that ingests messy email threads, extracts structured insights via separate LLM calls, and verify that parsing happens before interpretation so that I can audit correctness, determinism, and stage separation.

## Problem → Solution

**Before**: Email threads are analyzed ad-hoc with unclear parsing logic, combined LLM extractions, no auditability, and static precomputed outputs.

**After**: Threads are parsed deterministically into email records → conversation graph → sub-threads, then facts/decisions/actions/conflicts extracted in separate LLM stages with vocabulary enforcement, all logged and replayable from clean state.

## Metadata

- **Complexity**: Large
- **Source PRD**: Problem.md
- **PRD Phase**: Full implementation (13 stages)
- **Estimated Files**: 12 (10 stages + run_pipeline.py + validate.py)
- **Key Constraint**: Facts, actions, conflicts MUST be separate LLM calls

---

## UX Design

### Before
```
[messy thread.txt] → [unclear parsing] → [one big LLM call] → [hard to debug]
                                                ↓
                                          [static artifacts]
```

### After
```
[thread.txt]
    ↓
[01_load] → [02_parse_emails] → [03_build_graph] → [04_extract_facts]
  (read)       (deterministic)      (deterministic)     (LLM Stage 1)
    ↓               ↓                    ↓                   ↓
              [emails.json]      [conversation_graph]   [facts_decision.json]
                                  [subthreads]
    
[05_extract_actions] → [06_identify_conflicts] → [07_generate_summary]
   (LLM Stage 2)          (LLM Stage 3)          (deterministic)
        ↓                       ↓                      ↓
[action_items.json]    [conflicts.json]      [executive_summary.md]
                                                      ↓
[08_draft_followups] → [09_optional] → [10_audit] → [validate.py]
  (LLM Stage 4)          (LLM)          (checks)      (exit 0/1)
      ↓                    ↓
[follow_up_drafts.md] [decision_log.json]
```

### Interaction Changes

| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Input | `thread.txt` (any format) | `thread.txt` (structured emails) | Format enforced via parse_emails |
| Parsing | Ad-hoc, unclear | Deterministic regex → email records | Full reproducibility |
| Extraction | One combined LLM call | Three separate calls (facts/actions/conflicts) | Auditability + clarity |
| Output | Static files | Deterministically regenerated | Clean checkout = full regeneration |
| Logging | None | `llm_calls.jsonl` with prompt hash | Every call recorded |
| Validation | Manual | `python validate.py` (exit code) | Automated checks |

---

## Mandatory Reading

Files that MUST be read before implementing:

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | Problem.md | All | Complete specification with all 13 stages |
| P0 | CLAUDE.md (updated) | All | Project structure, patterns, stage enforcement, LLM templates |
| P1 | data/thread.txt | All | Sample fixture for local testing |
| P2 | existing code (if any) | N/A | Adapt existing parsing if available |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| Anthropic SDK | anthropic.readthedocs.io | Use claude-sonnet-4-20250514, max_tokens=4096, system prompts |
| JSON Schema | No external dependency | All artifacts are plain JSON or Markdown |
| Regex (email parsing) | Python re module docs | Multiline patterns, group extraction |

---

## Patterns to Mirror

### STAGE_ENFORCEMENT
// SOURCE: CLAUDE.md
```python
STAGES = [
    "INIT", "THREAD_LOADED", "EMAILS_PARSED", "CONVERSATION_GRAPH_BUILT",
    "SUBTHREADS_IDENTIFIED", "FACTS_AND_DECISIONS_EXTRACTED", 
    "ACTION_ITEMS_EXTRACTED", "CONFLICTS_IDENTIFIED", "SUMMARY_GENERATED",
    "FOLLOW_UPS_DRAFTED", "OPTIONAL_ANALYSES_GENERATED", "VALIDATION_COMPLETE",
    "RESULTS_FINALISED",
]

def advance(expected_current: str, next_stage: str):
    global current_stage
    assert current_stage == expected_current, (
        f"Stage violation: expected {expected_current}, got {current_stage}"
    )
    current_stage = next_stage
    print(f"[STAGE] {current_stage}")
```

### LLM_CALL_WITH_LOGGING
// SOURCE: CLAUDE.md
```python
def llm_call(stage: str, system: str, user_content: str, input_artifacts: list[str], 
             output_artifact: str, entity_id: str | None = None) -> str:
    prompt_hash = hashlib.sha256((system + user_content).encode()).hexdigest()[:16]
    response = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=4096,
                                       system=system, messages=[{"role": "user", "content": user_content}])
    result = response.content[0].text
    log_entry = {
        "stage": stage, "entity_id": entity_id, 
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "provider": "anthropic", "model": "claude-sonnet-4-20250514",
        "prompt_hash": prompt_hash, "input_artifacts": input_artifacts, "output_artifact": output_artifact,
    }
    with open("llm_calls.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    return result
```

### VOCABULARY_ENFORCEMENT
// SOURCE: CLAUDE.md
```python
def enforce_vocabulary(value: str | list, allowed: set, field: str):
    values = [value] if isinstance(value, str) else value
    invalid = [v for v in values if v not in allowed]
    if invalid:
        raise ValueError(f"{field}: invalid values {invalid}. Allowed: {allowed}")
```

### EMAIL_PARSING_DETERMINISTIC
// SOURCE: CLAUDE.md
```python
def parse_emails_from_thread(thread_text: str) -> list:
    EMAIL_PATTERN = re.compile(
        r'^From:\s*(.+?)$\n^To:\s*(.+?)$\n^Date:\s*(.+?)$\n^Subject:\s*(.+?)$\n^$\n(.*?)(?=^From:|$)',
        re.MULTILINE | re.DOTALL
    )
    emails = []
    email_id = 1
    for match in EMAIL_PATTERN.finditer(thread_text):
        emails.append({
            "email_id": f"EMAIL_{email_id}",
            "from": match.group(1).strip(),
            "to": [e.strip() for e in match.group(2).split(',')],
            "date": match.group(3).strip(),
            "subject": match.group(4).strip(),
            "body": match.group(5).strip(),
            "reply_to_inferred": None,
        })
        email_id += 1
    return emails
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `run_pipeline.py` | CREATE | Entry point with stage enforcement |
| `validate.py` | CREATE | Evaluator runs this — all artifact checks |
| `requirements.txt` | CREATE | anthropic + python-dateutil |
| `data/thread.txt` | ENSURE EXISTS | Sample fixture for testing |
| `stages/01_load_thread.py` | CREATE | Load and validate thread format |
| `stages/02_parse_emails.py` | CREATE | Deterministic email parsing → email records |
| `stages/03_build_graph.py` | CREATE | Conversation graph + reply inference |
| `stages/04_extract_facts.py` | CREATE | LLM Stage 1: facts/decisions/risks/blockers |
| `stages/05_extract_actions.py` | CREATE | LLM Stage 2: action items with status taxonomy |
| `stages/06_identify_conflicts.py` | CREATE | LLM Stage 3: conflicts/tensions/blockers |
| `stages/07_generate_summary.py` | CREATE | Deterministic executive summary template |
| `stages/08_draft_followups.py` | CREATE | LLM Stage 4: draft communications |
| `stages/09_optional_analyses.py` | CREATE | Optional LLM calls (decision log, health score, stakeholders) |
| `stages/10_audit.py` | CREATE | Final validation checks |
| `email_analysis_model.md` | CREATE | Extraction rules, vocabularies, validation |
| `CLAUDE.md` | UPDATE | ✓ Already updated with email-specific patterns |

## NOT Building

- Automatic email threading based on ML — using deterministic regex matching only
- Advanced NLP for topic clustering — using simple subject-based grouping
- Real-time streaming pipeline — batch processing only
- GUI or web interface — CLI only
- Database persistence — file-based artifacts only
- API for thread submission — file-based input/output only
- Webhook drafting or sending — drafts only, no execution
- Sentiment analysis — not required by Problem.md
- Named entity extraction — not required by Problem.md

---

## Step-by-Step Tasks

### Task 1: Setup — Create directory structure and requirements.txt
- **ACTION**: Create project directories and Python dependencies
- **IMPLEMENT**: 
  - Create `stages/` directory
  - Create `artifacts/` directory
  - Write `requirements.txt` with anthropic>=0.25.0, python-dateutil>=2.8.2
  - Create `.env` template (optional, if using .env for ANTHROPIC_API_KEY)
- **MIRROR**: Standard Python project structure from CLAUDE.md
- **IMPORTS**: None yet
- **GOTCHA**: Ensure `artifacts/` is git-ignored but directory is created during pipeline
- **VALIDATE**: `ls -la` shows stages/ and artifacts/ directories, `cat requirements.txt` shows deps

### Task 2: Implement run_pipeline.py — Stage orchestrator
- **ACTION**: Create main entry point with stage enforcement
- **IMPLEMENT**:
  - Define STAGES list (13 stages from Problem.md)
  - Implement `advance(expected_current, next_stage)` function
  - Import all stage modules
  - Call each stage in order
  - Wrap each call in try-except to fail fast on stage violations
- **MIRROR**: STAGE_ENFORCEMENT pattern from CLAUDE.md
- **IMPORTS**: `from stages.* import *`
- **GOTCHA**: Stage names must match Problem.md exactly. If any stage fails, pipeline halts at that point (no continuation)
- **VALIDATE**: `python run_pipeline.py` should progress through all 13 stages or fail with stage violation error

### Task 3: Implement 01_load_thread.py — Load thread.txt
- **ACTION**: Load raw email thread from disk, validate format
- **IMPLEMENT**:
  - Read `data/thread.txt`
  - Validate that file exists and is non-empty
  - Return raw thread text for next stage
  - Log to stdout: "[LOAD] Read thread.txt (X bytes)"
- **MIRROR**: Input validation pattern from trading pipeline CLAUDE.md
- **IMPORTS**: `import os`
- **GOTCHA**: File must exist or pipeline halts. Encoding assumed UTF-8.
- **VALIDATE**: Run stage in isolation — should read thread.txt without errors

### Task 4: Implement 02_parse_emails.py — Deterministic email parsing
- **ACTION**: Parse thread text into structured email records
- **IMPLEMENT**:
  - Use regex pattern from CLAUSE.md to extract emails
  - Build email record for each match: {email_id, from, to, date, subject, body, reply_to_inferred}
  - Infer reply-to by matching subject + participant
  - Save `artifacts/parsed_thread.json` with { "emails": [...] }
- **MIRROR**: EMAIL_PARSING_DETERMINISTIC + infer_reply_relationships from CLAUDE.md
- **IMPORTS**: `import re, json`
- **GOTCHA**: Regex must handle multiline bodies and varied formatting. Subject matching is case-sensitive but "RE:" prefix is stripped.
- **VALIDATE**: Run stage, check `artifacts/parsed_thread.json` has array of emails with all required fields

### Task 5: Implement 03_build_graph.py — Conversation graph & sub-threads
- **ACTION**: Build conversation structure showing reply chains and sub-threads
- **IMPLEMENT**:
  - Build graph with branches: { email_id → [list of replies] }
  - Collect participants
  - Identify sub-threads by clustering emails with same base subject
  - Save `artifacts/parsed_thread.json` with { "emails": [...], "conversation_graph": {...}, "subthreads": [...] }
- **MIRROR**: Patterns from CLAUDE.md for graph building
- **IMPORTS**: `import json`
- **GOTCHA**: Sub-threads must cluster by base subject (strip "RE:"). At least 2 expected in fixture.
- **VALIDATE**: Check `artifacts/parsed_thread.json` has `conversation_graph` and `subthreads` keys

### Task 6: Implement 04_extract_facts.py — LLM Stage 1
- **ACTION**: Extract facts, decisions, risks, blockers via LLM
- **IMPLEMENT**:
  - Read `artifacts/parsed_thread.json`
  - Build system prompt (SYSTEM_EXTRACT_FACTS from CLAUDE.md)
  - Call `llm_call(stage="FACTS_AND_DECISIONS_EXTRACTED", system=..., user_content=json.dumps(emails), ...)`
  - Parse JSON response
  - Validate confidence/severity vocabularies
  - Save `artifacts/facts_decisions.json`
  - Validate all email_id_sources exist in parsed_thread.json
- **MIRROR**: LLM_CALL_WITH_LOGGING + VOCABULARY_ENFORCEMENT from CLAUDE.md
- **IMPORTS**: `import json, hashlib, datetime, from anthropic import Anthropic`
- **GOTCHA**: LLM response must be valid JSON. Parse with json.loads(). Validate vocabularies immediately after call. All email citations must be valid.
- **VALIDATE**: `artifacts/facts_decisions.json` exists, has decisions/risks/blockers, all email_ids are valid

### Task 7: Implement 05_extract_actions.py — LLM Stage 2
- **ACTION**: Extract action items with status taxonomy via separate LLM call
- **IMPLEMENT**:
  - Read `artifacts/parsed_thread.json` + `artifacts/facts_decisions.json`
  - Build system prompt with action status taxonomy (SYSTEM_EXTRACT_ACTIONS from CLAUDE.md)
  - Call llm_call with stage="ACTION_ITEMS_EXTRACTED"
  - Parse response, validate status vocabulary (only 5 values: confirmed, requested, implied, completed, pending)
  - Save `artifacts/action_items.json`
  - Validate all email_id_sources exist
- **MIRROR**: LLM_CALL_WITH_LOGGING + VOCABULARY_ENFORCEMENT
- **IMPORTS**: Same as Task 6
- **GOTCHA**: Action status taxonomy is strict — raise ValueError if any action has invalid status. "James's rate-limiting document suggestion" should be captured as implied or pending action.
- **VALIDATE**: `artifacts/action_items.json` exists, all actions have valid status, all email_ids are valid

### Task 8: Implement 06_identify_conflicts.py — LLM Stage 3
- **ACTION**: Identify conflicts, tensions, blockers via separate LLM call
- **IMPLEMENT**:
  - Read all artifacts (parsed_thread, facts, actions)
  - Build system prompt with conflict type vocabulary (SYSTEM_IDENTIFY_CONFLICTS from CLAUDE.md)
  - Call llm_call with stage="CONFLICT_IDENTIFICATION"
  - Parse response, validate type + severity vocabularies
  - Save `artifacts/conflicts.json`
  - Validate all email_id_sources exist
- **MIRROR**: LLM_CALL_WITH_LOGGING + VOCABULARY_ENFORCEMENT
- **IMPORTS**: Same as Task 6
- **GOTCHA**: Conflict types are strict (5 types). All conflicts must explain "why_it_matters". All citations must be valid email_ids.
- **VALIDATE**: `artifacts/conflicts.json` exists, all conflicts have valid type/severity, all email_ids valid

### Task 9: Implement 07_generate_summary.py — Executive summary (deterministic)
- **ACTION**: Generate executive summary from extracted data (NO LLM)
- **IMPLEMENT**:
  - Read facts_decisions, action_items, conflicts
  - Use template-based generation from CLAUDE.md
  - Build sections: Current Situation, Key Blockers, Immediate Next Actions, Unresolved Risks, Unresolved Tensions
  - Save `artifacts/executive_summary.md` (~200 words)
  - Do NOT call LLM
- **MIRROR**: Executive summary generation function from CLAUDE.md
- **IMPORTS**: `import json`
- **GOTCHA**: This is purely deterministic — no LLM call allowed. Summarize from extracted data only.
- **VALIDATE**: `artifacts/executive_summary.md` exists, contains sections, is ~200 words

### Task 10: Implement 08_draft_followups.py — LLM Stage 4
- **ACTION**: Draft follow-up communications grounded in extracted data
- **IMPLEMENT**:
  - Read all artifacts
  - Build system prompt (SYSTEM_DRAFT_FOLLOWUPS from CLAUDE.md)
  - Call llm_call with stage="FOLLOW_UPS_DRAFTED"
  - Parse response (array of draft objects)
  - Validate that Priya's draft addresses SLA complication (cites Email 5 or mentions 5k req/min or contractual)
  - Save `artifacts/follow_up_drafts.md`
- **MIRROR**: LLM_CALL_WITH_LOGGING
- **IMPORTS**: Same as Task 6
- **GOTCHA**: Priya's draft MUST address the 5k req/min SLA complication from Email 5. This will be validated in validate.py. All drafts must ground citations in emails or extracted facts.
- **VALIDATE**: `artifacts/follow_up_drafts.md` exists, contains 3 drafts (Priya, Sarah, James), Priya's draft mentions SLA

### Task 11: Implement 09_optional_analyses.py — Optional LLM calls
- **ACTION**: Generate optional analyses (decision log, health score, missing stakeholders)
- **IMPLEMENT**:
  - For each optional analysis:
    - Build system prompt
    - Call llm_call with appropriate stage name
    - Validate output
    - Save artifact if generated
  - Optional outputs: decision_log.json, thread_health_score.json, missing_stakeholders.md
  - If any call fails, log warning but don't halt pipeline
- **MIRROR**: LLM_CALL_WITH_LOGGING
- **IMPORTS**: Same as Task 6
- **GOTCHA**: Failures here don't halt pipeline. validate.py will check if optional artifacts exist but not fail if missing.
- **VALIDATE**: Optional artifacts generated (or gracefully skipped with warnings)

### Task 12: Implement 10_audit.py — Final validation
- **ACTION**: Run end-to-end consistency checks on all artifacts
- **IMPLEMENT**:
  - Check all required files exist
  - Check JSON validity
  - Check email_id cross-references
  - Check vocabulary compliance
  - Check that LLM calls are logged separately (not combined)
  - Report findings to stdout
- **MIRROR**: Validation patterns from trading pipeline CLAUDE.md
- **IMPORTS**: `import json, os`
- **GOTCHA**: This is internal to pipeline. validate.py (evaluator-facing) does the final check with exit code.
- **VALIDATE**: Run stage — should report all checks passing

### Task 13: Implement validate.py — Evaluator-facing validation
- **ACTION**: Comprehensive validation script that evaluator runs independently
- **IMPLEMENT**:
  - Check all required artifacts exist
  - Check JSON validity
  - Check email fields complete
  - Check conversation graph + sub-threads exist
  - Check action statuses valid (5 values only)
  - Check all email_ids cited are in parsed_thread.json
  - Check facts, actions, conflicts extracted in separate LLM calls (3 separate log entries)
  - Check Priya's draft addresses SLA
  - Report results with OK/FAIL for each check
  - Exit code 0 if all pass, 1 if any fail
- **MIRROR**: validate.py pattern from trading pipeline CLAUDE.md
- **IMPORTS**: `import json, os, sys`
- **GOTCHA**: This must be run independently by evaluator. Use clear OK/FAIL messages. Exit code must be 0 or 1 (no partial success).
- **VALIDATE**: Run `python validate.py` — should exit 0 (all checks pass)

### Task 14: Create email_analysis_model.md
- **ACTION**: Document all extraction rules, vocabularies, and validation
- **IMPLEMENT**:
  - Document thread format assumptions
  - Document email record schema
  - List all 4 extraction stages + vocabularies
  - List validation rules
  - Include examples where helpful
- **MIRROR**: email_analysis_model.md template from CLAUDE.md
- **IMPORTS**: None
- **GOTCHA**: This is documentation — keep it accurate to implementation. Update if rules change.
- **VALIDATE**: File exists, is readable, covers all extraction stages

### Task 15: Test full pipeline end-to-end
- **ACTION**: Run complete pipeline from clean state
- **IMPLEMENT**:
  - Delete all `artifacts/` files
  - Ensure `data/thread.txt` exists with sample fixture
  - Run `python run_pipeline.py`
  - Verify all 13 stages complete
  - Verify all required artifacts generated
  - Run `python validate.py`
  - Verify exit code 0
- **MIRROR**: Checklist from CLAUDE.md
- **IMPORTS**: None (just bash execution)
- **GOTCHA**: If any stage fails, pipeline halts. Debug which stage failed and why.
- **VALIDATE**: Both scripts run without errors, validate.py exits 0

---

## Testing Strategy

### Unit Tests

Not explicitly required by Problem.md, but recommended:

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| parse_emails | thread with 3 emails | 3 email records with all fields | Yes |
| infer_reply_to | email + prior emails | email.reply_to_inferred set or None | Yes (no match) |
| sub_thread_cluster | emails with 2 topics | 2 sub-threads | Yes |
| enforce_vocabulary | valid value | passes | No |
| enforce_vocabulary | invalid value | raises ValueError | Yes |
| validate_json | valid JSON | parses | No |
| validate_json | invalid JSON | raises JSONDecodeError | Yes |

### Edge Cases Checklist

- [ ] Empty thread.txt → should fail with clear error message
- [ ] Thread with 1 email → no reply-to, single subthread
- [ ] Thread with malformed email (missing From/To) → skip or error gracefully
- [ ] LLM returns non-JSON → parse_json_response strips markdown, raises if still invalid
- [ ] LLM returns invalid vocabulary → enforce_vocabulary raises, pipeline halts
- [ ] Missing email_id sources → validate.py reports failure
- [ ] Priya's draft without SLA mention → validate.py reports failure

---

## Validation Commands

### Static Analysis
```bash
python -m py_compile run_pipeline.py validate.py stages/*.py
```
EXPECT: Zero syntax errors

### Unit Tests (if implemented)
```bash
python -m pytest tests/ -v
```
EXPECT: All tests pass

### Full Pipeline
```bash
rm -rf artifacts/*
python run_pipeline.py
```
EXPECT: All 13 stages complete, all required artifacts generated, no errors

### Validation
```bash
python validate.py
```
EXPECT: Exit code 0, all checks pass

### Clean Regeneration
```bash
rm -rf artifacts/llm_calls.jsonl
python run_pipeline.py
python validate.py
```
EXPECT: Identical artifacts to first run, exit code 0

### Sample Fixture Replacement (Evaluator)
```bash
cp data/thread.txt data/thread.txt.backup
# Replace thread.txt with equivalent fixture
python run_pipeline.py
python validate.py
```
EXPECT: Exit code 0, no errors, artifacts regenerated

---

## Acceptance Criteria

- [ ] All 13 stages implemented and enforced in order
- [ ] Thread parsing deterministic (regex only, no LLM)
- [ ] Conversation graph + sub-threads identified (≥2)
- [ ] Facts, actions, conflicts extracted in separate LLM calls
- [ ] All vocabularies validated after LLM calls
- [ ] All extracted items cite valid email_ids
- [ ] Executive summary deterministically generated (no LLM)
- [ ] Follow-up drafts grounded in extracted data
- [ ] Priya's draft addresses 5k req/min SLA complication
- [ ] All artifacts regenerated from clean state
- [ ] `validate.py` exits 0
- [ ] `llm_calls.jsonl` has separate entries for Stage 1/2/3/4
- [ ] `email_analysis_model.md` documents all rules
- [ ] README or inline comments explain how to run

## Completion Checklist

- [ ] Code follows established patterns from CLAUDE.md
- [ ] All files created (stages/01-10, run_pipeline.py, validate.py, etc.)
- [ ] Stage enforcement working (advance function prevents stage skips)
- [ ] LLM calls logged with prompt hashing
- [ ] All vocabularies enforced
- [ ] Email citations validated
- [ ] Deterministic code has no randomness or LLM calls
- [ ] No hardcoded values (use constants)
- [ ] Error messages clear and helpful
- [ ] Code style consistent
- [ ] All validation checks working
- [ ] Documentation complete
- [ ] Self-contained — no questions remain

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM response not valid JSON | Medium | Pipeline fails | Test with different LLM responses, robust parsing + error handling |
| Regex doesn't match thread format variation | Medium | Emails not parsed | Use flexible regex, test with multiple thread formats |
| Email citations become invalid | Low | Validation fails | Cross-check email_ids immediately after extraction, fail fast |
| Stage order not enforced correctly | Low | Silent stage skips | Use strict advance() guards, test stage progression |
| Evaluator replaces thread, pipeline fails | Low | Evaluator can't verify | Ensure regex is generic, doesn't depend on exact content |
| LLM vocabulary enforcement too strict | Medium | Legitimate values rejected | Include all valid vocabularies upfront, test LLM responses |

## Notes

- Thread parsing uses regex — this is deterministic and replayable
- All 13 stages must complete or pipeline halts (no recovery)
- LLM calls are separate and logged — each call is auditable
- Artifacts are overwritten on each run — there's no incremental mode
- Evaluator can replace thread.txt with equivalent fixture — pipeline must be format-agnostic within reason
- All citations are email_id based — this ensures traceability
- Priya's draft is critical validation point — must address SLA explicitly
