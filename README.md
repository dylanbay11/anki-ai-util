# Anki AI Companion

A local tool that runs alongside Anki and brings AI assistance to card creation and editing. Anki stays open as normal — this tool talks to it in the background via AnkiConnect.

---

## What it does

### Generate cards from notes or reading material

Paste in anything — a paragraph, a bullet list, a chunk of lecture notes. The AI drafts a set of Anki cards following good principles (one fact per card, cloze for lists, no "list everything" fronts). You step through each draft and Accept, Edit, or Skip before anything touches your deck.

### Bulk-edit an entire deck with a single instruction

Select a deck and type a plain-English instruction: *"make the backs more concise"*, *"add a mnemonic to each card"*, *"rewrite everything in simple English"*. The AI proposes edits for every card. You review each one — nothing is written until you say so.

### Edit the card you're currently reviewing

While you're doing a review session in Anki, the tool shows you the current card's content as editable text. Fix a typo, reword a clunky front, or hit "Suggest improvement" to ask the AI for a rewrite based on how the card has been performing. Changes are saved immediately back to Anki.

---

## Setup (one time)

**1. Install Anki and AnkiConnect**

Install [Anki](https://apps.ankiweb.net). Then inside Anki go to *Tools → Add-ons → Get Add-ons* and enter code `2055492159`. Restart Anki.

**2. Get an Anthropic API key**

Sign up at [console.anthropic.com](https://console.anthropic.com) and create an API key.

**3. Install this tool**

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/dylanbay11/anki-ai-util
cd anki-ai-util
cp .env.example .env
# open .env and paste in your ANTHROPIC_API_KEY
```

---

## Running it

1. Open Anki (leave it open in the background)
2. In this project's directory:

```bash
uv run uvicorn main:app --reload
```

3. Open `http://localhost:8000` in your browser

That's it. The tool checks that AnkiConnect is reachable on startup and shows a warning on the home page if it isn't.

---

## Typical workflows

**Creating cards after reading something:**
Home → Generate Cards → paste your text → choose a deck → Generate → step through the drafts → Accept the ones you want.

**Cleaning up a deck:**
Home → Bulk AI Edit → pick a deck → type your instruction → Run → step through proposed edits → Accept what looks good.

**During a review session:**
Keep the browser open to `http://localhost:8000` alongside Anki. The current card appears automatically and updates as you move through your reviews. Edit inline and Save, or click Suggest to get an AI rewrite.
