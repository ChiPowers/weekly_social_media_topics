# Phase 2: Research Engine - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Web search integration that autonomously discovers trending niches and top-performing creators across 5 major social platforms (TikTok, YouTube, Facebook, Instagram, X/Twitter). Produces structured JSON findings broken down by topic, content style, posting frequency, and media type. No user input required during a run.

</domain>

<decisions>
## Implementation Decisions

### Trending Signal Definition
- **Timeframe:** This week — agent queries for what's trending right now, not the past 30 days
- **Signal priority:** High engagement volume (views, likes, shares) is the primary trending indicator — the crowd has already voted
- **Discovery mode:** Fully autonomous — no seed topics or pre-set categories; agent discovers whatever is actually gaining momentum
- **Platform attribution gaps:** Claude's discretion — handle ambiguous platform attribution without a fixed rule (include with best-guess or note uncertainty as appropriate)

### Creator Signal Detection
- **Primary profitability indicator:** Follower count — most reliably surfaced from web search snippets
- **Target creator tier:** Mid-tier (100K–1M followers) — proven enough to be a real signal, tactically replicable
- **Brand deal / sponsorship:** Flag when found (optional field) — do not require it, but capture it if detectable from search results (e.g., "#ad", "#sponsored", "partnership with")
- **Creators per niche:** 3–5 named creators per niche/topic in research output

### Claude's Discretion
- Platform attribution ambiguity handling (include with caveat vs. best-guess vs. exclude — Claude decides per case)
- Search query construction and how to phrase "trending this week" queries per platform
- Result deduplication strategy when the same creator appears across multiple searches
- How to infer "content style" and "posting frequency" from web search results (since these aren't always explicit)

</decisions>

<specifics>
## Specific Ideas

- The "this week" framing should be reflected in search queries — time-bounded language like "viral this week", "trending now", "most viewed this week" rather than general popularity
- Follower count is the anchor signal but should not be the only thing reported — if brand deals or cross-platform presence surface naturally, capture them
- 3–5 creators per niche is the target, but quality over quantity — better to have 2 well-sourced creators than 5 with thin data

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-research-engine*
*Context gathered: 2026-02-28*
