# Anki Companion — AI Coding Starter Document

## What This Is

A local companion utility for Anki that provides AI-assisted card creation and editing without replacing Anki or modifying its internals. The user runs Anki normally. This tool runs alongside it, communicating via AnkiConnect (a free Anki add-on that exposes a local REST API on port 8765). Anki never knows this tool exists — it just sees normal card edits coming through its API.

The core problem being solved: Anki's card creation and editing workflow is hostile to AI assistance. Fields are stored as HTML, the editing UI is a modal database browser, and there is no clean interface for bulk operations. This tool presents card content as Markdown, lets the user work with AI to create or edit cards, and converts back to HTML before writing to Anki.

---

## Environment Notes (Dev Machine)

- **OS:** Ubuntu 22.04 LTS (older release; Anki version constraints apply)
- **Anki:** Installed from an older/LTS-compatible package. Anki is running and functional. It may log a timezone-change warning on startup — this is cosmetic and does not affect AnkiConnect operation.
- **AnkiConnect:** Installed and confirmed responding on `http://localhost:8765` (returns `{"result": 6, "error": null}` to a `version` action).
- **Node.js:** Not available via system package manager at a usable version. Installed Node.js 20 via nvm. Always load nvm before running `node`/`npm`: `export NVM_DIR="$HOME/.nvm" && source "$NVM_DIR/nvm.sh"`.
- **gh CLI:** Available (`gh version 2.4.0`), authenticated as `dylanbay11`. Repo: `https://github.com/dylanbay11/anki-ai-util`.

---

## Prerequisites (User's Responsibility)

- Anki is installed and running
- The AnkiConnect add-on is installed in Anki (code: 2055492159)
- AnkiConnect is accessible at `http://localhost:8765`
- An Anthropic API key is available in the environment

---

## Tech Stack

- **Runtime:** Node.js
- **Framework:** Next.js (App Router) — local dev server only, not deployed
- **Styling:** Tailwind CSS
- **AI:** Anthropic SDK (`@anthropic-ai/sdk`), model `claude-sonnet-4-20250514`
- **Markdown↔HTML:** Turndown (HTML → Markdown) + marked (Markdown → HTML)
- **AnkiConnect:** Plain fetch calls to `http://localhost:8765` (no special library needed)

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

## Conversion Layer

This is the foundation everything else builds on. Implement as `lib/convert.ts`:

- `htmlToMarkdown(html: string): string` — use Turndown; handle common Anki patterns (cloze spans, image tags, code blocks)
- `markdownToHtml(md: string): string` — use marked; output must be clean HTML Anki will render correctly
- Cloze syntax must be preserved: Anki uses `{{c1::text}}` — this should pass through both directions unchanged

---

## Features

### 1. Card Generation from Text

User pastes source material (notes, a paragraph, a list of facts). AI generates a set of draft notes (front/back pairs or cloze cards). User reviews each draft — Accept, Edit, or Skip. Accepted drafts are pushed to Anki via `addNote`.

AI prompt strategy: instruct the model to follow the minimum information principle (one fact per card), prefer cloze for lists and enumerations, avoid cards with fronts like "list all X". Return structured JSON — an array of `{front, back, type}` objects where type is `"basic"` or `"cloze"`.

### 2. Bulk AI Editing

User selects a deck. The tool fetches all notes via `findNotes` + `notesInfo`, converts fields to Markdown, and displays them in a list. User writes a natural language instruction ("make these more concise", "add a mnemonic hint to each back", "rewrite in simple English"). AI processes all notes and returns proposed edits. User steps through proposals — Accept, Edit, or Skip — and accepted edits are written back via `updateNoteFields` with Markdown converted back to HTML.

Batch in groups of 20 notes per AI call. Do not send entire decks in one prompt.

### 3. Current Card Quick Edit

Polls `guiCurrentCard` every 2 seconds while Anki is open. Displays the current card's fields as Markdown in a small persistent panel. User can edit inline and save — changes are written back immediately via `updateNoteFields`. Optionally, a "Suggest improvement" button sends the card to the AI with its recent review history as context and proposes a rewrite.

This is the highest-value feature. The review session is the highest-intent moment for card edits and Anki provides no good path for it.

### 4. AI Edit Proposal for a Single Card

Given a note ID, fetch the note, fetch its review history via `getReviewsOfCards`, send both to the AI, and return a proposed edit with a one-sentence rationale. Display as a diff (original vs. proposed). User accepts, edits, or rejects.

---

## AI Layer

All AI calls go through a single `lib/llm.ts` module. It should:

- Accept a system prompt, user prompt, and optional structured output schema
- Use the Anthropic SDK with `claude-sonnet-4-20250514`
- Return parsed JSON when structured output is requested, raw text otherwise
- Handle retries (max 2) on rate limit errors

For structured outputs, instruct the model in the system prompt to return only valid JSON with no preamble or markdown fences. Parse with a try/catch and surface parse errors clearly.

---

## Project Structure

```
/
├── app/
│   ├── page.tsx               # Home: deck selector + feature entry points
│   ├── generate/page.tsx      # Card generation from text
│   ├── bulk-edit/page.tsx     # Bulk AI editing for a deck
│   └── api/
│       ├── anki/route.ts      # Proxy to AnkiConnect (avoids CORS)
│       └── ai/route.ts        # AI call handler
├── lib/
│   ├── anki.ts                # AnkiConnect wrapper functions
│   ├── convert.ts             # HTML ↔ Markdown conversion
│   └── llm.ts                 # AI service layer
└── components/
    ├── ProposalReviewer.tsx    # Step-through accept/reject UI for AI proposals
    ├── MarkdownEditor.tsx      # Markdown textarea with live preview
    └── CurrentCard.tsx        # Live current-card panel
```

---

## Environment Variables

```
ANTHROPIC_API_KEY=        # Required
ANKI_CONNECT_URL=         # Default: http://localhost:8765
```

---

## Key Implementation Notes

- **Always check AnkiConnect availability on startup.** Hit `http://localhost:8765` with a `version` action. If it fails, show a clear "Anki is not running or AnkiConnect is not installed" message before rendering anything.
- **Never write directly to Anki without user confirmation.** Every AI-generated or AI-modified card goes through the proposal UI before `addNote` or `updateNoteFields` is called.
- **Cloze and Basic are different note types in Anki.** When adding notes, `addNote` requires specifying the model name (`"Basic"` or `"Cloze"`). Do not mix them. The deck the user selects may contain both types; handle this when fetching and displaying notes.
- **AnkiConnect field names are deck-specific.** The default Basic note type has fields named `"Front"` and `"Back"`. But users may have custom note types with different field names. When displaying or editing fields, use the actual field names from `notesInfo` — do not hardcode `"Front"`/`"Back"`.
- **HTML → Markdown conversion will be lossy for some cards.** Cards with tables, complex formatting, or LaTeX will not convert cleanly. Flag these and show the raw HTML as a fallback rather than a broken Markdown rendering.