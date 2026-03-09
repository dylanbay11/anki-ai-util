"""Feature: Live current-card panel."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from lib import anki, convert

router = APIRouter(prefix="/current-card")
templates = Jinja2Templates(directory="templates")


@router.get("/poll", response_class=HTMLResponse)
async def poll_current_card(request: Request):
    """
    Called by HTMX every 2s. Returns a rendered card fragment or empty string.

    gui_current_card() returns both a cardId and a noteId — these are
    different things. We pass both to the template:
      - note_id is used when saving edits (update_note_fields takes a noteId)
      - card_id is used when fetching review history (get_reviews_of_cards takes cardIds)
    """
    card = await anki.gui_current_card()
    if not card:
        return HTMLResponse("")
    note_id: int = card["noteId"]
    card_id: int = card["cardId"]
    fields_html: dict = card.get("fields", {})
    fields_md = {k: convert.html_to_markdown(v["value"]) for k, v in fields_html.items()}
    return templates.TemplateResponse(
        "partials/current_card.html",
        {"request": request, "note_id": note_id, "card_id": card_id, "fields": fields_md},
    )


# TODO: POST /current-card/save
#   Body: note_id (int), fields (dict of field_name → markdown string)
#   Convert each field markdown_to_html, then call update_note_fields(note_id, ...)

# TODO: POST /current-card/suggest
#   Body: note_id (int), card_id (int)
#   1. notes_info([note_id]) to get current field content
#   2. get_reviews_of_cards([card_id]) to get review history
#      NOTE: pass card_id here, not note_id — they are different
#   3. Send both to LLM, return proposed edit as a diff fragment
