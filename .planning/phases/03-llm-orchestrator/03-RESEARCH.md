# Phase 3: LLM Orchestrator — Research

**Phase:** 3 — LLM Orchestrator
**Goal:** Agent converts raw research findings into 5–10 specific, evidence-grounded content ideas
**Written:** 2026-03-02

---

## RESEARCH COMPLETE

---

## 1. What Phase 3 Must Build

Phase 3 adds a synthesis layer between the research engine (Phase 2) and the email report (Phase 4). It reads `research_output.json` (a `ResearchFindings` object) and produces a list of `ContentIdea` objects, each containing:

- A **topic** (the niche/subject area)
- An **angle** (title-level hook, e.g., "Why 80% of TikTok creators are using the wrong hook format")
- **2–3 bullet talking points** (what you'd actually cover — not meta-notes)
- A **rationale** citing creator name + platform + metric, with "this week" / "recently" language
- Optional: **platform** (include only when research clearly points to one)
- Optional: **content_format** (include only when research surfaced a clear format signal)

Requirements IDEA-01 and IDEA-02 from REQUIREMENTS.md must be satisfied.

---

## 2. Existing Codebase — Integration Points

### `agent/models.py`
- `ResearchFindings` — the input; loaded via `ResearchFindings.from_json_file("research_output.json")`
- `NicheFindings` — per-niche data with `topic`, `platform_attribution`, `engagement_signal`, `top_creators`, `content_style`, `posting_frequency`, `media_type`
- `CreatorProfile` — `name`, `platform`, `follower_count_approx`, `brand_deal_detected`

### `agent/pipeline.py`
- Currently ends after writing `research_output.json`
- Phase 3 adds a synthesis step after research completes

### `agent/config.py`
- Budget is initialized from `API_CALL_BUDGET` env var (default 50)
- Phase 2 uses ~25 calls; 25 remain for synthesis

### `agent/budget.py`
- `BudgetTracker.charge(1)` called before every LLM call — same pattern required in synthesizer

---

## 3. ContentIdea Schema Design

New Pydantic v2 model in `agent/models.py`:

```python
class ContentIdea(BaseModel):
    topic: str                          # niche/subject (e.g., "skincare routines")
    angle: str                          # title-level hook — the specific framing
    talking_points: list[str]           # 2-3 bullets of actual content to cover
    rationale: str                      # creator + platform + metric + "this week"
    platform: Optional[str] = None      # include only when clearly supported
    content_format: Optional[str] = None # include only when research surfaced signal
```

`IdeaReport` wraps the list for serialization:

```python
class IdeaReport(BaseModel):
    run_date: str
    ideas: list[ContentIdea]
    niches_processed: int
    ideas_generated: int
    budget_used: int

    def to_json_file(self, path: str) -> None: ...
    @classmethod
    def from_json_file(cls, path: str) -> "IdeaReport": ...
```

---

## 4. Anthropic Structured Output — Tool Use Approach

The Anthropic Python SDK (`anthropic>=0.40.0`) supports structured output via **tool use**. This is the most reliable way to get JSON that validates against a schema.

### Approach: Tool use with JSON schema

```python
tools = [{
    "name": "generate_content_ideas",
    "description": "Generate content ideas from research findings",
    "input_schema": IdeaReport.model_json_schema()
}]

message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=4096,
    tools=tools,
    tool_choice={"type": "auto"},
    messages=[{"role": "user", "content": prompt}]
)

# Extract tool use block
for block in message.content:
    if block.type == "tool_use":
        return block.input  # already a dict
```

**Alternative (simpler):** Instruct JSON output + `json.loads()` + `model_validate()` with retry — same pattern as `_extract_with_llm()` in Phase 2. This is simpler and already battle-tested in the codebase.

**Recommendation:** Use the JSON instruction approach (matching existing `_extract_with_llm()` pattern) for consistency, with Pydantic `model_validate()` + retry on `ValidationError`. Tool use is more complex and adds schema generation overhead.

---

## 5. Multi-Pass vs. Single-Pass Synthesis

### Context says: Claude's discretion on prompt structure

**Option A: Single prompt — all niches in one call**
- Prompt includes all `NicheFindings` serialized as JSON
- Claude generates all 5–10 ideas in one response
- Pros: 1 LLM call, lowest budget; global deduplication (no repeated creators) is natural
- Cons: Large prompt for many niches; harder to enforce per-niche evidence isolation

**Option B: One call per niche — aggregate ideas**
- One LLM call per niche → 1–2 ideas per niche
- Aggregate and trim to 5–10 total
- Pros: Focused evidence per niche, easier citation enforcement
- Cons: N LLM calls (5+ niches × 1 call = 5+ calls); cross-niche deduplication must be post-process

**Option C: Two-pass (extract signals → generate ideas)**
- Pass 1: Extract trend/creator signals from all niches (1 call)
- Pass 2: Generate ideas from extracted signals (1 call)
- Pros: Cleaner separation of concerns
- Cons: 2 calls minimum, intermediate state to manage

**Recommendation: Option A (single prompt, all niches)**
- Keeps synthesis within budget (1–2 calls total vs. 5–10)
- Niches already structured — easy to serialize as context
- Global deduplication (each idea cites different evidence) is natural when all niches are visible at once
- Matches the "one LLM call per niche (batch efficiency)" decision already made in Phase 2

---

## 6. Prompt Design — Synthesis

The synthesis prompt must enforce all CONTEXT.md decisions:

```
You are a content strategy analyst generating weekly content briefings for social media creators.

Below is this week's research data: trending niches and top-performing creators discovered via live web search.

Generate {MIN}–{MAX} content ideas. For each idea:
- topic: the niche/subject area
- angle: a specific title-level hook (e.g., "Why 80% of TikTok creators use the wrong hook format") — NOT a format recommendation
- talking_points: exactly 2-3 bullets covering what you'd actually say in the content
- rationale: cite [Creator name] ([follower count], [platform]) [did something] this week/recently — specific numbers only, no explanation of why it works
- platform: include ONLY if research clearly points to one platform
- content_format: include ONLY if research surfaced a clear format signal (e.g., "short-form video dominates")

Rules:
- Each idea MUST cite different creators — never repeat the same creator across ideas
- Rationale must contain "this week" or "recently"
- Do NOT generate ideas without a named creator citation
- Return ONLY valid JSON. No markdown, no explanation.

RESEARCH DATA:
{serialized_niches}

Return JSON matching this schema:
{idea_report_schema}
```

---

## 7. Thin Research Handling (from CONTEXT.md)

| Condition | Action |
|-----------|--------|
| Niche has no named creators (all names are article titles / "Unknown") | Skip that niche — do not generate idea |
| Fewer than 5 ideas available after processing all niches | Still produce and deliver the report |
| Empty research (zero niches in ResearchFindings) | Halt with logged error — do not generate from Claude's general knowledge |

**Detection heuristic for "no named creators":**
- Creator name is a URL fragment, article title (contains ":", "|", "–", starts with "How", "The", "Why", "Top"), or "Unknown"
- Platform is "unknown" and follower_count_approx is None

---

## 8. Retry Logic

After the LLM call, validate the response with `IdeaReport.model_validate()`. On `ValidationError`:
1. Retry once with a clarification prompt ("Your previous response had validation errors: {errors}. Please fix and return only valid JSON.")
2. If second attempt also fails: log error and return partial results (whatever passed validation) or empty `IdeaReport`

Max 2 attempts per synthesis run. Budget: 2 LLM calls for synthesis (matches 25-call slack from Phase 2).

---

## 9. Budget Accounting

| Phase | Target | Slack |
|-------|--------|-------|
| Phase 2 (Research) | ~25 calls | 25 remaining |
| Phase 3 (Synthesis) | 1–2 calls | 23+ remaining for Phase 4 |

Synthesis stays well within budget. `budget.charge(1)` called before each LLM call.

---

## 10. File Structure for Phase 3

New files:
- `agent/synthesizer.py` — `IdeaSynthesizer` class (analogous to `ResearchEngine`)

Modified files:
- `agent/models.py` — Add `ContentIdea`, `IdeaReport` Pydantic models
- `agent/pipeline.py` — Add synthesis step after research, write `ideas_output.json`

Output file:
- `ideas_output.json` — gitignored (same as `research_output.json`); `IdeaReport.to_json_file()`

---

## 11. IdeaSynthesizer Class Design

```python
class IdeaSynthesizer:
    def __init__(self, anthropic_client: Anthropic, budget: BudgetTracker) -> None:
        self.anthropic = anthropic_client
        self.budget = budget

    def run(self, findings: ResearchFindings, dry_run: bool = False) -> IdeaReport:
        """
        Synthesize ResearchFindings into ContentIdeas.
        dry_run=True returns a stub IdeaReport without API calls.
        """
        if dry_run:
            return IdeaReport(...)

        # Filter thin niches (no named creators)
        valid_niches = self._filter_valid_niches(findings.niches)

        if not valid_niches:
            logger.error("No valid niches with named creators — cannot synthesize ideas")
            raise ValueError("No valid research data for synthesis")

        return self._synthesize(valid_niches)

    def _filter_valid_niches(self, niches: list[NicheFindings]) -> list[NicheFindings]:
        """Skip niches where all creator names look like article titles."""
        ...

    def _synthesize(self, niches: list[NicheFindings]) -> IdeaReport:
        """Single-pass synthesis: all niches in one LLM call with retry."""
        ...
```

---

## 12. Pipeline Integration

```python
# pipeline.py — after research step
synthesizer = IdeaSynthesizer(anthropic_client=anthropic_client, budget=budget)
idea_report = synthesizer.run(findings, dry_run=dry_run)
idea_report.to_json_file("ideas_output.json")
logger.info("Synthesis complete: %d ideas generated", len(idea_report.ideas))
```

The `pipeline.py` already imports `Anthropic` (passed to `ResearchEngine`) — same client reused for synthesis.

---

## 13. Known Risks

| Risk | Mitigation |
|------|-----------|
| Phase 2 heuristic fallback produces no named creators | `_filter_valid_niches()` detects and skips; raise error if zero valid niches |
| Claude wraps JSON in markdown code fences | Strip ` ``` ` fences (same logic as `_extract_with_llm()`) |
| LLM repeats same creator across ideas | Enforce uniqueness via post-processing + prompt instruction |
| `model_validate()` fails on partial response | Retry once with validation error details; fall back to empty report |
| Budget exceeded before synthesis | `BudgetExceededError` propagates up — pipeline logs and exits cleanly |

---

## 14. Requirements Coverage

| Req ID | Requirement | How Phase 3 Addresses It |
|--------|-------------|--------------------------|
| IDEA-01 | Agent produces 5–10 content ideas per run, each with a specific angle grounded in research | `IdeaSynthesizer.run()` → `IdeaReport` with 5–10 `ContentIdea` objects; angle field enforced by Pydantic schema |
| IDEA-02 | Each idea cites real creator evidence from this week's research | Rationale field required; synthesis prompt enforces "this week"/"recently" + creator name + metric; thin niche skipping ensures no fabricated citations |
