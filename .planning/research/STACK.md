# Technology Stack

**Project:** Social Media Content Intelligence Agent
**Researched:** 2026-02-28
**Research mode:** Ecosystem (training data only — external verification tools unavailable during this session)

> **Confidence note:** WebSearch, WebFetch, and Context7 tools were unavailable during this research session. All findings derive from training data (knowledge cutoff August 2025). Versions must be verified against current PyPI/npm before use. Flag: LOW confidence on specific version numbers, MEDIUM-HIGH on ecosystem choices and patterns.

---

## Recommended Stack

### Core Language

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.11+ | Primary language | Strong AI/ML ecosystem, native cron support via system scheduler, rich HTTP and email libraries, Claude SDK is Python-first. Prefer 3.12 for performance improvements. |

**NOT Node.js:** While viable, Python has a stronger ecosystem for AI agent work. Claude's Python SDK is more mature. The scientific/data community patterns (which AI research agents draw from) are Python-native. Node.js adds no meaningful benefit here.

---

### LLM / AI Orchestration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `anthropic` (Python SDK) | `>=0.25.0` (verify on PyPI) | Claude API calls for synthesis | Official Anthropic Python client. Direct API access is preferred over LangChain for this use case — the agent is simple enough that an orchestration framework adds indirection without value. |

**Confidence:** MEDIUM (SDK versions change frequently; verify current on pypi.org/project/anthropic)

**NOT LangChain / LlamaIndex:** These frameworks are designed for complex multi-agent pipelines with retrieval chains, memory, and tool-routing. This agent has a single, linear flow: search -> synthesize -> email. Adding LangChain means learning their abstractions and debugging their internals for no added capability. Use the Anthropic SDK directly.

**NOT OpenAI:** Project specifies Claude. Claude 3.5 Sonnet or Claude 3 Haiku are appropriate model choices depending on cost vs. quality tradeoff.

**Model recommendation:** `claude-3-5-sonnet-20241022` for synthesis quality. `claude-3-haiku-20240307` if cost is primary concern. (Verify model availability in Claude API docs — models are updated frequently.)

**Confidence on models:** LOW — model names/versions update frequently, verify at console.anthropic.com before shipping.

---

### Web Search

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Brave Search API | REST (no package needed, use `httpx`) | Discover trending social media content | Independent index (not Google/Bing), fast, low-cost, designed for programmatic use. $3/1000 queries. No OAuth required — API key only. |
| `httpx` | `>=0.27.0` | HTTP client for API calls | Modern async-ready Python HTTP client. Preferred over `requests` for new projects because it supports both sync and async patterns. |

**Alternatives considered:**

| Option | Why Not |
|--------|---------|
| Google Custom Search API | Rate limits are restrictive (100 queries/day free tier), expensive at scale, Google Search API has been inconsistently maintained |
| SerpAPI | Good but adds a paid intermediary layer ($50+/month) — unnecessary when Brave Search API provides direct access at lower cost |
| Tavily Search API | Purpose-built for AI agents, good option, but Brave is cheaper and more flexible for general-purpose search |
| Bing Search API (Azure) | Requires Azure account, corporate pricing, overkill for solo project |
| DuckDuckGo (unofficial) | No official API, unofficial libraries are fragile and Terms-of-Service-risky |

**Confidence:** MEDIUM — Brave Search API is well-established. Tavily is also a strong choice if you want an AI-optimized search API that returns cleaner results; evaluate both. Verify current pricing before committing.

**Alternative worth evaluating:** Tavily (`tavily-python`) is specifically designed for AI research agents and may produce higher-quality summaries. Use Brave if you want raw search results to process yourself; use Tavily if you want pre-processed content. For this project, Brave + Claude synthesis is preferred — keeps Claude in the synthesis role.

---

### Scheduling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| System cron (crontab) | OS-native | Weekly trigger | For a solo, single-server application running on a fixed schedule, system cron is the simplest and most reliable scheduler. No dependencies, no process management overhead, no in-process scheduler to crash. A Python script that runs via `cron` once per week and then exits is architecturally clean. |

**Cron entry example:**
```
0 8 * * 1  /path/to/venv/bin/python /path/to/agent/main.py >> /path/to/logs/agent.log 2>&1
```
(Runs every Monday at 8:00 AM)

**NOT APScheduler / Celery / Airflow:**

| Option | Why Not |
|--------|---------|
| APScheduler | Adds in-process scheduling complexity. Requires a long-running process. For one job per week, system cron is far simpler. |
| Celery | Requires Redis/RabbitMQ broker. Massive overkill for a single weekly job. |
| Airflow | ETL orchestration framework. Correct tool for data pipelines with many dependent tasks. Wrong tool for a simple weekly script. |
| GitHub Actions scheduled workflows | Valid alternative for zero-infrastructure use — run the agent as a GitHub Action on a schedule. Free tier may cover this use case. Worth evaluating as an alternative to hosting the script on a server. |

**Confidence:** HIGH — System cron for simple periodic tasks is a well-established, stable pattern.

**Alternative worth evaluating:** GitHub Actions with `schedule:` trigger. Eliminates need for a dedicated server entirely. The agent runs in a GitHub Actions runner, which is free for public repos and has a generous free tier for private repos. This is increasingly common for lightweight automation agents in 2025/2026.

---

### Email Delivery

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `resend` Python SDK | `>=2.0.0` (verify PyPI) | Transactional email delivery | Resend is the modern default for developer-friendly transactional email. Clean API, generous free tier (100 emails/day), excellent deliverability, no complex SMTP setup. For a single weekly email, this is the right tool. |

**Confidence:** MEDIUM — Resend has grown significantly in 2024/2025. Verify current Python SDK version on PyPI.

**Alternatives considered:**

| Option | Why Not |
|--------|---------|
| SendGrid | More established but heavier API, free tier has been reduced, more complex setup for simple use cases. Overkill for one email/week. |
| Mailgun | Valid alternative to Resend. More established but older API design. Resend has better DX for Python developers. |
| AWS SES | Very cheap at scale but requires AWS account, IAM setup, domain verification. Significant infrastructure overhead for one email/week. |
| SMTP (smtplib) | Built into Python standard library. Works, but deliverability is poor without proper SPF/DKIM setup. Gmail SMTP limits make this unreliable. Avoid for production. |
| Postmark | Excellent deliverability, but pricing starts higher than Resend for low-volume use. |

**Alternative worth considering:** If you already have a SendGrid or Mailgun account, use that instead of adding Resend. The switching cost is low. Resend is the recommendation for greenfield because of DX quality and free tier.

---

### Data Storage

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| None (stateless design) | — | — | The v1 agent does not need persistent storage. Each weekly run is independent: search, synthesize, send, exit. No database required. |
| Plain-text log files | OS-native | Run history / debugging | Log each run's output to a timestamped file. Simple, inspectable, zero-overhead. |

**If state becomes needed (future):**

| Option | When to Add | Why |
|--------|-------------|-----|
| SQLite (via `sqlite3` stdlib or `aiosqlite`) | When you need to deduplicate topics across weeks | Zero-infrastructure, file-based, Python-native. Correct first step before any cloud DB. |
| JSON flat files | When you need to cache search results between runs | Even simpler than SQLite. Serialize results as JSON, load on next run. |

**NOT PostgreSQL / Redis / MongoDB:** Databases with servers are architectural overkill for a script that runs once per week. Add infrastructure only when a flat file or SQLite genuinely cannot solve the problem.

**Confidence:** HIGH — Stateless design for v1 is the correct call. The PROJECT.md constraints confirm no persistence requirement for initial version.

---

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `python-dotenv` | `>=1.0.0` | Load env vars from `.env` file | Store API keys (Anthropic, Brave, Resend) in `.env`, not hardcoded. Always use this. |
| `pydantic` | `>=2.5.0` | Data validation / typed config | Define strongly-typed config objects and validate LLM output structure. Pydantic v2 is substantially faster than v1. |
| `jinja2` | `>=3.1.0` | HTML email templating | Render the weekly report as clean HTML email. Much cleaner than f-string concatenation for multi-section reports. |
| `tenacity` | `>=8.2.0` | Retry logic with backoff | Wrap API calls (search, Claude) with exponential backoff retries. Essential for production reliability. |
| `loguru` | `>=0.7.0` | Structured logging | Better default than stdlib `logging`. Simple to set up, outputs to file and stdout, handles log rotation. |

**Confidence on libraries:** MEDIUM — These are well-established libraries, versions may have incremented. Verify on PyPI.

---

## Environment / Infrastructure

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Python version manager | `pyenv` | Manage Python versions without system pollution |
| Dependency management | `uv` (preferred) or `pip` + `requirements.txt` | `uv` is the 2025 standard for fast Python package management, drops in as pip replacement |
| Environment isolation | Python virtualenv (via `uv venv`) | Standard isolation for the project |
| Secrets management | `.env` file + `python-dotenv` | Sufficient for solo project; never commit `.env` to git |
| Hosting | Local machine cron OR GitHub Actions | Local is simplest; GitHub Actions eliminates server requirement entirely |

**On `uv`:** `uv` (from Astral, same team as `ruff`) is the current best-practice Python package manager as of 2025. It replaces pip, pip-tools, and virtualenv with a single fast tool. If unfamiliar, `pip` + `requirements.txt` works fine — but `uv` is worth learning for any new Python project.

**Confidence on `uv`:** MEDIUM-HIGH — `uv` was well-established by mid-2025 with strong community adoption. Verify it's still the current recommendation.

---

## Complete Dependency List

```toml
# pyproject.toml (if using uv)
[project]
name = "social-media-intelligence-agent"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "anthropic>=0.25.0",       # Claude API — VERIFY version on PyPI
    "httpx>=0.27.0",           # HTTP client for Brave Search API
    "resend>=2.0.0",           # Email delivery — VERIFY version on PyPI
    "python-dotenv>=1.0.0",    # Environment variable management
    "pydantic>=2.5.0",         # Data validation and typed config
    "jinja2>=3.1.0",           # HTML email templating
    "tenacity>=8.2.0",         # Retry logic with backoff
    "loguru>=0.7.0",           # Structured logging
]
```

```bash
# Or with pip
pip install anthropic httpx resend python-dotenv pydantic jinja2 tenacity loguru
```

---

## Alternatives Considered: Language Choice

| Language | Verdict | Reason |
|----------|---------|--------|
| Python | RECOMMENDED | First-class AI ecosystem, Claude SDK is Python-first, strong HTTP/email libraries, large community for agent patterns |
| Node.js / TypeScript | Valid alternative | Claude also has a Node.js SDK. Choose if the team is more comfortable with TypeScript. No ecosystem advantage over Python for this use case. |
| Go | Not recommended for v1 | Faster execution, but no advantage for a script that runs once per week. Smaller AI tooling ecosystem. |

---

## Sources

- Project context: `/Users/chivonpowers/gsd-test-project/.planning/PROJECT.md`
- Training data (knowledge cutoff August 2025) — external verification tools unavailable during this session
- **Action required before implementation:** Verify all package versions on pypi.org and official docs. Verify Claude model availability at console.anthropic.com. Verify Brave Search API pricing at brave.com/search/api/. Verify Resend pricing at resend.com.

### Confidence Summary

| Area | Confidence | Notes |
|------|------------|-------|
| Language (Python) | HIGH | Well-established for AI agent work |
| LLM SDK (anthropic) | MEDIUM | Package exists and is maintained; version needs PyPI verification |
| Web Search (Brave API) | MEDIUM | Solid choice; Tavily is valid alternative |
| Scheduling (system cron) | HIGH | Stable OS primitive; GitHub Actions is strong alternative |
| Email (Resend) | MEDIUM | Strong DX choice; verify current SDK version |
| Storage (stateless) | HIGH | Correct for v1 per project constraints |
| Supporting libraries | MEDIUM | All are active; versions need PyPI verification |
| `uv` package manager | MEDIUM-HIGH | Was standard by mid-2025; verify still current |
