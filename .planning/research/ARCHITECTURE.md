# Architecture Patterns

**Domain:** Scheduled AI Research Agent (Web Search + LLM Synthesis + Email Delivery)
**Researched:** 2026-02-28
**Confidence:** MEDIUM — Based on established patterns from training data (cutoff August 2025). External verification tools were unavailable during this research session. Patterns reflect the dominant approach in production AI agent systems as of mid-2025.

---

## Recommended Architecture

A scheduled AI research agent is a linear pipeline with five discrete layers: Scheduler, Research Engine, LLM Orchestrator, Report Builder, and Delivery. Data flows in one direction from trigger to inbox. There is no feedback loop in v1.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          SYSTEM BOUNDARY                                │
│                                                                         │
│  ┌───────────────┐                                                       │
│  │   Scheduler   │  (cron / cloud scheduler)                            │
│  │  [TRIGGER]    │                                                       │
│  └───────┬───────┘                                                       │
│          │ fires weekly                                                  │
│          ▼                                                               │
│  ┌───────────────────────────────┐                                       │
│  │      Research Engine          │                                       │
│  │  [GATHER]                     │                                       │
│  │  - Trend discovery queries    │                                       │
│  │  - Creator research queries   │                                       │
│  │  - Web search tool calls      │                                       │
│  │  - Raw result collection      │                                       │
│  └───────────────┬───────────────┘                                       │
│                  │ raw search results (structured JSON)                  │
│                  ▼                                                        │
│  ┌───────────────────────────────┐                                       │
│  │      LLM Orchestrator         │                                       │
│  │  [SYNTHESIZE]                 │                                       │
│  │  - Trend analysis pass        │                                       │
│  │  - Creator signal extraction  │                                       │
│  │  - Idea generation pass       │                                       │
│  │  - Rationale enrichment       │                                       │
│  └───────────────┬───────────────┘                                       │
│                  │ structured ideas + analysis (JSON)                    │
│                  ▼                                                        │
│  ┌───────────────────────────────┐                                       │
│  │      Report Builder           │                                       │
│  │  [FORMAT]                     │                                       │
│  │  - Template rendering         │                                       │
│  │  - HTML / plain text email    │                                       │
│  │  - Subject line generation    │                                       │
│  └───────────────┬───────────────┘                                       │
│                  │ formatted email (HTML string)                         │
│                  ▼                                                        │
│  ┌───────────────────────────────┐                                       │
│  │      Email Sender             │                                       │
│  │  [DELIVER]                    │                                       │
│  │  - API call to email service  │                                       │
│  │  - Delivery confirmation      │                                       │
│  │  - Error handling / retry     │                                       │
│  └───────────────────────────────┘                                       │
│                                                                         │
│  ┌───────────────────────────────┐                                       │
│  │  Config + State Store         │  (cross-cutting concern)             │
│  │  - API keys                   │                                       │
│  │  - Prompt templates           │                                       │
│  │  - Run logs / last-run state  │                                       │
│  └───────────────────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

| Component | Responsibility | Accepts | Produces | Communicates With |
|-----------|---------------|---------|----------|-------------------|
| Scheduler | Fires the pipeline on a fixed weekly cadence | Time signal (cron) | Execution trigger | Research Engine |
| Research Engine | Issues web search queries, collects raw results | Trigger + config | Raw search results (JSON) | LLM Orchestrator, Web Search API |
| LLM Orchestrator | Synthesizes raw data into structured insights and ideas | Raw search results | Structured ideas + trend analysis (JSON) | Research Engine (receives), Report Builder (sends), LLM API |
| Report Builder | Renders structured data into a formatted email | Structured ideas JSON | HTML + plain text email body | LLM Orchestrator (receives), Email Sender (sends) |
| Email Sender | Delivers the formatted email to the recipient | Email body + metadata | Delivery confirmation / error | Email service API |
| Config + State Store | Provides API keys, prompts, recipient address; logs run history | Any component (read) | Config values, run log entries | All components |

---

## Data Flow

Data flows linearly in one direction. No component writes back to an upstream component in v1.

### Stage 1: Trigger

The scheduler fires once per week (Monday morning). It invokes the pipeline entry point — this is the only external trigger in the system. No user interaction required after setup.

### Stage 2: Research (Web Search → Raw Results)

The Research Engine issues a predetermined battery of search queries designed to surface:
- Trending niches and topics across social media
- Top-performing creators as profitability proxies
- Platform-specific engagement signals (TikTok, YouTube, Facebook, Instagram)

Each query returns a set of web results (titles, URLs, snippets). These are assembled into a raw results payload — a structured JSON object grouping results by query intent (trend discovery vs. creator analysis).

**Key design decision:** Queries are generated by the LLM in a preceding step or hardcoded as prompt-driven templates. Avoid purely hardcoded queries — the LLM can generate better, context-aware queries than static strings.

```
{
  "trend_results": [...],       // results from trend discovery queries
  "creator_results": [...],     // results from creator research queries
  "run_timestamp": "ISO8601",
  "query_count": 12
}
```

### Stage 3: Synthesis (Raw Results → Structured Ideas)

The LLM Orchestrator processes raw results in 2–3 sequential LLM passes to avoid overloading a single prompt:

**Pass 1 — Trend Extraction:** Given trend results, identify 5–8 niches or topics currently gaining momentum. Extract signals (what's growing, why, on which platforms).

**Pass 2 — Creator Signal Extraction:** Given creator results per trend, identify patterns (content style, posting frequency, media type, brand deal signals). Do not enumerate individual creators — extract the pattern.

**Pass 3 — Idea Generation:** Given the trend + creator signal data, generate 5–10 actionable content ideas. Each idea: topic, angle, data-backed rationale ("why this is working right now").

Output is a structured JSON payload:

```
{
  "trends": [
    {
      "niche": "string",
      "momentum_signal": "string",
      "platform_focus": ["TikTok", "YouTube"],
      "creator_pattern": "string"
    }
  ],
  "ideas": [
    {
      "topic": "string",
      "angle": "string",
      "rationale": "string",
      "platform_fit": ["TikTok"],
      "confidence": "high|medium|low"
    }
  ]
}
```

### Stage 4: Formatting (Structured Ideas → Email Body)

The Report Builder takes the structured ideas JSON and renders it into an email. This is a pure formatting step — no additional LLM calls unless the subject line requires one. Use a Jinja2-style template (or equivalent) to produce consistent HTML output each week.

The report has two sections:
1. Trend Analysis — what's moving and why
2. Content Ideas — the 5–10 actionable ideas with rationale

### Stage 5: Delivery (Email Body → Inbox)

The Email Sender calls the chosen email service API (SendGrid, Resend, or similar), passes the rendered HTML + plain text fallback, and records the delivery result in the state store.

---

## Patterns to Follow

### Pattern 1: Multi-Pass LLM Synthesis

**What:** Break synthesis into sequential LLM calls with focused prompts rather than one giant prompt.

**When:** Any time a single prompt would need to process more than ~10 search results AND produce structured output.

**Why:** Single large prompts with mixed tasks produce lower quality output and are harder to debug. Separate passes allow you to inspect intermediate state and retry failed steps without re-running the whole pipeline.

```python
# Example: two-pass synthesis
trend_data = llm.invoke(trend_extraction_prompt(raw_results))
ideas = llm.invoke(idea_generation_prompt(trend_data))
```

### Pattern 2: Structured Output at Every Boundary

**What:** Every component handoff uses JSON (not raw text). LLM outputs are parsed to JSON before being passed downstream.

**When:** Always — between every component.

**Why:** Prevents downstream parsing failures. Allows each stage to be unit-tested independently. Makes debugging trivial (you can inspect the JSON at any stage).

Use Pydantic models (Python) or Zod schemas (TypeScript) to validate LLM output at each boundary. If validation fails, retry the LLM call with a corrective prompt before failing the run.

### Pattern 3: Stateless Pipeline, Stateful Log

**What:** The pipeline itself holds no state between runs. The state store logs each run result (timestamp, success/failure, ideas generated, email sent).

**When:** Always for scheduled agents.

**Why:** Stateless pipelines are easier to test, restart, and debug. The log provides audit trail and enables future features (deduplication, trend continuity across weeks) without refactoring the pipeline itself.

### Pattern 4: Fail-Safe Email Delivery

**What:** Email delivery is always the last step. If synthesis fails, do not attempt delivery. If delivery fails, log the failure and retain the formatted email for retry.

**When:** All scheduled agents with email delivery.

**Why:** A blank email or error email reaching the inbox destroys trust in the system. Better to silently retry than to deliver garbage.

### Pattern 5: Query Battery Design

**What:** The Research Engine issues a structured battery of queries (not one query). Divide queries into two types: discovery queries (what's trending?) and depth queries (who's winning in this niche?).

**When:** Web research agents covering broad domains (social media trends).

**Why:** A single query cannot surface both trend breadth and creator depth. Discovery queries find niches; depth queries research those niches. The LLM's trend extraction output can seed the depth queries dynamically.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: One Giant Prompt

**What:** A single LLM call that receives all raw search results and outputs a finished email.

**Why bad:** Context window limitations reduce quality on large inputs. Impossible to debug which step failed. Cannot retry partial failures. Output quality degrades significantly with mixed task instructions.

**Instead:** Multi-pass synthesis (see Pattern 1). Each pass has one job.

### Anti-Pattern 2: Raw Text Handoffs Between Components

**What:** Passing LLM response text directly to the next component without parsing.

**Why bad:** One malformed sentence in LLM output breaks the downstream component. Brittle string parsing is a maintenance nightmare.

**Instead:** Parse to JSON at each boundary. Validate with a schema. Retry on validation failure.

### Anti-Pattern 3: Hardcoded Search Queries

**What:** A static list of search strings that never changes.

**Why bad:** Social media trends shift weekly. Static queries become stale within a month. The agent's value proposition (autonomous discovery) is undermined.

**Instead:** Use a two-phase approach: start with broad discovery queries (which can be semi-static), then use the LLM to generate tailored depth queries based on what the discovery phase surfaced.

### Anti-Pattern 4: Synchronous Blocking Architecture

**What:** Running all web searches sequentially, waiting for each before issuing the next.

**Why bad:** If you run 12 queries sequentially at 1–2 seconds each, the pipeline takes 12–24 seconds just for search. This compounds with LLM latency.

**Instead:** Run web search queries concurrently (asyncio in Python, Promise.all in Node.js). Search queries within the same phase have no dependencies on each other.

### Anti-Pattern 5: Embedding Config in Code

**What:** API keys, recipient email, prompt templates, and query lists hardcoded in source files.

**Why bad:** Secrets in source code is a security risk. Changing the recipient email requires a code deployment. Prompt iteration requires code changes.

**Instead:** All config in environment variables or a config file excluded from version control. Prompt templates in separate files that can be edited without touching pipeline logic.

---

## Suggested Build Order

Build order is determined by data flow direction: you cannot test a downstream component until its upstream dependency exists.

### Layer 1: Config + State Store (build first)
Every other component needs config (API keys, prompts, recipient). Build the config loader first so all subsequent components can read from it.
- Environment variable loading
- Config schema definition
- Run log structure (even if it writes to a simple JSON file initially)

### Layer 2: Web Search Integration (build second)
The Research Engine needs a working search tool before anything else can be tested end-to-end. Build and validate the search integration in isolation before wiring it to the LLM.
- Choose and configure search API (Brave Search, Serper, Tavily)
- Implement query execution
- Validate raw result structure

### Layer 3: LLM Orchestrator (build third)
With real search results available, build the synthesis passes. Test each LLM pass independently with saved fixture data (sample search results) so you don't burn API credits on every iteration.
- Trend extraction pass
- Creator signal extraction pass
- Idea generation pass
- Structured output validation (Pydantic / Zod)

### Layer 4: Report Builder (build fourth)
With structured ideas JSON available, build the email renderer. This can be developed with fixture JSON without needing live LLM calls.
- Email template (HTML + plain text)
- Template rendering logic
- Subject line

### Layer 5: Email Sender (build fifth)
Wire up the email delivery. Test with a real email address (your own inbox) before pointing at the production recipient.
- Email service integration
- Send call implementation
- Delivery confirmation handling

### Layer 6: Scheduler (build last)
Wire everything together under a scheduler only after all components work in isolation. The scheduler is the simplest layer — it just invokes the pipeline entry point. The complexity is in the pipeline, not the scheduler.
- Choose scheduler mechanism (cron, cloud scheduler)
- Implement pipeline entry point function
- End-to-end test run

### Layer 7: Hardening (after first successful run)
- Retry logic for LLM failures
- Retry logic for search failures
- Retry logic for email delivery failures
- Run logging with success/failure status
- Error alerting (email yourself on failure)

---

## LLM Orchestration Layer Detail

The LLM Orchestrator is the core intelligence of the system. It warrants more detail on internal structure.

### Prompt Architecture

Each LLM pass has three components:
1. **System prompt** — defines the LLM's role and output format for this pass
2. **Context prompt** — injects the input data for this pass (search results or prior pass output)
3. **Instruction prompt** — specifies the exact task and constraints

Keep system prompts stable. Keep context and instruction prompts parameterized. This separation makes prompt iteration fast — you can change instructions without touching system role definitions.

### Output Validation Loop

Every LLM call should include a validation-and-retry loop:

```
call LLM
parse response to JSON
validate against schema
  if valid → pass to next stage
  if invalid → retry with corrective prompt (max 2 retries)
  if still invalid after retries → log failure, abort run
```

This prevents a single malformed LLM response from silently corrupting the rest of the pipeline.

### Token Budget Management

The LLM Orchestrator must manage token usage across passes:
- Trend extraction: receives raw search snippets (can be verbose)
- Idea generation: receives compressed trend/creator summary (must be tighter)

Summarize or truncate raw search results before passing them to the LLM. Search snippet text can be aggressively truncated (first 200 characters of each snippet is usually sufficient). The LLM does not need full web page content — it needs enough signal to identify patterns.

---

## Scalability Considerations

| Concern | At v1 (solo creator) | At v2 (small team) | At v3 (SaaS) |
|---------|----------------------|---------------------|---------------|
| Scheduling | Single cron job | Multiple cron schedules per user | Queue-based job system (BullMQ, Celery) |
| Research | Sequential query battery | Concurrent query execution | Distributed web scraping workers |
| LLM calls | Direct API calls | Direct API calls | Rate-limit aware queue, cost tracking per user |
| Storage | JSON file or SQLite | Postgres | Postgres with multi-tenant isolation |
| Email delivery | Single recipient | Per-user recipient | Transactional email with templating service |
| Observability | Console logs | Structured logs | Distributed tracing, per-run dashboards |

v1 does not need to solve for any of these. Design component boundaries so that swapping the implementation of one layer (e.g., SQLite → Postgres) does not require changes in other layers.

---

## Technology Fit Notes

These are architecture-level technology observations. Full technology decisions are in STACK.md.

- **Python is the natural fit** for this architecture: asyncio for concurrent web search, Pydantic for structured LLM output validation, mature LLM SDK ecosystem (Anthropic, OpenAI clients), and strong scheduler libraries (APScheduler, or plain cron).
- **The LLM call is the longest-latency operation** in the pipeline (~2–10 seconds per call). With 3 passes, expect 6–30 seconds of LLM time per run. This is acceptable for a weekly background job.
- **Web search is the least reliable component** — rate limits, CAPTCHA, and API changes are common failure modes. Abstract the search tool behind an interface so the provider can be swapped without touching the rest of the pipeline.
- **Email delivery is the most consequential operation** — a failed or malformed email is visible to the user. Test this layer most thoroughly.

---

## Sources

- Architecture patterns synthesized from training data (knowledge cutoff August 2025). External search and documentation tools were unavailable during this research session.
- Confidence: MEDIUM. These patterns are stable and well-established in the AI agent ecosystem as of mid-2025. Core data flow and component boundary decisions are unlikely to have changed significantly.
- Specific technology version recommendations: see STACK.md (to be written with external source verification if tools become available).
