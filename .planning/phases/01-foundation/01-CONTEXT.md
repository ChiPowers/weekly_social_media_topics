# Phase 1: Foundation - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Project scaffold, environment management, and dry-run harness. The goal is that a developer can run and test the full pipeline locally without spending any API credits or sending real emails. This phase produces the structural skeleton (file layout, config loading, budget enforcement, dry-run mode) that all later phases build on.

</domain>

<decisions>
## Implementation Decisions

### Execution environment
- Production runs on **GitHub Actions** (cloud-scheduled weekly, no local machine required)
- Project structure must be GitHub Actions-compatible from the start (workflow YAML, secrets via repo settings)

### Local development & testing
- Local testing via `python run.py --dry-run`
- `--dry-run` flag must complete the full pipeline without making real API calls or sending email
- Single command, no install step required — just clone and run

### Dependency management
- `requirements.txt + pip` — standard, simple, works everywhere including GitHub Actions
- No uv, poetry, or other tooling required

### Claude's Discretion
- Exact project directory structure (module layout, file naming)
- Config file format for non-secret settings (if any)
- How mock/stub data is structured in dry-run mode
- Budget enforcement implementation (counter, decorator, or middleware)

</decisions>

<specifics>
## Specific Ideas

- User's mental model is "it runs in the cloud every week automatically" — GitHub Actions is the target, not an afterthought
- Invocation syntax doesn't matter as long as it's simple (`python run.py` is fine)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-02-28*
