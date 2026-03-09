"""Feature: Live current-card panel."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from lib import anki, convert

router = APIRouter(prefix="/current-card")
templates = Jinja2Templates(directory="templates")


@router.get("/poll", response_class=HTMLResponse)
async def poll_current_card(request: Request):
    """Called by HTMX every 2s. Returns a rendered card fragment or empty."""
    card = await anki.gui_current_card()
    if not card:
        return HTMLResponse("")
    note_id = card.get("noteId")
    fields_html: dict = card.get("fields", {})
    fields_md = {k: convert.html_to_markdown(v["value"]) for k, v in fields_html.items()}
    return templates.TemplateResponse(
        "partials/current_card.html",
        {"request": request, "note_id": note_id, "fields": fields_md},
    )


# TODO: POST /current-card/save — convert fields MD→HTML, call update_note_fields
# TODO: POST /current-card/suggest — send card + review history to LLM, return proposal
