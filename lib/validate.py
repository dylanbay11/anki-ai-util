"""Domain validation for LLM proposal responses.

Structural validation (field types, JSON shape) is handled by Pydantic + Instructor.
This module enforces Anki-specific rules that require comparing the proposal
against the original card content:

  - All original field names must be present in the proposal
  - Cloze tokens ({{c1::text}}) must appear verbatim and unchanged
  - Media tokens ([img:filename], [sound:filename]) must appear verbatim and unchanged
  - has_changes is detected by field equality (stripped)
"""
import re
from dataclasses import dataclass, field as dc_field

from lib.models import CardProposal

_CLOZE_RE = re.compile(r"\{\{c\d+::.*?\}\}")
_IMG_TOKEN_RE = re.compile(r"\[img:[^\]]+\]")
_SOUND_TOKEN_RE = re.compile(r"\[sound:[^\]]+\]")


def _cloze_tokens(text: str) -> set[str]:
    return set(_CLOZE_RE.findall(text))


def _media_tokens(text: str) -> set[str]:
    return set(_IMG_TOKEN_RE.findall(text)) | set(_SOUND_TOKEN_RE.findall(text))


@dataclass
class ProposalResult:
    fields: dict[str, str]
    rationale: str
    has_changes: bool
    warnings: list[str] = dc_field(default_factory=list)


def validate_proposal(
    original_fields: dict[str, str], proposal: CardProposal
) -> ProposalResult:
    """Validate a CardProposal against the original note fields.

    Raises ValueError with a user-readable message on hard errors.
    Returns ProposalResult; non-fatal issues are recorded in .warnings.
    """
    warnings: list[str] = []

    missing_fields = set(original_fields) - set(proposal.fields)
    if missing_fields:
        raise ValueError(f"AI response missing field(s): {missing_fields}")

    for field_name, original_value in original_fields.items():
        proposed_value = proposal.fields[field_name]

        # Verbatim cloze check — full {{cN::text}} tokens must be preserved exactly
        orig_clozes = _cloze_tokens(original_value)
        prop_clozes = _cloze_tokens(proposed_value)
        missing_clozes = orig_clozes - prop_clozes
        if missing_clozes:
            raise ValueError(
                f"Field {field_name!r}: cloze token(s) dropped or altered: {missing_clozes}"
            )
        extra_clozes = prop_clozes - orig_clozes
        if extra_clozes:
            warnings.append(
                f"Field {field_name!r}: new cloze token(s) added by AI: {extra_clozes}"
            )

        # Verbatim media check — [img:...] and [sound:...] tokens must be preserved exactly
        orig_media = _media_tokens(original_value)
        prop_media = _media_tokens(proposed_value)
        missing_media = orig_media - prop_media
        if missing_media:
            raise ValueError(
                f"Field {field_name!r}: media token(s) dropped: {missing_media}"
            )
        extra_media = prop_media - orig_media
        if extra_media:
            warnings.append(
                f"Field {field_name!r}: unexpected new media token(s) added by AI: {extra_media}"
            )

    proposed_fields = {k: proposal.fields[k] for k in original_fields}
    has_changes = any(
        proposed_fields[k].strip() != original_fields[k].strip()
        for k in original_fields
    )

    return ProposalResult(
        fields=proposed_fields,
        rationale=proposal.rationale,
        has_changes=has_changes,
        warnings=warnings,
    )
