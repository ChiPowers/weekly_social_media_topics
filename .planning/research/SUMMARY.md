# Project Research Summary

**Project:** Social Media Content Intelligence Agent
**Domain:** Scheduled AI Research Agent (LLM + Web Search + Email Delivery)
**Researched:** 2026-02-28
**Confidence:** MEDIUM (all research from training data, knowledge cutoff August 2025; external verification tools unavailable)

## Executive Summary

This is a scheduled AI research agent: a weekly pipeline that autonomously discovers trending social media niches, synthesizes signals via LLM, and delivers actionable content ideas to a creator's inbox every Monday. The expert approach is a linear, stateless pipeline with five discrete layers — Scheduler, Research Engine, LLM Orchestrator, Report Builder, and Email Sender — with structured JSON handoffs at every boundary. Python is the clear language choice given its first-class AI ecosystem, and the stack is intentionally lean: Anthropic SDK directly (no orchestration framework), Brave Search API, Resend for email, and system cron or GitHub Actions for scheduling. No database is needed for v1; the pipeline is stateless between runs.

The core differentiator of this product is full autonomy — no user input required after setup, evidence-grounded idea generation with topic + angle + rationale, and solo-creator-optimized email delivery. No existing tool in the market combines automated niche discovery, creator profitability signal analysis, evidence-linked idea framing, and scheduled email push in a single product. The v1 scope should be ruthlessly constrained: no dashboard, no platform API integrations, no multi-user support, no content scheduling. The value proposition is "open your inbox Monday, know what to make" — everything that doesn't serve that sentence is out of scope.

The top risks are prompt brittleness producing hallucinated but plausible-sounding rationale, silent scheduler failure, and cost runaway from unbounded multi-step API call loops. All three must be addressed architecturally in Phase 1 — they are expensive to retrofit. The mitigation strategy is: require evidence citation in LLM output schema, add a dead man's switch health-check from day one, and hard-code a bounded call budget (max 20 search calls, max 5 LLM calls per run). Build in fixture-based local testing from the start so prompt iteration doesn't burn API credits.

---

## Key Findings

### Recommended Stack

Python 3.11+ is the unambiguous choice for an AI agent: first-class Anthropic SDK, strong asyncio support for concurrent web search, Pydantic v2 for structured LLM output validation, and the widest ecosystem for AI agent patterns. Use the Anthropic SDK directly — LangChain and similar frameworks add indirection with no benefit for a linear pipeline of this scope.

The critical infrastructure choices are: Brave Search API (low cost, no OAuth, programmatic-first), Resend for transactional email (clean Python SDK, generous free tier, strong deliverability), and `uv` as the package manager. The stack is intentionally minimal — no database, no in-process scheduler, no orchestration framework. GitHub Actions with a `schedule:` trigger is worth evaluating as an alternative to local cron; it eliminates server infrastructure entirely, though its 60-day inactivity timeout is a known risk.

**Core technologies:**
- Python 3.12: Primary language — dominant AI/ML ecosystem, asyncio for concurrent search, Pydantic for LLM output validation
- `anthropic` SDK (>=0.25.0): LLM calls — official Python client, direct API preferred over frameworks for this linear pipeline
- `httpx` (>=0.27.0): HTTP client — async-ready, modern replacement for `requests`, used for Brave Search API calls
- Brave Search API: Web search — independent index, API-key-only auth, low cost (~$3/1000 queries), no OAuth
- `resend` (>=2.0.0): Email delivery — clean DX, generous free tier, strong deliverability, handles SPF/DKIM
- `jinja2` (>=3.1.0): Email templating — structured HTML email rendering, far cleaner than f-string concatenation
- `pydantic` (>=2.5.0): Data validation — typed config objects and LLM output schema validation at every component boundary
- `tenacity` (>=8.2.0): Retry logic — exponential backoff on all external API calls
- `loguru` (>=0.7.0): Structured logging — simple setup, file + stdout output, rotation support
- `python-dotenv` (>=1.0.0): Secrets management — load API keys from `.env`, never hardcode credentials
- System cron or GitHub Actions: Scheduling — cron is simplest; GitHub Actions eliminates server requirement at the cost of inactivity timeout risk

See `.planning/research/STACK.md` for full alternatives analysis and version notes.

### Expected Features

The feature dependency chain is strictly sequential: trend discovery is the root, creator analysis depends on trends, idea generation depends on both, report assembly depends on all three, email delivery is the final step. Nothing can be built out of order.

**Must have (table stakes):**
- Autonomous trend discovery across TikTok, YouTube, Instagram, X via web search synthesis — the entire data foundation; without this nothing downstream exists
- Niche-level trend identification (not macro trends) — the value is specific actionable niches, not "AI is trending globally"
- Content idea generation with topic + angle + rationale — the deliverable; raw trend data without ideas requires interpretation the tool should do
- Creator identification as profitability proxy per niche — distinguishes the report from a generic "what's trending" list
- Structured email report with consistent format — same sections every week; reader builds a mental model
- Weekly automated delivery, Monday morning — must be automatic; the whole value is "open inbox Monday, know what to make"
- "Why this is working now" rationale per idea — tied to specific evidence, not generic claims

**Should have (competitive differentiators):**
- Profitability-signal creator analysis (brand deal signals, cross-platform footprint, sponsorship language) — not just follower counts; most tools report vanity metrics only
- Evidence-linked angle framing ("budget headphones that outperform flagship models" vs. "review budget headphones") — the insight that makes ideas non-obvious
- Explicit "why now" timing signal — distinguishes timely from evergreen content; creators need to know if a window is open or closing
- Platform-specific signal weighting — TikTok virality differs from YouTube growth; conflating reduces report accuracy

**Defer to v2:**
- Trend velocity / week-over-week niche tracking — requires multi-week state; add after v1 loop is proven reliable
- Cross-platform presence mapping per creator — raises data synthesis complexity; strong v2 differentiator
- Posting cadence analysis — useful but secondary to core idea generation loop
- Hashtag/keyword surface — additive but not foundational

**Defer indefinitely (anti-features):**
- Real-time social platform API integrations — OAuth complexity, rate limits, ToS risk; web search synthesis delivers sufficient signal
- Dashboard or web UI — adds front-end surface, auth system, hosting overhead with no v1 value
- Multi-user support — requires user management, billing, customization
- Content scheduling / publishing — out of scope; this is an intelligence tool, not a distribution tool
- Custom niche configuration — reintroduces the weekly friction the autonomous approach eliminates

See `.planning/research/FEATURES.md` for full competitive analysis and feature dependency map.

### Architecture Approach

The system is a linear pipeline with no feedback loops in v1. Data flows in one direction: Scheduler fires trigger -> Research Engine issues search query battery -> LLM Orchestrator runs 2-3 sequential synthesis passes -> Report Builder renders structured JSON to HTML email -> Email Sender delivers to inbox. A Config + State Store cross-cuts all layers for API keys, prompt templates, and run logging. Every component handoff uses validated JSON — never raw text. The pipeline is stateless between runs; state (run logs, report history) lives in append-only files, not a database.

**Major components:**
1. Scheduler — fires the pipeline on a weekly cadence; cron entry or GitHub Actions `schedule:` trigger; invokes the pipeline entry point and exits
2. Research Engine — issues a structured battery of discovery + depth search queries concurrently via asyncio; returns raw results as a structured JSON payload grouped by query intent
3. LLM Orchestrator — runs 3 sequential LLM passes: (1) trend extraction from raw results, (2) creator signal extraction per trend, (3) idea generation with rationale; validates each pass output against a Pydantic schema before passing downstream
4. Report Builder — pure formatting step: takes structured ideas JSON, renders Jinja2 template to HTML + plain text email body; no additional LLM calls unless subject line requires one
5. Email Sender — calls Resend API, logs delivery confirmation or error; never fires if upstream steps failed
6. Config + State Store — environment variable loading, prompt template files, append-only run log (JSON file or SQLite); cross-cutting read dependency for all components

**Key patterns:**
- Multi-pass LLM synthesis: never one giant prompt; each pass has one focused job and is independently inspectable
- Structured output at every boundary: Pydantic validation + retry loop on every LLM call; if validation fails after 2 retries, abort the run and log failure
- Map-reduce search synthesis: summarize each search result chunk independently before synthesizing across summaries; never concatenate raw results into a single prompt
- Concurrent search execution: asyncio for all web search queries within a phase; eliminates sequential latency
- Search provider abstraction: wrap all search calls behind a `search()` interface so the provider can be swapped without touching agent logic

See `.planning/research/ARCHITECTURE.md` for full build order, data schemas, and scalability notes.

### Critical Pitfalls

1. **Prompt brittleness producing hallucinated rationale** — require the LLM to cite specific evidence (named creator or platform, approximate timeframe, engagement signal) in a structured output schema; if evidence fields are unpopulated, the idea is excluded; store raw search results alongside every report to enable audit
2. **Silent scheduler failure** — add a dead man's switch health-check (healthchecks.io or equivalent) that alerts when no ping arrives on schedule; for GitHub Actions, note the 60-day inactivity timeout that disables scheduled workflows on inactive repos
3. **Cost runaway from unbounded API call loops** — hard-code a bounded call budget per run (max ~20 search calls, max 5 LLM calls); summarize search snippets before passing to LLM; set hard billing alerts on every API account from day one; log cost per run
4. **Context window saturation degrading synthesis quality** — implement map-reduce pattern: summarize each search result independently, then synthesize across summaries; never concatenate raw results; cap search results per step at 3-5 high-quality results
5. **Email deliverability failure (reports land in spam)** — use Resend or equivalent transactional service that handles SPF/DKIM/DMARC; validate deliverability with mail-tester.com before treating the system as functional; keep email HTML simple with minimal links
6. **Trend discovery echo chamber** — design search queries around momentum signals (what changed this week, what's newly gaining attention) not absolute popularity; explicitly instruct the LLM to avoid topics popular for more than 3 months; rotate query formulations weekly
7. **Report quality drift** — store all reports and raw search data; add a self-evaluation LLM step that scores each idea on specificity and evidence quality; periodic manual audit against cited evidence

See `.planning/research/PITFALLS.md` for full pitfall analysis with prevention strategies and phase-specific warnings.

---

## Implications for Roadmap

The feature dependency chain (trend discovery -> creator analysis -> idea generation -> report assembly -> email delivery) maps directly to a natural phase structure. Architecture's suggested build order (Config -> Search -> LLM -> Report -> Email -> Scheduler -> Hardening) confirms this sequencing. Pitfalls make clear that core quality and cost guardrails must be in Phase 1, not added later.

### Phase 1: Foundation and Scaffolding
**Rationale:** Every downstream component depends on config loading, secrets management, and a local development harness. Pitfall 14 (secrets in version control) and Pitfall 13 (no local test mode) are both Phase 1 non-negotiables — they cannot be added later without pain.
**Delivers:** Working project scaffold, environment management, `--dry-run` and `--mock-search` modes, CI-ready structure, `.env` pattern enforced from first commit
**Addresses:** Configuration, secrets management, developer experience
**Avoids:** Secrets in version control (Pitfall 14), no local test mode (Pitfall 13)
**Research flag:** Standard patterns — well-documented Python project setup; no phase research needed

### Phase 2: Search Integration and Research Engine
**Rationale:** Search is the root dependency of the entire feature chain. Nothing can be tested end-to-end until search returns real results. Build and validate in isolation before wiring to LLM.
**Delivers:** Working Research Engine that issues a structured query battery (discovery + depth queries) concurrently via asyncio, returns raw results as validated JSON
**Addresses:** Trend discovery (table stakes), platform signal collection
**Uses:** `httpx`, Brave Search API, Pydantic for result schema
**Avoids:** Cost runaway (Pitfall 3) — bounded call budget implemented here; echo chamber (Pitfall 7) — momentum-focused query strategy designed here; search provider abstraction (Pitfall 9)
**Research flag:** Needs phase research — Brave Search API query design, rate limits, and response format require verification against current API docs before implementation

### Phase 3: LLM Orchestrator and Synthesis
**Rationale:** With real search results available (from Phase 2 fixtures), build the multi-pass synthesis pipeline. This is the highest-complexity component and the core value generator — it warrants its own phase.
**Delivers:** 3-pass LLM synthesis (trend extraction -> creator signal extraction -> idea generation), Pydantic schema validation at each boundary, retry loop on validation failure, evidence citation requirement enforced in schema
**Addresses:** Niche-level trend identification, creator profitability signals, content idea generation with topic + angle + rationale, "why this is working now" rationale (all table stakes)
**Uses:** `anthropic` SDK, `pydantic`, `tenacity`
**Implements:** LLM Orchestrator component; multi-pass pattern; map-reduce search synthesis
**Avoids:** Prompt brittleness / hallucination (Pitfall 1) — evidence citation schema enforced; context saturation (Pitfall 4) — map-reduce pattern implemented; structured output parsing failures (Pitfall 8)
**Research flag:** Needs phase research — Anthropic structured output/tool use availability, token budget management for multi-pass synthesis, and prompt architecture for evidence-grounded idea generation benefit from targeted research before implementation

### Phase 4: Report Builder and Email Delivery
**Rationale:** With structured ideas JSON available from Phase 3 fixtures, build the formatting and delivery layer. Email delivery is the most consequential user-facing operation and must be validated thoroughly before treating the system as functional.
**Delivers:** Jinja2 email template (HTML + plain text), subject line generation, Resend integration with delivery confirmation, SPF/DKIM validation, mail-tester.com deliverability check
**Addresses:** Consistent report structure, weekly email delivery (table stakes)
**Uses:** `jinja2`, `resend`, HTML email best practices
**Implements:** Report Builder and Email Sender components; fail-safe delivery pattern
**Avoids:** Email deliverability failure (Pitfall 5) — Resend handles domain authentication; HTML rendering inconsistency (Pitfall 12) — inline styles, tested against Gmail and Outlook
**Research flag:** Standard patterns — Resend integration and email deliverability are well-documented; no phase research needed

### Phase 5: Scheduler and End-to-End Integration
**Rationale:** Wire all components together only after each works in isolation. Scheduling is the simplest layer; its complexity is in the pipeline, not the trigger mechanism. End-to-end integration surfaces cross-component issues that unit testing cannot.
**Delivers:** Cron entry or GitHub Actions workflow, full end-to-end pipeline test with real APIs, run logging to append-only file, dead man's switch health-check, timezone handling
**Addresses:** Weekly automated delivery, Monday morning arrival (table stakes)
**Implements:** Scheduler component; stateful run log
**Avoids:** Silent scheduler failure (Pitfall 2) — dead man's switch from day one; timezone edge cases (Pitfall 10)
**Research flag:** Standard patterns — cron and GitHub Actions scheduling are well-documented; GitHub Actions inactivity timeout (60 days) needs verification against current docs

### Phase 6: Hardening and Reliability
**Rationale:** After the first successful end-to-end run, harden the system against production failure modes. Retry logic, cost tracking, and error alerting turn a working prototype into a reliable weekly delivery system.
**Delivers:** Exponential backoff retry on all external API calls, cost-per-run logging (search calls, token counts, estimated cost), error alerting on failure (email notification to self), LLM API outage handling, quality self-evaluation step (idea scoring on specificity and evidence quality)
**Addresses:** Reliability, cost visibility, report quality monitoring
**Uses:** `tenacity`, `loguru`, structured run logs
**Avoids:** LLM API outages breaking the weekly run (Pitfall 11); report quality drift (Pitfall 6); cost runaway going undetected (Pitfall 3)
**Research flag:** Standard patterns — retry and logging patterns are well-established; no phase research needed

### Phase Ordering Rationale

- Config before search, search before LLM, LLM before report, report before email, email before scheduler: this is the feature dependency chain from FEATURES.md and the build order from ARCHITECTURE.md — they agree completely
- Scheduler is last because it wraps a working pipeline; building it early means wiring untested components together, which makes debugging harder
- Hardening is its own phase because retrofitting retry logic, cost logging, and quality monitoring into an already-wired pipeline is significantly harder than adding it incrementally after the first successful run
- Pitfall prevention for Pitfalls 1, 3, 4, and 7 (hallucination, cost runaway, context saturation, echo chamber) is embedded into Phases 2 and 3 — these are foundational architectural decisions that cannot be added later without restructuring the pipeline

### Research Flags

Phases needing deeper research during planning:
- **Phase 2 (Search Integration):** Brave Search API current rate limits, response schema, and query syntax require verification against live API docs before implementation. Tavily is a strong alternative worth evaluating — decision should be made here, not assumed.
- **Phase 3 (LLM Orchestrator):** Anthropic structured output / tool use availability for enforcing JSON output schema needs verification against current API docs. Prompt architecture for multi-pass synthesis with evidence citation is complex enough to benefit from targeted research before writing prompts.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Python project scaffolding, `.env` pattern, virtual environments — fully standard, no research needed
- **Phase 4 (Report + Email):** Resend Python SDK integration and email HTML best practices are well-documented
- **Phase 5 (Scheduler):** Cron and GitHub Actions scheduling are well-documented; only verification needed is GitHub Actions inactivity timeout current policy
- **Phase 6 (Hardening):** `tenacity` retry patterns and structured logging are well-established

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Language, ecosystem, and architecture-level choices are HIGH confidence; specific package versions are LOW and must be verified on PyPI before implementation |
| Features | MEDIUM | Core feature patterns for social intelligence tools are stable and well-documented; specific competitor feature details may have evolved since training cutoff |
| Architecture | MEDIUM | Linear pipeline pattern for scheduled AI agents is well-established; specific LLM behavior (context degradation, structured output support) evolves and should be tested empirically |
| Pitfalls | MEDIUM-HIGH | LLM hallucination, cost runaway, and email deliverability pitfalls are HIGH confidence from well-documented production patterns; API-specific behavior (rate limits, pricing) is MEDIUM and requires verification |

**Overall confidence:** MEDIUM

All research was conducted from training data (knowledge cutoff August 2025) without access to live documentation, current API pricing, or external verification tools. The architectural approach, technology choices, and pitfall patterns are stable and well-established — the core recommendations are sound. Version numbers, API pricing, and specific API behavior (especially Anthropic structured output, Brave Search query syntax, GitHub Actions inactivity timeout) must be verified against live documentation before implementation.

### Gaps to Address

- **Package versions:** All version numbers in the dependency list (anthropic, resend, httpx, pydantic, jinja2, tenacity, loguru) must be verified on pypi.org before committing to a `pyproject.toml`. Treat all versions as approximate minimums, not exact pins.
- **Claude model availability:** `claude-3-5-sonnet-20241022` and `claude-3-haiku-20240307` are recommended but model names change frequently. Verify current available models at console.anthropic.com before implementation.
- **Brave Search API vs. Tavily decision:** Both are viable; this decision was deferred in research. Phase 2 should include a brief evaluation of current pricing and response quality for both before committing.
- **Anthropic structured output support:** The LLM Orchestrator architecture assumes enforced JSON output. Verify current Anthropic tool use / structured output capabilities at the time of Phase 3 implementation — the approach may need adjustment based on what's currently supported.
- **GitHub Actions inactivity timeout:** Research confirms a 60-day inactivity timeout for scheduled workflows, but this policy should be verified against current GitHub documentation before relying on GitHub Actions as the scheduler.
- **Email deliverability validation:** Must be tested empirically with mail-tester.com after initial Resend setup — cannot be assumed to work without verification.

---

## Sources

### Primary (HIGH confidence)
- Project context: `/Users/chivonpowers/gsd-test-project/.planning/PROJECT.md` — used as source-of-truth for scope constraints
- Training data on LLM agent production patterns and hallucination behavior (cutoff August 2025) — well-documented across production systems

### Secondary (MEDIUM confidence)
- Training data: Python AI ecosystem (anthropic SDK, pydantic, httpx, tenacity, loguru, jinja2, python-dotenv) — package choices are stable; versions need PyPI verification
- Training data: Email deliverability requirements (SPF/DKIM/DMARC, transactional email service behavior) — stable industry standards
- Training data: Scheduled job patterns (cron, GitHub Actions, inactivity timeout behavior) — patterns are stable; specific GitHub Actions policy needs live verification
- Training data: Social media intelligence tool feature landscape (BuzzSumo, Exploding Topics, SparkToro, Semrush Social, Brandwatch, Modash, Feedly Intelligence) — feature patterns are stable; specific tool offerings may have evolved

### Tertiary (LOW confidence — verify before use)
- All package version numbers — verify on pypi.org
- Claude model names and availability — verify at console.anthropic.com
- Brave Search API pricing and rate limits — verify at brave.com/search/api/
- Resend Python SDK current version — verify at resend.com and PyPI
- GitHub Actions 60-day inactivity timeout — verify at docs.github.com
- Anthropic structured output / tool use availability — verify at docs.anthropic.com

---

*Research completed: 2026-02-28*
*Ready for roadmap: yes*
