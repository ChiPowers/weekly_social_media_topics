# agent/mailer.py
"""
EmailDeliverer: renders IdeaReport to HTML + plain-text and delivers via Resend.
"""
import logging
import os
from datetime import datetime

import resend
import resend.exceptions
from jinja2 import Environment, FileSystemLoader, select_autoescape

from agent.config import Config
from agent.models import IdeaReport

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(enabled_extensions=("html",)),
)


def _format_date(run_date: str) -> str:
    """Convert ISO date string (e.g. '2026-03-03') to 'March 3, 2026'."""
    return datetime.strptime(run_date, "%Y-%m-%d").strftime("%B %-d, %Y")


class EmailDeliverer:
    """Renders and delivers content idea reports via Resend email API."""

    def __init__(self, config: Config) -> None:
        self._config = config
        resend.api_key = config.resend_api_key
        self._logger = logging.getLogger(__name__)

    def render_report(self, report: IdeaReport) -> tuple:
        """
        Render report into (subject, html_body).

        Returns:
            tuple[str, str]: (subject line, rendered HTML body)
        """
        n = len(report.ideas)
        subject = f"{n} content idea{'s' if n != 1 else ''} for this week"
        template = _jinja_env.get_template("report.html")
        html_body = template.render(
            ideas=report.ideas,
            header_date=_format_date(report.run_date),
        )
        return subject, html_body

    def render_plain_text(self, report: IdeaReport) -> str:
        """
        Build plain-text version of the report directly from IdeaReport fields.

        Returns:
            str: Plain-text representation of the report.
        """
        lines = []
        for i, idea in enumerate(report.ideas, start=1):
            lines.append(f"{i}. {idea.topic}")
            lines.append(f"   {idea.angle}")
            for point in idea.talking_points:
                lines.append(f"   - {point}")
            lines.append(f"   {idea.rationale}")
            if idea.platform:
                lines.append(f"   Best for: {idea.platform}")
            if idea.content_format:
                lines.append(f"   Format: {idea.content_format}")
            lines.append("")
        return "\n".join(lines)

    def send_report(self, report: IdeaReport) -> None:
        """
        Render and send the idea report email via Resend.

        Raises:
            resend.exceptions.ResendError: On delivery failure — not caught here,
            propagates to pipeline.py.
        """
        subject, html = self.render_report(report)
        text = self.render_plain_text(report)
        resend.Emails.send({
            "from": self._config.email_from,
            "to": [self._config.email_recipient],
            "subject": subject,
            "html": html,
            "text": text,
        })
        self._logger.info(
            "Email sent to %s at %s",
            self._config.email_recipient,
            datetime.now().isoformat(),
        )

    def send_error(self, reason: str) -> None:
        """
        Send an error notification email.

        If sending the error email itself fails, the exception is logged and
        swallowed so it does not mask the original pipeline exception.
        """
        try:
            subject = f"Content agent error — {_format_date(datetime.now().strftime('%Y-%m-%d'))}"
            template = _jinja_env.get_template("error.html")
            html = template.render(reason=reason)
            text = reason
            resend.Emails.send({
                "from": self._config.email_from,
                "to": [self._config.email_recipient],
                "subject": subject,
                "html": html,
                "text": text,
            })
        except resend.exceptions.ResendError as exc:
            self._logger.error(
                "Failed to send error notification email: %s", exc
            )
