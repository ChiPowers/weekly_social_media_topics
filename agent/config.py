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
    tavily_api_key: str
    resend_api_key: str
    email_from: str

    @classmethod
    def from_env(cls) -> "Config":
        """
        Load and validate all required environment variables.
        Raises ValueError listing ALL missing variables at once if any are absent.
        References .env.example in the error message so the fix is obvious.
        """
        required = ["ANTHROPIC_API_KEY", "EMAIL_RECIPIENT", "TAVILY_API_KEY", "RESEND_API_KEY", "EMAIL_FROM"]
        missing = [var for var in required if not os.environ.get(var)]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Copy .env.example to .env and fill in the values."
            )
        return cls(
            anthropic_api_key=os.environ["ANTHROPIC_API_KEY"].strip(),
            email_recipient=os.environ["EMAIL_RECIPIENT"].strip(),
            api_call_budget=int(os.environ.get("API_CALL_BUDGET") or "50"),
            tavily_api_key=os.environ["TAVILY_API_KEY"].strip(),
            resend_api_key=os.environ["RESEND_API_KEY"].strip(),
            email_from=os.environ["EMAIL_FROM"].strip(),
        )
