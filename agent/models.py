# agent/models.py
"""
Pydantic v2 output schema for research engine findings.
This is the contract between Phase 2 (research) and Phase 3 (idea generation).
All fields that web search may not surface reliably are Optional.
"""
from typing import Optional
from pydantic import BaseModel


class CreatorProfile(BaseModel):
    """A named creator with profitability signals extracted from web search snippets."""
    name: str
    platform: str                                  # e.g. "TikTok", "YouTube", "TikTok/Instagram"
    follower_count_approx: Optional[str] = None    # e.g. "450K", "1.2M" — string from snippet
    follower_count_numeric: Optional[int] = None   # parsed int for filtering; None if not found
    content_style: Optional[str] = None            # e.g. "short-form tutorial", "reaction"
    posting_frequency: Optional[str] = None        # e.g. "daily", "3x/week"
    brand_deal_detected: bool = False              # True if "#ad", "#sponsored", "partnership" found
    brand_deal_details: Optional[str] = None       # e.g. "#ad NordVPN" — raw text when detected
    source_url: Optional[str] = None               # URL of search result that surfaced this creator


class NicheFindings(BaseModel):
    """
    Findings for a single trending niche/topic discovered this week.
    Covers RSCH-04 dimensions: topic, content_style, posting_frequency, media_type.
    """
    topic: str                                     # e.g. "AI productivity tools"
    platform_attribution: str                      # free-text, e.g. "TikTok" or "TikTok/Instagram"
    engagement_signal: str                         # why it's trending, e.g. "millions of views this week"
    media_type: Optional[str] = None               # "short-form video", "carousel", "live stream", etc.
    content_style: Optional[str] = None            # e.g. "tutorial", "reaction", "day-in-the-life"
    posting_frequency: Optional[str] = None        # e.g. "multiple times daily"
    top_creators: list[CreatorProfile] = []        # 3-5 named creators per niche (CONTEXT.md decision)


class ResearchFindings(BaseModel):
    """
    Top-level container for a complete research engine run.
    Serialized to JSON and passed to Phase 3 idea generation.
    """
    run_date: str                                  # ISO date string, e.g. "2026-02-28"
    niches: list[NicheFindings]
    total_searches: int                            # Tavily + Claude calls made this run
    budget_used: int                               # budget.used at end of run

    def to_json_file(self, path: str) -> None:
        """Write findings to a JSON file. Used by pipeline.py after research completes."""
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_json_file(cls, path: str) -> "ResearchFindings":
        """Load findings from a JSON file. Used by Phase 3 for idea generation."""
        with open(path) as f:
            return cls.model_validate_json(f.read())
