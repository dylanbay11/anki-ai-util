"""Pydantic output models for structured LLM responses."""
from pydantic import BaseModel, Field


class JudgeResult(BaseModel):
    needs_changes: bool
    reason: str = Field(
        description="Brief explanation of why the card does or does not need changes"
    )


class CardProposal(BaseModel):
    rationale: str = Field(
        description="One concise sentence describing the main improvement made"
    )
    fields: dict[str, str] = Field(
        description="Mapping of Anki field name to improved Markdown value"
    )
