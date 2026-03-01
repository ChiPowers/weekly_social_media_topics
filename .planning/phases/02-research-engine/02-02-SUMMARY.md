---
phase: 02-research-engine
plan: 02
subsystem: api
tags: [tavily, pydantic, research-engine, web-search, creator-discovery]

# Dependency graph
requires:
  - phase: 02-01
    provides: "Pydantic v2 models (CreatorProfile, NicheFindings, ResearchFindings), Config.tavily_api_key, BudgetTracker"
  - phase: 01-foundation
    provides: "BudgetTracker, Config dataclass, run_pipeline, run.py dry-run harness"
provides:
  - "ResearchEngine class with two-pass autonomous niche and creator discovery"
  - "NICHE_DISCOVERY_QUERIES covering all 5 platforms (TikTok, YouTube, Instagram, Facebook, X/Twitter)"
  - "CREATOR_QUERY_TEMPLATES for per-niche creator discovery"
  - "Budget-guarded _search() method (charges before every Tavily call)"
  - "_parse_follower_count() regex utility (K/M suffix parsing)"
  - "BRAND_DEAL_SIGNALS keyword list"
  - "Heuristic stub assembler — replaced by Plan 03 LLM extraction"
  - "pipeline.py live path integrated with ResearchEngine"
affects:
  - 02-03-PLAN
  - 03-idea-generation

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Budget-guard pattern: budget.charge(1) always called BEFORE API call in _search()"
    - "Dry-run pattern: run(dry_run=True) returns stub without API calls, zero budget charges"
    - "Heuristic stub pattern: Plan 02 builds structure, Plan 03 replaces stubs with LLM extraction"
    - "Deduplication pattern: normalized name key in seen_names dict across creator result passes"

key-files:
  created:
    - agent/research.py
  modified:
    - agent/pipeline.py

key-decisions:
  - "topic='news' for niche discovery queries (surfaces recently published articles), topic='general' for creator queries (profiles don't appear in news mode)"
  - "Budget target 15 Tavily searches + 10 Claude calls = 25 total per run — leaves 25 slack in default budget of 50"
  - "Cap at 5 niche topics (2 creator queries each = 10 searches max) to control budget per CONTEXT.md"
  - "BRAND_DEAL_SIGNALS keyword list for heuristic detection until Plan 03 LLM enhancement"
  - "Heuristic stubs in _assemble_stub_niches and _extract_creators_heuristic — deliberately minimal, Plan 03 replaces with LLM"

patterns-established:
  - "Budget-guard pattern: _search() calls self.budget.charge(1) before self.tavily.search()"
  - "Partial-result pattern: BudgetExceededError caught mid-loop, partial results returned with warning log"
  - "Query-tagging pattern: result['_query'] and result['_niche'] attached for debugging"

requirements-completed: [RSCH-01, RSCH-02, RSCH-03]

# Metrics
duration: 2min
completed: 2026-03-01
---

# Phase 2 Plan 02: Research Engine Summary

**ResearchEngine class with two-pass autonomous discovery — budget-guarded Tavily search, 5-platform niche queries, heuristic creator extraction with follower-count regex and brand-deal detection**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T04:20:49Z
- **Completed:** 2026-03-01T04:23:22Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created agent/research.py with ResearchEngine class implementing two-pass autonomous discovery strategy
- NICHE_DISCOVERY_QUERIES covers all five platforms (TikTok, YouTube, Instagram, Facebook, X/Twitter) satisfying RSCH-02
- Every Tavily call goes through _search() which calls budget.charge(1) before the API call — budget safety enforced at the point of call
- Creator deduplication by normalized name across search passes satisfying RSCH-03
- ResearchEngine.run(dry_run=True) returns stub ResearchFindings with zero API calls satisfying RSCH-01 dry-run path
- Heuristic niche and creator extraction stubs pipeline end-to-end until Plan 03 LLM extraction
- pipeline.py live path updated to instantiate ResearchEngine and call research_engine.run()

## Task Commits

Each task was committed atomically:

1. **Task 1: Query bank and budget-guarded search infrastructure** - `8342813` (feat)
2. **Task 2: Dry-run smoke test and pipeline integration stub** - `1540404` (feat)

**Plan metadata:** (docs commit — created after this summary)

## Files Created/Modified

- `agent/research.py` - ResearchEngine class, NICHE_DISCOVERY_QUERIES, CREATOR_QUERY_TEMPLATES, BRAND_DEAL_SIGNALS, _parse_follower_count() utility
- `agent/pipeline.py` - Live path replaced with ResearchEngine instantiation and run; imports added (TavilyClient, Anthropic, ResearchEngine)

## Decisions Made

- topic="news" for niche discovery queries (surfaces recently published articles); topic="general" for creator queries (profiles don't appear in news mode) — follows locked CONTEXT.md decisions
- Budget target 15 Tavily + 10 Claude = 25 total per run, leaving 25 slack in default budget of 50
- Cap at 5 niche topics for creator pass (2 templates each = 10 searches max) to control budget per CONTEXT.md
- Heuristic stubs in _assemble_stub_niches and _extract_creators_heuristic deliberately minimal — Plan 03 replaces with LLM extraction; stubs enable end-to-end pipeline verification now

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — dry-run path verified with mock env vars. Live Tavily calls require TAVILY_API_KEY in .env (pre-existing concern documented in STATE.md from Plan 02-01).

## Next Phase Readiness

- agent/research.py is ready for Plan 03 LLM extraction (_assemble_stub_niches and _extract_creators_heuristic are the replacement targets)
- pipeline.py live path calls research_engine.run(dry_run=False) — Plan 03 adds LLM synthesis after this call
- All RSCH-01, RSCH-02, RSCH-03 requirements satisfied
- Remaining concern: TAVILY_API_KEY must be in .env for live runs (Plans 02-02 and 02-03)

## Self-Check: PASSED

- agent/research.py: FOUND
- agent/pipeline.py: FOUND
- 02-02-SUMMARY.md: FOUND
- Commit 8342813 (Task 1): FOUND
- Commit 1540404 (Task 2): FOUND

---
*Phase: 02-research-engine*
*Completed: 2026-03-01*
