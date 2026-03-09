"""Feature: Bulk AI editing of a deck."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/bulk-edit")
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def bulk_edit_page(request: Request):
    return templates.TemplateResponse("bulk_edit.html", {"request": request})


# TODO: GET /bulk-edit/decks — return deck list for selector (HTMX)
# TODO: POST /bulk-edit/run — fetch notes, batch through LLM, return proposals
# TODO: POST /bulk-edit/accept — write accepted edits back via update_note_fields
