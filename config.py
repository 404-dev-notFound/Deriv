"""
Configuration for LLM and Pipeline
Supports both Anthropic and OpenRouter
"""

import os
from dotenv import load_dotenv

# Try to load .env from current directory (for local development)
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()
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
    """Return the model name for the current provider."""
    return LLM_MODEL
