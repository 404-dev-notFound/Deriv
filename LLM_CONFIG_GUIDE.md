# LLM Configuration Guide

## Configuration Files

### 1. **config.py** (Main Configuration)
**Location**: `config.py`

This is the **PRIMARY CONFIG FILE** for all LLM model settings and parameters.

**Configuration options**:
```python
LLM_PROVIDER = "openrouter" or "anthropic"  # Which provider to use
LLM_MODEL = "claude-3.5-sonnet"              # Model name
MAX_TOKENS = 4096                             # Max output tokens
TEMPERATURE = 0.7                             # Response temperature
```

**How it works**:
- Reads from `.env` file automatically
- Provides `get_llm_client()` - returns configured LLM client
- Provides `get_llm_model_name()` - returns correct model ID for provider

---

### 2. **.env** (Secrets and Runtime Settings)
**Location**: `.env`

**NEVER commit this file to git** - it contains your API keys.

Create this file with your actual keys:

```env
# LLM Provider: "openrouter" or "anthropic"
LLM_PROVIDER=openrouter

# OpenRouter API Key - Get from https://openrouter.ai/keys
OPENROUTER_API_KEY=your-actual-key-here

# Anthropic API Key - Get from https://console.anthropic.com/
ANTHROPIC_API_KEY=your-actual-key-here

# LLM Model
# For OpenRouter: "claude-3.5-sonnet", "claude-3-sonnet", "gpt-4", etc.
LLM_MODEL=claude-3.5-sonnet

# LLM Parameters
MAX_TOKENS=4096
TEMPERATURE=0.7
```

**Getting API Keys:**
- **OpenRouter**: https://openrouter.ai/keys
- **Anthropic**: https://console.anthropic.com/account/keys

---

### 3. **STAGES/llm_helper.py** (LLM Call Handler)
**Location**: `STAGES/llm_helper.py`

Unified interface for both OpenRouter and Anthropic.

**Key functions**:
- `llm_call()` - Make an LLM call (automatically uses configured provider)
- `parse_json_response()` - Extract JSON from markdown-formatted LLM response
- `validate_response()` - Validate response against Pydantic model

---

## Switching Providers

No code changes needed - just edit `.env`:

### Switch to OpenRouter
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
```

### Switch to Anthropic
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key
```

The provider auto-detects from the environment variable.

---

## Available LLM Models

### OpenRouter
- `claude-3.5-sonnet` (best quality)
- `claude-3-sonnet`
- `claude-3-opus`
- `gpt-4` (via OpenRouter)
- `gpt-4-turbo`

### Anthropic Direct
- `claude-3-5-sonnet-20241022`
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`

---

## Testing Your Configuration

**Check if .env is loaded correctly:**
```bash
python config.py
```

**Check if API keys work:**
```bash
python -c "from config import get_llm_client; print('✓ Config loaded')"
```

**Test a single LLM call:**
```python
from STAGES.llm_helper import llm_call

result = llm_call(
    stage="test",
    system="You are a test assistant.",
    user_content="Say hello",
    input_artifacts=[],
    output_artifact="test.json",
)
print(result)
```

---

## Environment Variables

Your `.env` file will be automatically loaded by `config.py`.

Required fields:
- `LLM_PROVIDER` - "openrouter" or "anthropic"
- API key matching your provider (OPENROUTER_API_KEY or ANTHROPIC_API_KEY)

Optional fields:
- `LLM_MODEL` - Model name (default: claude-3.5-sonnet)
- `MAX_TOKENS` - Max output (default: 4096)
- `TEMPERATURE` - Temperature (default: 0.7)

---

## Troubleshooting

### "Unknown LLM provider"
**Problem**: LLM_PROVIDER not set in .env
**Solution**: Add `LLM_PROVIDER=openrouter` to .env

### "API key missing"
**Problem**: API key not found in environment
**Solution**: 
1. Check .env has correct key
2. No extra spaces: `KEY=value` not `KEY = value`
3. Key should not have quotes

### "Invalid model name"
**Problem**: Model name not recognized
**Solution**: For OpenRouter, use format: `claude-3.5-sonnet`

### "Rate limit exceeded"
**Problem**: Too many API calls
**Solution**: Add delay between calls or upgrade API plan

---

## Best Practices

1. **Never commit .env** - Add to .gitignore
2. **Use placeholder in docs** - Show `sk-or-v1-...` not real keys
3. **Rotate keys regularly** - If exposed, regenerate API keys
4. **Use separate keys** - Different keys for dev/staging/prod
5. **Monitor usage** - Check API dashboard for quota limits

---

## See Also

- `config.py` - Configuration factory
- `STAGES/llm_helper.py` - LLM interface
- `QUICK_REFERENCE.md` - Quick reference card
- `CLAUDE.md` - Full project guide
