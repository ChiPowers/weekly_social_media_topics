# Phase 2: Research Engine - Research

**Researched:** 2026-02-28
**Domain:** Web search API integration + autonomous trending discovery + structured JSON output
**Confidence:** HIGH (core stack verified via official docs and PyPI; patterns verified with multiple sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Trending timeframe:** This week — agent queries for what's trending right now, not the past 30 days
- **Signal priority:** High engagement volume (views, likes, shares) is the primary trending indicator — the crowd has already voted
- **Discovery mode:** Fully autonomous — no seed topics or pre-set categories; agent discovers whatever is actually gaining momentum
- **Primary profitability indicator:** Follower count — most reliably surfaced from web search snippets
- **Target creator tier:** Mid-tier (100K–1M followers) — proven enough to be a real signal, tactically replicable
- **Brand deal / sponsorship:** Flag when found (optional field) — do not require it, but capture it if detectable from search results (e.g., "#ad", "#sponsored", "partnership with")
- **Creators per niche:** 3–5 named creators per niche/topic in research output

### Claude's Discretion
- Platform attribution ambiguity handling (include with caveat vs. best-guess vs. exclude — Claude decides per case)
- Search query construction and how to phrase "trending this week" queries per platform
- Result deduplication strategy when the same creator appears across multiple searches
- How to infer "content style" and "posting frequency" from web search results (since these aren't always explicit)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RSCH-01 | Agent autonomously discovers trending social media niches and topics each run — no user input required | Multi-query autonomous discovery pattern with Tavily `topic="news"` + `time_range="week"` documented; query bank strategy outlined in Architecture Patterns |
| RSCH-02 | Research covers all major platforms (TikTok, YouTube, Facebook, Instagram, X/Twitter) | Per-platform query templates documented; Tavily returns web-wide results allowing platform-specific query targeting |
| RSCH-03 | Research identifies top-performing creators in discovered niches and extracts profitability signals (follower counts, brand deal indicators, cross-platform presence) | Regex-based follower count extraction pattern documented; brand deal signal keywords identified; Pydantic schema for structured output verified |
| RSCH-04 | Research produces findings broken down by topic, content style, posting frequency, and media type | Pydantic output schema with all four dimensions designed; LLM extraction approach for implicit signals (content style, posting frequency) documented |
</phase_requirements>

---

## Summary

The research engine phase adds real web search capability to replace the pipeline stub from Phase 1. The core work is: (1) choose and integrate a search API, (2) build an autonomous multi-query discovery strategy for trending niches and creators, (3) extract structured data from unstructured search snippets, and (4) output normalized JSON using Pydantic models.

**Tavily is the clear choice over Brave Search** for this use case. Tavily was built from the ground up for AI agents: it provides a first-party Python SDK (`tavily-python`), explicit `time_range="week"` and `topic="news"` parameters, relevance scoring, and LLM-ready content snippets already trimmed for context windows. Brave Search is a raw SERP API requiring `requests` and manual response parsing — better suited for high-volume traditional search tasks. Tavily's free tier (1,000 credits/month, no credit card) is sufficient for development, and 1 credit per basic search means the project's `API_CALL_BUDGET` pattern from Phase 1 maps directly onto Tavily credits.

The extraction challenge is that web search snippets are unstructured text — follower counts, content style, and posting frequency are never returned as labeled fields. The recommended pattern is: run targeted search queries → collect raw snippets → pass snippet batches to Claude for structured extraction into Pydantic models. This avoids brittle regex-only parsing while staying within the budget (Claude API calls are already tracked by `BudgetTracker`).

**Primary recommendation:** Use Tavily (`tavily-python==0.7.22`) with `topic="news"`, `time_range="week"`, `search_depth="basic"` and a 10–15 query bank per run; extract structured findings via Claude into Pydantic v2 models.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tavily-python | 0.7.22 | Web search with time-bounded, AI-optimized results | First-party Python SDK, built for agents, `time_range="week"` + `topic="news"` native, 1,000 free credits/month |
| pydantic | 2.12.5 | Structured output schema + validation for research findings | Already decision for v2 per REQUIREMENTS.md SYNTH-02; v2 `BaseModel` + `model_dump_json()` is the standard pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.2.1 | Load TAVILY_API_KEY from .env (already in requirements.txt) | Already installed from Phase 1 — zero-cost addition |
| re (stdlib) | stdlib | Regex extraction of follower counts from snippets as fallback | When LLM extraction is not cost-efficient for simple numeric patterns |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tavily | Brave Search API | Brave is cheaper at scale ($5/1K vs Tavily PAYGO $8/1K) but has no Python SDK, no semantic re-ranking, and no `time_range` native support — requires `requests` and manual result parsing. Brave free tier was eliminated Feb 2025 (replaced by $5 monthly credits). Use Brave only if cost becomes critical at high volume. |
| Tavily | SerpAPI | SerpAPI offers Google/Bing results and is stronger for traditional SERP data, but costs $15-22/1K queries and lacks AI-native features. |
| Pydantic BaseModel | Python dataclasses | Project already uses `dataclasses` for Config — either works, but Pydantic's `model_dump_json()` and field validation make output serialization trivial. Favor Pydantic for research output schema. |

**Installation:**
```bash
pip install tavily-python==0.7.22 pydantic==2.12.5
```

---

## Architecture Patterns

### Recommended Project Structure
```
agent/
├── config.py          # Already exists — add TAVILY_API_KEY field
├── budget.py          # Already exists — unchanged
├── pipeline.py        # Replace stub with real research call
├── research.py        # NEW: ResearchEngine class + multi-query discovery
└── models.py          # NEW: Pydantic schemas for research output
```

### Pattern 1: Multi-Query Autonomous Discovery

**What:** The agent runs a bank of 10–15 targeted search queries against Tavily — one pass for trending niches, one pass per platform for creators — then aggregates and deduplicates results. No seed topics required.

**When to use:** Always. The "fully autonomous" requirement means discovery must emerge from search results, not from hardcoded categories.

**Query bank structure:**
```python
# Source: Tavily SDK docs + verified pattern from product-news-tracker tutorial

NICHE_DISCOVERY_QUERIES = [
    "viral TikTok content trending this week 2026",
    "most viewed YouTube videos this week topics",
    "trending Instagram Reels niche this week",
    "Facebook viral content topics this week",
    "X Twitter trending topics creators this week",
    "social media viral niche content style this week high engagement",
]

CREATOR_DISCOVERY_QUERIES_TEMPLATE = [
    "{niche} TikTok creator 100K followers trending this week",
    "{niche} YouTube creator viral video this week subscribers",
    "{niche} Instagram creator brand deal sponsorship 2026",
]
```

**Two-pass search pattern:**
```python
from tavily import TavilyClient

client = TavilyClient(api_key=config.tavily_api_key)

# Pass 1: Discover trending niches
niche_results = client.search(
    query="viral social media content trending this week high engagement",
    topic="news",
    time_range="week",
    search_depth="basic",
    max_results=10,
)

# Pass 2: Per-niche creator discovery (budget.charge() before each call)
for niche in discovered_niches:
    creator_results = client.search(
        query=f"{niche} creator 100K followers trending this week brand deal",
        topic="general",
        time_range="week",
        search_depth="basic",
        max_results=10,
    )
```

### Pattern 2: LLM-Assisted Structured Extraction

**What:** Pass Tavily result snippets (title + content fields) to Claude with a structured extraction prompt. Claude returns JSON matching the Pydantic schema. This handles the implicit signals (content style, posting frequency) that regex cannot reliably extract.

**When to use:** After each search batch — pass aggregated snippets to Claude once per niche, not per result.

**Example:**
```python
# Source: Anthropic Python SDK + Pydantic v2 pattern

import json
from anthropic import Anthropic
from agent.models import NicheFindings

anthropic_client = Anthropic(api_key=config.anthropic_api_key)

snippets_text = "\n\n".join(
    f"Title: {r['title']}\nContent: {r['content']}"
    for r in search_results["results"]
)

message = anthropic_client.messages.create(
    model="claude-haiku-4-5",  # cheapest, fast for extraction
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": (
            f"Extract structured findings from these search results.\n\n"
            f"{snippets_text}\n\n"
            f"Return JSON matching this schema:\n{NicheFindings.model_json_schema()}\n"
            f"Only return valid JSON, no explanation."
        )
    }]
)

findings = NicheFindings.model_validate_json(message.content[0].text)
```

### Pattern 3: Pydantic v2 Output Schema

**What:** Define the research output schema as Pydantic v2 `BaseModel` subclasses. Use `model_dump_json()` to serialize, `model_validate_json()` to deserialize.

**When to use:** Always — this is the contract between the research engine (Phase 2) and the idea generator (Phase 3).

```python
# agent/models.py
# Source: Pydantic v2 official docs (docs.pydantic.dev/latest/concepts/models/)

from typing import Optional
from pydantic import BaseModel


class CreatorProfile(BaseModel):
    name: str
    platform: str
    follower_count_approx: Optional[str] = None   # e.g. "450K", "1.2M"
    follower_count_numeric: Optional[int] = None   # parsed int for filtering
    content_style: Optional[str] = None            # e.g. "short-form tutorial"
    posting_frequency: Optional[str] = None        # e.g. "daily", "3x/week"
    brand_deal_detected: bool = False
    brand_deal_details: Optional[str] = None       # e.g. "#ad NordVPN"
    source_url: Optional[str] = None


class NicheFindings(BaseModel):
    topic: str
    platform_attribution: str                      # e.g. "TikTok" or "TikTok/Instagram"
    engagement_signal: str                         # why it's trending (views, shares)
    media_type: Optional[str] = None               # "short-form video", "carousel", etc.
    content_style: Optional[str] = None
    posting_frequency: Optional[str] = None
    top_creators: list[CreatorProfile]


class ResearchFindings(BaseModel):
    run_date: str
    niches: list[NicheFindings]
    total_searches: int
    budget_used: int

    def to_json_file(self, path: str) -> None:
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))
```

### Pattern 4: Config Extension

**What:** Add `TAVILY_API_KEY` to `Config.from_env()`. Follow the existing Phase 1 pattern exactly — collect all missing vars before raising, reference `.env.example`.

```python
# Extend agent/config.py — add to required list and dataclass field
required = ["ANTHROPIC_API_KEY", "EMAIL_RECIPIENT", "TAVILY_API_KEY"]

@dataclass
class Config:
    anthropic_api_key: str
    email_recipient: str
    api_call_budget: int
    tavily_api_key: str  # NEW
```

### Pattern 5: Budget Integration

**What:** Tavily basic search = 1 API call. Call `budget.charge(1)` before every `client.search()`. Claude extraction calls = separate `budget.charge(1)` per LLM call.

```python
# In research.py
def _search_with_budget(self, budget: BudgetTracker, **kwargs) -> dict:
    budget.charge(1)  # raises BudgetExceededError before calling API
    return self.client.search(**kwargs)
```

### Anti-Patterns to Avoid

- **One search per creator:** Searching for each creator individually burns budget fast. Batch creator discovery per niche into single queries.
- **Hardcoded platform list in queries:** Don't build separate query banks per platform at the niche discovery stage — let a cross-platform query surface trending topics first, then drill down.
- **Direct regex-only extraction for all fields:** Regex works for follower counts (`r'(\d+\.?\d*)\s*[KkMm]\s*followers?'`) but fails for content style and posting frequency inference. Use LLM for those.
- **Calling `model_validate_json()` without try/except:** Claude sometimes returns malformed JSON. Wrap in try/except `ValidationError` and log the failure — never let a parse failure crash the pipeline.
- **Overusing `search_depth="advanced"`:** Advanced costs 2 credits vs 1 for basic. Use `basic` for discovery passes; reserve `advanced` only if result quality proves insufficient after testing.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Time-bounded web search | Custom scraper with date filtering | Tavily `time_range="week"` | Platform anti-scraping, freshness indexing complexity, maintenance burden |
| Semantic result relevance ranking | TF-IDF or cosine similarity over snippets | Tavily's built-in `score` field + `search_depth="basic"` | Tavily already applies semantic re-ranking; the `score` (0–1) is usable directly |
| Follower count normalization ("450K" → 450000) | Manual string parsing | Simple regex + `int()` conversion (2 lines) | This IS simple enough — do it directly, no library needed |
| LLM output schema enforcement | String parsing + validation logic | Pydantic v2 `model_validate_json()` | Handles nested models, Optional fields, type coercion, and raises clear `ValidationError` |
| API key loading | Custom env parsing | `python-dotenv` already installed + `Config.from_env()` pattern from Phase 1 | Already built, consistent with project pattern |

**Key insight:** The hardest part of this phase is query construction (what to ask) and snippet parsing (what to extract). Both have established patterns — don't reinvent the search relevance layer or the validation layer.

---

## Common Pitfalls

### Pitfall 1: Budget Burn from Too Many Searches
**What goes wrong:** Running 5 platforms × 5 creator queries × per niche = 25+ searches per run, easily blowing a 50-call budget before the LLM synthesis step.
**Why it happens:** It feels natural to query each platform-niche combination separately.
**How to avoid:** Run 5–8 niche discovery queries first, extract top 3–5 niches, then run 1–2 creator queries per niche (not per platform). Budget: ~15 Tavily calls + ~5 Claude calls = 20 total per run.
**Warning signs:** Budget counter reaching 30+ before any Claude calls fire.

### Pitfall 2: Tavily `ValidationError` on `model_validate_json()`
**What goes wrong:** Claude returns JSON with missing required fields or wrong types, crashing the pipeline.
**Why it happens:** LLM output is probabilistic — Claude may omit a field or use a slightly different schema.
**How to avoid:** All fields in `NicheFindings` and `CreatorProfile` that aren't guaranteed should be `Optional[X] = None`. Wrap extraction in try/except `pydantic.ValidationError` — log the raw response and continue with partial results.
**Warning signs:** Pipeline crashes on `model_validate_json()` during testing.

### Pitfall 3: Platform Attribution Ambiguity
**What goes wrong:** Search results about "viral content" often span platforms or don't specify. Forcing a single platform label produces incorrect data.
**Why it happens:** Web articles write "viral this week" without specifying TikTok vs Instagram.
**How to avoid:** Claude's discretion — use a compound attribution string like `"TikTok/Instagram"` when source doesn't disambiguate. `NicheFindings.platform_attribution` is a free-text field, not an enum, for this reason.
**Warning signs:** Claude consistently assigns "unknown" as platform — indicates queries need more platform-specific language.

### Pitfall 4: Stale Results Despite `time_range="week"`
**What goes wrong:** Some Tavily results for trending topics return articles from months ago that happen to mention "this week."
**Why it happens:** Tavily's `time_range` filters by indexed date, not always by article publication date. News topic mode is more reliable.
**How to avoid:** Use `topic="news"` for niche discovery queries — news mode preferentially surfaces recently published articles. Check `published_date` field in results (present when `topic="news"`); filter out results older than 14 days.
**Warning signs:** Research output cites trends from more than 2 weeks ago.

### Pitfall 5: Creator Follower Count Not in Snippet
**What goes wrong:** Tavily snippets frequently don't include follower counts — they're in the platform profile page, not search result excerpts.
**Why it happens:** Web articles about creators often say "popular creator" without quoting follower numbers.
**How to avoid:** Design queries to include the tier signal: `"100K followers TikTok creator trending niche"`. When count is absent, set `follower_count_approx=None` and `follower_count_numeric=None` rather than defaulting to zero. Phase 3 should tolerate missing counts.
**Warning signs:** All `CreatorProfile.follower_count_approx` fields are `None` after extraction.

### Pitfall 6: Same Creator Deduped Incorrectly
**What goes wrong:** "MrBeast" appearing in 3 searches gets included 3 times in the output, inflating apparent creator count.
**Why it happens:** No dedup step between search passes.
**How to avoid:** After extraction, deduplicate `CreatorProfile` by normalized name (lowercased, stripped). Keep the entry with the most complete data. Implement in `research.py` before building `ResearchFindings`.
**Warning signs:** Output JSON has duplicate creator names in a single niche.

---

## Code Examples

### Tavily Basic Search with Time Bound
```python
# Source: github.com/tavily-ai/tavily-python (verified 2026-02-28)
from tavily import TavilyClient

client = TavilyClient(api_key="tvly-YOUR_API_KEY")

response = client.search(
    query="viral TikTok content trending this week high engagement",
    topic="news",
    time_range="week",
    search_depth="basic",
    max_results=10,
)

# Response structure:
# {
#   "query": "...",
#   "results": [
#     {
#       "title": "...",
#       "url": "...",
#       "content": "...",     # AI-extracted relevant snippet
#       "score": 0.95,        # relevance 0-1
#       "published_date": "2026-02-26"  # present when topic="news"
#     }
#   ],
#   "response_time": 1.2
# }
```

### Pydantic v2 Model Validation and Serialization
```python
# Source: docs.pydantic.dev/latest/concepts/models/ (verified 2026-02-28)
from pydantic import BaseModel, ValidationError
from typing import Optional

class CreatorProfile(BaseModel):
    name: str
    platform: str
    follower_count_approx: Optional[str] = None
    brand_deal_detected: bool = False

# Serialize to JSON
profile = CreatorProfile(name="Creator X", platform="TikTok")
print(profile.model_dump_json())
# {"name":"Creator X","platform":"TikTok","follower_count_approx":null,"brand_deal_detected":false}

# Parse from LLM JSON output (with error handling)
try:
    parsed = CreatorProfile.model_validate_json(llm_json_output)
except ValidationError as e:
    logger.warning("Extraction parse failed: %s", e)
    parsed = None
```

### Regex Follower Count Extraction (Fallback)
```python
# Source: Python stdlib re docs (stdlib, no install required)
import re

def parse_follower_count(text: str) -> tuple[str | None, int | None]:
    """Extract follower count like '450K' or '1.2M' from text snippet."""
    pattern = r'(\d+\.?\d*)\s*([KkMm])\s*(?:followers?|subscribers?)?'
    match = re.search(pattern, text)
    if not match:
        return None, None
    num_str, suffix = match.group(1), match.group(2).upper()
    approx = f"{num_str}{suffix}"
    multiplier = 1_000 if suffix == "K" else 1_000_000
    numeric = int(float(num_str) * multiplier)
    return approx, numeric
```

### Budget-Aware Search Wrapper
```python
# Integration pattern using Phase 1 BudgetTracker
from agent.budget import BudgetTracker, BudgetExceededError

class ResearchEngine:
    def __init__(self, tavily_client, anthropic_client, budget: BudgetTracker):
        self.tavily = tavily_client
        self.anthropic = anthropic_client
        self.budget = budget

    def search(self, query: str, **kwargs) -> dict:
        self.budget.charge(1)          # raises before API call if exceeded
        return self.tavily.search(query=query, **kwargs)

    def extract_with_llm(self, snippets: str, schema_json: str) -> str:
        self.budget.charge(1)          # LLM call also costs budget
        response = self.anthropic.messages.create(
            model="claude-haiku-4-5",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"Extract JSON:\n{snippets}\nSchema:\n{schema_json}"}]
        )
        return response.content[0].text
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bing Search API | Bing Search APIs retired | August 2025 | Do not use — Microsoft shut it down |
| Brave free tier (5,000 queries/month) | Brave metered billing ($5/1K) | February 2025 | Brave no longer free for new users; Tavily is the better agent choice anyway |
| Pydantic v1 (`BaseSettings`, `.dict()`) | Pydantic v2 (`BaseModel`, `model_dump()`) | June 2023 | v1 patterns produce deprecation warnings in v2; use `model_dump()` not `.dict()` |
| Raw Anthropic `messages.create()` for structured output | Claude native structured output (`.parse()`) or Instructor library | Late 2025 | Native structured output available on Claude Sonnet/Haiku 4.5+; but for this project the manual JSON prompt + Pydantic validation pattern is sufficient and avoids extra dependencies |

**Deprecated/outdated:**
- `BingSearchAPI`: Retired August 2025 — do not reference
- Pydantic v1 `.dict()` method: Replaced by `.model_dump()` in v2 — using `.dict()` will trigger deprecation warnings
- Tavily `TavilyClient(api_key).get_search_context()`: Older method — use `.search()` with `include_answer` parameter instead

---

## Open Questions

1. **How many Tavily searches fit comfortably within the default budget of 50?**
   - What we know: Default `API_CALL_BUDGET=50` from Phase 1. Each Tavily basic search = 1 credit. Each Claude extraction call = 1 credit.
   - What's unclear: How many niches will be discovered per run, directly affecting search count.
   - Recommendation: Design for 15 Tavily searches + 10 Claude calls = 25 total. This leaves 25 calls as slack. Document the expected call count in `research.py` as a comment.

2. **Will Tavily `topic="news"` consistently surface social media creator content?**
   - What we know: `topic="news"` prefers reputable news sources. Creator/influencer content sometimes appears in entertainment news; sometimes it doesn't.
   - What's unclear: Whether `topic="general"` or `topic="news"` produces higher quality results for "trending creator" queries.
   - Recommendation: Build query execution with both modes and test both during Wave 1 development. Use `topic="news"` for niche discovery, `topic="general"` for creator-specific queries. A/B test and document findings.

3. **Will `REQUIREMENTS.md SYNTH-02` (Pydantic schema validation) be enforced in Phase 2 or Phase 3?**
   - What we know: SYNTH-02 is a v2 requirement assigned to no phase in REQUIREMENTS.md. RSCH-04 requires structured output from Phase 2.
   - What's unclear: Whether Phase 2 should enforce strict Pydantic validation or treat it as aspirational.
   - Recommendation: Implement Pydantic schema in Phase 2 (it's a foundational output contract), but treat validation failures as soft errors (log + continue) rather than hard halts.

---

## Sources

### Primary (HIGH confidence)
- `github.com/tavily-ai/tavily-python` — `search()` method signature, all parameters, `time_range` valid values verified from source code (2026-02-28)
- `docs.tavily.com/sdk/python/reference` — Parameter details, response fields, `topic` and `time_range` documented
- `docs.tavily.com/documentation/api-credits` — Credit costs: basic=1, advanced=2; free tier: 1,000/month, no credit card
- `pypi.org/project/tavily-python/` — Current stable version: 0.7.22 (released 2026-02-26)
- `pypi.org/project/pydantic/` — Current stable version: 2.12.5 (released 2025-11-26)
- `docs.pydantic.dev/latest/concepts/models/` — `BaseModel`, `model_dump_json()`, `model_validate_json()`, nested model patterns
- `brave.com/search/api/` — Pricing ($5/1K requests, $5 monthly credits), freshness parameter (`pw`=7 days), rate limits (50 QPS), no Python SDK
- `api-dashboard.search.brave.com/app/documentation/web-search/get-started` — `freshness` parameter values: `pd/pw/pm/py`, `extra_snippets`, response schema

### Secondary (MEDIUM confidence)
- `data4ai.com/blog/vendors-comparison/brave-vs-tavily/` — Design philosophy comparison, SDK differences, free tier comparison (verified against official docs)
- `docs.tavily.com/examples/quick-tutorials/product-news-tracker` — Dual-query methodology pattern (official Tavily example)
- `implicator.ai` — Brave free tier elimination confirmed February 2025 (consistent with Brave pricing page)
- `firecrawl.dev/blog/top_web_search_api_2025` — Market overview: SerpAPI/Exa/Tavily/Brave comparison

### Tertiary (LOW confidence)
- WebSearch results on "autonomous trending niche discovery query strategy" — no single authoritative source; query patterns derived from synthesis of multiple community articles

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Tavily version and API verified against PyPI + source code; Pydantic version verified against PyPI; Brave pricing verified against official docs
- Architecture: HIGH — Two-pass search pattern verified against official Tavily tutorial; Pydantic patterns verified against official docs; BudgetTracker integration follows established Phase 1 pattern
- Pitfalls: MEDIUM — Most pitfalls are reasoned from API behavior and known LLM extraction challenges; some (e.g., stale results despite `time_range`) are based on general knowledge of search API behavior, not empirically confirmed for Tavily specifically

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (Tavily is actively developed; recheck version before production deploy)
