"""
Research engine: autonomous trending niche and creator discovery via Tavily web search.
Expected API call budget per run: ~15 Tavily searches + ~10 Claude extraction calls = ~25 total.
Designed for default API_CALL_BUDGET=50; leaves 25 calls as slack for Phase 3 LLM synthesis.
"""
import logging
import re
from datetime import date
from typing import Optional

from tavily import TavilyClient
from anthropic import Anthropic

from agent.budget import BudgetTracker, BudgetExceededError
from agent.models import CreatorProfile, NicheFindings, ResearchFindings

logger = logging.getLogger(__name__)

# --- Query bank ---
# Niche discovery: cross-platform trending queries (topic="news", time_range="week")
# "This week" language is required per CONTEXT.md — do not use "popular" or "all-time"
NICHE_DISCOVERY_QUERIES = [
    "viral TikTok content trending this week high engagement 2026",
    "most viewed YouTube videos topics trending this week 2026",
    "trending Instagram Reels niche viral this week",
    "Facebook viral content topics this week high shares",
    "X Twitter trending topics creators viral this week",
    "social media viral niche content style most viewed this week",
]

# Creator discovery: per-niche template (topic="general", time_range="week")
# {niche} is replaced at runtime with discovered niche topic
# Includes "100K followers" to surface mid-tier creator tier per CONTEXT.md decision
CREATOR_QUERY_TEMPLATES = [
    "{niche} TikTok creator 100K followers trending this week",
    "{niche} YouTube Instagram creator brand deal sponsorship viral 2026",
]

# Brand deal signal keywords per CONTEXT.md — flag if any appear in snippet
BRAND_DEAL_SIGNALS = ["#ad", "#sponsored", "partnership with", "paid partnership", "gifted by"]


class ResearchEngine:
    """
    Autonomous trending niche and creator discovery.
    Pass budget into constructor — engine charges before every API call.
    Pass dry_run=True to skip all API calls and return a stub result.
    """

    def __init__(
        self,
        tavily_client: TavilyClient,
        anthropic_client: Anthropic,
        budget: BudgetTracker,
    ) -> None:
        self.tavily = tavily_client
        self.anthropic = anthropic_client
        self.budget = budget

    def _search(self, query: str, topic: str = "news", **kwargs) -> dict:
        """
        Budget-guarded Tavily search.
        Calls budget.charge(1) BEFORE the API call — raises BudgetExceededError if exceeded.
        Uses search_depth="basic" always (1 credit); never "advanced" (2 credits) here.
        """
        self.budget.charge(1)
        logger.debug("Searching: %s (topic=%s)", query, topic)
        return self.tavily.search(
            query=query,
            topic=topic,
            time_range="week",
            search_depth="basic",
            max_results=10,
            **kwargs,
        )

    def run(self, dry_run: bool = False) -> ResearchFindings:
        """
        Full two-pass research run.
        Pass 1: Discover trending niches using NICHE_DISCOVERY_QUERIES.
        Pass 2: Per-niche creator discovery using CREATOR_QUERY_TEMPLATES.
        Returns ResearchFindings with all discovered niches and creators.
        """
        if dry_run:
            logger.info(
                "[DRY-RUN] Research engine: would run %d niche queries + creator queries — skipping",
                len(NICHE_DISCOVERY_QUERIES),
            )
            return ResearchFindings(
                run_date=date.today().isoformat(),
                niches=[],
                total_searches=0,
                budget_used=0,
            )

        logger.info(
            "Research engine starting — Pass 1: niche discovery (%d queries)",
            len(NICHE_DISCOVERY_QUERIES),
        )
        raw_niche_results = self._run_niche_discovery()

        logger.info(
            "Research engine — Pass 2: creator discovery for %d niches",
            len(raw_niche_results),
        )
        raw_creator_results = self._run_creator_discovery(raw_niche_results)

        # Structured extraction happens in Plan 03 — for now, return raw results bundled
        # into NicheFindings stubs so the pipeline can call research.run() end-to-end.
        # Plan 03 replaces this stub assembly with LLM extraction.
        niches = self._assemble_stub_niches(raw_niche_results, raw_creator_results)

        return ResearchFindings(
            run_date=date.today().isoformat(),
            niches=niches,
            total_searches=self.budget.used,
            budget_used=self.budget.used,
        )

    def _run_niche_discovery(self) -> list[dict]:
        """
        Execute all NICHE_DISCOVERY_QUERIES against Tavily.
        Returns list of raw Tavily result dicts (each dict has 'query' and 'results' keys).
        Stops early and logs warning if BudgetExceededError fires mid-run.
        """
        all_results = []
        for query in NICHE_DISCOVERY_QUERIES:
            try:
                result = self._search(query, topic="news")
                result["_query"] = query  # tag with originating query for debugging
                all_results.append(result)
            except BudgetExceededError:
                logger.warning(
                    "Budget exceeded during niche discovery after %d queries — returning partial results",
                    len(all_results),
                )
                break
        logger.info("Niche discovery complete: %d query results collected", len(all_results))
        return all_results

    def _run_creator_discovery(self, niche_results: list[dict]) -> dict[str, list[dict]]:
        """
        For each discovered niche topic, run CREATOR_QUERY_TEMPLATES queries.
        Returns dict mapping niche_topic -> list of raw Tavily result dicts.
        Extracts niche topics from snippet text heuristically — Plan 03 replaces with LLM.
        """
        # Heuristic topic extraction: take first result title from each niche query batch
        # Plan 03 replaces this with LLM-extracted topics from NicheFindings objects
        niche_topics = self._extract_niche_topics_heuristic(niche_results)
        logger.info(
            "Extracted %d niche topics for creator discovery: %s",
            len(niche_topics),
            niche_topics,
        )

        creator_results: dict[str, list[dict]] = {}
        for niche in niche_topics:
            niche_creator_results = []
            for template in CREATOR_QUERY_TEMPLATES:
                query = template.format(niche=niche)
                try:
                    result = self._search(query, topic="general")
                    result["_query"] = query
                    result["_niche"] = niche
                    niche_creator_results.append(result)
                except BudgetExceededError:
                    logger.warning(
                        "Budget exceeded during creator discovery for niche '%s' — skipping remaining queries",
                        niche,
                    )
                    break
            creator_results[niche] = niche_creator_results

        return creator_results

    def _extract_niche_topics_heuristic(self, niche_results: list[dict]) -> list[str]:
        """
        Heuristic extraction of niche topic strings from raw search result titles.
        Limits to top 3–5 niches to control creator query count and budget.
        Plan 03 replaces this with LLM extraction returning structured NicheFindings.
        """
        topics = []
        for result_batch in niche_results:
            results = result_batch.get("results", [])
            if results:
                # Use first result title as niche proxy — crude but sufficient for Pass 2 query construction
                title = results[0].get("title", "")
                if title and len(title) > 5:
                    # Trim to first 50 chars for use as query fragment
                    topics.append(title[:50].strip())
        # Deduplicate and cap at 5 niches (3 queries each = 10 creator searches max)
        seen = set()
        unique = []
        for t in topics:
            normalized = t.lower()
            if normalized not in seen:
                seen.add(normalized)
                unique.append(t)
            if len(unique) >= 5:
                break
        return unique

    def _assemble_stub_niches(
        self,
        niche_results: list[dict],
        creator_results: dict[str, list[dict]],
    ) -> list[NicheFindings]:
        """
        Stub assembler: wraps raw results into NicheFindings with minimal field population.
        Plan 03 REPLACES this method body with LLM extraction — do not make this smarter.
        The stub ensures the pipeline runs end-to-end before Plan 03 adds LLM extraction.
        """
        niches = []
        for niche_topic, creator_result_list in creator_results.items():
            creators = self._extract_creators_heuristic(creator_result_list)
            niches.append(NicheFindings(
                topic=niche_topic,
                platform_attribution="unknown",  # Plan 03 sets this from LLM extraction
                engagement_signal="trending this week",  # Plan 03 sets this from LLM extraction
                top_creators=creators,
            ))
        return niches

    def _extract_creators_heuristic(self, creator_result_list: list[dict]) -> list[CreatorProfile]:
        """
        Heuristic creator extraction: parses follower counts from snippets via regex,
        detects brand deal signals from BRAND_DEAL_SIGNALS keywords.
        Returns at most 5 creators (CONTEXT.md: 3–5 per niche, quality over quantity).
        Plan 03 enhances this with LLM for content_style and posting_frequency fields.
        """
        creators = []
        seen_names: dict[str, CreatorProfile] = {}  # deduplication by normalized name

        for result_batch in creator_result_list:
            for result in result_batch.get("results", []):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                combined_text = f"{title} {content}"

                # Follower count extraction (regex per RESEARCH.md pattern)
                approx, numeric = _parse_follower_count(combined_text)

                # Brand deal detection (keyword scan per CONTEXT.md decision)
                brand_detected = any(signal.lower() in combined_text.lower() for signal in BRAND_DEAL_SIGNALS)
                brand_details = None
                if brand_detected:
                    for signal in BRAND_DEAL_SIGNALS:
                        idx = combined_text.lower().find(signal.lower())
                        if idx >= 0:
                            brand_details = combined_text[idx:idx + 60].strip()
                            break

                # Name heuristic: use title as creator name proxy — Plan 03 replaces with LLM
                creator_name = title[:60].strip() if title else "Unknown"
                normalized_name = creator_name.lower()

                if normalized_name not in seen_names:
                    profile = CreatorProfile(
                        name=creator_name,
                        platform="unknown",  # Plan 03 sets from LLM
                        follower_count_approx=approx,
                        follower_count_numeric=numeric,
                        brand_deal_detected=brand_detected,
                        brand_deal_details=brand_details,
                        source_url=url or None,
                    )
                    seen_names[normalized_name] = profile
                    creators.append(profile)
                else:
                    # Keep entry with more complete data
                    existing = seen_names[normalized_name]
                    if numeric and not existing.follower_count_numeric:
                        existing.follower_count_numeric = numeric
                        existing.follower_count_approx = approx

                if len(creators) >= 5:  # CONTEXT.md: 3–5 creators per niche
                    break
            if len(creators) >= 5:
                break

        return creators


def _parse_follower_count(text: str) -> tuple[Optional[str], Optional[int]]:
    """
    Extract follower/subscriber count from text snippet.
    Returns (approx_string, numeric_int) or (None, None) if not found.
    Example: "450K followers" -> ("450K", 450000)
    """
    pattern = r'(\d+\.?\d*)\s*([KkMm])\s*(?:followers?|subscribers?)?'
    match = re.search(pattern, text)
    if not match:
        return None, None
    num_str, suffix = match.group(1), match.group(2).upper()
    approx = f"{num_str}{suffix}"
    multiplier = 1_000 if suffix == "K" else 1_000_000
    numeric = int(float(num_str) * multiplier)
    return approx, numeric
