"""
Seed test decks directly into Anki via AnkiConnect.

Usage
-----
    uv run python scripts/seed_test_decks.py           # seed (skips duplicates)
    uv run python scripts/seed_test_decks.py --reset   # wipe TestDecks::* then reseed

The --reset flag deletes every deck whose name starts with "TestDecks"
(including the parent and all subdecks) and then re-creates them from
scratch. Use this after experimenting with edits to restore a clean state.
Without --reset, re-running is safe: allowDuplicate:false means existing
cards are skipped and nothing is overwritten.

Decks created
-------------
TestDecks::Biology             Basic science Q&A — clean well-formed cards
TestDecks::History             Mix of good and intentionally vague cards
TestDecks::Programming::Python Cloze cards covering Python syntax
TestDecks::Programming::General Cards with code / list formatting
TestDecks::Languages::Spanish  Vocab using Basic (and reversed card)
TestDecks::AI Editing Targets  Deliberately poor cards for testing AI features

Coverage rationale
------------------
- Basic note type (Front / Back)
- Cloze note type (Text / Extra) with {{c1:: }} syntax
- Basic (and reversed card) — one note generates two cards
- Subdecks via :: notation
- HTML formatting in fields: <b>, <i>, <code>, <ul>/<li>
- Cards good enough to use as baselines
- Cards bad enough to need AI help (too broad, "list all", over-stuffed backs)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx

ANKI_URL = "http://localhost:8765"


async def invoke(action: str, **params):
    payload = {"action": action, "version": 6, "params": params}
    async with httpx.AsyncClient() as client:
        r = await client.post(ANKI_URL, json=payload, timeout=10)
        r.raise_for_status()
    data = r.json()
    if data.get("error"):
        raise RuntimeError(f"AnkiConnect: {data['error']}")
    return data["result"]


async def create_deck(name: str):
    await invoke("createDeck", deck=name)


async def add(deck: str, model: str, fields: dict, tags: list[str] | None = None) -> int | None:
    try:
        return await invoke(
            "addNote",
            note={
                "deckName": deck,
                "modelName": model,
                "fields": fields,
                "tags": tags or [],
                "options": {"allowDuplicate": False},
            },
        )
    except RuntimeError as e:
        if "duplicate" in str(e).lower():
            return None  # already exists, safe to skip
        raise


async def reset_test_decks():
    """
    Delete every deck whose name starts with 'TestDecks', including the
    parent deck and all subdecks. cardsToo=True removes all notes as well.
    """
    all_decks: list[str] = await invoke("deckNames")
    to_delete = [d for d in all_decks if d == "TestDecks" or d.startswith("TestDecks::")]
    if not to_delete:
        print("  No TestDecks found — nothing to delete.")
        return
    # Delete deepest paths first so parent decks are empty before removal
    to_delete.sort(key=lambda d: d.count("::"), reverse=True)
    await invoke("deleteDecks", decks=to_delete, cardsToo=True)
    print(f"  Deleted: {', '.join(to_delete)}")


# ---------------------------------------------------------------------------
# Deck definitions
# ---------------------------------------------------------------------------

BIOLOGY = "TestDecks::Biology"
HISTORY = "TestDecks::History"
PY = "TestDecks::Programming::Python"
CS = "TestDecks::Programming::General"
ES = "TestDecks::Languages::Spanish"
AI_TARGETS = "TestDecks::AI Editing Targets"

ALL_DECKS = [BIOLOGY, HISTORY, PY, CS, ES, AI_TARGETS]


async def seed_biology():
    """Clean, well-formed Basic cards. Happy path for the edit panel."""
    cards = [
        ("What is the powerhouse of the cell?", "The mitochondrion."),
        ("What is the process by which plants convert sunlight into sugar?", "Photosynthesis."),
        ("What molecule carries genetic information in most organisms?", "DNA (deoxyribonucleic acid)."),
        ("What is osmosis?", "The diffusion of water across a semi-permeable membrane from a region of lower solute concentration to higher solute concentration."),
        ("What is the function of ribosomes?", "Ribosomes synthesise proteins by translating messenger RNA."),
        ("What is natural selection?", "The process by which individuals with traits better suited to their environment tend to survive and reproduce more successfully."),
        ("What is the difference between mitosis and meiosis?",
         "<b>Mitosis:</b> produces 2 identical diploid daughter cells (growth, repair).<br>"
         "<b>Meiosis:</b> produces 4 genetically distinct haploid cells (sexual reproduction)."),
        ("What are the four bases in DNA?",
         "<ul><li>Adenine (A)</li><li>Thymine (T)</li><li>Cytosine (C)</li><li>Guanine (G)</li></ul>"),
        ("What is a catalyst?", "A substance that increases the rate of a chemical reaction without being consumed in the process. Biological catalysts are called enzymes."),
        ("What is the pH of a neutral solution at 25°C?", "7"),
    ]
    for front, back in cards:
        await add(BIOLOGY, "Basic", {"Front": front, "Back": back}, tags=["test", "biology"])

    # Cloze cards — one note can produce multiple cards (one per cN marker)
    cloze_cards = [
        (
            "During {{c1::cellular respiration}}, glucose is broken down to release energy "
            "in the form of {{c2::ATP}}.",
            "Occurs in the mitochondria. Opposite process to photosynthesis.",
        ),
        (
            "The {{c1::double helix}} structure of DNA was described by Watson and Crick in {{c2::1953}}, "
            "based partly on X-ray diffraction images by {{c3::Rosalind Franklin}}.",
            "One of the most important discoveries in biology.",
        ),
    ]
    for text, extra in cloze_cards:
        await add(BIOLOGY, "Cloze", {"Text": text, "Extra": extra}, tags=["test", "biology"])
    print(f"  {BIOLOGY}: {len(cards)} basic + {len(cloze_cards)} cloze notes")


async def seed_history():
    """Mix of decent cards and intentionally vague ones for AI editing tests."""
    cards = [
        # Good cards
        ("In what year did World War II end?", "1945."),
        ("Who wrote the Communist Manifesto?", "Karl Marx and Friedrich Engels, published in 1848."),
        ("What was the main cause of the First World War?",
         "A combination of factors: the assassination of Archduke Franz Ferdinand, entangled alliances, imperial rivalry, and an arms race."),
        ("What does <i>Magna Carta</i> mean, and when was it signed?",
         "<i>Magna Carta</i> means 'Great Charter'. It was signed in 1215 by King John of England, limiting royal power."),
        # Intentionally vague / too broad — good targets for AI editing
        ("Tell me about the French Revolution.",
         "The French Revolution was a very important event in history. Lots of things happened. The king was executed. There was a Reign of Terror. Napoleon came after. It changed France and Europe in many ways and had many causes and effects that are important to know about."),
        ("What are all the things you need to know about the Roman Empire?",
         "The Roman Empire started and then expanded and then fell. It had emperors and a senate and legions. Julius Caesar was famous. So was Augustus. And Nero. And Constantine. There were roads and aqueducts and laws. It's a big topic."),
        ("List everything about the Industrial Revolution.",
         "Steam power, factories, urbanisation, child labour, cotton mills, James Watt, spinning jenny, railways, coal, iron."),
        ("What happened in 1066?",
         "The Norman Conquest. William the Conqueror defeated King Harold at the Battle of Hastings and became King of England."),
    ]
    for front, back in cards:
        await add(HISTORY, "Basic", {"Front": front, "Back": back}, tags=["test", "history"])
    print(f"  {HISTORY}: {len(cards)} cards ({len(cards)-4} intentionally poor)")


async def seed_python():
    """
    Cloze cards for Python syntax.
    Cloze note type uses field 'Text' (with {{c1::}} markers) and 'Extra'.
    One note can have multiple cloze deletions (c1, c2, ...) — each becomes
    a separate card. A single cloze note is still one *note* but many *cards*.
    """
    cards = [
        # (text_with_cloze, extra_hint)
        ("In Python, {{c1::list}} is a mutable ordered sequence; {{c2::tuple}} is immutable.",
         "Mutability is the key distinction."),
        ("To open a file safely in Python: {{c1::with open('file.txt') as f:}}",
         "The 'with' statement ensures the file is closed even if an exception occurs."),
        ("A Python {{c1::decorator}} is a function that wraps another function to extend its behaviour without modifying it.",
         "Example: @staticmethod, @property, @functools.lru_cache"),
        ("In a Python dict, {{c1::dict.get(key, default)}} returns the default value instead of raising KeyError if the key is missing.",
         "Contrast with dict[key] which raises KeyError."),
        ("{{c1::List comprehension}} syntax: <code>[expr for item in iterable if condition]</code>",
         "More readable and often faster than a for-loop with append."),
        ("Python's {{c1::GIL}} (Global Interpreter Lock) prevents true multi-threaded parallelism for {{c2::CPU-bound}} tasks.",
         "Use multiprocessing or async/await instead for parallelism."),
        ("The {{c1::__init__}} method in a Python class is called when a new instance is {{c2::created}}.",
         "It initialises instance attributes. Not the same as __new__."),
        ("{{c1::f-strings}} (formatted string literals) were introduced in Python {{c2::3.6}}.",
         "Syntax: f'Hello {name}'"),
    ]
    for text, extra in cards:
        await add(PY, "Cloze", {"Text": text, "Extra": extra}, tags=["test", "python"])
    print(f"  {PY}: {len(cards)} notes (each may produce multiple cards via multiple cloze markers)")


async def seed_cs():
    """General CS cards with code and list formatting in HTML."""
    cards = [
        ("What is Big-O notation?",
         "A way to describe the <b>upper bound</b> of an algorithm's time or space complexity as input size grows. "
         "Common complexities:<br><ul>"
         "<li><code>O(1)</code> — constant</li>"
         "<li><code>O(log n)</code> — logarithmic</li>"
         "<li><code>O(n)</code> — linear</li>"
         "<li><code>O(n²)</code> — quadratic</li>"
         "</ul>"),
        ("What is the difference between a stack and a queue?",
         "<b>Stack:</b> LIFO — last in, first out. Push/pop from the same end.<br>"
         "<b>Queue:</b> FIFO — first in, first out. Enqueue at back, dequeue from front."),
        ("What does <code>git rebase</code> do?",
         "Moves or replays commits from one branch onto the tip of another, resulting in a linear history. "
         "Unlike merge, it rewrites commit history."),
        ("What is a REST API?",
         "An architectural style for HTTP APIs using standard verbs:<br>"
         "<ul><li><code>GET</code> — read</li><li><code>POST</code> — create</li>"
         "<li><code>PUT/PATCH</code> — update</li><li><code>DELETE</code> — delete</li></ul>"
         "Resources are identified by URLs; responses are stateless."),
        ("What is a foreign key in a relational database?",
         "A column (or set of columns) in one table that references the <b>primary key</b> of another table, "
         "enforcing referential integrity."),
        ("What does <code>async/await</code> solve in Python?",
         "Allows writing non-blocking I/O code in a readable synchronous style. "
         "The event loop suspends a coroutine at each <code>await</code> point and resumes it when the awaited result is ready, "
         "without blocking the thread."),
    ]
    for front, back in cards:
        await add(CS, "Basic", {"Front": front, "Back": back}, tags=["test", "cs"])
    print(f"  {CS}: {len(cards)} cards")


async def seed_spanish():
    """
    Vocabulary using 'Basic (and reversed card)'.
    Each note generates TWO cards: EN→ES and ES→EN.
    This tests that the tool handles notes where card count != 1.
    """
    cards = [
        ("to speak / hablar", "hablar / to speak"),
        ("the house / la casa", "la casa / the house"),
        ("I am hungry / Tengo hambre", "Tengo hambre / I am hungry"),
        ("yesterday / ayer", "ayer / yesterday"),
        ("the library / la biblioteca", "la biblioteca / the library"),
        ("How much does it cost? / ¿Cuánto cuesta?", "¿Cuánto cuesta? / How much does it cost?"),
        ("red / rojo (m), roja (f)", "rojo/roja / red"),
        ("to remember / recordar", "recordar / to remember"),
    ]
    for front, back in cards:
        await add(ES, "Basic (and reversed card)", {"Front": front, "Back": back},
                  tags=["test", "spanish", "vocabulary"])
    print(f"  {ES}: {len(cards)} notes → {len(cards)*2} cards (reversed type)")


async def seed_ai_targets():
    """
    Cards specifically designed to be improved by the AI features:
    - Too broad / 'list everything' fronts
    - Over-stuffed backs
    - Fronts that are questions with obvious answers
    - Cards where cloze would be more appropriate
    - Inconsistent style across the deck
    Use this deck for testing bulk edit and single-card suggest.
    """
    cards = [
        ("What is HTTP?",
         "HTTP stands for HyperText Transfer Protocol. It is used for the internet. There are status codes like 200 and 404. "
         "It has methods. GET is for getting things. POST is for posting things. It was invented by Tim Berners-Lee. "
         "HTTPS is the secure version. It uses TCP. Ports 80 and 443 are common. It is stateless."),
        ("Tell me everything about neurons.",
         "Neurons are brain cells. They have dendrites and axons and a cell body. They communicate via synapses. "
         "There are different types. They use electrical signals. Neurotransmitters are involved. Myelin helps speed."),
        ("What are variables?",
         "In programming, variables are used to store values. You can assign values to them and use them later."),
        ("Explain machine learning.",
         "Machine learning is a type of AI where computers learn from data. There are different types like supervised, "
         "unsupervised, and reinforcement learning. It uses algorithms and models and training data. Neural networks are "
         "a kind of machine learning. Deep learning is a subset. It is used in many applications."),
        ("What is the heart?",
         "The heart pumps blood. It has four chambers: left/right atrium, left/right ventricle. "
         "It beats about 60-100 times per minute. It sends blood to the lungs to get oxygen and then to the body."),
        ("list the planets",
         "mercury venus earth mars jupiter saturn uranus neptune"),
        ("What is JSON and what do you use it for and how does it work and what are some examples?",
         'JSON is JavaScript Object Notation. Example: {"key": "value"}. It is used for APIs and config files. '
         "It supports strings, numbers, booleans, null, objects, and arrays. It is human-readable."),
        ("What does the term 'refactoring' mean?",
         "Refactoring means changing code."),
    ]
    for front, back in cards:
        await add(AI_TARGETS, "Basic", {"Front": front, "Back": back},
                  tags=["test", "ai-target", "needs-improvement"])
    print(f"  {AI_TARGETS}: {len(cards)} cards (all intentionally imperfect)")


# ---------------------------------------------------------------------------

async def main():
    do_reset = "--reset" in sys.argv

    print("Checking AnkiConnect...")
    version = await invoke("version")
    print(f"  AnkiConnect version {version} — connected.\n")

    if do_reset:
        print("Resetting: deleting all TestDecks::* ...")
        await reset_test_decks()
        print()

    print("Creating decks...")
    for deck in ALL_DECKS:
        await create_deck(deck)
        print(f"  {deck}")

    print("\nSeeding cards...")
    await seed_biology()
    await seed_history()
    await seed_python()
    await seed_cs()
    await seed_spanish()
    await seed_ai_targets()

    print("\nDone. Open Anki's card browser to verify.")
    print("\nDecks by use case:")
    print(f"  Happy-path editing / suggest:  {BIOLOGY}, {CS}")
    print(f"  HTML formatting in fields:     {CS}")
    print(f"  Cloze syntax:                  {PY}")
    print(f"  note-per-card != 1 (reversed): {ES}")
    print(f"  Subdecks:                      TestDecks::Programming::*, TestDecks::Languages::*")
    print(f"  Bulk edit / AI suggest target: {AI_TARGETS}, {HISTORY} (last 4 cards)")


if __name__ == "__main__":
    asyncio.run(main())
