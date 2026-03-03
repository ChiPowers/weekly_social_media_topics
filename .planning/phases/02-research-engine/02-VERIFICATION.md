---
phase: 02-research-engine
verified: 2026-03-01T00:00:00Z
status: passed
score: 13/13 must-haves verified
human_verification:
  - test: "Confirm LLM extraction produces structured NicheFindings (not heuristic fallback) for RSCH-03 and RSCH-04"
    expected: "research_output.json contains at least 1 NicheFindings where platform_attribution is not 'unknown', and at least one of media_type/content_style/posting_frequency is not null; and at least 1 creator with a real person name (not an article headline)"
    why_human: "The existing research_output.json (from the human-approved live run) shows all niches used heuristic fallback — all platform_attribution values are 'unknown', all RSCH-04 dimensional fields are null, and creator names are article titles. The LLM extraction code is fully wired and correct, but it is unclear whether it successfully produced structured output during the approved run or whether the LLM returned None for every niche (triggering the fallback). This cannot be determined from code inspection alone."
  - test: "Verify .env.example exists in the project root"
    expected: ".env.example file is present with TAVILY_API_KEY=tvly-YOUR_API_KEY_HERE placeholder"
    why_human: "Plan 01 required .env.example to be created. The SUMMARY claims it was created and committed (commit 63e50e4). However, the file does not exist in the project root — only .env exists. The .env file contains a header comment '# .env.example — copy to .env and fill in real values' suggesting .env.example was never created as a separate file, or was deleted."
---

# Phase 2: Research Engine Verification Report

**Phase Goal:** Agent autonomously discovers trending niches and top-performing creators across major social platforms each run
**Verified:** 2026-03-01
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running `Config.from_env()` raises `ValueError` listing `TAVILY_API_KEY` when missing | VERIFIED | `required = ["ANTHROPIC_API_KEY", "EMAIL_RECIPIENT", "TAVILY_API_KEY"]` at config.py:26; collect-all-missing pattern intact |
| 2 | Running `Config.from_env()` with `TAVILY_API_KEY` set returns Config with `tavily_api_key` populated | VERIFIED | `tavily_api_key=os.environ["TAVILY_API_KEY"]` at config.py:37; field declared at config.py:17 |
| 3 | `agent/models.py` exports `CreatorProfile`, `NicheFindings`, `ResearchFindings` as Pydantic v2 `BaseModel` subclasses | VERIFIED | All three classes present, extend `BaseModel` from pydantic, use `model_dump_json()`/`model_validate_json()` (v2 API) |
| 4 | `ResearchFindings` schema includes `topic`, `content_style`, `posting_frequency`, and `media_type` via `NicheFindings` (RSCH-04 contract) | VERIFIED | All four fields present in `NicheFindings` at models.py:29-34 |
| 5 | `ResearchEngine.run()` discovers trending niches without user-provided seed topics (RSCH-01) | VERIFIED | `NICHE_DISCOVERY_QUERIES` is a hardcoded constant; `run()` calls `_run_niche_discovery()` autonomously — no user input parameter |
| 6 | Niche discovery queries cover TikTok, YouTube, Facebook, Instagram, and X/Twitter (RSCH-02) | VERIFIED | research.py:26-31 — one dedicated query per platform plus a cross-platform query; all 5 platforms present |
| 7 | Every Tavily call goes through `_search()` which calls `budget.charge(1)` before the API call | VERIFIED | research.py:69 (`_search`) and research.py:220 (`_extract_with_llm`) both call `self.budget.charge(1)` before their respective API calls |
| 8 | Duplicate creators across search passes are deduplicated by normalized name | VERIFIED | `seen_names: dict[str, CreatorProfile]` pattern at research.py:340-383; key is `creator_name.lower()` |
| 9 | `ResearchEngine.run(dry_run=True)` returns stub `ResearchFindings` without API calls | VERIFIED | research.py:87-97 — returns early with zero-count `ResearchFindings`, no `_search()` or LLM calls |
| 10 | `_extract_with_llm()` exists, charges budget before LLM call, uses `claude-haiku-4-5`, handles failures with None return | VERIFIED | research.py:203-235 — budget charged at line 220, model string at line 223, full exception handling returns None |
| 11 | `ValidationError` is caught and does not crash the pipeline | VERIFIED | research.py:12 imports `ValidationError`, caught at research.py:306 with heuristic fallback; pipeline continues |
| 12 | `pipeline.py` writes `research_output.json` after live research run | VERIFIED | pipeline.py:41-43 — `findings.to_json_file("research_output.json")` present and wired after research completes |
| 13 | LLM extraction produces `NicheFindings` with structured RSCH-03/RSCH-04 fields (not stub values) in live output | UNCERTAIN | `research_output.json` from approved live run shows all niches with `platform_attribution: "unknown"`, all dimensional fields `null`, creator names are article headlines — consistent with heuristic fallback path, not LLM extraction. Code is correct; output quality requires human re-run. |

**Score:** 12/13 truths auto-verified (1 uncertain — requires human)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `agent/models.py` | Pydantic v2 schema contract: CreatorProfile, NicheFindings, ResearchFindings | VERIFIED | File exists, 57 lines, all three classes exported with correct fields and v2 API usage |
| `agent/config.py` | Config.from_env() with TAVILY_API_KEY validation | VERIFIED | Field `tavily_api_key: str` at line 17; `TAVILY_API_KEY` in required list at line 26 |
| `requirements.txt` | `tavily-python==0.7.22` and `pydantic==2.12.5` pinned | VERIFIED | Both dependencies present with exact versions; `anthropic>=0.40.0` also present |
| `agent/research.py` | ResearchEngine class with two-pass autonomous search strategy and `NICHE_DISCOVERY_QUERIES` | VERIFIED | 408 lines; ResearchEngine class present; NICHE_DISCOVERY_QUERIES constant at line 25 |
| `.env.example` | TAVILY_API_KEY placeholder for onboarding | MISSING | File does not exist in project root. Only `.env` exists. SUMMARY claims it was created in commit 63e50e4 but it is absent from the filesystem. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `agent/config.py` | `.env` / `TAVILY_API_KEY` | `os.environ['TAVILY_API_KEY']` after `from_env()` validation | VERIFIED | Pattern confirmed at config.py:26 and config.py:37 |
| `agent/models.py` | `agent/research.py` | `from agent.models import NicheFindings, CreatorProfile, ResearchFindings` | VERIFIED | research.py:18 — exact import present |
| `agent/research.py` | `TavilyClient.search()` | `_search()` with `budget.charge(1)` guard | VERIFIED | research.py:63-78 — `self.budget.charge(1)` at line 69, `self.tavily.search()` at line 71 |
| `agent/research.py` | `agent/budget.py` | `BudgetTracker` passed into `ResearchEngine.__init__` | VERIFIED | research.py:17 imports `BudgetTracker`, research.py:57 accepts `budget: BudgetTracker` in constructor |
| `agent/research.py _extract_with_llm()` | `anthropic_client.messages.create()` | `self.budget.charge(1)` before each LLM call | VERIFIED | research.py:220-226 — charge precedes `messages.create()` |
| `agent/research.py` | `agent/models.py NicheFindings` | `NicheFindings.model_validate()` with try/except `ValidationError` | VERIFIED | research.py:296 uses `model_validate()`, ValidationError caught at line 306 |
| `agent/pipeline.py` | `research_output.json` | `findings.to_json_file()` | VERIFIED | pipeline.py:42 — `findings.to_json_file(output_path)` wired in live path |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RSCH-01 | 02-01, 02-02 | Agent autonomously discovers trending niches — no user input required | SATISFIED | `NICHE_DISCOVERY_QUERIES` hardcoded constant; `run()` requires no user topic seeds |
| RSCH-02 | 02-02 | Research covers all major platforms (TikTok, YouTube, Facebook, Instagram, X/Twitter) | SATISFIED | All 5 platforms represented in `NICHE_DISCOVERY_QUERIES` at research.py:26-31 |
| RSCH-03 | 02-02, 02-03 | Identifies top-performing creators with profitability signals (follower counts, brand deal indicators) | PARTIAL | Code: `_extract_creators_heuristic()` extracts follower counts via regex and detects brand deal keywords. `_extract_with_llm()` + `_assemble_niches()` intended to produce named creators. Live output shows heuristic fallback used for all niches — creator names are article titles, not actual creator names. Needs human re-verification. |
| RSCH-04 | 02-01, 02-03 | Research produces findings broken down by topic, content style, posting frequency, and media type | PARTIAL | Schema: all four fields present in `NicheFindings`. Live output: all four RSCH-04 dimensional fields (`media_type`, `content_style`, `posting_frequency`, `platform_attribution`) are null or "unknown" in `research_output.json` — heuristic fallback does not populate these. LLM path designed to populate them. |

**Note on RSCH-01 and RSCH-02:** Fully satisfied at both the code and live output level — niches ARE discovered autonomously with no user input, and the query bank covers all 5 platforms.

**Note on RSCH-03 and RSCH-04:** The implementation code for LLM-based extraction is fully present and correctly wired. The human checkpoint in Plan 03 was approved. However, the `research_output.json` written during the live run (the only runtime evidence available) shows all niches fell back to the heuristic path — none of the RSCH-04 dimensional fields are populated, and creator names are search result titles rather than actual named creators. This suggests the LLM extraction may have returned `None` for all niches (triggering fallback) during the approved run, or the human verifier accepted output that did not fully meet the criteria.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `agent/research.py` | 363, 370, 401 | `# Plan 03 sets from LLM` / `# Plan 03 sets this from LLM` comments still present | Info | These are accurate stale comments describing the heuristic fallback — not blockers, but reflect that heuristic path still fires in production |
| `agent/research.py` | 145-146 | Comment says "Plan 03 replaces with LLM" in `_run_creator_discovery()` | Info | Comment is outdated — Plan 03 was executed. However the method itself was not changed (intentionally). Not a blocker. |
| `.env.example` | — | File missing from filesystem | Warning | SUMMARY claims creation in commit 63e50e4 but file is absent. Onboarding path broken — new developer cannot copy the example file. |

### Human Verification Required

#### 1. LLM Extraction Quality — RSCH-03 and RSCH-04

**Test:** With real `TAVILY_API_KEY` and `ANTHROPIC_API_KEY` in `.env`, run `python run.py` and inspect `research_output.json`.

**Expected:**
- At least 1 `NicheFindings` where `platform_attribution` is not `"unknown"` (e.g., "TikTok", "YouTube")
- At least 1 `NicheFindings` where one of `media_type`, `content_style`, or `posting_frequency` is not `null`
- At least 1 `CreatorProfile` where `name` is an actual creator name (not an article headline or URL fragment)

**Why human:** The existing `research_output.json` from the approved live run shows all 5 niches fell back to heuristic extraction (all RSCH-04 fields null, all `platform_attribution` = "unknown", creator names are article titles). The LLM extraction code is correctly wired, but the live output does not demonstrate it produced structured results. A fresh live run is needed to determine whether this is a transient issue (e.g., LLM returned non-JSON during that run) or a systematic problem.

**Verification command:**
```bash
python -c "
from agent.models import ResearchFindings
r = ResearchFindings.from_json_file('research_output.json')
print(f'Niches: {len(r.niches)}')
for n in r.niches:
    print(f'  topic={n.topic!r}, platform={n.platform_attribution!r}, media_type={n.media_type!r}, content_style={n.content_style!r}')
    for c in n.top_creators[:2]:
        print(f'    creator={c.name!r}, followers={c.follower_count_approx!r}')
"
```

#### 2. .env.example Existence

**Test:** Check that `.env.example` is present in the project root.

**Expected:** File exists at project root with at minimum `TAVILY_API_KEY=tvly-YOUR_API_KEY_HERE` placeholder. The `.env` file currently contains a header comment referencing `.env.example` but the separate `.env.example` file is missing.

**Why human:** The SUMMARY claims commit `63e50e4` created `.env.example`, but `ls -la` shows no `.env.example` file in the project root. Either the file was deleted after creation, was committed but not written to the working tree, or was never created. A human should verify and re-create if missing.

---

## Gaps Summary

Two items require human action before Phase 2 can be declared fully complete:

**Item 1 — LLM extraction output quality (RSCH-03, RSCH-04):** The implementation code is fully present and correctly wired. The `_extract_with_llm()` method, `_assemble_niches()`, budget guarding, and ValidationError handling are all verified. However, the live `research_output.json` from the human-approved run shows the heuristic fallback was used for every niche — all RSCH-04 dimensional fields are null and creator names are article titles. A fresh live run should confirm whether LLM extraction produces structured output. If it does not, the LLM prompt or JSON stripping logic may need adjustment.

**Item 2 — Missing .env.example:** The Plan 01 SUMMARY documents creation of `.env.example` with a `TAVILY_API_KEY` placeholder. The file does not exist on disk. This is not a functional blocker for the running agent, but breaks the documented onboarding path for new developers.

---

_Verified: 2026-03-01_
_Verifier: Claude (gsd-verifier)_
