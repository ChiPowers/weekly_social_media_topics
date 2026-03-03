# Phase 1: Foundation - Research

**Researched:** 2026-02-28
**Domain:** Python project scaffold, env loading, CLI flags, API budget enforcement, GitHub Actions
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Production runs on **GitHub Actions** (cloud-scheduled weekly, no local machine required)
- Project structure must be GitHub Actions-compatible from the start (workflow YAML, secrets via repo settings)
- Local testing via `python run.py --dry-run`
- `--dry-run` flag must complete the full pipeline without making real API calls or sending email
- Single command, no install step required — just clone and run
- `requirements.txt + pip` — standard, simple, works everywhere including GitHub Actions
- No uv, poetry, or other tooling required

### Claude's Discretion

- Exact project directory structure (module layout, file naming)
- Config file format for non-secret settings (if any)
- How mock/stub data is structured in dry-run mode
- Budget enforcement implementation (counter, decorator, or middleware)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SETUP-01 | User can configure all API keys via a `.env` file without modifying source code | python-dotenv 1.2.1 `load_dotenv()` handles this; `override=False` ensures GitHub Actions secrets take precedence in production |
| SETUP-02 | User can run the pipeline in dry-run mode to test without making real API calls or sending email | argparse `--dry-run` with `action='store_true'`; pass `dry_run` bool through to all I/O callsites |
| SETUP-03 | Agent enforces a hard per-run API call budget and halts cleanly if the limit would be exceeded | Custom `BudgetTracker` class with a counter; raise custom `BudgetExceededError` (inherits `Exception`) caught at `run.py` top level; print informative message + `sys.exit(1)` |
</phase_requirements>

---

## Summary

This phase establishes the developer-facing skeleton of the agent: file layout, config loading from `.env`, a `--dry-run` mode, and a hard API call budget that halts cleanly before any over-budget call is made. No real data-fetching or email logic is implemented here — only the harness those systems will plug into in later phases.

The core stack is deliberately minimal: Python stdlib (`argparse`, `os`, `sys`) plus one third-party dependency (`python-dotenv 1.2.1`). This keeps the install surface tiny, makes GitHub Actions integration straightforward, and ensures there's nothing exotic to explain when a developer clones and runs for the first time.

A key architectural decision is that `load_dotenv(override=False)` (the default) gives GitHub Actions secrets precedence over `.env` values automatically — the same `config.py` module works in both local and production contexts without branching.

**Primary recommendation:** Build a flat project layout with `run.py` at root, a `agent/` package for all logic, `config.py` for config loading + validation, and a `budget.py` module for the call counter. Wire the `--dry-run` flag through as a single boolean that every downstream callsite checks before making real I/O.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-dotenv | 1.2.1 | Load `.env` key-value pairs into `os.environ` at startup | De facto standard for 12-factor config in Python scripts; handles variable expansion, does not override existing env vars by default (production-safe) |
| argparse | stdlib | Parse `--dry-run` and any future CLI flags | Built-in, zero install cost, stable API, produces `--help` for free |
| sys | stdlib | `sys.exit(1)` for clean halt with non-zero exit code | Correct way to signal error exit to shell and GitHub Actions |
| os | stdlib | `os.environ.get()` / `os.environ[key]` to read credentials | Standard env access; raises `KeyError` on missing required vars |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging | stdlib | Structured log output during dry-run and production runs | Use from the start; dry-run logs replace real side-effects |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-dotenv | pydantic-settings | pydantic-settings is excellent but adds Pydantic dependency — overkill for Phase 1; appropriate if SYNTH-02 (structured output) adopts Pydantic in a later phase |
| requirements.txt + pip | uv | uv is faster but user explicitly decided against non-standard tooling |
| argparse | click / typer | click/typer are more ergonomic but add a dependency; argparse is sufficient for a single `--dry-run` flag |

**Installation:**
```bash
pip install python-dotenv
# or
pip install -r requirements.txt
```

`requirements.txt` contents for Phase 1:
```
python-dotenv==1.2.1
```

---

## Architecture Patterns

### Recommended Project Structure

```
/                          # repo root
├── run.py                 # entry point: parse args, call agent.main()
├── requirements.txt       # pip dependencies
├── .env                   # local secrets (gitignored)
├── .env.example           # template showing required variable names
├── .gitignore             # must include .env
├── .github/
│   └── workflows/
│       └── agent.yml      # GitHub Actions schedule workflow
└── agent/
    ├── __init__.py
    ├── config.py          # load_dotenv + validation + settings dataclass
    ├── budget.py          # BudgetTracker class
    └── pipeline.py        # stub: orchestrates research → ideas → delivery
```

Rationale: flat layout (no `src/`) is appropriate for a single-package agent script. `run.py` at root keeps the invocation `python run.py --dry-run` exactly as the user expects. The `agent/` package isolates all logic so future phases add modules without touching `run.py`.

### Pattern 1: Config Loading with Validation

**What:** `load_dotenv()` at module import time in `config.py`; each required variable is read with `os.environ[key]` (raises `KeyError` on missing) and wrapped in a dataclass. Optional variables use `os.environ.get(key, default)`.

**When to use:** At application startup, before any other module imports that need credentials.

**Example:**
```python
# agent/config.py
# Source: python-dotenv 1.2.1 README (https://github.com/theskumar/python-dotenv/blob/main/README.md)
#         Python docs os.environ (https://docs.python.org/3/library/os.html#os.environ)

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # override=False by default — GitHub Actions secrets take precedence

@dataclass
class Config:
    anthropic_api_key: str
    email_recipient: str
    api_call_budget: int

    @classmethod
    def from_env(cls) -> "Config":
        missing = []
        required = ["ANTHROPIC_API_KEY", "EMAIL_RECIPIENT"]
        for var in required:
            if not os.environ.get(var):
                missing.append(var)
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Copy .env.example to .env and fill in the values."
            )
        return cls(
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            email_recipient=os.environ["EMAIL_RECIPIENT"],
            api_call_budget=int(os.environ.get("API_CALL_BUDGET", "50")),
        )
```

**Key behavior:** `load_dotenv(override=False)` means if `ANTHROPIC_API_KEY` is already in the environment (i.e., GitHub Actions secrets injected it), the `.env` value is ignored — no code change needed between local and production.

### Pattern 2: CLI Entry Point with --dry-run

**What:** `run.py` parses args with argparse; `args.dry_run` (bool) is passed into the pipeline.

**When to use:** Any time the pipeline would make a real API call or send email.

**Example:**
```python
# run.py
# Source: Python docs argparse store_true (https://docs.python.org/3/library/argparse.html)

import sys
import argparse
from agent.config import Config
from agent.budget import BudgetTracker
from agent.pipeline import run_pipeline

def main():
    parser = argparse.ArgumentParser(description="Social Media Content Intelligence Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run the full pipeline without making real API calls or sending email",
    )
    args = parser.parse_args()

    config = Config.from_env()
    budget = BudgetTracker(limit=config.api_call_budget)

    try:
        run_pipeline(config=config, budget=budget, dry_run=args.dry_run)
    except ValueError as e:
        print(f"ERROR: Configuration problem — {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Pattern 3: Budget Enforcement Counter

**What:** A `BudgetTracker` class tracks calls made and raises a custom exception before any over-budget call.

**When to use:** Every callsite that would consume an API credit calls `budget.charge(n=1)` before making the call.

**Example:**
```python
# agent/budget.py

import sys

class BudgetExceededError(Exception):
    """Raised when an API call would exceed the configured per-run budget."""
    pass

class BudgetTracker:
    def __init__(self, limit: int):
        self.limit = limit
        self.used = 0

    def charge(self, n: int = 1) -> None:
        """
        Declare intent to make n API calls. Raises BudgetExceededError
        BEFORE the call is made if it would exceed the budget.
        """
        if self.used + n > self.limit:
            raise BudgetExceededError(
                f"API call budget exceeded: would use {self.used + n} calls "
                f"but limit is {self.limit}. Halting cleanly."
            )
        self.used += n

    @property
    def remaining(self) -> int:
        return self.limit - self.used
```

Usage in `run.py` top-level exception handler:
```python
    except BudgetExceededError as e:
        print(f"BUDGET HALT: {e}", file=sys.stderr)
        sys.exit(1)
```

**Critical:** The exception must be caught at the outermost call frame and converted to `sys.exit(1)`. GitHub Actions treats non-zero exit codes as workflow failures — this is the correct signal.

### Pattern 4: GitHub Actions Workflow YAML

**What:** `.github/workflows/agent.yml` defines the weekly schedule and injects secrets as environment variables.

**Example:**
```yaml
# .github/workflows/agent.yml
# Source: GitHub Actions docs (https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)

name: Content Intelligence Agent

on:
  schedule:
    - cron: '0 9 * * 1'   # Every Monday at 09:00 UTC
  workflow_dispatch:         # Allow manual trigger for testing

jobs:
  run-agent:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run agent
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          EMAIL_RECIPIENT: ${{ secrets.EMAIL_RECIPIENT }}
          API_CALL_BUDGET: ${{ vars.API_CALL_BUDGET }}
        run: python run.py
```

**Key:** Secrets injected via `env:` in the step are available as environment variables. `load_dotenv(override=False)` will not overwrite them, so production uses secrets while local development uses `.env`.

### Pattern 5: Dry-Run Stub in pipeline.py

**What:** Every real I/O call checks `dry_run` and logs instead of acting.

**Example:**
```python
# agent/pipeline.py

import logging

logger = logging.getLogger(__name__)

def run_pipeline(config, budget, dry_run: bool) -> None:
    logger.info(f"Pipeline starting (dry_run={dry_run})")

    # In dry-run: skip API call, log what would happen
    if dry_run:
        logger.info("[DRY-RUN] Would call Anthropic API — skipping")
        logger.info("[DRY-RUN] Would send email to %s — skipping", config.email_recipient)
        return

    # Real path (Phase 2+ will fill this in)
    budget.charge(1)
    # ... actual API call ...
```

### Anti-Patterns to Avoid

- **Hardcoding API keys in source:** Any key in source is a security incident. Always use `os.environ`.
- **Calling `load_dotenv()` more than once:** Call it once at module import in `config.py`. Calling it in multiple files causes confusion about which `.env` was loaded.
- **Catching `BudgetExceededError` inside the pipeline:** The budget error must propagate up to `run.py` so it always exits with code 1. Don't catch and swallow it deeper in the stack.
- **Using `sys.exit()` inside library code (budget.py, config.py):** Only `run.py` should call `sys.exit()`. Library code raises exceptions; the entry point decides what to do with them.
- **Checking `dry_run` in config loading:** Config must always load (it validates the environment). `dry_run` only suppresses actual I/O calls inside the pipeline.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| .env file parsing | Custom parser (split on `=`, strip quotes) | `python-dotenv` | Handles quoted values, `#` comments, variable expansion, multiline values, missing files gracefully |
| CLI argument parsing | `sys.argv` slicing | `argparse` (stdlib) | Automatic `--help`, type coercion, error messages, zero dependencies |
| Secret validation | Ad-hoc `if not os.environ.get(...)` scattered everywhere | Centralized `Config.from_env()` with one pass over all required vars | Single point of failure, clear error message listing ALL missing vars at once |

**Key insight:** The parsing edge cases in `.env` files (quotes, escapes, comments, multi-line values) make hand-rolling a correctness risk. `python-dotenv` handles all of them.

---

## Common Pitfalls

### Pitfall 1: .env File Committed to Git

**What goes wrong:** Developer commits `.env` with real API keys. Keys are exposed in git history permanently.
**Why it happens:** Forgetting to add `.env` to `.gitignore` before the first commit.
**How to avoid:** Add `.env` to `.gitignore` in the very first commit, before the `.env` file exists. Create `.env.example` with dummy values as the template.
**Warning signs:** `git status` shows `.env` as untracked or modified.

### Pitfall 2: load_dotenv Silently Ignores Missing .env

**What goes wrong:** Developer forgets to create `.env`, runs the script, and gets a confusing `KeyError` on `os.environ["ANTHROPIC_API_KEY"]` rather than a clear "file not found" message.
**Why it happens:** `load_dotenv()` does not raise an error if the `.env` file is absent — it just continues. The error surfaces later when code tries to read a var that was never set.
**How to avoid:** `Config.from_env()` validates all required vars and lists them all in one error message. The message should reference `.env.example` explicitly.
**Warning signs:** `KeyError: 'ANTHROPIC_API_KEY'` without a clear "check your .env" message.

### Pitfall 3: Budget Check After the API Call

**What goes wrong:** Budget counter is incremented after the call returns, so the Nth+1 call still fires before the halt.
**Why it happens:** Natural to write `call_api(); budget.used += 1`.
**How to avoid:** `budget.charge(n)` must be called BEFORE the API call. The check-then-increment pattern in `BudgetTracker.charge()` enforces this — you can't get a result without going through the check first.
**Warning signs:** Actual API usage exceeds configured limit by 1 on each run.

### Pitfall 4: GitHub Actions Workflow Fails Silently

**What goes wrong:** `run.py` catches all exceptions but calls `sys.exit(0)` on error, so GitHub Actions reports the job as successful even when the agent failed.
**Why it happens:** Developers sometimes use `sys.exit(0)` to avoid noisy failure emails.
**How to avoid:** Budget halts and config errors must exit with code 1. GitHub Actions marks a job failed when the exit code is non-zero, which triggers notifications.
**Warning signs:** GitHub Actions UI shows green checks even when the agent produced no output.

### Pitfall 5: Dry-Run Mode Missing a Real Call Path

**What goes wrong:** A new callsite in Phase 2+ makes a real API call without checking `dry_run`, breaking the guarantee that `--dry-run` makes no real calls.
**Why it happens:** `dry_run` bool is passed around but forgotten at a new callsite.
**How to avoid:** In Phase 2+, establish a convention: every function that makes an external call takes `dry_run: bool` as a parameter. The pipeline passes it through from `run.py` to every callsite. Consider a single "client" wrapper class that holds `dry_run` so it cannot be forgotten.
**Warning signs:** `--dry-run` mode produces API errors or email delivery attempts.

---

## Code Examples

Verified patterns from official sources:

### load_dotenv with override behavior

```python
# Source: python-dotenv README (https://github.com/theskumar/python-dotenv/blob/main/README.md)
from dotenv import load_dotenv

# Default: does NOT override existing env vars (production-safe)
load_dotenv()

# Override existing env vars (useful for forcing .env in tests)
load_dotenv(override=True)

# Custom path
load_dotenv(dotenv_path="/path/to/.env")

# Get values as dict without touching os.environ
from dotenv import dotenv_values
config = dotenv_values(".env")  # {"API_KEY": "abc123", ...}
```

### argparse --dry-run flag

```python
# Source: Python docs argparse (https://docs.python.org/3/library/argparse.html)
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", default=False)
args = parser.parse_args()
# args.dry_run is True when flag is present, False when absent
# Note: --dry-run becomes args.dry_run (hyphen → underscore)
```

### Clean halt with sys.exit

```python
# Source: Python docs sys.exit (https://docs.python.org/3/library/sys.html#sys.exit)
import sys

# Exit with error — GitHub Actions marks job as FAILED
sys.exit(1)

# Exit cleanly — GitHub Actions marks job as SUCCESS
sys.exit(0)

# Raising SystemExit(1) is equivalent to sys.exit(1)
raise SystemExit(1)
```

### GitHub Actions cron schedule for Monday 09:00 UTC

```yaml
# Source: GitHub Actions workflow syntax docs
# (https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)
on:
  schedule:
    - cron: '0 9 * * 1'   # min hour dom month dow — Monday 09:00 UTC
  workflow_dispatch: {}     # manual trigger
```

### .env.example template

```bash
# .env.example — copy to .env and fill in real values
# Never commit .env to git

ANTHROPIC_API_KEY=your-anthropic-api-key-here
EMAIL_RECIPIENT=you@example.com

# Optional: default is 50
API_CALL_BUDGET=50
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual `os.environ` parsing of .env | `python-dotenv` load_dotenv | 2015+ | Handles edge cases (quotes, comments, expansion) |
| `actions/checkout@v2`, `setup-python@v2` | `actions/checkout@v4`, `setup-python@v5` | 2023-2024 | v2 uses deprecated Node 16 runner; always use latest major |
| Hardcoded secrets in workflow YAML | `${{ secrets.NAME }}` in env: | GitHub Actions launch 2018 | Secrets are encrypted, masked in logs |

**Deprecated/outdated:**
- `actions/checkout@v2` and `actions/setup-python@v2`: Uses deprecated Node 16. Use v4/v5 respectively.
- `python-dotenv` versions before 1.0: API was different. Current stable is 1.2.1 (released October 2025).

---

## Open Questions

1. **What variables will be required in .env?**
   - What we know: Phase 1 needs at least `ANTHROPIC_API_KEY` and `EMAIL_RECIPIENT`; `API_CALL_BUDGET` is optional with a default
   - What's unclear: Phase 2 may add `BRAVE_SEARCH_API_KEY` or `TAVILY_API_KEY` depending on web search provider chosen (flagged as deferred decision in STATE.md)
   - Recommendation: Design `Config.from_env()` so adding a new required var in Phase 2 is one line; document in `.env.example` with placeholder

2. **What does dry-run output look like?**
   - What we know: Dry-run must log what it WOULD have done (Claude's discretion per CONTEXT.md)
   - What's unclear: Format — plain print vs. structured logging vs. a dry-run report file
   - Recommendation: Use Python `logging` with a consistent `[DRY-RUN]` prefix on all skipped calls; output goes to stdout at INFO level; no file needed for Phase 1

3. **What is the right default API call budget?**
   - What we know: Budget is per-run; Phase 2 will determine actual call volume when research engine is built
   - What's unclear: How many calls a full run will realistically make
   - Recommendation: Default to 50 in Phase 1; make it easily overridable via `API_CALL_BUDGET` env var; Phase 2 research should establish a real baseline

---

## Validation Architecture

*`nyquist_validation` not present in `.planning/config.json` — section skipped.*

---

## Sources

### Primary (HIGH confidence)
- `https://pypi.org/project/python-dotenv/` — current version (1.2.1), release date (October 2025)
- `https://github.com/theskumar/python-dotenv/blob/main/README.md` — `load_dotenv()` API, `override` parameter, `dotenv_values()`, merge pattern
- `https://docs.python.org/3/library/argparse.html` — `store_true` action, `--dry-run` flag pattern
- `https://docs.python.org/3/library/sys.html` — `sys.exit()` semantics, exit codes
- `https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions` — cron schedule syntax, secrets injection via `env:` in steps

### Secondary (MEDIUM confidence)
- `https://davidmuraya.com/blog/schedule-python-scripts-github-actions/` — complete GitHub Actions YAML example for Python scripts (verified against official docs)
- `https://docs.python-guide.org/writing/structure/` — flat project layout guidance (verified against Python packaging docs)
- Multiple WebSearch results confirming `load_dotenv(override=False)` behavior in GitHub Actions context (consistent with official README behavior description)

### Tertiary (LOW confidence)
- WebSearch results on budget counter patterns — no canonical source; pattern derived from Python stdlib exception and sys.exit semantics which ARE high confidence

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — python-dotenv 1.2.1 verified against PyPI; argparse/sys/os are stdlib
- Architecture: HIGH — project layout based on established Python conventions verified against official guidance; GitHub Actions YAML verified against official docs
- Pitfalls: HIGH for git/.env pitfall (universal), HIGH for load_dotenv override behavior (verified against README), MEDIUM for dry-run propagation pitfall (based on patterns, not a cited source)
- Budget enforcement pattern: MEDIUM — `BudgetTracker` class design is based on stdlib primitives (all HIGH) but the specific class design is Claude's discretion per CONTEXT.md

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (python-dotenv is stable; GitHub Actions action versions may update sooner)
