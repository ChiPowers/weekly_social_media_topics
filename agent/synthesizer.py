"""
LLM synthesizer: reads ResearchFindings, filters niches with no real named creators,
calls Claude Haiku to generate 5-10 ContentIdea objects, validates via Pydantic v2.
Expected API call budget: 1 Claude call per run (single-pass synthesis).
"""
import json
import logging
from datetime import date
from typing import Optional

from pydantic import ValidationError
from anthropic import Anthropic

from agent.budget import BudgetTracker, BudgetExceededError
from agent.models import ResearchFindings, NicheFindings, IdeaReport, ContentIdea

logger = logging.getLogger(__name__)

# Article-title-like prefixes that indicate a "creator" name is not a real person
_ARTICLE_TITLE_PREFIXES = ("How", "The", "Why", "Top", "Best", "What")

# Separators that appear in article titles but not real names
_ARTICLE_TITLE_SEPARATORS = (":", "|", "\u2013", " - ")  # colon, pipe, en-dash, hyphen with spaces


def _looks_like_article_title(name: str, platform: str, follower_count_approx: Optional[str]) -> bool:
    """
    Return True if a creator name looks like an article title rather than a real human.

    A name is an article title if any of the following are true:
    - Contains ":", "|", "–" (en-dash), or " - "
    - Starts with "How", "The", "Why", "Top", "Best", "What"
    - Is "Unknown" (case-insensitive)
    - platform is "unknown" AND follower_count_approx is None
    """
    if name.lower() == "unknown":
        return True
    for sep in _ARTICLE_TITLE_SEPARATORS:
        if sep in name:
            return True
    for prefix in _ARTICLE_TITLE_PREFIXES:
        if name.startswith(prefix):
            return True
    if platform.lower() == "unknown" and follower_count_approx is None:
        return True
    return False


class IdeaSynthesizer:
    """
    Single-pass idea synthesizer over all valid niches.
    Pass budget into constructor — synthesizer charges before every API call.
    Pass dry_run=True to skip all API calls and return a stub result.
    """

    def __init__(self, anthropic_client: Anthropic, budget: BudgetTracker) -> None:
        self.anthropic = anthropic_client
        self.budget = budget

    def run(self, findings: ResearchFindings, dry_run: bool = False) -> IdeaReport:
        """
        Full synthesis run.
        1. Dry-run stub (no API calls).
        2. Guard: empty niches raises ValueError.
        3. Filter niches to those with at least one real named creator.
        4. Guard: zero valid niches raises ValueError.
        5. Single-pass synthesis via Claude Haiku.
        """
        if dry_run:
            logger.info(
                "[DRY-RUN] Synthesizer: would process %d niches — skipping API calls",
                len(findings.niches),
            )
            return IdeaReport(
                run_date=date.today().isoformat(),
                ideas=[],
                niches_processed=len(findings.niches),
                ideas_generated=0,
                budget_used=0,
            )

        if not findings.niches:
            logger.error("No research data available — cannot synthesize ideas")
            raise ValueError("No research data available — cannot synthesize ideas")

        valid_niches = self._filter_valid_niches(findings.niches)

        if not valid_niches:
            logger.error("No valid niches with named creators — cannot synthesize ideas")
            raise ValueError("No valid niches with named creators — cannot synthesize ideas")

        logger.info(
            "Synthesizer starting: %d valid niches (of %d total) — single-pass synthesis",
            len(valid_niches),
            len(findings.niches),
        )

        return self._synthesize(valid_niches)

    def _filter_valid_niches(self, niches: list[NicheFindings]) -> list[NicheFindings]:
        """
        Return niches that have at least one creator who does NOT look like an article title.
        Skip niches where ALL creators look like article titles (no real named humans).
        """
        valid = []
        for niche in niches:
            has_real_creator = any(
                not _looks_like_article_title(
                    c.name,
                    c.platform,
                    c.follower_count_approx,
                )
                for c in niche.top_creators
            )
            if has_real_creator:
                valid.append(niche)
            else:
                logger.info(
                    "Skipping niche '%s' — no real named creators found (all look like article titles)",
                    niche.topic,
                )
        return valid

    def _synthesize(self, valid_niches: list[NicheFindings]) -> IdeaReport:
        """
        Single-pass synthesis: serialize all valid niches into one prompt, one LLM call.
        Retries once on ValidationError with error details appended to prompt.
        Returns empty IdeaReport on second ValidationError or JSONDecodeError.
        BudgetExceededError is NOT caught — propagates up to pipeline.
        """
        min_ideas = 5
        max_ideas = 10
        serialized_niches = json.dumps([n.model_dump() for n in valid_niches], indent=2)
        idea_report_schema = json.dumps(IdeaReport.model_json_schema(), indent=2)

        prompt = (
            "You are a content strategy analyst generating weekly content briefings for social media creators.\n\n"
            "Below is this week's research data: trending niches and top-performing creators discovered via live web search.\n\n"
            f"Generate {min_ideas}\u2013{max_ideas} content ideas. For each idea:\n"
            "- topic: the niche/subject area\n"
            "- angle: a specific title-level hook (e.g., \"Why 80% of TikTok creators use the wrong hook format\") "
            "— NOT a format recommendation or audience segment\n"
            "- talking_points: exactly 2-3 bullets covering what you'd actually say in the content — not meta-notes\n"
            "- rationale: cite [Creator name] ([follower count], [platform]) [specific action] this week/recently "
            "— specific numbers only, no explanation of why it works\n"
            "- platform: include ONLY if research clearly points to one platform\n"
            "- content_format: include ONLY if research surfaced a clear format signal (e.g., \"short-form video dominates\")\n\n"
            "Rules:\n"
            "- Each idea MUST cite different creators — never repeat the same creator across ideas\n"
            "- Rationale MUST contain \"this week\" or \"recently\"\n"
            "- Do NOT generate ideas for niches where you cannot cite a real named creator with metrics\n"
            "- Return ONLY valid JSON. No markdown, no explanation.\n\n"
            f"RESEARCH DATA:\n{serialized_niches}\n\n"
            f"Return JSON matching this schema exactly:\n{idea_report_schema}"
        )

        # Attempt 1
        raw_data = self._call_llm(prompt)
        if raw_data is None:
            logger.error("Synthesis LLM call returned unparseable JSON on attempt 1 — returning empty report")
            return IdeaReport(
                run_date=date.today().isoformat(),
                ideas=[],
                niches_processed=len(valid_niches),
                ideas_generated=0,
                budget_used=self.budget.used,
            )

        try:
            report = IdeaReport.model_validate(raw_data)
        except ValidationError as e:
            logger.warning("IdeaReport validation failed on attempt 1: %s — retrying with clarification", e)
            # Attempt 2: retry with error details
            retry_prompt = (
                f"Your previous response had validation errors: {e}. "
                "Please fix and return only valid JSON matching the schema."
            )
            raw_data2 = self._call_llm(retry_prompt)
            if raw_data2 is None:
                logger.error("Synthesis LLM call returned unparseable JSON on attempt 2 — returning empty report")
                return IdeaReport(
                    run_date=date.today().isoformat(),
                    ideas=[],
                    niches_processed=len(valid_niches),
                    ideas_generated=0,
                    budget_used=self.budget.used,
                )
            try:
                report = IdeaReport.model_validate(raw_data2)
            except ValidationError as e2:
                logger.error("IdeaReport validation failed on attempt 2: %s — returning empty report", e2)
                return IdeaReport(
                    run_date=date.today().isoformat(),
                    ideas=[],
                    niches_processed=len(valid_niches),
                    ideas_generated=0,
                    budget_used=self.budget.used,
                )

        # Post-processing: enforce creator uniqueness across ideas
        report = self._deduplicate_creators(report, len(valid_niches))
        return report

    def _call_llm(self, prompt: str) -> Optional[dict]:
        """
        Budget-guarded LLM call following the exact pattern from research.py.
        Returns parsed dict on success, None on JSONDecodeError.
        BudgetExceededError propagates — never caught here.
        """
        self.budget.charge(1)  # BEFORE messages.create() — raises BudgetExceededError if exceeded
        message = self.anthropic.messages.create(
            model="claude-haiku-4-5",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = message.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = "\n".join(raw_text.split("\n")[1:])
            raw_text = raw_text.rstrip("`").strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError as e:
            logger.error("JSON parse error in LLM response: %s", e)
            return None

    def _deduplicate_creators(self, report: IdeaReport, niches_processed: int) -> IdeaReport:
        """
        Remove ideas where the rationale cites a creator already cited in an earlier idea.
        Case-insensitive match on creator name extracted from rationale string.
        Logs a warning with the count of dropped duplicates.
        """
        seen_creators: set[str] = set()
        unique_ideas: list[ContentIdea] = []
        dropped = 0

        for idea in report.ideas:
            # Extract candidate creator name: first token sequence before first "("
            rationale_lower = idea.rationale.lower()
            # Find the first parenthetical — creator name precedes it
            paren_pos = idea.rationale.find("(")
            if paren_pos > 0:
                creator_key = idea.rationale[:paren_pos].strip().lower()
            else:
                # Fallback: use first 30 chars as proxy
                creator_key = rationale_lower[:30].strip()

            if creator_key and creator_key in seen_creators:
                dropped += 1
                logger.warning(
                    "Dropping duplicate idea for creator '%s' (topic: '%s')",
                    creator_key,
                    idea.topic,
                )
            else:
                if creator_key:
                    seen_creators.add(creator_key)
                unique_ideas.append(idea)

        if dropped > 0:
            logger.warning("Deduplicated %d idea(s) citing the same creator", dropped)

        return IdeaReport(
            run_date=report.run_date,
            ideas=unique_ideas,
            niches_processed=niches_processed,
            ideas_generated=len(unique_ideas),
            budget_used=self.budget.used,
        )
