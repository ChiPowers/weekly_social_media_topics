---
phase: 02-research-engine
plan: 01
subsystem: api
tags: [tavily, pydantic, python, web-search, research-engine]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Config dataclass and from_env() pattern that was extended with TAVILY_API_KEY

provides:
  - tavily-python==0.7.22 installed and importable as TavilyClient
  - pydantic==2.12.5 installed with v2 BaseModel
  - Config.from_env() now validates and populates tavily_api_key from TAVILY_API_KEY env var
  - agent/models.py with CreatorProfile, NicheFindings, ResearchFindings Pydantic v2 schemas
  - Phase 2/Phase 3 contract: ResearchFindings serialized to JSON with to_json_file() / from_json_file()

affects:
  - 02-research-engine (Plans 02-03 import NicheFindings, CreatorProfile, ResearchFindings)
  - 03-idea-generator (uses from_json_file() to load research output)

# Tech tracking
tech-stack:
  added:
    - tavily-python==0.7.22
    - pydantic==2.12.5
    - anthropic>=0.40.0
  patterns:
    - Pydantic v2 BaseModel with Optional fields for unreliable web-search data
    - model_dump_json() / model_validate_json() (v2 style, not .dict() / .parse_raw())
    - ResearchFindings.to_json_file() / from_json_file() as the inter-phase JSON contract

key-files:
  created:
    - agent/models.py
  modified:
    - requirements.txt
    - agent/config.py
    - .env.example

key-decisions:
  - "TAVILY_API_KEY added to required list in Config.from_env() — follows existing collect-all-missing-before-raising pattern"
  - "Optional fields in CreatorProfile and NicheFindings default to None (not empty string) — web search snippets may not surface all data"
  - "ResearchFindings serializes via model_dump_json() / model_validate_json() — avoids deprecated Pydantic v1 .dict() / .parse_raw()"
  - "anthropic>=0.40.0 pinned in requirements.txt now — prevents Phase 3 from revisiting dependency resolution"

patterns-established:
  - "Phase contract pattern: Output schema defined in agent/models.py before any implementation — types-first"
  - "Optional fields for web-scraped data: any field web search may not surface reliably is Optional[X] = None"
  - "Inter-phase serialization: to_json_file() / from_json_file() methods on ResearchFindings for pipeline handoff"

requirements-completed: [RSCH-01, RSCH-04]

# Metrics
duration: 2min
completed: 2026-03-01
---

# Phase 2 Plan 01: Research Engine Foundation Summary

**Tavily TavilyClient wired via Config.from_env() with TAVILY_API_KEY validation, and Pydantic v2 CreatorProfile/NicheFindings/ResearchFindings schema contract established for Phase 2-to-Phase 3 handoff**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T04:16:32Z
- **Completed:** 2026-03-01T04:18:01Z
- **Tasks:** 2
- **Files modified:** 4 (3 modified, 1 created)

## Accomplishments
- Installed tavily-python==0.7.22, pydantic==2.12.5, anthropic>=0.40.0 via requirements.txt
- Extended Config dataclass with tavily_api_key field and TAVILY_API_KEY in required env var list
- Created agent/models.py with three Pydantic v2 BaseModel classes: CreatorProfile, NicheFindings, ResearchFindings
- NicheFindings covers all four RSCH-04 dimensions: topic, content_style, posting_frequency, media_type
- ResearchFindings provides to_json_file() / from_json_file() for pipeline inter-phase JSON handoff
- Confirmed Phase 1 dry-run still passes with all env vars set (no regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Tavily and Pydantic, extend Config with TAVILY_API_KEY** - `63e50e4` (feat)
2. **Task 2: Define Pydantic v2 output schema in agent/models.py** - `aa2ab76` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `agent/models.py` - Pydantic v2 output schema: CreatorProfile, NicheFindings, ResearchFindings with JSON serialization methods
- `requirements.txt` - Added tavily-python==0.7.22, pydantic==2.12.5, anthropic>=0.40.0
- `agent/config.py` - Extended Config dataclass with tavily_api_key field; TAVILY_API_KEY added to required list
- `.env.example` - Added TAVILY_API_KEY=tvly-YOUR_API_KEY_HERE placeholder

## Decisions Made
- TAVILY_API_KEY added to required list in Config.from_env() — maintains existing collect-all-missing-before-raising pattern from Phase 1
- All Optional fields in CreatorProfile and NicheFindings default to None — web search snippets may not surface follower counts, posting frequency, etc.
- Uses model_dump_json() / model_validate_json() exclusively — avoids deprecated Pydantic v1 .dict() / .parse_raw() style
- anthropic>=0.40.0 pinned now to prevent Phase 3 from needing another dependency resolution pass

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all dependencies installed cleanly. pydantic-core 2.41.5 (Rust-backed) installed without issues on macOS arm64.

## User Setup Required

**External services require manual configuration.** Before Plans 02-03 can execute live Tavily searches:

1. Sign up at app.tavily.com (free, no credit card required)
2. Copy API key from dashboard
3. Add to `.env`: `TAVILY_API_KEY=tvly-<your-key>`

Verification: `python -c "from agent.config import Config; c = Config.from_env(); print('Tavily configured:', c.tavily_api_key[:8])"`

## Next Phase Readiness
- Plan 02-02 (research.py) can now import `from agent.models import NicheFindings, CreatorProfile, ResearchFindings` — types are defined
- Plan 02-02 can instantiate `TavilyClient(api_key=config.tavily_api_key)` — config wiring is complete
- TAVILY_API_KEY must be present in .env for live search calls in Plan 02-02 onwards

## Self-Check: PASSED

- FOUND: agent/models.py
- FOUND: requirements.txt
- FOUND: agent/config.py
- FOUND: .env.example
- FOUND: 02-01-SUMMARY.md
- FOUND: commit 63e50e4 (Task 1 - feat)
- FOUND: commit aa2ab76 (Task 2 - feat)
- All verification commands passed: tavily ok, pydantic 2.12.5, config ok, models ok
- Dry-run passes with all env vars set (Phase 1 not broken)

---
*Phase: 02-research-engine*
*Completed: 2026-03-01*
