# Anki Companion — AI Coding Starter Document

## What This Is

A local companion utility for Anki that provides AI-assisted card creation and editing without replacing Anki or modifying its internals. The user runs Anki normally. This tool runs alongside it, communicating via AnkiConnect (a free Anki add-on that exposes a local REST API on port 8765). Anki never knows this tool exists — it just sees normal card edits coming through its API.

The core problem being solved: Anki's card creation and editing workflow is hostile to AI assistance. Fields are stored as HTML, the editing UI is a modal database browser, and there is no clean interface for bulk operations. This tool presents card content as Markdown, lets the user work with AI to create or edit cards, and converts back to HTML before writing to Anki.

---

## Environment Notes (Dev Machine)

- **OS:** Ubuntu 22.04 LTS (older release; Anki version constraints apply)
- **Anki:** Installed from an older/LTS-compatible package. Anki is running and functional. It may log a timezone-change warning on startup — this is cosmetic and does not affect AnkiConnect operation.
- **AnkiConnect:** Installed and confirmed responding on `http://localhost:8765` (returns `{"result": 6, "error": null}` to a `version` action).
- **Python:** 3.13.7 via pyenv. Package management via **uv**. Run everything with `uv run ...`.
- **gh CLI:** Available (`gh version 2.4.0`), authenticated as `dylanbay11`. Repo: `https://github.com/dylanbay11/anki-ai-util`.

---

## Prerequisites (User's Responsibility)

- Anki is installed and running
- The AnkiConnect add-on is installed in Anki (code: 2055492159)
- AnkiConnect is accessible at `http://localhost:8765`
- An Anthropic API key is set in `.env` (copy `.env.example`)

---

## Tech Stack

- **Runtime:** Python 3.13.7, managed via uv
- **Web framework:** FastAPI + Uvicorn
- **Frontend:** Jinja2 templates + HTMX (no build step, no JS framework)
- **Styling:** Plain CSS (`static/style.css`)
- **AI:** Anthropic SDK (`anthropic`), model `claude-sonnet-4-20250514`
- **Markdown↔HTML:** `markdownify` (HTML → Markdown) + `markdown` (Markdown → HTML)
- **AnkiConnect:** `httpx` async calls to `http://localhost:8765`

---

## Running the Dev Server

```bash
uv run uvicorn main:app --reload
```

Then open `http://localhost:8000`.

---

## Notes vs Cards — Critical Distinction

This is a common source of bugs and AI confusion. Read this before touching anything Anki-related.

**Note** — the unit of *content*.
- Has fields (e.g. `Front`, `Back`), tags, and a note type (model name).
- Identified by a `noteId`.
- One note produces **one or more cards** depending on the note type's templates. Example: a "Basic (and reversed card)" note type generates 2 cards from the same fields — one asking Front→Back and one Back→Front.
- You **edit content** at the note level: `updateNoteFields(noteId, fields)`.

**Card** — the unit of *scheduling*.
- Tracks due date, interval, ease factor, and review history.
- Identified by a `cardId`. Many-to-one with notes.
- You **query review history** at the card level: `getReviewsOfCards([cardId, ...])`.

**Practical consequences for this project:**

| Operation | Use |
|---|---|
| Find content by deck/tag | `findNotes` → returns `noteId` list |
| Read or edit field content | `notesInfo(noteIds)` / `updateNoteFields(noteId, ...)` |
| Get review history | `getReviewsOfCards(cardIds)` — **cardIds, not noteIds** |
| Current review session | `guiCurrentCard()` → returns **both** `cardId` and `noteId` |
| Bridge note → its cards | `notesInfo` result includes `"cards": [cardId, ...]` for each note |

**`guiCurrentCard` returns both IDs — don't mix them up:**
- Use `result["noteId"]` when saving edits to field content.
- Use `result["cardId"]` when fetching review history.

**To get review history for a note:** you cannot do it directly. First call `notesInfo([noteId])`, then take the `"cards"` list from the result, then pass those cardIds to `getReviewsOfCards`.

---

## AnkiConnect Basics

All AnkiConnect calls are POST requests to `http://localhost:8765` with this shape:

```json
{
  "action": "actionName",
  "version": 6,
  "params": {}
}
```

Key actions used in this project:

| Action | Purpose |
|---|---|
| `deckNames` | List all decks |
| `findNotes` | Find note IDs by query string (e.g. `"deck:MyDeck"`) |
| `notesInfo` | Get full note content (fields, tags) by note ID array |
| `addNote` | Create a new note |
| `updateNoteFields` | Update fields of an existing note |
| `guiCurrentCard` | Get the card currently shown in Anki's review window |
| `getReviewsOfCards` | Get review history for a set of card IDs |

All field values coming from AnkiConnect are HTML strings. All field values being written back must be HTML strings. The conversion layer handles this transparently.

---

## Conversion Layer (`lib/convert.py`)

- `html_to_markdown(html: str) -> str` — uses markdownify; preserves cloze syntax
- `markdown_to_html(md: str) -> str` — uses markdown lib; output is clean HTML for Anki
- Cloze syntax `{{c1::text}}` is encoded to a placeholder before conversion and decoded after, so it passes through both directions unchanged

---

## Features

### 1. Card Generation from Text

User pastes source material (notes, a paragraph, a list of facts). AI generates a set of draft notes (front/back pairs or cloze cards). User reviews each draft — Accept, Edit, or Skip. Accepted drafts are pushed to Anki via `addNote`.

AI prompt strategy: instruct the model to follow the minimum information principle (one fact per card), prefer cloze for lists and enumerations, avoid cards with fronts like "list all X". Return structured JSON — an array of `{front, back, type}` objects where type is `"basic"` or `"cloze"`.

### 2. Bulk AI Editing

User selects a deck. The tool fetches all notes via `findNotes` + `notesInfo`, converts fields to Markdown, and displays them in a list. User writes a natural language instruction ("make these more concise", "add a mnemonic hint to each back", "rewrite in simple English"). AI processes all notes and returns proposed edits. User steps through proposals — Accept, Edit, or Skip — and accepted edits are written back via `updateNoteFields` with Markdown converted back to HTML.

Batch in groups of 20 notes per AI call. Do not send entire decks in one prompt.

### 3. Current Card Quick Edit

Polls `guiCurrentCard` every 2 seconds via HTMX while the page is open. Displays the current card's fields as Markdown in a persistent panel. User can edit inline and save — changes are written back immediately via `updateNoteFields`. Optionally, a "Suggest improvement" button sends the card to the AI with its recent review history as context and proposes a rewrite.

This is the highest-value feature. The review session is the highest-intent moment for card edits and Anki provides no good path for it.

### 4. AI Edit Proposal for a Single Card

Given a `noteId`, fetch the note via `notesInfo` (which also returns the note's `cards: [cardId, ...]`). Then fetch review history via `getReviewsOfCards` using those cardIds — **not** the noteId, which would be wrong. Send both the field content and review history to the AI and return a proposed edit with a one-sentence rationale. Display as a diff (original vs. proposed). User accepts, edits, or rejects.

---

## AI Layer (`lib/llm.py`)

- `call_llm(system, user) -> str` — async; retries up to 2 times on rate limit errors
- `call_llm_json(system, user) -> object` — same, but parses the response as JSON; strips markdown fences if present

---

## Project Structure

```
/
├── main.py                    # FastAPI app, mounts routers
├── pyproject.toml             # uv/pip dependencies
├── .env.example               # Copy to .env and fill in key
├── lib/
│   ├── anki.py                # AnkiConnect async wrapper (httpx)
│   ├── convert.py             # HTML ↔ Markdown (cloze-safe)
│   └── llm.py                 # Anthropic SDK wrapper
├── routers/
│   ├── generate.py            # /generate — card generation from text
│   ├── bulk_edit.py           # /bulk-edit — bulk AI editing
│   └── current_card.py        # /current-card — live card panel + polling
├── templates/
│   ├── base.html              # Shared layout with nav + HTMX CDN
│   ├── index.html             # Home page with AnkiConnect status
│   ├── generate.html
│   ├── bulk_edit.html
│   └── partials/
│       └── current_card.html  # HTMX-swapped fragment
└── static/
    └── style.css
```

---

## Environment Variables

```
ANTHROPIC_API_KEY=        # Required
ANKI_CONNECT_URL=         # Default: http://localhost:8765
```

---

## Key Implementation Notes

- **Always check AnkiConnect availability on startup.** The lifespan handler in `main.py` checks the connection and warns if unavailable. The home page also shows live status.
- **Never write directly to Anki without user confirmation.** Every AI-generated or AI-modified card goes through the proposal UI before `addNote` or `updateNoteFields` is called.
- **Cloze and Basic are different note types in Anki.** When adding notes, `addNote` requires specifying the model name (`"Basic"` or `"Cloze"`). Do not mix them.
- **AnkiConnect field names are deck-specific.** The default Basic note type has fields named `"Front"` and `"Back"`. But users may have custom note types with different field names. Use the actual field names from `notesInfo` — do not hardcode `"Front"`/`"Back"`.
- **HTML → Markdown conversion will be lossy for some cards.** Cards with tables, complex formatting, or LaTeX will not convert cleanly. Flag these and show the raw HTML as a fallback.
- **HTMX is used for interactivity.** Loaded from CDN in `base.html`. Polling uses `hx-trigger="every 2s"`. Proposal step-through uses `hx-swap` to replace partial fragments. No JS framework needed.
