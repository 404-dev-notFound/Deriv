# Quick Reference Card

## Config File Location
📍 **Main Config**: `config.py`
📍 **Secrets**: `.env`
📍 **LLM Helper**: `STAGES/llm_helper.py`

## What's in config.py?
```python
LLM_PROVIDER = "openrouter"        # or "anthropic"
LLM_MODEL = "claude-3.5-sonnet"    # Model name
MAX_TOKENS = 4096
TEMPERATURE = 0.7
```

## What's in .env?
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...    # Your key is here
LLM_MODEL=claude-3.5-sonnet
```

## Switch to Anthropic?
Just change `.env`:
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```
Code auto-detects! No other changes needed.

## File Structure
```
STAGES/
├── llm_helper.py                    ← Uses config.py automatically
├── facts_and_decisions_extracted.py ← Stage 1 (LLM)
├── actions_items_extracted.py       ← Stage 2 (LLM)
├── conflicts_identified.py          ← Stage 3 (LLM)
├── follow_ups_drafted.py            ← Stage 4 (LLM)
├── summary_generated.py             ← Stage 5 (deterministic, no LLM)
└── optional_analyses_generated.py   ← Stage 6 (optional LLM)
```

## LLM Call Pattern
```python
from STAGES.llm_helper import llm_call, parse_json_response

result = llm_call(
    stage="facts_and_decisions_extraction",
    system=SYSTEM_PROMPT,
    user_content=json.dumps(data),
    input_artifacts=["ARTIFACTS/parsed_thread.json"],
    output_artifact="ARTIFACTS/facts_decisions.json",
)

extracted = parse_json_response(result)
```

## Stages at a Glance

| Stage | Type | Input | Output |
|-------|------|-------|--------|
| 1 | LLM | parsed_thread.json | facts_decisions.json |
| 2 | LLM | parsed_thread + facts | action_items.json |
| 3 | LLM | all prev + facts | conflicts.json |
| 4 | LLM | all prev + conflicts | follow_up_drafts.json |
| 5 | CODE | facts + actions + conflicts | executive_summary.md |
| 6 | LLM | all prev | optional/*.json |

## Anti-Hallucination Rules
✅ Ground EVERYTHING in emails
✅ Cite EMAIL_1, EMAIL_2, etc.
✅ No invention or assumptions
✅ No speculation or inference
✅ Only explicitly stated content

## Check LLM Calls
```bash
tail -f llm_calls.jsonl
```
Shows: stage, timestamp, provider, model, prompt_hash

## Install Dependencies
```bash
pip install -r requirements.txt
```
Gets: anthropic, openai, python-dotenv

## Test a Stage
```bash
python -m STAGES.facts_and_decisions_extracted
```

## Validate Email Citations
Look for ERROR messages about invalid EMAIL_X references. Fix or exclude.

## JSON Output Schemas
All outputs are valid JSON matching Problem.md exactly.
See `IMPLEMENTATION_COMPLETE.md` for schema details.

## Documentation Files
- `CLAUDE.md` - Full project guide
- `LLM_CONFIG_GUIDE.md` - Config details
- `NO_HALLUCINATION_RULES.md` - Anti-hallucination rules
- `IMPLEMENTATION_COMPLETE.md` - What's implemented
- `SETUP_COMPLETE.md` - Setup summary
- `QUICK_REFERENCE.md` - This file

## Available Models (OpenRouter)
- `claude-3.5-sonnet` → `anthropic/claude-3.5-sonnet`
- `claude-3-sonnet` → `anthropic/claude-3-sonnet`
- `gpt-4` → `openai/gpt-4`
- `gpt-4-turbo` → `openai/gpt-4-turbo`

## Troubleshooting
| Problem | Solution |
|---------|----------|
| "Unknown LLM provider" | Check `.env`: `LLM_PROVIDER=openrouter` |
| "API key missing" | Check `.env` has correct key, no extra spaces |
| "Model not found" | For OpenRouter: use `provider/model-name` format |
| JSON parse error | LLM response not valid JSON; check `parse_json_response()` |
| Invalid email_id | EMAIL_1, EMAIL_2, etc. must exist in parsed_thread.json |

## Key Files to Know
| File | Purpose |
|------|---------|
| config.py | ⚙️ LLM configuration |
| STAGES/llm_helper.py | 🔌 Unified LLM interface |
| STAGES/*.py | 🔧 Pipeline stages |
| ARTIFACTS/ | 📁 Generated outputs |
| llm_calls.jsonl | 📋 LLM call log |

## Next: You Need To Create
- `run_pipeline.py` - Orchestrate all stages
- `validate.py` - Verify all artifacts
- `data/thread.txt` - Sample email thread

Then run:
```bash
python run_pipeline.py
python validate.py
```

**That's it! Everything else is ready to go.**
