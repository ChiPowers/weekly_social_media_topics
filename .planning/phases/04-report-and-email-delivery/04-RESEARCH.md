# Phase 4: Report and Email Delivery - Research

**Researched:** 2026-03-03
**Domain:** Jinja2 HTML email templating + Resend Python SDK delivery
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Email Layout and Visual Style**
- Visual polish: Clean minimal — styled text, clear hierarchy, no heavy design. Minimal CSS, no images. Renders reliably in all email clients.
- Structure: Numbered list — ideas displayed 1 through N in sequence, no grid or columns.
- Color scheme: Light background, dark text — neutral/white. No accent colors.
- Dividers: Horizontal rule between each idea for visual separation.

**Idea Presentation**
- Idea label: Number + topic name as the primary heading — e.g., "1. Skincare Routines" (bold). The topic name is the primary label.
- Angle: Displayed as a subheading under the topic name — the specific hook framing.
- Talking points: All 2–3 bullets shown — these are the actual content the creator would cover.
- Rationale: Italicized or muted text below the bullets — visually distinct as supporting evidence, not the main message.
- Optional fields: `platform` and `content_format` shown as small inline labels when present (e.g., "Best for: TikTok", "Format: Short-form video"). Omitted gracefully when null.

**Subject Line and Framing**
- Subject line: Dynamic — includes the date or week. e.g., "Your content ideas — week of March 3" or "5 content ideas for this week".
- Email header: Short header only — title + date, then straight into ideas. e.g., "Your Weekly Content Intel — March 3, 2026". No intro paragraph.
- Footer: None — no footer at the bottom of the email.

**Error and Edge Case Behavior**
- On pipeline error (no valid niches, API failure): Send a brief error notification email. Subject: "Content agent error — [date]". Body: one-line reason (e.g., "No trending niches with named creators found this week.") — minimal, no stack trace.
- Freshness: Email always uses ideas just generated in the current run. Never send from a stale `ideas_output.json`. Pipeline is sequential: research → synthesize → email.
- Delivery confirmation: Log to console only — "Email sent to [recipient] at [time]". No delivery receipt file.

### Claude's Discretion
- Jinja2 template structure and variable naming
- Exact inline CSS values (font sizes, spacing, colors within the neutral/minimal constraint)
- Plain-text fallback formatting
- Resend API integration details (how to instantiate client, which SDK method)
- How to pass error reason string to the error email template

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DLVR-01 | Report is delivered as an HTML email to a configured recipient address | Resend Python SDK 2.23.0 `resend.Emails.send()` with `html` param delivers to any verified-domain recipient; `RESEND_API_KEY` added to Config |
| DLVR-02 | Email body contains an ideas section with all 5–10 ideas and their rationale | Jinja2 3.1.6 `FileSystemLoader` + `for` loop over `IdeaReport.ideas`; conditional display of optional fields via `{% if %}` blocks |
</phase_requirements>

---

## Summary

Phase 4 adds the final output layer: rendering the `IdeaReport` produced by Phase 3 into a styled HTML email and delivering it to the configured recipient via Resend. The two-component design is straightforward: Jinja2 renders the template, Resend delivers it.

The standard stack is well-established and actively maintained. Jinja2 3.1.6 (March 2025) is a stable templating engine already used in the Python ecosystem broadly. Resend 2.23.0 (February 2026) is the current SDK release — the `resend.Emails.send()` call accepts `html` and `text` parameters, returns a response id, and raises typed exceptions (`ResendError` subclasses) for all failure modes. Both libraries integrate cleanly with the project's existing Python/Pydantic/dotenv architecture.

The key constraint for reliable email rendering is using inline CSS only — no external stylesheets, no flexbox, no grid. Tables are the safe layout primitive for multi-client compatibility. For this phase's minimal numbered-list design, even tables are unnecessary; a simple `<div>`-based structure with inline styles works because Gmail, Outlook (new), and Apple Mail all render basic block elements reliably. The `<hr>` element for dividers is safe across all major clients.

**Primary recommendation:** Create `agent/templates/report.html` and `agent/templates/error.html` as Jinja2 templates; create `agent/mailer.py` as the Resend delivery module; extend `agent/config.py` with `RESEND_API_KEY`; wire into `pipeline.py` with error fallback sending.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.1.6 | HTML template rendering | Pallets-maintained, ships with Flask/Ansible, stable 3.x API, `autoescape` prevents XSS in HTML output |
| resend | 2.23.0 | Transactional email delivery | Developer-first API, Python SDK actively maintained (released Feb 23 2026), typed exceptions, no SMTP setup required |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime (stdlib) | — | Format run_date for subject line and header | Building dynamic subject lines from `IdeaReport.run_date` |
| logging (stdlib) | — | Delivery confirmation log line | Console-only confirmation per CONTEXT.md decision |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 | Python f-strings | f-strings work for simple templates; Jinja2 wins for loops, conditionals, autoescape, and maintainability at >3 ideas |
| Resend | smtplib + MIME | smtplib requires SMTP credentials, TLS config, and manual multipart assembly; Resend handles all of this and adds deliverability infrastructure |
| Resend | sendgrid, mailgun | Both are heavier SDKs; Resend has the simplest Python API and is already a standard choice for developer-built pipelines |

**Installation:**
```bash
pip install Jinja2==3.1.6 resend==2.23.0
```

---

## Architecture Patterns

### Recommended Project Structure

```
agent/
├── config.py           # Add RESEND_API_KEY field (already has EMAIL_RECIPIENT)
├── mailer.py           # NEW: EmailDeliverer class, render + send
├── pipeline.py         # Extended: call mailer after synthesizer, wrap in try/except
├── templates/          # NEW: Jinja2 template directory
│   ├── report.html     # Main ideas email — loops over IdeaReport.ideas
│   └── error.html      # Error notification — single reason string
└── models.py           # IdeaReport already defined, no changes needed
```

### Pattern 1: Jinja2 Template with FileSystemLoader

**What:** Load templates from a `templates/` subdirectory adjacent to the module, using an absolute path so the loader works regardless of `cwd`.
**When to use:** Always — avoids cwd-relative path bugs.

```python
# agent/mailer.py
# Source: https://jinja.palletsprojects.com/en/stable/api/
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

_jinja_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(enabled_extensions=("html",)),
)
```

### Pattern 2: Rendering an IdeaReport to HTML

**What:** Pass the `IdeaReport` and a formatted date to `template.render()`.
**When to use:** Main report email — called after successful synthesis.

```python
# agent/mailer.py
# Source: https://jinja.palletsprojects.com/en/stable/api/
from agent.models import IdeaReport

def render_report(report: IdeaReport) -> tuple[str, str]:
    """Returns (subject, html_body)."""
    template = _jinja_env.get_template("report.html")
    idea_count = len(report.ideas)
    formatted_date = _format_date(report.run_date)  # e.g., "March 3, 2026"
    subject = f"{idea_count} content ideas for this week"
    html_body = template.render(
        ideas=report.ideas,
        header_date=formatted_date,
    )
    return subject, html_body
```

### Pattern 3: Sending via Resend SDK

**What:** Set `resend.api_key` from config, call `resend.Emails.send()` with `html` and `text` params.
**When to use:** Every delivery call.

```python
# agent/mailer.py
# Source: https://resend.com/docs/send-with-python
import resend

def send_email(api_key: str, from_addr: str, to_addr: str,
               subject: str, html: str, text: str) -> str:
    """Returns the sent email ID. Raises resend.exceptions.ResendError on failure."""
    resend.api_key = api_key
    params = {
        "from": from_addr,
        "to": [to_addr],
        "subject": subject,
        "html": html,
        "text": text,
    }
    response = resend.Emails.send(params)
    return response["id"]
```

### Pattern 4: report.html Jinja2 Template

**What:** Numbered list of ideas with inline CSS for email-client compatibility.
**When to use:** Main report rendering.

```html
<!-- agent/templates/report.html -->
<!-- Source: https://jinja.palletsprojects.com/en/stable/templates/ -->
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Georgia, serif; background-color: #ffffff; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 24px;">

  <h2 style="font-size: 20px; font-weight: bold; margin-bottom: 4px;">Your Weekly Content Intel</h2>
  <p style="color: #666666; font-size: 14px; margin-top: 0; margin-bottom: 32px;">{{ header_date }}</p>

  {% for idea in ideas %}
  <div style="margin-bottom: 32px;">
    <p style="font-size: 18px; font-weight: bold; margin: 0 0 4px 0;">{{ loop.index }}. {{ idea.topic }}</p>
    <p style="font-size: 15px; color: #333333; margin: 0 0 12px 0;">{{ idea.angle }}</p>
    <ul style="margin: 0 0 12px 0; padding-left: 20px;">
      {% for point in idea.talking_points %}
      <li style="font-size: 14px; margin-bottom: 6px;">{{ point }}</li>
      {% endfor %}
    </ul>
    <p style="font-size: 13px; color: #666666; font-style: italic; margin: 0 0 8px 0;">{{ idea.rationale }}</p>
    {% if idea.platform or idea.content_format %}
    <p style="font-size: 12px; color: #888888; margin: 0;">
      {% if idea.platform %}Best for: {{ idea.platform }}{% endif %}
      {% if idea.platform and idea.content_format %} &nbsp;|&nbsp; {% endif %}
      {% if idea.content_format %}Format: {{ idea.content_format }}{% endif %}
    </p>
    {% endif %}
  </div>
  {% if not loop.last %}
  <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 0 0 32px 0;">
  {% endif %}
  {% endfor %}

</body>
</html>
```

### Pattern 5: Error Notification Email

**What:** Minimal error email with a single reason string.
**When to use:** When pipeline raises `ValueError` (no valid niches) or Resend API fails.

```html
<!-- agent/templates/error.html -->
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: Georgia, serif; background-color: #ffffff; color: #1a1a1a; max-width: 600px; margin: 0 auto; padding: 24px;">
  <p style="font-size: 15px;">{{ reason }}</p>
</body>
</html>
```

### Pattern 6: Plain-Text Fallback

**What:** Render a plain-text version for multipart email.
**When to use:** Always — passed as `text` param alongside `html` to Resend.

```python
# agent/mailer.py — build plain text from IdeaReport directly (no template needed)
def render_plain_text(report: IdeaReport) -> str:
    lines = []
    for i, idea in enumerate(report.ideas, 1):
        lines.append(f"{i}. {idea.topic}")
        lines.append(f"   {idea.angle}")
        for point in idea.talking_points:
            lines.append(f"   - {point}")
        lines.append(f"   {idea.rationale}")
        if idea.platform:
            lines.append(f"   Best for: {idea.platform}")
        if idea.content_format:
            lines.append(f"   Format: {idea.content_format}")
        lines.append("")  # blank line between ideas
    return "\n".join(lines)
```

### Pattern 7: Config Extension for RESEND_API_KEY

**What:** Add `resend_api_key` field to the existing `Config` dataclass following the established pattern.
**When to use:** Required — Resend needs an API key separate from Anthropic.

```python
# agent/config.py — additions only, following existing pattern
@dataclass
class Config:
    anthropic_api_key: str
    email_recipient: str
    api_call_budget: int
    tavily_api_key: str
    resend_api_key: str        # NEW
    email_from: str            # NEW — e.g., "Content Agent <agent@yourdomain.com>"

    @classmethod
    def from_env(cls) -> "Config":
        required = ["ANTHROPIC_API_KEY", "EMAIL_RECIPIENT", "TAVILY_API_KEY",
                    "RESEND_API_KEY", "EMAIL_FROM"]  # EMAIL_FROM added
        # ... same collect-all-missing pattern
```

### Pattern 8: Pipeline Integration with Error Fallback

**What:** After synthesis, call mailer; on pipeline error, attempt error notification email.
**When to use:** Extends existing `pipeline.py` structure.

```python
# agent/pipeline.py — additions after Phase 3 synthesis block
from agent.mailer import EmailDeliverer

# Phase 4: Deliver report
deliverer = EmailDeliverer(config=config)
deliverer.send_report(idea_report)
```

```python
# In pipeline error handling (wraps existing ValueError raises from synthesizer)
# pipeline.py raises ValueError → run.py catches it → also send error email
# OR: pipeline.py catches ValueError internally and delegates error email to mailer
```

### Anti-Patterns to Avoid

- **Calling `resend.api_key` inside a loop:** Set it once at module import or class init; not on every send call.
- **External `<style>` blocks or linked stylesheets:** Stripped by Gmail. Use inline styles only.
- **Flexbox or CSS Grid for layout:** Not supported in Outlook. Use block elements for a simple vertical list.
- **Reading `ideas_output.json` from disk in the mailer:** The CONTEXT.md decision locks freshness — mailer receives the live `IdeaReport` object from the synthesizer directly via pipeline. No disk reads.
- **Catching `BudgetExceededError` in the mailer:** Follow the existing pattern — budget exceptions propagate to `run.py`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email delivery with deliverability | Custom SMTP + TLS + SPF/DKIM wiring | Resend SDK | Resend handles SPF/DKIM/DMARC on their end; building this manually risks spam filtering |
| HTML escaping in templates | Manual `str.replace()` for `<`, `>`, `&` | Jinja2 `autoescape` | Misses edge cases; Jinja2's autoescape is correct and automatic for `.html` extensions |
| Plain-text extraction from HTML | HTML parser stripping tags | Simple string construction from `IdeaReport` fields | The data model is already structured; parsing HTML back to text is unnecessary complexity |
| Dynamic subject line date formatting | Custom date string logic | `datetime.strptime(run_date, "%Y-%m-%d").strftime(...)` | One line; no library needed |

**Key insight:** Resend offloads all email infrastructure complexity (SMTP, TLS, SPF, DKIM, bounce handling). The team should never build any of that. The only hand-written code is template content and the thin delivery wrapper.

---

## Common Pitfalls

### Pitfall 1: `from` Address Domain Not Verified with Resend

**What goes wrong:** Resend raises `ValidationError` (HTTP 403) with `type: validation_error` if the `from` address domain is not verified in the Resend dashboard.
**Why it happens:** Resend requires DNS records (SPF + DKIM) on the sending domain. Attempting to send from an unverified domain fails at the API level.
**How to avoid:** Add `EMAIL_FROM` to `.env` with a domain the user has verified. Document the domain verification step in `.env.example`. For testing, Resend allows sending from `onboarding@resend.dev` to your own address only.
**Warning signs:** `resend.exceptions.ValidationError` on first `send()` call in a fresh environment.

### Pitfall 2: Inline CSS vs. External Styles

**What goes wrong:** Gmail strips `<style>` blocks and external CSS. An email that looks correct in a browser test renders as unstyled plain text in Gmail.
**Why it happens:** Gmail's HTML sanitizer removes `<style>` tags to prevent CSS injection. Outlook on Windows uses Word's renderer which ignores many CSS properties.
**How to avoid:** Use only `style="..."` attributes on each HTML element. No `<style>` blocks. No external CSS files. Stick to: `font-family`, `font-size`, `font-weight`, `color`, `background-color`, `padding`, `margin`, `border-top`.
**Warning signs:** Beautiful preview in browser, broken in Gmail.

### Pitfall 3: `resend.api_key` Is a Module-Level Global

**What goes wrong:** Setting `resend.api_key` is a side effect that mutates module state. In test environments with multiple tests, a test that sets a bad key can corrupt subsequent tests.
**Why it happens:** Resend SDK uses a module-level variable, not per-instance config.
**How to avoid:** Set `resend.api_key` once during `EmailDeliverer.__init__()`, not inside `send()`. In tests, restore the original value or mock the module.
**Warning signs:** Tests that pass individually but fail in sequence.

### Pitfall 4: Error Email Delivery Can Also Fail

**What goes wrong:** When the pipeline errors and tries to send an error notification email, the Resend call itself may fail (network error, rate limit). Raising in the error handler masks the original exception.
**Why it happens:** The error email path is triggered when things are already broken; the network or API may be the cause.
**How to avoid:** Wrap the error email send in its own `try/except ResendError`; log and swallow delivery failures in the error path. Only the original error should propagate to `run.py`.
**Warning signs:** `run.py` exits with a `ResendError` traceback instead of the original `ValueError`.

### Pitfall 5: `loop.index` vs `loop.index0` in Jinja2

**What goes wrong:** Using `loop.index0` (0-based) when the email should display 1-based idea numbers.
**Why it happens:** Developers familiar with Python's 0-based indexing default to `loop.index0`.
**How to avoid:** Use `loop.index` (1-based) — this is Jinja2's default 1-indexed loop counter. Matches the CONTEXT.md decision ("ideas displayed 1 through N").
**Warning signs:** First idea shows as "0." instead of "1.".

---

## Code Examples

### Sending an Email with HTML and Plain-Text Fallback

```python
# Source: https://resend.com/docs/send-with-python
# Source: https://resend.com/docs/api-reference/emails/send-email
import resend

resend.api_key = "re_..."  # set once

params = {
    "from": "Content Agent <agent@yourdomain.com>",
    "to": ["recipient@example.com"],
    "subject": "7 content ideas for this week",
    "html": "<strong>HTML body</strong>",
    "text": "Plain text fallback body",
}
response = resend.Emails.send(params)
email_id = response["id"]  # e.g., "49a3999c-0ce1-4ea6-ab68-afcd6dc2e794"
```

### Catching Resend Exceptions

```python
# Source: https://github.com/resend/resend-python (exceptions.py)
from resend.exceptions import ResendError, ValidationError, RateLimitError

try:
    response = resend.Emails.send(params)
except ValidationError as e:
    # 400/422 — bad params or unverified domain
    logger.error("Email validation error: %s — %s", e.message, e.suggested_action)
except RateLimitError as e:
    # 429 — quota or rate limit exceeded
    logger.error("Email rate limit: %s", e.message)
except ResendError as e:
    # Catch-all for 401, 403, 500, etc.
    logger.error("Email delivery failed (code=%s): %s", e.code, e.message)
```

### Jinja2 Environment Setup

```python
# Source: https://jinja.palletsprojects.com/en/stable/api/
import os
from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(enabled_extensions=("html",)),
)

# Rendering
template = env.get_template("report.html")
html_output = template.render(ideas=idea_list, header_date="March 3, 2026")
```

### Jinja2 Optional Field Display Pattern

```jinja2
{# Source: https://jinja.palletsprojects.com/en/stable/templates/ #}
{% if idea.platform or idea.content_format %}
<p style="font-size: 12px; color: #888888; margin: 0;">
  {% if idea.platform %}Best for: {{ idea.platform }}{% endif %}
  {% if idea.platform and idea.content_format %} | {% endif %}
  {% if idea.content_format %}Format: {{ idea.content_format }}{% endif %}
</p>
{% endif %}
```

### Date Formatting for Subject Line

```python
# stdlib only — no extra dependencies
from datetime import datetime

def _format_date(run_date: str) -> str:
    """Convert '2026-03-03' to 'March 3, 2026'."""
    return datetime.strptime(run_date, "%Y-%m-%d").strftime("%B %-d, %Y")

def build_subject(idea_count: int, run_date: str) -> str:
    """e.g., '7 content ideas for this week'"""
    return f"{idea_count} content idea{'s' if idea_count != 1 else ''} for this week"
```

Note: `%-d` (Linux/macOS) removes leading zero from day. On Windows use `%#d`. Since this project runs on GitHub Actions (Linux) and local macOS dev, `%-d` is safe.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| smtplib + MIME multipart manual assembly | Resend SDK `resend.Emails.send()` | 2022-2023 (Resend launched) | Eliminates SMTP config, TLS setup, SPF/DKIM wiring |
| External `<style>` blocks in HTML email | Inline `style=""` attributes | Email clients have always stripped styles; awareness increased ~2015 | Required for Gmail compatibility |
| Table-based email layout | Div/block layout (for simple single-column) | Gmail improved rendering ~2020 for simple cases | For a simple vertical list, tables are no longer strictly required |
| `resend.Emails.send()` (pre-2.0) | Same API, minor improvements in v2.0 (typed responses, better exceptions) | resend-python 2.0 changelog | Better exception types, `SendResponse` typed object |

**Deprecated/outdated:**
- `smtplib` for transactional email: Still works but adds infrastructure burden; replaced by services like Resend for developer-built pipelines.

---

## Open Questions

1. **`EMAIL_FROM` address configuration**
   - What we know: Resend requires a verified domain for the `from` address. The config already has `EMAIL_RECIPIENT` but no `EMAIL_FROM`.
   - What's unclear: The user needs to have verified a domain with Resend. For testing, `onboarding@resend.dev` works only for sending to the account's own email.
   - Recommendation: Add `EMAIL_FROM` as a required env var in `Config.from_env()`. Document in `.env.example`. The user will need to verify their domain in Resend dashboard before Phase 4 works end-to-end.

2. **Error email triggering point**
   - What we know: `ValueError` from `IdeaSynthesizer.run()` propagates to `run.py`. The CONTEXT.md says to send an error email on pipeline failure.
   - What's unclear: Should `pipeline.py` catch `ValueError` internally to send the error email, or should `run.py` do it?
   - Recommendation: Have `pipeline.py` catch `ValueError` from the synthesizer, send the error email via mailer, then re-raise (or return) — keeps error email logic co-located with the pipeline steps that can produce errors.

3. **`%-d` date formatting portability**
   - What we know: `%-d` removes leading zero from day on Linux/macOS. `%#d` is the Windows equivalent.
   - What's unclear: The project runs on macOS dev + GitHub Actions (Linux). No Windows runner is indicated.
   - Recommendation: Use `%-d` — safe for the known targets. Document in a comment.

---

## Sources

### Primary (HIGH confidence)
- https://resend.com/docs/api-reference/emails/send-email — Full SendParams including `text` field, response structure `{"id": "..."}`, verified 2026-03-03
- https://resend.com/docs/api-reference/errors — Complete error code reference, all HTTP status codes, verified 2026-03-03
- https://github.com/resend/resend-python (exceptions.py) — Exception class hierarchy: `ResendError`, `ValidationError`, `RateLimitError`, `MissingApiKeyError`, etc., verified 2026-03-03
- https://jinja.palletsprojects.com/en/stable/api/ — `Environment`, `FileSystemLoader`, `select_autoescape`, `template.render()` API, verified 2026-03-03
- https://jinja.palletsprojects.com/en/stable/templates/ — `loop.index`, `{% if %}` blocks, `default` filter, verified 2026-03-03
- https://pypi.org/project/resend/ — Version 2.23.0, released February 23, 2026
- https://pypi.org/project/Jinja2/ — Version 3.1.6, released March 5, 2025

### Secondary (MEDIUM confidence)
- https://resend.com/docs/send-with-python — Official Python quickstart, `resend.Emails.send(params)` pattern
- https://resend.com/docs/dashboard/domains/introduction — Domain verification requirement (SPF + DKIM)

### Tertiary (LOW confidence)
- CSS email compatibility patterns (from multiple web searches) — Safe CSS properties, inline-only recommendation. Cross-verified across Campaign Monitor, Gmail developer docs, and multiple 2026 articles; elevated to MEDIUM.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Jinja2 and Resend versions verified from PyPI and official docs; Resend 2.23.0 released February 2026 (current)
- Architecture: HIGH — Patterns derived from official Jinja2 and Resend docs; align with existing project patterns in synthesizer.py and config.py
- Pitfalls: HIGH — Domain verification requirement and inline CSS constraints verified from official Resend and Gmail docs; exception types verified from SDK source

**Research date:** 2026-03-03
**Valid until:** 2026-04-03 (Resend API is stable; Jinja2 3.1.x has been stable for a year; check for resend SDK updates if delayed)
