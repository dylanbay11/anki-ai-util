"""Loads versioned prompt files from the prompts/ directory.

Prompt files contain task-specific instructions only.
Shared knowledge (e.g. card quality policy) lives in policies/ and is
concatenated with the task prompt at call time:

    system = policy.CARD_QUALITY + "\\n\\n" + prompts.load("judge_v1.md")
"""
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def load(name: str) -> str:
    """Return the contents of prompts/<name> as a string."""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8").strip()
