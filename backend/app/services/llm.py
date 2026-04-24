"""
LLM abstraction layer.
Routes requests to either Claude API or Ollama based on configuration.
Supports swapping backends without changing calling code.
"""

import json

import httpx
import structlog

from app.core.config import settings

logger = structlog.stdlib.get_logger()


async def chat_completion(
    *,
    system: str,
    user_message: str,
    max_tokens: int = 500,
    model_tier: str = "fast",
) -> str:
    """Send a chat completion request to the configured LLM backend.

    Args:
        system: System prompt.
        user_message: User message content.
        max_tokens: Maximum response tokens.
        model_tier: "fast" for categorization/classification (Sonnet or small local),
                    "reasoning" for diagnosis/reports (Opus or large local).

    Returns:
        The assistant's response text.
    """
    if settings.llm_backend == "ollama":
        return await _ollama_chat(system, user_message, max_tokens, model_tier)
    else:
        return await _claude_chat(system, user_message, max_tokens, model_tier)


async def _claude_chat(
    system: str, user_message: str, max_tokens: int, model_tier: str
) -> str:
    """Call Claude API via the Anthropic SDK."""
    import anthropic

    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    model = (
        settings.claude_sonnet_model
        if model_tier == "fast"
        else settings.claude_opus_model
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    response_text = message.content[0].text.strip()
    logger.info("claude_completion", model=model, tokens=message.usage.output_tokens)
    return response_text


async def _ollama_chat(
    system: str, user_message: str, max_tokens: int, model_tier: str
) -> str:
    """Call Ollama's chat API."""
    model = (
        settings.ollama_fast_model
        if model_tier == "fast"
        else settings.ollama_reasoning_model
    )

    url = f"{settings.ollama_base_url}/api/chat"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {
            "num_predict": max_tokens,
        },
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    response_text = data["message"]["content"].strip()
    logger.info(
        "ollama_completion",
        model=model,
        eval_count=data.get("eval_count"),
        total_duration_ms=data.get("total_duration", 0) // 1_000_000,
    )
    return response_text


async def chat_completion_json(
    *,
    system: str,
    user_message: str,
    max_tokens: int = 500,
    model_tier: str = "fast",
) -> dict:
    """Send a chat completion and parse the response as JSON.

    Falls back to extracting JSON from markdown code blocks if needed.
    """
    text = await chat_completion(
        system=system,
        user_message=user_message,
        max_tokens=max_tokens,
        model_tier=model_tier,
    )

    # Clean common LLM quirks before parsing
    cleaned = _clean_json_response(text)

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```" in text:
        blocks = text.split("```")
        for block in blocks[1::2]:
            block_cleaned = block.strip()
            if block_cleaned.startswith("json"):
                block_cleaned = block_cleaned[4:].strip()
            block_cleaned = _clean_json_response(block_cleaned)
            try:
                return json.loads(block_cleaned)
            except json.JSONDecodeError:
                continue

    # Last resort: find first { ... } or [ ... ] in the text
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = cleaned.find(start_char)
        end = cleaned.rfind(end_char)
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                continue

    # Try to repair truncated JSON (LLM hit max_tokens mid-response)
    repaired = _repair_truncated_json(cleaned)
    if repaired is not None:
        return repaired

    logger.warning("json_parse_failed", response_preview=text[:200])
    raise ValueError(f"Could not parse LLM response as JSON: {text[:200]}")


def _clean_json_response(text: str) -> str:
    """Clean common LLM JSON formatting issues."""
    import re

    # Replace double braces {{ }} with single { } (common LLM escape issue)
    text = text.replace("{{", "{").replace("}}", "}")

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Strip leading/trailing whitespace and common prefixes
    text = text.strip()
    for prefix in ("json", "JSON", "```json", "```"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def _repair_truncated_json(text: str) -> dict | list | None:
    """Attempt to repair JSON that was truncated by max_tokens.

    Strategy: find the opening brace/bracket, then try progressively
    closing open strings and braces until it parses.
    """
    # Find the start of JSON
    start = -1
    for i, ch in enumerate(text):
        if ch in ("{", "["):
            start = i
            break

    if start == -1:
        return None

    fragment = text[start:]

    # Count open braces/brackets
    open_braces = fragment.count("{") - fragment.count("}")
    open_brackets = fragment.count("[") - fragment.count("]")

    # Check if we're inside an unclosed string
    in_string = False
    for ch in fragment:
        if ch == '"' and (not in_string or fragment[max(0, fragment.index(ch) - 1)] != "\\"):
            in_string = not in_string

    repair = fragment
    if in_string:
        repair += '"'

    # Remove any trailing partial key-value (ends with comma or colon)
    import re
    repair = re.sub(r',\s*"[^"]*$', "", repair)
    repair = re.sub(r',\s*$', "", repair)

    # Close open structures
    repair += "}" * open_braces
    repair += "]" * open_brackets

    # Clean again
    repair = _clean_json_response(repair)

    try:
        return json.loads(repair)
    except json.JSONDecodeError:
        return None
