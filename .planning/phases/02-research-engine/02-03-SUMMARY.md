---
phase: 02-research-engine
plan: 03
subsystem: api
tags: [anthropic, claude-haiku, pydantic, llm-extraction, research-engine, json-output]

# Dependency graph
requires:
  - phase: 02-02
    provides: "ResearchEngine class, _search(), _run_niche_discovery(), _run_creator_discovery(), _extract_creators_heuristic(), pipeline.py live path"
  - phase: 02-01
    provides: "Pydantic v2 models (CreatorProfile, NicheFindings, ResearchFindings with to_json_file/from_json_file)"
provides:
  - "_extract_with_llm(): budget-guarded LLM call using claude-haiku-4-5, handles JSON parse failure, returns None on error"
  - "_build_snippets_text(): aggregates Tavily snippets, filters stale (>14 days), caps at 15"
  - "_assemble_niches(): LLM extraction per niche with ValidationError fallback to heuristic"
  - "pipeline.py writes research_output.json after live research run"
  - "research_output.json gitignored"
  - "Live run verified: research_output.json produced with valid NicheFindings and named creators"
affects:
  - 03-idea-generation

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LLM extraction pattern: budget.charge(1) BEFORE messages.create(), return None on any failure"
    - "Code-fence stripping: strip markdown backtick blocks from LLM output before JSON parse"
    - "Stale-result filter: filter snippets with published_date older than 14 days (news topic only)"
    - "LLM-per-niche batch pattern: one LLM call per niche topic aggregating all related snippets"
    - "ValidationError fallback: catch pydantic.ValidationError on model_validate(), log warning, use heuristic"

key-files:
  created: []
  modified:
    - agent/research.py
    - agent/pipeline.py
    - .gitignore

key-decisions:
  - "One LLM call per niche (not per search result) — batch efficiency within budget target of 10 Claude calls"
  - "budget.charge(1) called BEFORE messages.create() — matches existing _search() pattern, prevents call on exceeded budget"
  - "ValidationError caught in _assemble_niches() — falls back to heuristic extractors, never crashes pipeline"
  - "research_output.json gitignored — contains live trend data, changes every run, not for version control"

patterns-established:
  - "LLM extraction pattern: charge budget before API call, catch all exceptions, return None, log warning"
  - "Graceful degradation: heuristic fallback when LLM fails — pipeline always completes"

requirements-completed: [RSCH-03, RSCH-04]

# Metrics
duration: 3min
completed: 2026-02-28
---

# Phase 2 Plan 03: LLM Extraction Summary

**LLM-powered structured NicheFindings extraction via claude-haiku-4-5 replacing stub assembler, with ValidationError fallback and research_output.json file output — live run verified by human approval**

## Performance

- **Duration:** ~3 min (Tasks 1-2 automated) + human verification (Task 3)
- **Started:** 2026-03-01T04:26:04Z
- **Completed:** 2026-02-28 (Tasks 1-2); human verification approved 2026-02-28
- **Tasks completed:** 3 of 3
- **Files modified:** 3

## Accomplishments

- Replaced `_assemble_stub_niches()` with `_assemble_niches()` — LLM extraction per niche with heuristic fallback
- Added `_extract_with_llm()`: charges `budget.charge(1)` before LLM call, uses `claude-haiku-4-5`, handles all JSON parse failures, returns `None` on failure (never raises)
- Added `_build_snippets_text()`: aggregates snippets from multiple Tavily result batches, filters results older than 14 days, caps at 15 snippets per LLM call
- ValidationError from `NicheFindings.model_validate()` caught and logged — pipeline always continues
- `pipeline.py` writes `findings.to_json_file("research_output.json")` after live research run
- `research_output.json` added to `.gitignore`
- All 4 automated verification checks pass; `python run.py --dry-run` exits 0 unchanged
- Live run with real API keys verified by human — `research_output.json` produced with valid NicheFindings and named creators (RSCH-03, RSCH-04 satisfied)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add LLM extraction to ResearchEngine — replace stub assembler** - `4e27a8a` (feat)
2. **Task 2: Write research_output.json and end-to-end dry-run verification** - `17e48e6` (feat)
3. **Task 3: Human verification of live research output** - approved by human (checkpoint:human-verify)

## Files Created/Modified

- `agent/research.py` - Added `_extract_with_llm()`, `_build_snippets_text()`, `_assemble_niches()`; removed `_assemble_stub_niches()`; updated `run()` to call `_assemble_niches()`; added `json` import and `from pydantic import ValidationError`
- `agent/pipeline.py` - Added `findings.to_json_file("research_output.json")` call with logger after live research run
- `.gitignore` - Added `research_output.json`

## Decisions Made

- One LLM call per niche (batch efficiency) — avoids per-result calls, keeps budget within 10 Claude call target
- `budget.charge(1)` before `messages.create()` — consistent with existing `_search()` pattern, prevents call on exceeded budget
- `ValidationError` caught in `_assemble_niches()` — falls back to heuristic extractors so pipeline always completes
- `research_output.json` gitignored — live trend data changes every run, not appropriate for version control

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Live verification (Task 3) required:
- `TAVILY_API_KEY` in `.env` (from app.tavily.com)
- `ANTHROPIC_API_KEY` in `.env` (real Anthropic key)
- `EMAIL_RECIPIENT` in `.env` (any valid email address)

Human verified: `research_output.json` produced valid NicheFindings with named creators. Approved.

## Next Phase Readiness

- `agent/research.py` with LLM extraction is complete and live-verified
- `pipeline.py` output wiring is complete — `research_output.json` written after live run
- Phase 3 (idea generation) can consume `research_output.json` via `ResearchFindings.from_json_file()`
- All Phase 2 requirements satisfied: RSCH-01, RSCH-02, RSCH-03, RSCH-04

## Self-Check: PASSED

- agent/research.py: FOUND
- agent/pipeline.py: FOUND
- .gitignore: FOUND
- 02-03-SUMMARY.md: FOUND
- Commit 4e27a8a (Task 1): FOUND
- Commit 17e48e6 (Task 2): FOUND
- Task 3: Human-approved (checkpoint:human-verify)

---
*Phase: 02-research-engine*
*Completed: 2026-02-28*
