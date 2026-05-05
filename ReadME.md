# Email Analysis Pipeline

A production-ready, replayable email thread analysis system that extracts facts, decisions, actions, risks, and conflicts with strict stage progression and LLM integration.

## Quick Start

### Local

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key
python run_pipeline.py
python validate.py
```

### Docker

```bash
docker-compose up
```

## What It Does

Processes messy email chains and extracts:
- Parsed emails with reply chains
- Conversation graph and topology
- Facts & decisions with confidence levels
- Action items with owners and status
- Conflicts and tensions
- Executive summary
- Follow-up drafts grounded in content

## Pipeline Stages (13)

```
INIT → THREAD_LOADED → EMAILS_PARSED → CONVERSATION_GRAPH_BUILT
→ SUBTHREADS_IDENTIFIED → FACTS_AND_DECISIONS_EXTRACTED
→ ACTION_ITEMS_EXTRACTED → CONFLICTS_IDENTIFIED → SUMMARY_GENERATED
→ FOLLOW_UPS_DRAFTED → OPTIONAL_ANALYSES_GENERATED
→ VALIDATION_COMPLETE → RESULTS_FINALISED
```

**Stages are enforced** - cannot skip or reorder.

## Configuration

### OpenRouter (Recommended)

```bash
# .env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
LLM_MODEL=claude-3.5-sonnet
```

Get key: https://openrouter.ai/keys

### Anthropic

```bash
# .env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

Get key: https://console.anthropic.com/account/keys

## Key Features

✅ Strict stage progression (enforced)
✅ Anti-hallucination rules on all LLM stages
✅ Email citation validation (all EMAIL_IDs verified)
✅ Controlled vocabulary (confirmed/implied/assumed, etc.)
✅ CLI logging with colors and real-time feedback
✅ Comprehensive validation suite
✅ Docker containerization
✅ Audit trail (llm_calls.jsonl)
✅ Pydantic model validation

## File Structure

```
.
├── run_pipeline.py          # Main orchestrator
├── validate.py              # Output validation
├── config.py                # LLM configuration
├── logger.py                # CLI logging
├── models.py                # Pydantic models
├── STAGES/                  # All pipeline stages
├── data/thread.txt          # Sample email thread
├── ARTIFACTS/               # Generated outputs
├── Dockerfile               # Docker build
├── docker-compose.yml       # Docker orchestration
├── .env                     # API keys (git-ignored)
└── README.md                # This file
```

## Sample Data

`data/thread.txt` contains 5 realistic emails:
- Discussion of Q2 performance targets (5k req/min)
- Database sharding concerns
- SLA and ops requirements
- Identified blockers and action items

## Validation

```bash
python validate.py
```

Checks:
- All required files exist and are valid JSON
- Email citations reference actual EMAIL_IDs
- Controlled vocabulary compliance
- Separate LLM calls for facts/actions/conflicts
- Executive summary from extracted data

## Output Artifacts

Generated in `ARTIFACTS/`:
- `parsed_thread.json` - Parsed emails, graph, subthreads
- `facts_and_decisions.json` - Decisions, risks, blockers
- `action_items.json` - Actions with status
- `conflicts.json` - Identified conflicts
- `executive_summary.md` - Overview
- `follow_up_drafts.json` - Draft communications
- `llm_calls.jsonl` - Audit trail

## Docker

### Build
```bash
docker build -t email-pipeline .
```

### Run with Compose
```bash
docker-compose up
```

### Environment Variables
- `LLM_PROVIDER` - openrouter or anthropic
- `OPENROUTER_API_KEY` - Your OpenRouter key
- `ANTHROPIC_API_KEY` - Your Anthropic key
- `LLM_MODEL` - Model name (claude-3.5-sonnet)

## Documentation

- **START_HERE.md** - Quick start
- **CLAUDE.md** - Full guide
- **LLM_CONFIG_GUIDE.md** - Configuration
- **DOCKER_SETUP.md** - Docker guide
- **QUICK_REFERENCE.md** - Reference card

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "LLM provider unknown" | Check .env: LLM_PROVIDER=openrouter |
| "API key missing" | Check .env format, no extra spaces |
| "Invalid email_id" | EMAIL_1, EMAIL_2, etc. must exist |
| Docker fails | docker build --no-cache -t email-pipeline . |

## Setup Verification

```bash
python test_setup.py
```

Quick verification that all files are present.

## Status

✅ Complete and production-ready
- 13-stage pipeline
- Enforced progression
- LLM integration (OpenRouter/Anthropic)
- Anti-hallucination validation
- Docker containerization
- Comprehensive audit trail

Ready to run: `python run_pipeline.py`
