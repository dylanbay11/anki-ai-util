"""Anthropic SDK wrapper with retry on rate limits."""
import json
import re
import anthropic

MODEL = "claude-sonnet-4-20250514"

_client = anthropic.AsyncAnthropic()


async def call_llm(system: str, user: str) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            msg = await _client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(
                block.text for block in msg.content if block.type == "text"
            )
        except anthropic.RateLimitError as e:
            last_error = e
            if attempt == 2:
                raise
            import asyncio
            await asyncio.sleep(2 * (attempt + 1))
    raise last_error  # type: ignore[misc]


async def call_llm_json(system: str, user: str) -> object:
    raw = await call_llm(system, user)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip markdown fences if present
        cleaned = re.sub(r"^```(?:json)?\n?", "", raw.strip())
        cleaned = re.sub(r"\n?```$", "", cleaned)
        return json.loads(cleaned)
