"""
AnkiConnect wrapper. All calls go through invoke().

IMPORTANT — Notes vs Cards:
  Anki separates content (notes) from scheduling (cards). This distinction
  causes bugs if confused.

  NOTE:   The unit of *content*. Has fields (e.g. Front/Back), tags, and a
          note type (model). Identified by a noteId. One note produces one or
          more cards depending on the note type's templates — e.g. a
          "Basic (and reversed)" note produces 2 cards from the same fields.
          You *edit content* at the note level via updateNoteFields(noteId).

  CARD:   The unit of *scheduling*. Tracks due date, interval, ease factor,
          and review history. Identified by a cardId. Many-to-one with notes.
          You *query review history* at the card level via getReviewsOfCards.

  Key consequence for this project:
    - find_notes / notes_info / update_note_fields / add_note → use noteIds
    - get_reviews_of_cards → uses cardIds
    - gui_current_card returns BOTH a cardId and a noteId. Use noteId to edit
      the note's fields; use cardId to fetch review history.
    - notes_info returns each note with a "cards" key: a list of cardIds for
      that note. Use those cardIds when you need review history for a note.
"""
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


# --- Note-level operations (content) ---

async def find_notes(query: str) -> list[int]:
    """Returns noteIds matching query. E.g. query='deck:MyDeck'."""
    return await invoke("findNotes", query=query)


async def notes_info(note_ids: list[int]) -> list[dict]:
    """
    Returns note dicts. Each dict contains:
      noteId, modelName, tags,
      fields: {field_name: {"value": html_string, "order": int}, ...}
      cards: [cardId, ...]   ← cardIds for this note; use for review history
    """
    return await invoke("notesInfo", notes=note_ids)


async def add_note(
    deck_name: str,
    model_name: str,
    fields: dict[str, str],
    tags: list[str] | None = None,
) -> int:
    """Creates a note. Returns the new noteId."""
    note = {
        "deckName": deck_name,
        "modelName": model_name,
        "fields": fields,
        "tags": tags or [],
        "options": {"allowDuplicate": False},
    }
    return await invoke("addNote", note=note)


async def update_note_fields(note_id: int, fields: dict[str, str]) -> None:
    """Updates a note's field content. Takes a noteId, not a cardId."""
    await invoke("updateNoteFields", note={"id": note_id, "fields": fields})


# --- Card-level operations (scheduling / review history) ---

async def gui_current_card() -> dict | None:
    """
    Returns the card currently shown in Anki's review window, or None.
    The returned dict contains BOTH:
      cardId  — use this for get_reviews_of_cards
      noteId  — use this for update_note_fields
      fields  — {field_name: {"value": html_string, "order": int}, ...}
    Do not confuse cardId with noteId — they are different numbers.
    """
    return await invoke("guiCurrentCard")


async def get_reviews_of_cards(card_ids: list[int]) -> dict:
    """
    Returns review history keyed by cardId (as strings).
    Takes cardIds, NOT noteIds. To get review history for a note, first
    retrieve its cardIds from notes_info(...)["cards"].
    """
    return await invoke("getReviewsOfCards", cards=card_ids)
