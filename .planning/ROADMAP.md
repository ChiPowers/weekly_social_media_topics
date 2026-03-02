# Roadmap: Social Media Content Intelligence Agent

## Overview

Five phases build the pipeline layer by layer, following the natural feature dependency chain: foundation first, then search, then LLM synthesis, then report delivery, then the scheduler that ties everything together. Each phase delivers a working, independently verifiable capability. Nothing is wired together until its parts work in isolation.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, environment management, and dry-run harness (completed 2026-03-01)
- [x] **Phase 2: Research Engine** - Autonomous trend and creator discovery via web search (completed 2026-03-01)
- [x] **Phase 3: LLM Orchestrator** - Multi-pass synthesis producing structured content ideas (completed 2026-03-02)
- [ ] **Phase 4: Report and Email Delivery** - HTML report rendering and inbox delivery
- [ ] **Phase 5: Scheduler and Integration** - Weekly automation and end-to-end pipeline wiring

## Phase Details

### Phase 1: Foundation
**Goal**: Developer can run and test the pipeline locally without spending API credits or sending real emails
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03
**Success Criteria** (what must be TRUE):
  1. Running the agent with a `.env` file loads all credentials without any code changes required
  2. Running with `--dry-run` flag completes without making any real API calls or sending email
  3. Running a query that would exceed the configured call budget causes the agent to halt cleanly with an informative error before any over-budget call is made
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Project scaffold, dependency setup, and `.env` config loading (Wave 1) — completed 2026-03-01
- [x] 01-02-PLAN.md — Dry-run mode and API call budget enforcement (Wave 2) — completed 2026-03-01

### Phase 2: Research Engine
**Goal**: Agent autonomously discovers trending niches and top-performing creators across major social platforms each run
**Depends on**: Phase 1
**Requirements**: RSCH-01, RSCH-02, RSCH-03, RSCH-04
**Success Criteria** (what must be TRUE):
  1. Running the research engine without any user input produces a structured JSON payload of trending niches discovered this week
  2. Research output covers signals from TikTok, YouTube, Facebook, Instagram, and X/Twitter in a single run
  3. Research output includes named creators per niche with at least one profitability signal (follower count, brand deal indicator, or cross-platform presence)
  4. Research output is broken down by topic, content style, posting frequency, and media type — not just topic alone
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Tavily + Pydantic install, Config TAVILY_API_KEY extension, research output schema (Wave 1) — completed 2026-03-01
- [x] 02-02-PLAN.md — ResearchEngine with two-pass autonomous discovery, budget-guarded search, pipeline wiring (Wave 2) — completed 2026-03-01
- [x] 02-03-PLAN.md — LLM-assisted structured extraction, ValidationError handling, research_output.json, human verification (Wave 3) — completed 2026-02-28

### Phase 3: LLM Orchestrator
**Goal**: Agent converts raw research findings into 5-10 specific, evidence-grounded content ideas
**Depends on**: Phase 2
**Requirements**: IDEA-01, IDEA-02
**Success Criteria** (what must be TRUE):
  1. Given research output, the orchestrator produces exactly 5-10 ideas each formatted as a topic plus a specific angle
  2. Each idea includes a rationale that cites a specific creator or metric and platform from the research — not a generic claim
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — ContentIdea/IdeaReport schemas and IdeaSynthesizer class with single-pass synthesis, thin niche filtering, retry logic (Wave 1) — completed 2026-03-02
- [ ] 03-02-PLAN.md — Pipeline wiring, ideas_output.json output, and human verification of live synthesis quality (Wave 2)

### Phase 4: Report and Email Delivery
**Goal**: Structured ideas are rendered into a readable HTML email and delivered to the creator's inbox
**Depends on**: Phase 3
**Requirements**: DLVR-01, DLVR-02
**Success Criteria** (what must be TRUE):
  1. Triggering the report step delivers an HTML email to the configured recipient address
  2. The email body contains all 5-10 ideas with their topic, angle, and rationale visible and readable
**Plans**: 3 plans

Plans:
- [ ] 04-01: Jinja2 HTML email template and plain-text fallback
- [ ] 04-02: Resend integration, delivery confirmation logging, and deliverability validation

### Phase 5: Scheduler and Integration
**Goal**: The complete pipeline runs automatically every Monday morning with no manual trigger required
**Depends on**: Phase 4
**Requirements**: SCHED-01
**Success Criteria** (what must be TRUE):
  1. The pipeline fires on Monday morning without any manual action by the user
  2. A full end-to-end run completes successfully — research, synthesis, and email delivery — without manual intervention between steps
**Plans**: 3 plans

Plans:
- [ ] 05-01: Cron or GitHub Actions schedule configuration and end-to-end integration test

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete    | 2026-03-01 |
| 2. Research Engine | 3/3 | Complete    | 2026-03-02 |
| 3. LLM Orchestrator | 2/2 | Complete   | 2026-03-02 |
| 4. Report and Email Delivery | 0/2 | Not started | - |
| 5. Scheduler and Integration | 0/1 | Not started | - |
