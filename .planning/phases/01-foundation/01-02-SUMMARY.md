---
phase: 01-foundation
plan: 02
subsystem: infra
tags: [python, argparse, budget, dry-run, cli, safety, exception-handling]

# Dependency graph
requires:
  - phase: 01-foundation/01-01
    provides: agent/config.py Config dataclass with from_env() validation and api_call_budget field
provides:
  - agent/budget.py with BudgetTracker class and BudgetExceededError exception
  - agent/pipeline.py pipeline orchestrator stub with dry-run awareness
  - run.py CLI entry point wiring config, budget, pipeline, and exception handling
affects: [02-data-collection, 03-analysis, 04-formatting, 05-delivery]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pre-call budget check: budget.charge(n) called BEFORE any API call — BudgetExceededError raised before counter increments"
    - "Dry-run mode: --dry-run flag passed through run.py -> pipeline, logs [DRY-RUN] messages and returns without real calls"
    - "Single exit point: only run.py calls sys.exit() — internal modules raise exceptions, never call sys.exit()"
    - "Logging configured once: logging.basicConfig() called once in run.py entry point only"

key-files:
  created:
    - agent/budget.py
    - agent/pipeline.py
    - run.py
  modified: []

key-decisions:
  - "BudgetTracker.charge() checks BEFORE incrementing — if self.used + n > self.limit: raise before self.used += n — guarantees exception fires before any API call"
  - "run.py is the only place sys.exit() is called — pipeline and budget modules raise exceptions only"
  - "BudgetExceededError caught at run.py level, prints BUDGET HALT to stderr, exits 1 — GitHub Actions reads exit code correctly"
  - "ValueError from Config.from_env() also caught at run.py level — config errors produce exit 1 with informative message"
  - "Pipeline live-mode stub calls budget.charge(1) even before Phase 2 adds real calls — exercises the budget system from day one"

patterns-established:
  - "Safety gate pattern: charge budget BEFORE making API call, never after"
  - "CLI entry point pattern: parse args -> load config -> create budget -> run pipeline -> catch exceptions -> exit with code"
  - "Exception propagation: internal modules raise, entry point catches and converts to exit codes"

requirements-completed: [SETUP-02, SETUP-03]

# Metrics
duration: 2min
completed: 2026-02-28
---

# Phase 1 Plan 02: Budget Enforcer and Dry-Run Harness Summary

**Pre-call API budget enforcement with BudgetTracker, dry-run pipeline stub, and complete CLI entry point wiring config + budget + exception exit codes**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-01T03:06:28Z
- **Completed:** 2026-03-01T03:07:28Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- BudgetTracker class with pre-call budget checking — BudgetExceededError raised before any increment or API call, guaranteeing safe halt
- Pipeline stub with dry-run mode that logs three [DRY-RUN] skip messages for research, LLM synthesis, and email delivery
- run.py CLI entry point with --dry-run flag, full exception wiring, and exit code 1 for both budget overrun and config errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Budget enforcement** - `61b0bac` (feat)
2. **Task 2: Pipeline stub and run.py entry point** - `a04a161` (feat)

**Plan metadata:** (docs: complete plan)

## Files Created/Modified
- `agent/budget.py` - BudgetTracker class with charge() pre-call check and BudgetExceededError exception
- `agent/pipeline.py` - Pipeline orchestrator stub with dry-run logging and live-mode budget charge
- `run.py` - CLI entry point: argparse --dry-run, Config.from_env(), BudgetTracker wiring, exception handling with sys.exit(1)

## Decisions Made
- BudgetTracker.charge() checks `self.used + n > self.limit` BEFORE incrementing `self.used` — this is the critical ordering that guarantees the exception fires before any API call is made
- Only run.py calls sys.exit() — internal modules raise exceptions, keeping them testable and reusable
- Pipeline live stub calls budget.charge(1) in the live path so budget system is exercised even before Phase 2 adds real API calls
- Both BudgetExceededError and ValueError exit with code 1 so GitHub Actions marks the job failed on any error condition

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - all files created cleanly, all verification tests passed on first run.

## User Setup Required
None - no external service configuration required at this stage. Developers set ANTHROPIC_API_KEY and EMAIL_RECIPIENT in .env to run locally.

## Next Phase Readiness
- `python run.py --dry-run` is a fully working, verifiable command — safe to use in local development and CI without real API calls
- Budget enforcement is active — any Phase 2+ code that calls budget.charge(n) before API calls is automatically protected from runaway spend
- Pipeline stub is ready for Phase 2+ to replace the stub body with real research/LLM/delivery steps
- Exception wiring is complete — Phase 2+ adds real API calls without touching run.py exception handling

## Self-Check: PASSED

All created files verified present:
- FOUND: agent/budget.py
- FOUND: agent/pipeline.py
- FOUND: run.py
- FOUND: .planning/phases/01-foundation/01-02-SUMMARY.md

All commits verified:
- FOUND: 61b0bac (Task 1 - budget enforcement)
- FOUND: a04a161 (Task 2 - pipeline stub and run.py)

---
*Phase: 01-foundation*
*Completed: 2026-02-28*
