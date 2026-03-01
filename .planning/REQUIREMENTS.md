# Requirements: Social Media Content Intelligence Agent

**Defined:** 2026-02-28
**Core Value:** Every Monday, the creator opens their inbox and knows exactly what to make that week — each idea grounded in evidence of what's actually driving engagement and profit for real creators.

## v1 Requirements

### Setup & Config

- [x] **SETUP-01**: User can configure all API keys via a `.env` file without modifying source code
- [x] **SETUP-02**: User can run the pipeline in dry-run mode to test without making real API calls or sending email
- [x] **SETUP-03**: Agent enforces a hard per-run API call budget and halts cleanly if the limit would be exceeded

### Research Engine

- [x] **RSCH-01**: Agent autonomously discovers trending social media niches and topics each run — no user input required
- [x] **RSCH-02**: Research covers all major platforms (TikTok, YouTube, Facebook, Instagram, X/Twitter)
- [x] **RSCH-03**: Research identifies top-performing creators in discovered niches and extracts profitability signals (follower counts, brand deal indicators, cross-platform presence)
- [x] **RSCH-04**: Research produces findings broken down by topic, content style, posting frequency, and media type

### Idea Generation

- [ ] **IDEA-01**: Agent generates 5–10 content ideas per report, each framed as a topic + angle
- [ ] **IDEA-02**: Each idea includes a data-backed rationale citing specific evidence (creator, metric, platform) from the research

### Delivery

- [ ] **DLVR-01**: Report is delivered as an HTML email to a configured recipient address
- [ ] **DLVR-02**: Email body contains an ideas section with all 5–10 ideas and their rationale

### Scheduling

- [ ] **SCHED-01**: Agent runs automatically on a fixed weekly schedule (every Monday morning) without manual triggering

## v2 Requirements

### Delivery

- **DLVR-03**: Email includes a trend analysis summary section (context before ideas)
- **DLVR-04**: Email deliverability configured with SPF/DKIM/DMARC to prevent spam filtering

### Reliability

- **RELY-01**: Dead man's switch health-check alerts if the agent silently stops running
- **RELY-02**: Per-run logging captures status, cost, and output for debugging and quality tracking

### Synthesis Quality

- **SYNTH-01**: Multi-pass LLM synthesis (separate passes for trend extraction, creator analysis, idea generation)
- **SYNTH-02**: Structured JSON output validated with Pydantic schema before report generation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Social media platform API integrations (OAuth/live data) | High complexity, no API credentials required; web search is sufficient signal for v1 |
| Dashboard or web UI | Email is the interface; a UI adds complexity without utility for a solo user |
| Full scripts or production-ready content outlines | Topic + angle is the right depth; full scripts are scope creep |
| Multi-user or client-facing delivery | Built for one inbox; multi-user requires auth, user management, billing |
| Manual niche configuration | Defeats the autonomous discovery value proposition |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Complete |
| SETUP-02 | Phase 1 | Complete |
| SETUP-03 | Phase 1 | Complete |
| RSCH-01 | Phase 2 | Complete |
| RSCH-02 | Phase 2 | Complete |
| RSCH-03 | Phase 2 | Complete |
| RSCH-04 | Phase 2 | Complete |
| IDEA-01 | Phase 3 | Pending |
| IDEA-02 | Phase 3 | Pending |
| DLVR-01 | Phase 4 | Pending |
| DLVR-02 | Phase 4 | Pending |
| SCHED-01 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-28*
*Last updated: 2026-02-28 after roadmap creation*
