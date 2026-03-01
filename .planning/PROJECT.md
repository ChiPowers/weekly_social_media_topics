# Social Media Content Intelligence Agent

## What This Is

A scheduled AI agent that runs every week and delivers an email report of 5–10 actionable content ideas backed by current trend data. It auto-discovers which niches and topics are gaining momentum across social media, researches what successful creators are doing in those spaces, and distills findings into ready-to-use ideas (topic + angle) tied explicitly to why they're working right now. Built for a solo content creator operating across multiple niches.

## Core Value

Every Monday, the creator opens their inbox and knows exactly what to make that week — each idea grounded in evidence of what's actually driving engagement and profit for real creators.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Agent auto-discovers trending niches/topics across social media weekly
- [ ] Research analyzes top-performing creators as proxies for profitability (followers, brand deals, likes, cross-platform presence)
- [ ] Research breaks down findings by: topic, content style, posting frequency, media type, and platform (TikTok, YouTube, Facebook, etc.)
- [ ] Agent synthesizes research into 5–10 content ideas, each framed as a topic + angle
- [ ] Each idea includes a data-backed rationale ("why this is working right now")
- [ ] Report is delivered via email on a fixed weekly schedule
- [ ] System runs fully automated — no manual trigger required

### Out of Scope

- Real-time social media API integrations — web search + AI synthesis is sufficient for v1; live API data adds complexity without proportional value at this stage
- Multi-user / client-facing delivery — built for one inbox only
- Full scripts or production-ready outlines — topic + angle is the right level of detail for now
- Dashboard or web UI — email is the interface

## Context

- Research methodology: web search + AI synthesis (no platform API keys required for v1)
- Trend discovery: agent autonomously identifies what's gaining momentum — no manual niche input
- Creator proxies: profitability inferred from follower count, cross-platform presence, brand sponsorship signals, and engagement volume
- Report depth: trend analysis section + actionable ideas section, combined in one email

## Constraints

- **Automation**: Must run on a schedule (cron or equivalent) without manual intervention
- **Delivery**: Must send email — specific email service TBD during implementation
- **Scope**: v1 is web search + AI only — no social platform API credentials required

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Web search + AI over platform APIs | Lower complexity, no OAuth/API key management, sufficient signal quality for content ideation | — Pending |
| Auto-discover niches (not user-configured) | Removes weekly friction; agent finds what's actually trending vs. what user thinks is trending | — Pending |
| Topic + angle depth (not full scripts) | Right level of utility — enough to act on, not so much it becomes noise | — Pending |

---
*Last updated: 2026-02-28 after initialization*
