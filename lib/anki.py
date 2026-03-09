"""AnkiConnect wrapper. All calls go through invoke()."""
import os
import httpx

ANKI_URL = os.getenv("ANKI_CONNECT_URL", "http://localhost:8765")


async def invoke(action: str, **params) -> object:
    payload = {"action": action, "version": 6, "params": params}
    async with httpx.AsyncClient() as client:
        r = await client.post(ANKI_URL, json=payload, timeout=10)
        r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"AnkiConnect error: {data['error']}")
    return data["result"]


async def check_connection() -> bool:
    try:
        await invoke("version")
        return True
    except Exception:
        return False


async def deck_names() -> list[str]:
    return await invoke("deckNames")


async def find_notes(query: str) -> list[int]:
    return await invoke("findNotes", query=query)


async def notes_info(note_ids: list[int]) -> list[dict]:
    return await invoke("notesInfo", notes=note_ids)


async def add_note(
    deck_name: str,
    model_name: str,
    fields: dict[str, str],
    tags: list[str] | None = None,
) -> int:
    note = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": tags or [],
        "options": {"allowDuplicate": False},
    }
    return await invoke("addNote", note=note)


async def update_note_fields(note_id: int, fields: dict[str, str]) -> None:
    await invoke("updateNoteFields", note={"id": note_id, "fields": fields})


async def gui_current_card() -> dict | None:
    return await invoke("guiCurrentCard")


async def get_reviews_of_cards(card_ids: list[int]) -> dict:
    return await invoke("getReviewsOfCards", cards=card_ids)
