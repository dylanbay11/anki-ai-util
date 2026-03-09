"""LLM client: structured calls via Instructor + Pydantic, with JSONL request logging.

Provider is selected by the LLM_PROVIDER env var (anthropic [default] | openai).
Model is selected by LLM_MODEL env var, or a sensible per-provider default.

Logging
-------
Every call is appended to logs/llm_requests.jsonl as a single JSON line:
  {"ts", "stage", "model", "system", "user", "response", "duration_ms", "error"}
The log directory is created automatically if absent.
"""
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar

import instructor
from pydantic import BaseModel

_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
MODEL = os.getenv("LLM_MODEL", "")

_LOG_FILE = Path(__file__).parent.parent / "logs" / "llm_requests.jsonl"

T = TypeVar("T", bound=BaseModel)

# ---------------------------------------------------------------------------
# Provider setup
# ---------------------------------------------------------------------------

if _PROVIDER == "openai":
    try:
        import openai as _openai_mod
        _openai_raw = _openai_mod.AsyncOpenAI()
        _client: instructor.AsyncInstructor = instructor.from_openai(_openai_raw)
    except ImportError as exc:
        raise RuntimeError("openai package not installed. Run: uv add openai") from exc
    if not MODEL:
        MODEL = "gpt-4o"

    async def _free_text(system: str, user: str) -> str:
        resp = await _openai_raw.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    _rate_limit_exc = _openai_mod.RateLimitError

else:
    import anthropic as _anthropic_mod
    from anthropic import AsyncAnthropic
    _anthropic_raw = AsyncAnthropic()
    _client = instructor.from_anthropic(_anthropic_raw)
    if not MODEL:
        MODEL = "claude-sonnet-4-20250514"

    async def _free_text(system: str, user: str) -> str:
        msg = await _anthropic_raw.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in msg.content if block.type == "text")

    _rate_limit_exc = _anthropic_mod.RateLimitError


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(
    stage: str,
    system: str,
    user: str,
    response: object,
    duration_ms: int,
    error: str | None = None,
) -> None:
    _LOG_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "model": MODEL,
        "system": system,
        "user": user,
        "response": response,
        "duration_ms": duration_ms,
        "error": error,
    }
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def call_structured(
    response_model: type[T],
    system: str,
    user: str,
    stage: str = "",
    max_retries: int = 2,
) -> T:
    """Call the LLM and return a validated Pydantic model instance.

    max_retries controls Instructor's validation retry count (not rate-limit retries).
    Rate-limit errors are retried up to 3 times with exponential back-off.
    """
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            start = time.monotonic()
            result: T = await _client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user}],
                response_model=response_model,
                max_retries=max_retries,
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            _log(stage, system, user, result.model_dump(), duration_ms)
            return result
        except _rate_limit_exc as e:
            last_error = e
            if attempt == 2:
                _log(stage, system, user, None, 0, error=str(e))
                raise
            await asyncio.sleep(2 * (attempt + 1))
    raise last_error  # type: ignore[misc]


async def call_llm(system: str, user: str, stage: str = "") -> str:
    """Free-text LLM call (no structured output). For non-JSON use cases."""
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            start = time.monotonic()
            text = await _free_text(system, user)
            duration_ms = int((time.monotonic() - start) * 1000)
            _log(stage, system, user, text, duration_ms)
            return text
        except _rate_limit_exc as e:
            last_error = e
            if attempt == 2:
                _log(stage, system, user, None, 0, error=str(e))
                raise
            await asyncio.sleep(2 * (attempt + 1))
    raise last_error  # type: ignore[misc]
