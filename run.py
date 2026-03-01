# run.py
import sys
import logging
import argparse

from agent.config import Config
from agent.budget import BudgetTracker, BudgetExceededError
from agent.pipeline import run_pipeline


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Social Media Content Intelligence Agent"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run the full pipeline without making real API calls or sending email",
    )
    args = parser.parse_args()

    try:
        config = Config.from_env()
        budget = BudgetTracker(limit=config.api_call_budget)
        run_pipeline(config=config, budget=budget, dry_run=args.dry_run)
    except BudgetExceededError as e:
        print(f"BUDGET HALT: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: Configuration problem — {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
