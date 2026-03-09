"""Loads policy files from the policies/ directory."""
from pathlib import Path

_POLICY_DIR = Path(__file__).parent.parent / "policies"


def _load(filename: str) -> str:
    return (_POLICY_DIR / filename).read_text(encoding="utf-8").strip()


CARD_QUALITY = _load("card_quality.md")
