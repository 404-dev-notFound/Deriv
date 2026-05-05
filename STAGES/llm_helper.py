"""
LLM Helper - Unified interface for Anthropic and OpenRouter with validation.
"""

import json
import hashlib
import datetime
from typing import Type
from pydantic import BaseModel, ValidationError
from config import get_llm_client, get_llm_model_name, LLM_PROVIDER
from logger import log_llm_call_start, log_llm_call_complete, log_error


def llm_call(
    stage: str,
    system: str,
    user_content: str,
    input_artifacts: list,
    output_artifact: str,
) -> str:
    """
    Make an LLM call using configured provider (Anthropic or OpenRouter).
    Logs call to llm_calls.jsonl with validation and CLI logging.
    """
    prompt_hash = hashlib.sha256((system + user_content).encode()).hexdigest()[:16]
    model = get_llm_model_name()
    client = get_llm_client()

    # Log LLM call start
    log_llm_call_start(stage, model)

    try:
        if LLM_PROVIDER == "openrouter":
            # OpenRouter uses OpenAI-compatible API
            # Prefix with anthropic/ if not already prefixed and it's a Claude model
            or_model = model
            if not or_model.startswith(("anthropic/", "openai/", "google/", "meta-llama/")) and "gpt" not in or_model:
                or_model = f"anthropic/{or_model}"
            response = client.chat.completions.create(
                model=or_model,
                max_tokens=4096,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
            )
            result = response.choices[0].message.content
        else:  # Anthropic
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user_content}],
            )
            result = response.content[0].text

    except Exception as e:
        error_msg = f"LLM API call failed: {str(e)}"
        log_error(f"Stage '{stage}': {error_msg}")

        # Log failed call
        log_entry = {
            "stage": stage,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            "provider": LLM_PROVIDER,
            "model": model,
            "prompt_hash": prompt_hash,
            "input_artifacts": input_artifacts,
            "output_artifact": output_artifact,
            "status": "error",
            "error": str(e),
        }
        with open("llm_calls.jsonl", "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        raise RuntimeError(error_msg)

    # Log LLM call complete
    log_llm_call_complete(stage)

    # Log the successful call
    log_entry = {
        "stage": stage,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "provider": LLM_PROVIDER,
        "model": model,
        "prompt_hash": prompt_hash,
        "input_artifacts": input_artifacts,
        "output_artifact": output_artifact,
        "status": "success",
    }
    with open("llm_calls.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return result


def parse_json_response(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def validate_response(
    data: dict,
    model_class: Type[BaseModel],
    stage: str,
) -> BaseModel:
    """
    Validate LLM response against Pydantic model.

    Args:
        data: Parsed JSON response
        model_class: Pydantic model to validate against
        stage: Pipeline stage (for logging)

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationError: If validation fails
    """
    try:
        validated = model_class(**data)
        return validated
    except ValidationError as e:
        error_msg = f"Validation failed for {stage}: {str(e)}"
        log_error(error_msg)
        raise ValueError(error_msg)
