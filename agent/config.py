# agent/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Call load_dotenv() once at module import.
# override=False (default) means GitHub Actions secrets take precedence over .env values —
# the same config.py works in local dev and production without branching.
load_dotenv()


@dataclass
class Config:
    anthropic_api_key: str
    email_recipient: str
    api_call_budget: int

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load and validate all required environment variables.
        Raises ValueError listing ALL missing variables at once if any are absent.
        References .env.example in the error message so the fix is obvious.
        """
        required = ["ANTHROPIC_API_KEY", "EMAIL_RECIPIENT"]
        missing = [var for var in required if not os.environ.get(var)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Copy .env.example to .env and fill in the values."
            )
        return cls(
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            email_recipient=os.environ["EMAIL_RECIPIENT"],
            api_call_budget=int(os.environ.get("API_CALL_BUDGET", "50")),
        )
