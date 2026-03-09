"""Feature: Generate cards from pasted text."""
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/generate")
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def generate_page(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})


# TODO: POST /generate/run — call LLM, return proposal list via HTMX swap
# TODO: POST /generate/accept — call anki.add_note for an accepted proposal
