# agent/pipeline.py
import logging

from tavily import TavilyClient
from anthropic import Anthropic

from agent.config import Config
from agent.budget import BudgetTracker
from agent.research import ResearchEngine
from agent.synthesizer import IdeaSynthesizer

logger = logging.getLogger(__name__)


def run_pipeline(config: Config, budget: BudgetTracker, dry_run: bool) -> None:
    """
    Orchestrate the full pipeline: research -> ideas -> delivery.
    Phase 2+ will implement the real steps. For now this is a verifiable stub.

    In dry-run mode: logs what WOULD happen instead of making real calls.
    In live mode: charges the budget before each real API call.
    """
    logger.info("Pipeline starting (dry_run=%s)", dry_run)

    if dry_run:
        logger.info("[DRY-RUN] Would call research engine — skipping")
        logger.info("[DRY-RUN] Would call LLM synthesizer — skipping")
        logger.info("[DRY-RUN] Would send email to %s — skipping", config.email_recipient)
        logger.info("[DRY-RUN] Pipeline complete. No real API calls or email sent.")
        return

    # Initialize search clients
    tavily_client = TavilyClient(api_key=config.tavily_api_key)
    anthropic_client = Anthropic(api_key=config.anthropic_api_key)

    # Phase 2: Run research engine
    research_engine = ResearchEngine(tavily_client, anthropic_client, budget)
    findings = research_engine.run(dry_run=False)
    logger.info("Research complete: %d niches discovered, %d budget used", len(findings.niches), findings.budget_used)

    # Write research output for Phase 3 consumption
    output_path = "research_output.json"
    findings.to_json_file(output_path)
    logger.info("Research findings written to %s (%d niches)", output_path, len(findings.niches))

    # Phase 3: Run idea synthesizer
    synthesizer = IdeaSynthesizer(anthropic_client=anthropic_client, budget=budget)
    idea_report = synthesizer.run(findings, dry_run=False)
    idea_report.to_json_file("ideas_output.json")
    logger.info(
        "Synthesis complete: %d ideas generated from %d niches",
        len(idea_report.ideas),
        idea_report.niches_processed,
    )
