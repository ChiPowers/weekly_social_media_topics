---
phase: 03-llm-orchestrator
plan: "01"
subsystem: api
tags: [pydantic, anthropic, claude-haiku, llm-synthesis, content-ideas]

# Dependency graph
requires:
  - phase: 02-research-engine
    provides: ResearchFindings, NicheFindings, CreatorProfile models and research_output.json output
provides:
  - ContentIdea Pydantic v2 model with topic, angle, talking_points, rationale (required), platform, content_format (optional)
  - IdeaReport Pydantic v2 model with run_date, ideas, niches_processed, ideas_generated, budget_used
  - IdeaReport.to_json_file / from_json_file for ideas_output.json serialization
  - IdeaSynthesizer class with run(), _filter_valid_niches(), _synthesize(), dry-run stub
affects: [03-02-pipeline-wiring, 04-email-delivery]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Single-pass LLM synthesis: all valid niches serialized into one prompt, one Claude Haiku call
    - Article-title heuristic: creator names checked for separators (: | – -), title-start prefixes, and unknown platform+no-follower signals
    - Retry-once pattern: ValidationError on IdeaReport triggers second LLM call with error details appended
    - Empty-report fallback: JSONDecodeError or second ValidationError returns IdeaReport(ideas=[]) without crashing
    - Creator deduplication: rationale string parsed for name before first parenthetical, case-insensitive set tracks seen creators

key-files:
  created:
    - agent/synthesizer.py
  modified:
    - agent/models.py

key-decisions:
  - "Single-pass synthesis: all valid niches in one prompt, one LLM call — matches RESEARCH.md discretion choice, avoids per-niche call cost"
  - "Article-title heuristic uses prefix list + separator presence + unknown-platform-no-follower as compound check — no regex, fast and readable"
  - "Retry once on ValidationError with error details — RESEARCH.md discretion, keeps budget cost to max 2 calls"
  - "BudgetExceededError propagates from IdeaSynthesizer to pipeline — never caught inside synthesizer"
  - "Creator deduplication parses name before first '(' in rationale string — matches expected rationale format from prompt"

patterns-established:
  - "_call_llm() extracted as shared helper: budget.charge(1) -> messages.create() -> strip fences -> json.loads() — mirrors research.py _extract_with_llm pattern"
  - "Dry-run stub returns IdeaReport(ideas=[], niches_processed=len(findings.niches), ideas_generated=0, budget_used=0)"
  - "IdeaReport.to_json_file/from_json_file follow ResearchFindings pattern: model_dump_json(indent=2) / model_validate_json()"

requirements-completed: [IDEA-01, IDEA-02]

# Metrics
duration: 2min
completed: 2026-03-02
---

# Phase 3 Plan 01: LLM Synthesizer Schema and Core Logic Summary

**ContentIdea/IdeaReport Pydantic v2 schemas plus IdeaSynthesizer with single-pass Claude Haiku synthesis, creator-title filtering, ValidationError retry, and creator deduplication**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-02T14:58:27Z
- **Completed:** 2026-03-02T15:00:53Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- ContentIdea model establishes the idea contract: required topic, angle, talking_points, rationale; optional platform and content_format
- IdeaReport model is the Phase 3 output container with to_json_file/from_json_file for Phase 4 email delivery
- IdeaSynthesizer filters niches missing real named creators, calls Claude Haiku once for all valid niches, retries once on ValidationError
- dry_run=True returns stub without any API calls; empty/invalid research raises ValueError cleanly

## Task Commits

Each task was committed atomically:

1. **Task 1: Add ContentIdea and IdeaReport to agent/models.py** - `f442561` (feat)
2. **Task 2: Implement IdeaSynthesizer in agent/synthesizer.py** - `ba7b1b7` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `agent/models.py` - Appended ContentIdea and IdeaReport Pydantic v2 models; added `from datetime import date` import
- `agent/synthesizer.py` - New file: IdeaSynthesizer class with run(), _filter_valid_niches(), _synthesize(), _call_llm(), _deduplicate_creators()

## Decisions Made
- Single-pass synthesis (all niches in one prompt) chosen over per-niche calls — reduces LLM budget from N calls to 1 call per run
- Article-title heuristic uses compound check: prefix list (How/The/Why/Top/Best/What), separator chars (:, |, –, " - "), "Unknown" name, unknown platform + no follower count
- Retry-once on ValidationError with error details — keeps max LLM spend at 2 calls, matches RESEARCH.md guidance on retry discretion
- BudgetExceededError intentionally NOT caught in synthesizer — propagates to pipeline for clean halt
- Creator deduplication scans name before first "(" in rationale — aligns with enforced rationale format from synthesis prompt

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- IdeaSynthesizer and IdeaReport models ready for pipeline wiring in Plan 03-02
- Plan 03-02 will call IdeaSynthesizer.run(findings) and write ideas_output.json using IdeaReport.to_json_file()
- No blockers: all imports resolve, dry-run pipeline still passes, BudgetTracker integration confirmed

---
*Phase: 03-llm-orchestrator*
*Completed: 2026-03-02*
