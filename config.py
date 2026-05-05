"""
Configuration for LLM and Pipeline
Supports both Anthropic and OpenRouter
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()  # "anthropic" or "openrouter"
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3.5-sonnet")

# Anthropic Configuration (if using Anthropic directly)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# LLM Parameters
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Pipeline Configuration
ARTIFACTS_DIR = "ARTIFACTS"
STAGES_DIR = "STAGES"
DATA_DIR = "data"

# Logging
LLM_CALLS_LOG = "llm_calls.jsonl"

def get_llm_client():
    """Factory function to get appropriate LLM client."""
    if LLM_PROVIDER == "openrouter":
        from openai import OpenAI
        return OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    elif LLM_PROVIDER == "anthropic":
        from anthropic import Anthropic
        return Anthropic(api_key=ANTHROPIC_API_KEY)
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


def get_llm_model_name():
    """Get LLM model name based on provider."""
    if LLM_PROVIDER == "openrouter":
        # Map friendly names to OpenRouter model IDs
        model_map = {
            "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
            "claude-3-sonnet": "anthropic/claude-3-sonnet",
            "gpt-4": "openai/gpt-4",
            "gpt-4-turbo": "openai/gpt-4-turbo",
        }
        return model_map.get(LLM_MODEL, f"anthropic/{LLM_MODEL}")
    return LLM_MODEL
