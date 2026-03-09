## Your task

You are evaluating a single Anki card to decide whether it would benefit from improvement.

Evaluate the card against the card quality principles above. Consider the field content and
the review history (if provided) — repeated "Again" or "Hard" responses may indicate a card
that is confusing, overloaded, or poorly worded.

Return `needs_changes: true` only when there is a clear, specific improvement that would
meaningfully help the learner — not minor stylistic preferences or trivial rephrasing.
Return `false` if the card is already well-formed and serves its purpose effectively.

Be conservative: a good card that could be slightly different is not a card that needs changes.
