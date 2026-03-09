"""Feature: Live current-card panel — view, edit, and AI-suggest improvements."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from lib import anki, convert, llm

router = APIRouter(prefix="/current-card")
templates = Jinja2Templates(directory="templates")

_EASE_LABEL = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}

_SUGGEST_SYSTEM = """You are an Anki flashcard editor. Improve the given card based on its \
content and recent review history. Follow the minimum information principle: one fact per \
card, unambiguous front, concise back. Preserve cloze syntax ({{c1::text}}) exactly. \
Return ONLY a JSON object with the same field names as the input and improved Markdown \
values. No preamble, no explanation, no code fences."""


def _summarise_reviews(reviews_by_card: dict, card_id: int) -> str:
    """Format the last 10 reviews of a card as a readable string for the LLM."""
    entries = reviews_by_card.get(str(card_id), [])
    if not entries:
        return "No review history."
    recent = sorted(entries, key=lambda r: r["id"], reverse=True)[:10]
    lines = [_EASE_LABEL.get(r["ease"], f"ease-{r['ease']}") for r in recent]
    return "Most recent first: " + ", ".join(lines)


@router.get("/poll", response_class=HTMLResponse)
async def poll_current_card(request: Request, current_note_id: int | None = None):
    """
    Called by HTMX every 2s.

    If the caller passes current_note_id and it matches what Anki is showing,
    returns 204 so HTMX does nothing — preserving any in-progress edits.
    Only returns the full card fragment when the card has changed (or on first load).
    """
    card = await anki.gui_current_card()
    if not card:
        return HTMLResponse("")

    note_id: int = card["noteId"]
    card_id: int = card["cardId"]

    # Same card still showing — tell HTMX to do nothing so the form isn't wiped
    if current_note_id is not None and current_note_id == note_id:
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
    fields_md = {k: str(v) for k, v in form.items() if k != "note_id"}
    fields_html = {k: convert.markdown_to_html(v) for k, v in fields_md.items()}
    await anki.update_note_fields(note_id, fields_html)
    return HTMLResponse('<p class="save-ok">Saved.</p>')


@router.post("/suggest", response_class=HTMLResponse)
async def suggest_edit(request: Request):
    """
    Asks the AI to propose an improved version of the current card.

    Expects form data: note_id (int), card_id (int).
    Fetches current field content and review history, sends both to the LLM,
    and returns a proposal fragment the user can accept or discard.

    Note: review history requires card_id (not note_id) — different things.
    """
    form = await request.form()
    note_id = int(form["note_id"])
    card_id = int(form["card_id"])

    # Fetch current note content (notesInfo takes noteId)
    notes = await anki.notes_info([note_id])
    note = notes[0]
    fields_md = {
        k: convert.html_to_markdown(v["value"])
        for k, v in note["fields"].items()
    }

    # Fetch review history (getReviewsOfCards takes cardId, not noteId)
    reviews = await anki.get_reviews_of_cards([card_id])
    review_summary = _summarise_reviews(reviews, card_id)

    fields_block = "\n".join(f"{k}: {v}" for k, v in fields_md.items())
    user_prompt = (
        f"Card fields (Markdown):\n{fields_block}\n\n"
        f"Review history (last 10, most recent first): {review_summary}\n\n"
        "Propose improved field values."
    )

    proposed: dict = await llm.call_llm_json(_SUGGEST_SYSTEM, user_prompt)

    return templates.TemplateResponse(
        "partials/proposal.html",
        {
            "request": request,
            "note_id": note_id,
            "original": fields_md,
            "proposed": proposed,
        },
    )
