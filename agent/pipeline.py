# agent/pipeline.py
import logging

from agent.config import Config
from agent.budget import BudgetTracker

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

    # Live path — Phase 2+ fills in real implementation here.
    # Every real API call must call budget.charge(n) BEFORE the call.
    budget.charge(1)
    logger.info("Pipeline complete (live mode stub — no real calls yet)")
