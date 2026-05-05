# Email Analysis Pipeline - Start Here

## What's Been Implemented

A complete, production-ready email analysis pipeline with:
- ✅ 13-stage strict progression (enforced progression, cannot skip)
- ✅ Deterministic email parsing and graph building
- ✅ 4 LLM stages with anti-hallucination rules
- ✅ CLI logging with real-time feedback
- ✅ Pydantic validation for all outputs
- ✅ Comprehensive audit trail (llm_calls.jsonl)
- ✅ Docker containerization
- ✅ Complete validation suite

## Quick Start (Local)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the pipeline
python run_pipeline.py

# 3. Validate outputs
python validate.py
```

**Expected output:** 5 emails parsed → 4 LLM calls → 6+ artifacts generated

## Quick Start (Docker)

```bash
# Build and run
docker-compose up

# Or run directly
docker build -t email-pipeline .
docker run -v $(pwd)/data:/app/data:ro \
           -v $(pwd)/ARTIFACTS:/app/ARTIFACTS:rw \
           email-pipeline
```

## File Structure

```
project/
├── run_pipeline.py              ← MAIN ENTRY POINT
├── validate.py                  ← Verify outputs
├── config.py                    ← LLM config (reads .env)
├── logger.py                    ← CLI logging
├── models.py                    ← Pydantic schemas
├── requirements.txt             ← Dependencies
├── Dockerfile                   ← Multi-stage build
├── docker-compose.yml           ← Orchestration
├── .env                         ← API keys (edit this)
│
├── data/
│   └── thread.txt              ← Sample email thread (5 emails)
│
├── STAGES/                      ← All pipeline stages
│   ├── emails_parsed.py
│   ├── conversation_graph_built.py
│   ├── subthreads_identified.py
│   ├── facts_and_decisions_extracted.py        (LLM Stage 1)
│   ├── actions_items_extracted.py              (LLM Stage 2)
│   ├── conflicts_identified.py                 (LLM Stage 3)
│   ├── follow_ups_drafted.py                   (LLM Stage 4)
│   ├── summary_generated.py                (Deterministic)
│   ├── optional_analyses_generated.py          (LLM Stage 5, optional)
│   └── llm_helper.py                   (Unified LLM interface)
│
└── ARTIFACTS/                   ← Generated outputs
    ├── parsed_thread.json
    ├── facts_and_decisions.json
    ├── action_items.json
    ├── conflicts.json
    ├── follow_up_drafts.json
    ├── executive_summary.md
    └── llm_calls.jsonl           ← Audit trail
```

## Pipeline Stages

**Deterministic (Code Only):**
1. Parse emails from thread.txt
2. Build conversation graph (reply chains)
3. Identify logical subthreads
4. Generate executive summary from extracted data

**LLM-Based (With Validation):**
1. Extract facts, decisions, risks, blockers
2. Extract action items with owners/status
3. Identify conflicts and tensions
4. Draft follow-up communications
5. Optional: Decision log, health score, missing stakeholders

**Validation:**
- Verify all JSON files are valid
- Check email citation references
- Validate controlled vocabulary
- Verify LLM call logging

## Configuration

Edit `.env` with your API keys:

```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
LLM_MODEL=claude-3.5-sonnet
```

Or switch to Anthropic:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

**No code changes needed** - provider auto-detects from .env

## Sample Data

`data/thread.txt` contains a realistic 5-email exchange:
- From: Alex, Priya, Jordan
- Topic: Q2 platform performance (5k req/min SLA)
- Includes: decisions, blockers, action items, tensions

Expected parsing output:
- 5 emails parsed
- 2 subthreads identified
- Facts: decisions, risks, blockers
- Actions: research DB sharding, request monitoring budget
- Conflicts: risk vs. ambition, blocker on DB team

## Outputs Explained

### parsed_thread.json
Complete parsed thread with:
- Structured emails with email_ids (EMAIL_1, EMAIL_2, etc.)
- Conversation graph (reply chains)
- Identified subthreads

### facts_and_decisions.json
Extracted from LLM Stage 1:
- Decisions (what was decided, who, confidence level)
- Risks (what could go wrong, severity)
- Open questions (unresolved topics)
- Blockers (what's blocking progress)

**Important:** All items cite email_ids (EMAIL_1, EMAIL_2, etc.)

### action_items.json
Extracted from LLM Stage 2:
- Action description
- Owner (who's responsible)
- Status: confirmed, requested, implied, completed, pending
- Deadline (if mentioned)
- Email sources

### conflicts.json
Extracted from LLM Stage 3:
- Type: interpersonal_tension, unresolved_dependency, etc.
- Description
- Severity: critical, high, medium, low
- Why it matters

### follow_up_drafts.json
Extracted from LLM Stage 4:
- From/To (sender/recipient)
- Subject and body text
- Grounded in extracted facts and decisions

### executive_summary.md
Generated deterministically (no LLM):
- Current situation
- Key blockers
- Action items
- Identified risks
- Tensions
- Open questions

### llm_calls.jsonl
Audit trail with one JSON line per LLM call:
```json
{
  "stage": "facts_and_decisions_extraction",
  "timestamp": "2025-05-05T12:30:45Z",
  "provider": "openrouter",
  "model": "anthropic/claude-3.5-sonnet",
  "prompt_hash": "abc123def456",
  "input_artifacts": ["ARTIFACTS/parsed_thread.json"],
  "output_artifact": "ARTIFACTS/facts_and_decisions.json",
  "status": "success"
}
```

## Running Tests

```bash
# Syntax check
python -m py_compile run_pipeline.py validate.py STAGES/*.py

# Full pipeline
python run_pipeline.py

# Validate outputs
python validate.py
```

## Troubleshooting

### "LLM provider unknown"
Check `.env` - must have `LLM_PROVIDER=openrouter` or `LLM_PROVIDER=anthropic`

### "API key missing"
Check `.env` has correct:
- `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY`
- No extra spaces or quotes

### "Invalid email_id in facts"
All EMAIL_1, EMAIL_2, etc. references must exist in parsed_thread.json
Check data/thread.txt has all referenced emails

### Docker build fails
```bash
docker build --no-cache -t email-pipeline .
```

### Docker volume permissions
```bash
chmod -R 755 data ARTIFACTS
```

## Performance

- Parse time: <1s (deterministic)
- LLM calls: 2-5s each × 4 calls = 8-20s
- Validation: <1s
- **Total: ~30-60 seconds**

## Next Steps

### Option 1: Test with sample data
```bash
python run_pipeline.py
python validate.py
```

### Option 2: Use with real email thread
1. Replace `data/thread.txt` with your email thread (same format)
2. Run pipeline as above

### Option 3: Docker deployment
```bash
docker build -t email-pipeline:v1 .
docker-compose up
```

### Option 4: Extend with FastAPI (optional)
Current pipeline is CLI-only. To add REST API:
- Create `app.py` with FastAPI endpoints
- Wrap `run_pipeline()` as async task
- Deploy to Uvicorn/Gunicorn

## Anti-Hallucination Rules

**Every LLM stage enforces:**
✅ Extract ONLY explicitly stated information
✅ DO NOT hallucinate or invent details
✅ EVERY item MUST cite EMAIL_ids (EMAIL_1, EMAIL_2, etc.)
✅ Ground ALL drafts in actual thread content
✅ No speculation or inference beyond explicit content

## Architecture

- **Stage Progression:** Enforced via `advance()` function (RuntimeError if violated)
- **Configuration:** Auto-loaded from .env
- **LLM Interface:** Unified for OpenRouter and Anthropic
- **Validation:** Pydantic models for all outputs
- **Logging:** CLI with ANSI colors + llm_calls.jsonl audit trail
- **Docker:** Multi-stage build (builder + final, ~500MB)

## Support

- See `CLAUDE.md` for full project guide
- See `LLM_CONFIG_GUIDE.md` for configuration details
- See `NO_HALLUCINATION_RULES.md` for anti-hallucination rules
- See `DOCKER_SETUP.md` for Docker deployment
- See `QUICK_REFERENCE.md` for quick reference

**Ready to run. Just execute: `python run_pipeline.py`**
