# Single-card AI suggest — implementation progress

## Steps

- [x] Add `instructor` dependency
- [x] `lib/models.py` — JudgeResult, CardProposal
- [x] `lib/prompts.py` — prompt file loader
- [x] `lib/validate.py` — domain validation (cloze, media, has_changes)
- [x] Refactor `lib/llm.py` — instructor + call_structured + JSONL logging
- [x] `prompts/judge_v1.md` + `prompts/suggest_v1.md`
- [x] `logs/.gitkeep` + `.gitignore` update
- [x] `.env.example` update (LLM_PROVIDER, LLM_MODEL)
- [x] Update `routers/current_card.py` — two-stage pipeline
- [x] Update `templates/partials/proposal.html` — rationale, editable textareas, warnings
- [x] New `templates/partials/no_changes.html`
- [x] Update `AGENT_BRIEF.md`
- [x] Smoke test — all checks passed

## Done. Ready for end-to-end test with live Anki.

## Key decisions recorded

- Flat JSON: `{"rationale": "...", "Front": "...", "Back": "..."}` — wait, actually nested:
  `{"rationale": "...", "fields": {"Front": "...", "Back": "..."}}` via CardProposal.fields
- "No changes" detected server-side by field equality; judge returns needs_changes=false first
- Verbatim cloze: full `{{c1::text}}` token must appear unchanged in proposed output
- Prompt files in `prompts/`, policy in `policies/` — concatenated at call time (no template vars)
- JSONL log at `logs/llm_requests.jsonl`
- Multi-provider: LLM_PROVIDER env var (anthropic|openai), default anthropic
