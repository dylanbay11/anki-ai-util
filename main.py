"""Anki AI Companion — FastAPI entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lib import anki
from routers import bulk_edit, current_card, generate


@asynccontextmanager
async def lifespan(app: FastAPI):
    ok = await anki.check_connection()
    if not ok:
        print("WARNING: AnkiConnect not reachable at startup. Start Anki and reload.")
    yield


app = FastAPI(title="Anki AI Companion", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(generate.router)
app.include_router(bulk_edit.router)
app.include_router(current_card.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    connected = await anki.check_connection()
    return templates.TemplateResponse(
        "index.html", {"request": request, "anki_connected": connected}
    )
