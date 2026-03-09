## Your task

Improve the Anki card below. A prior evaluation has already determined that it needs changes.

You are editing a **single existing note in place**. You must return exactly the same set of
fields that were given to you — no more, no fewer.

Hard rules — violations will cause the output to be rejected:
- Cloze tokens (e.g. `{{c1::mitochondria}}`) must appear verbatim and unchanged in your output.
  Do not add, remove, reorder, or alter the text inside any cloze token.
- Media tokens (`[img:filename]`, `[sound:filename]`) must appear verbatim and unchanged.
- Do not suggest splitting this card into multiple cards. You cannot create new notes here —
  propose the best in-place improvement possible within the existing fields.
- Do not suggest merging this card with another card.

Style guidance:
- Write field values as plain Markdown.
- Use **bold** sparingly — only for the single most important term or phrase per field side,
  if at all.
- Keep each field concise. If the card covers too many ideas, focus on the most important one
  and trim the rest — do not instruct the user to split manually.

Output guidance:
- `rationale`: one concise sentence describing the main improvement made. Do not narrate every
  small change; focus on the primary reason.
