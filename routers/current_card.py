"""Feature: Live current-card panel — view, edit, and AI-suggest improvements."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from lib import anki, convert, llm, policy, prompts, validate
from lib.models import CardProposal, JudgeResult

router = APIRouter(prefix="/current-card")
templates = Jinja2Templates(directory="templates")

_EASE_LABEL = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}


def _summarise_reviews(reviews_by_card: dict, card_id: int) -> str:
    """Format the last 10 reviews of a card as a readable string for the LLM."""
    entries = reviews_by_card.get(str(card_id), [])
    if not entries:
        return "No review history."
    recent = sorted(entries, key=lambda r: r["id"], reverse=True)[:10]
    lines = [_EASE_LABEL.get(r["ease"], f"ease-{r['ease']}") for r in recent]
    return "Most recent first: " + ", ".join(lines)


@router.get("/poll", response_class=HTMLResponse)
async def poll_current_card(request: Request, current_note_id: str = ""):
    """
    Called by HTMX every 2s.

    If the caller passes current_note_id and it matches what Anki is showing,
    returns 204 so HTMX does nothing — preserving any in-progress edits.
    Only returns the full card fragment when the card has changed (or on first load).
    """
    try:
        card = await anki.gui_current_card()
    except Exception:
        return HTMLResponse("")
    if not card:
        return HTMLResponse("")

    card_id: int = card["cardId"]
    # guiCurrentCard does not include noteId — look it up via cardsInfo
    card_info = (await anki.cards_info([card_id]))[0]
    note_id: int = card_info["note"]

    # Same card still showing — tell HTMX to do nothing so the form isn't wiped
    parsed_note_id = int(current_note_id) if current_note_id.isdigit() else None
    if parsed_note_id is not None and parsed_note_id == note_id:
        return Response(status_code=204)

    fields_html: dict = card.get("fields", {})
    fields_md = {k: convert.html_to_markdown(v["value"]) for k, v in fields_html.items()}
    return templates.TemplateResponse(
        "partials/current_card.html",
        {"request": request, "note_id": note_id, "card_id": card_id, "fields": fields_md},
    )


@router.post("/save", response_class=HTMLResponse)
async def save_current_card(request: Request):
    """
    Saves edited field values back to Anki.

    Expects form data with:
      note_id — the noteId to update (not the cardId)
      one key per field, named by the Anki field name, value in Markdown
    Converts each field Markdown → HTML before writing.
    """
    form = await request.form()
    note_id = int(form["note_id"])
    # Skip metadata keys; every other key is an Anki field name
    skip = {"note_id", "card_id"}
    fields_md = {k: str(v) for k, v in form.items() if k not in skip}
    fields_html = {k: convert.markdown_to_html(v) for k, v in fields_md.items()}
    await anki.update_note_fields(note_id, fields_html)
    return HTMLResponse('<p class="save-ok">Saved.</p>')


@router.get("/clear-proposal", response_class=HTMLResponse)
async def clear_proposal():
    """Called by the Discard/Dismiss button to empty the proposal div."""
    return HTMLResponse("")


@router.post("/suggest", response_class=HTMLResponse)
async def suggest_edit(request: Request):
    """
    Two-stage pipeline: judge evaluates whether the card needs changes, then
    suggest proposes the actual edits if it does.

    Expects form data: note_id (int), card_id (int).
    """
    form = await request.form()
    note_id = int(form["note_id"])
    card_id = int(form["card_id"])  # cardId from guiCurrentCard, not noteId

    # Fetch current note content (notesInfo takes noteId)
    notes = await anki.notes_info([note_id])
    note = notes[0]
    fields_md = {
        k: convert.html_to_markdown(v["value"])
        for k, v in note["fields"].items()
    }

    # Fetch review history (getReviewsOfCards takes cardId, not noteId).
    # Older AnkiConnect versions don't support this action — degrade gracefully.
    try:
        reviews = await anki.get_reviews_of_cards([card_id])
        review_summary = _summarise_reviews(reviews, card_id)
    except RuntimeError:
        review_summary = "No review history available."

    fields_block = "\n".join(f"{k}: {v}" for k, v in fields_md.items())
    base_user_prompt = (
        f"Card fields (Markdown):\n{fields_block}\n\n"
        f"Review history (last 10, most recent first): {review_summary}"
    )

    # Stage 1: judge — decide if the card needs changes at all
    judge_system = policy.CARD_QUALITY + "\n\n" + prompts.load("judge_v1.md")
    judge: JudgeResult = await llm.call_structured(
        JudgeResult, judge_system, base_user_prompt, stage="judge"
    )

    if not judge.needs_changes:
        return templates.TemplateResponse(
            "partials/no_changes.html",
            {"request": request, "reason": judge.reason},
        )

    # Stage 2: suggest — propose the actual edits
    suggest_user_prompt = (
        base_user_prompt + f"\n\nImprovement area identified: {judge.reason}"
    )
    suggest_system = policy.CARD_QUALITY + "\n\n" + prompts.load("single_suggestion_v1.md")
    proposal: CardProposal = await llm.call_structured(
        CardProposal, suggest_system, suggest_user_prompt, stage="suggest"
    )

    try:
        result = validate.validate_proposal(fields_md, proposal)
    except ValueError as e:
        return HTMLResponse(f'<p class="proposal-error">Validation error: {e}. Try again.</p>')

    original_html = {k: convert.markdown_to_html(v) for k, v in fields_md.items()}
    return templates.TemplateResponse(
        "partials/proposal.html",
        {
            "request": request,
            "note_id": note_id,
            "original": fields_md,
            "original_html": original_html,
            "proposed": result.fields,
            "rationale": result.rationale,
            "has_changes": result.has_changes,
            "warnings": result.warnings,
        },
    )
