# Domain Pitfalls

**Domain:** Scheduled AI research agent — LLM + web search + email delivery
**Researched:** 2026-02-28
**Confidence Note:** Web search and WebFetch tools were unavailable during this research session. All findings are drawn from training knowledge (cutoff August 2025) about LLM agent systems, web search API behavior, email deliverability, and scheduled automation production failures. Confidence is noted per section; claims about specific API behavior should be verified against current documentation before implementation.

---

## Critical Pitfalls

Mistakes that cause rewrites, silent failures, or completely useless reports.

---

### Pitfall 1: Prompt Brittleness — The Agent Produces Confident-Sounding Garbage

**What goes wrong:** The LLM synthesizes web search results into plausible-sounding content ideas that are not actually grounded in current evidence. The agent hallucinates trend rationale, attributes engagement to the wrong creators, or generates ideas that would have been relevant 6 months ago. Because the report reads well and arrives on schedule, the user trusts it — and acts on bad information.

**Why it happens:** LLMs are trained to produce coherent, confident prose. When web search results are sparse, ambiguous, or contradictory, the model fills gaps with training-data priors rather than saying "insufficient signal." Without explicit output validation, there is no catch. The prompt asks for a rationale and the model provides one — real or not.

**Consequences:**
- Creator acts on ideas that are not actually trending
- Trust in the tool erodes after 2–3 bad weeks
- Hard to detect because each report looks good in isolation
- No audit trail to diagnose which step went wrong

**Warning signs:**
- Report ideas feel generic (could have been written without any search data)
- "Why this is working right now" rationale cites no specific creators, platforms, or recent events
- The same ideas recur across multiple weeks with minor variation
- Trend signals in the report predate the current week by months

**Prevention:**
- Require the model to cite specific evidence for each idea: named creator, platform, approximate timeframe, engagement signal. If it cannot, the idea is excluded.
- Add a structured output schema (JSON or similar) that separates evidence fields from synthesis fields. Validate that evidence fields are populated before accepting the output.
- Build a "freshness check" step: have a second prompt evaluate whether each cited trend signal is current (contains date references or recent event markers)
- Store raw search results alongside reports. If a report idea has no matching raw search content to support it, flag it.

**Phase to address:** Foundation / Core Agent Logic (Phase 1–2). Prompt architecture decisions made here are extremely expensive to revisit later.

---

### Pitfall 2: Silent Scheduler Failure — The Agent Stops Running and Nobody Knows

**What goes wrong:** The scheduler (cron, GitHub Actions, cloud scheduler) silently stops firing. This can happen due to repository inactivity timeouts (GitHub Actions disables scheduled workflows after 60 days of no pushes), cloud function cold-start timeouts, deployment drift, or environment configuration changes. The creator expects Monday reports; none arrive; weeks pass before they realize the system is down.

**Why it happens:** Scheduled jobs have no external caller watching for success. Unlike a web server (which fails visibly when a request comes in), a cron job simply does not run — and nothing complains. GitHub Actions specifically disables scheduled workflows on repos with no recent activity, which is a common trap for weekly automation projects.

**Consequences:**
- Complete loss of value delivery — the core product stops working
- No indication of failure until the user notices (often 2–4 weeks later)
- If logs are not persisted, diagnosing the failure is difficult

**Warning signs:**
- GitHub repo has had no pushes in 60 days (GitHub Actions disables scheduled workflows)
- No email arrived on the expected day
- Cloud function logs show no invocations in the expected time window

**Prevention:**
- Add a dead man's switch: send a brief "Agent ran successfully" notification alongside (or instead of) each report, or send a "no report this week" alert if the agent does not complete by a deadline
- Use a monitoring service (healthchecks.io or equivalent) that expects a ping from the agent on schedule; alerts when no ping arrives within the window
- For GitHub Actions: keep the repo active or switch to a cloud scheduler (AWS EventBridge, GCP Cloud Scheduler, Render cron jobs) that does not have inactivity timeouts
- Document the scheduler mechanism and its failure modes explicitly in the project

**Phase to address:** Infrastructure / Scheduling (Phase 1 or dedicated infrastructure phase). Add health-check from day one, not as an afterthought.

---

### Pitfall 3: Cost Runaway — Web Search + LLM Costs Compound Unpredictably

**What goes wrong:** The agent makes more API calls than expected. A loop that searches for 5 niches, then researches 3 creators per niche, then fetches supporting articles for each creator rapidly multiplies: 5 * 3 * 3 = 45 search API calls per run, plus LLM token costs for each synthesis step. If the search API bills per query and the LLM is called with large context windows, a single weekly run can cost $5–$20 instead of the expected $0.50.

**Why it happens:** Multi-step agent pipelines have multiplicative cost structures that are not obvious during design. Each sub-task spawns further tasks. Token costs scale with context length; if search results are passed verbatim into the prompt, context windows bloat. There are rarely hard limits in place during development.

**Consequences:**
- Monthly costs far exceed expectations (easily 10x–50x)
- No way to detect the problem until the billing statement arrives
- Cost limits can cut the agent mid-run, producing partial or broken reports

**Warning signs:**
- Agent pipeline has nested loops (research niches, then research within each niche)
- Search results passed verbatim to LLM without chunking or summarization
- No hard spending caps configured on API accounts
- Cost not tracked per weekly run

**Prevention:**
- Design the pipeline with a fixed, bounded call budget per run: e.g., max 20 search API calls, max 5 LLM synthesis calls. Hard-code these limits.
- Summarize search results before passing to LLM: extract the 3–5 most relevant sentences per result, not the full page text
- Set hard spending alerts (not just "notify me" — use hard limits that cut off billing) on every API account from day one
- Log cost per run in a structured way: search calls used, tokens consumed, estimated cost. Review weekly.
- Use a cheaper model (e.g., Claude Haiku or GPT-4o-mini) for intermediate steps (extraction, filtering) and reserve the expensive model for final synthesis only

**Phase to address:** Core Agent Logic (Phase 1). Cost architecture is foundational — changing it later requires restructuring the entire pipeline.

---

### Pitfall 4: LLM Context Window Saturation — Long Searches Kill Coherence

**What goes wrong:** Web search returns 10–20 results, each with hundreds of words of snippet or page content. Concatenating all of this into a single prompt produces a 20,000–80,000 token context. The LLM's attention degrades at very long contexts: it underweights content in the middle, over-indexes on the beginning and end, and loses coherence in synthesis. The resulting ideas are a random blend of whatever happened to land at the start and end of the prompt.

**Why it happens:** "Pass everything to the model and let it figure it out" is the naive approach. Context length limits have increased dramatically (many models now support 128K–200K tokens), which creates a false sense of safety. Long context != coherent synthesis across long context.

**Consequences:**
- Report ideas are incoherent or inconsistently sourced
- Some search results are effectively invisible to the model despite being in the context
- Report quality degrades as search result volume grows

**Warning signs:**
- Prompt includes raw search result dumps without preprocessing
- Context length regularly exceeds 30K tokens
- Ideas in the report cluster around the same 2–3 topics despite broader search inputs

**Prevention:**
- Implement a "map-reduce" pattern: summarize each search result chunk independently (map step), then synthesize across summaries (reduce step). Never concatenate raw results.
- Hard cap the number of search results per step. 3–5 high-quality results beats 20 mediocre ones.
- Pre-filter results by relevance score before including in the prompt
- Test context saturation explicitly: run the agent with 5 results vs 15 results and compare output quality

**Phase to address:** Core Agent Logic (Phase 1–2). Prompt architecture decision.

---

### Pitfall 5: Email Deliverability Failure — Reports Land in Spam

**What goes wrong:** The weekly report is generated correctly but the email is never seen because it lands in spam or is blocked outright. This is especially common when using raw SMTP, programmatic Gmail via app passwords, or transactional email services with new/unverified domains.

**Why it happens:** Email deliverability requires domain authentication (SPF, DKIM, DMARC records), sender reputation, and consistent sending patterns. Programmatic senders that skip these steps are treated as spam. Gmail and Outlook spam filters have become aggressive against unformatted, link-heavy HTML or bare-text emails from programmatic senders.

**Consequences:**
- Report never reaches the creator — the system appears to work but delivers no value
- No error is raised (the email "sent" successfully from the sending library's perspective)
- Detecting this requires actively checking spam folders

**Warning signs:**
- Using raw SMTP without an established transactional email service
- Domain has no SPF/DKIM/DMARC records
- Email contains many URLs (linking to creator profiles, articles) which triggers spam filters
- Sending from a new domain with no sending history

**Prevention:**
- Use a reputable transactional email service (Resend, SendGrid, Postmark) from day one. These services handle domain authentication and have established sender reputation.
- Verify domain SPF, DKIM, and DMARC records before first send
- Test deliverability explicitly using mail-tester.com or similar before treating the system as working
- Keep the email format simple: minimal HTML, avoid excessive links, use plain-text alternative
- Send to an address you actively monitor (the creator's primary inbox) and confirm receipt after first deployment

**Phase to address:** Email Delivery (Phase 2 or dedicated). Deliverability must be validated before the full pipeline is considered functional.

---

### Pitfall 6: Report Quality Drift — Gradual Degradation That's Hard to Notice

**What goes wrong:** The agent works well at launch. Over weeks, the quality of ideas gradually degrades — they become more generic, less grounded in current data, or repetitive. Because the creator sees one report per week and has no baseline for comparison, they adapt their expectations downward. The system continues running but delivers diminishing value.

**Why it happens:** Web search result quality fluctuates. SEO-optimized content increasingly dominates search results, meaning the agent is synthesizing marketing content rather than genuine trend signals. Prompts that were effective in week 1 may not handle different search result compositions as well. No feedback loop exists to catch drift.

**Consequences:**
- Tool delivers less value over time without any visible failure
- Creator gradually stops acting on ideas without consciously deciding the tool is broken
- No metric to identify the degradation point

**Warning signs:**
- Ideas feel increasingly similar week over week
- The "why this is working right now" sections become more vague
- The report could have been written the previous month without meaningful change

**Prevention:**
- Store all reports. Make it easy to compare this week's report to 4 weeks ago.
- Add a self-evaluation step: after synthesis, have the LLM score each idea on specificity (1–5) and evidence quality (1–5). If average scores drop below a threshold, flag the report.
- Rotate search query formulations weekly to avoid getting trapped in the same result pools
- Periodically audit: manually check one idea per report against its cited evidence

**Phase to address:** Polish / Reliability Phase (later phases). Initial implementation, then monitored over time. Architecture to support audit (storing raw data + reports) must be in place from Phase 1.

---

### Pitfall 7: Trend Discovery Becoming an Echo Chamber

**What goes wrong:** The agent discovers "trending" topics but the search queries it uses are too narrow or predictable. It ends up reporting on the same 3–4 niches every week because those are the highest-traffic topics in search results (fitness, finance, productivity). The creator who operates in niche markets gets no signal about their actual niches.

**Why it happens:** Web search results are popularity-biased. Queries like "trending social media topics this week" return mainstream, high-traffic niches. The agent mistakes "most searched" for "gaining momentum." Niche topics with rapid percentage-growth are invisible compared to established mega-niches.

**Consequences:**
- Report is irrelevant for niche creators
- Creator receives the same suggestions repeatedly
- The autonomous discovery value proposition fails

**Warning signs:**
- The same 3–4 broad niches appear in consecutive reports
- No mention of emerging or niche-specific topics
- "Trending" in the report means "popular" not "gaining momentum"

**Prevention:**
- Design search strategy around momentum signals (what changed this week, what's newly gaining attention) rather than absolute popularity
- Use multiple search query templates targeting different trend signals: platform-specific searches, "rising" + niche, creator growth stories, recent viral content
- Track which niches appeared in previous reports and deprioritize repeat appearances
- Include explicit instruction in prompts: "Focus on topics that are gaining momentum this week, not topics that are broadly popular. Avoid recommending topics that have been popular for more than 3 months."

**Phase to address:** Core Agent Logic / Research Strategy (Phase 1–2). Query design is as important as prompt design.

---

## Moderate Pitfalls

---

### Pitfall 8: No Structured Output — Parsing Failures Break the Pipeline

**What goes wrong:** The agent asks the LLM to return a report in a specific format (JSON, markdown with specific headers). Occasionally the model returns slightly different formatting — an extra field, a missing section, markdown code fences around JSON. The downstream parsing breaks, the email is not sent, and the run silently fails or sends a garbled email.

**Warning signs:** Report generation depends on string parsing of LLM output. No schema validation layer between LLM output and email template.

**Prevention:**
- Use structured output modes where available (OpenAI function calling, Anthropic tool use, or response_format JSON mode) instead of prompt-based formatting
- Add a validation step that checks the output schema before passing to the email formatter
- Build a fallback: if parsing fails, send a plain-text version of the raw output rather than nothing

**Phase to address:** Core Agent Logic (Phase 1).

---

### Pitfall 9: Web Search API Deprecation or Terms of Service Changes

**What goes wrong:** The chosen web search API (SerpAPI, Brave Search API, Tavily, etc.) changes pricing, rate limits, or terms of service. The agent silently starts failing or incurring unexpected costs.

**Warning signs:** Single external dependency for all search with no abstraction layer.

**Prevention:**
- Wrap the search API behind an abstraction layer (a `search()` function) so the provider can be swapped without rewriting agent logic
- Monitor API changelog and subscribe to provider status notifications
- Test with a secondary search provider occasionally to ensure the abstraction holds

**Phase to address:** Infrastructure / Core Agent (Phase 1). Abstraction decision.

---

### Pitfall 10: Timezone and Scheduling Edge Cases

**What goes wrong:** The agent runs at the right time in UTC but the creator expects it Monday morning in their local timezone. Daylight saving time transitions cause the delivery to shift by an hour. The agent occasionally runs twice on DST transition days or skips a Monday.

**Warning signs:** Schedule defined in UTC without explicit timezone handling. No local timezone configuration documented.

**Prevention:**
- Define the desired delivery time in the creator's local timezone and convert explicitly
- Use a scheduler that supports IANA timezone specifications (most modern cloud schedulers do)
- Add a run timestamp to every email ("This report was generated at [time]")

**Phase to address:** Infrastructure (Phase 1).

---

### Pitfall 11: LLM API Outages Break the Weekly Run

**What goes wrong:** The LLM API is down or rate-limited at the scheduled run time. The agent fails with no retry logic. The creator receives no report that week.

**Warning signs:** Agent has no retry mechanism. A single API call failure aborts the entire run.

**Prevention:**
- Implement exponential backoff with retry (3 attempts minimum) on all external API calls
- Use a circuit breaker pattern: if retries fail, send a notification ("Could not generate this week's report due to API unavailability") rather than silent failure
- Consider scheduling at off-peak times (e.g., 3 AM Monday) when API load is lower

**Phase to address:** Core Agent Logic / Reliability (Phase 1–2).

---

## Minor Pitfalls

---

### Pitfall 12: Email HTML Rendering Inconsistency

**What goes wrong:** The report looks great in one email client and broken in another. Outlook strips CSS, Gmail ignores certain HTML elements. The report is unreadable for some clients.

**Prevention:** Use battle-tested email HTML (inline styles only, table-based layouts, or a prebuilt email template service). Test in at least Gmail and Outlook before shipping.

**Phase to address:** Email Delivery (Phase 2).

---

### Pitfall 13: No Local Development Environment for Testing

**What goes wrong:** Testing the agent requires triggering the scheduler and waiting. Development iteration is slow. Bugs introduced in one step take a full run cycle to surface.

**Prevention:**
- Build a `--dry-run` mode that runs the full pipeline without sending email and prints the output
- Build a `--mock-search` mode that uses pre-recorded search results for fast local testing
- Each pipeline step should be independently runnable and testable

**Phase to address:** Foundation (Phase 1). Developer experience decision.

---

### Pitfall 14: Secrets and API Keys in Version Control

**What goes wrong:** LLM API keys, search API keys, or email service credentials are committed to the repository. If the repository is public, keys are immediately compromised. Even in private repos, leaked keys can incur unauthorized costs.

**Prevention:**
- Use environment variables or a secrets manager from day one. Never hardcode credentials.
- Add a pre-commit hook or git-secrets check to the repository
- Rotate keys if there is any doubt about exposure

**Phase to address:** Foundation (Phase 1). Non-negotiable from the first commit.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Foundation / Scaffolding | No local test mode built; secrets in code | Build `--dry-run` from day one; use .env pattern from first commit |
| Trend Discovery / Search | Echo chamber effect; cost runaway from unbounded loops | Fixed call budget per run; query diversity strategy |
| LLM Synthesis / Prompt Design | Hallucinated rationale; context saturation | Map-reduce pattern; evidence citation requirement in schema |
| Email Delivery | Deliverability failure; HTML rendering issues | Use Resend/SendGrid; validate SPF/DKIM; test with mail-tester.com |
| Scheduler / Automation | Silent failure; GitHub Actions inactivity timeout | Dead man's switch; health-check ping service |
| Ongoing Operation | Report quality drift; cost drift | Store all reports + raw data; log cost per run; periodic manual audit |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| LLM prompt brittleness / hallucination | HIGH | Well-documented behavior across production LLM systems as of training cutoff |
| Cost runaway patterns | HIGH | Multiplicative cost structure is a known pattern in multi-step agent pipelines |
| GitHub Actions inactivity timeout (60 days) | HIGH | Documented GitHub behavior as of training cutoff; verify current policy before relying on it |
| Email deliverability requirements | HIGH | SPF/DKIM/DMARC requirements are stable; transactional service recommendation is standard |
| Specific search API behavior | MEDIUM | General patterns apply; specific rate limits/pricing require verification against current API docs |
| Context window degradation at long contexts | MEDIUM | Research existed as of training cutoff but model behavior evolves; test empirically |
| Report quality drift patterns | MEDIUM | Based on patterns observed in production AI agent deployments documented before cutoff |

---

## Sources

- Training knowledge on LLM agent production patterns (cutoff August 2025) — MEDIUM to HIGH confidence
- GitHub Actions scheduled workflow documentation (inactivity timeout behavior) — verify current policy at https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule
- Email deliverability: SPF/DKIM/DMARC requirements are stable industry standards; verify domain authentication with https://mail-tester.com before first send
- LLM structured output: verify current availability for chosen provider (Anthropic tool use, OpenAI response_format) before implementation
- Web search API terms: verify current pricing and rate limits for chosen provider (Tavily, Brave Search API, SerpAPI) before committing to implementation
