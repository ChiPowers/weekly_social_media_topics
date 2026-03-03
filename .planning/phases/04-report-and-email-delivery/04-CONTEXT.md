# Phase 4: Report and Email Delivery - Context

**Gathered:** 2026-03-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Format the `IdeaReport` (5–10 `ContentIdea` objects from Phase 3) into an HTML email with a plain-text fallback and deliver it to the configured recipient via Resend. No user input at delivery time. Error notification email sent on pipeline failure.

</domain>

<decisions>
## Implementation Decisions

### Email Layout and Visual Style
- **Visual polish:** Clean minimal — styled text, clear hierarchy, no heavy design. Minimal CSS, no images. Renders reliably in all email clients.
- **Structure:** Numbered list — ideas displayed 1 through N in sequence, no grid or columns.
- **Color scheme:** Light background, dark text — neutral/white. No accent colors.
- **Dividers:** Horizontal rule between each idea for visual separation.

### Idea Presentation
- **Idea label:** Number + topic name as the primary heading — e.g., "1. Skincare Routines" (bold). The topic name is the primary label.
- **Angle:** Displayed as a subheading under the topic name — the specific hook framing.
- **Talking points:** All 2–3 bullets shown — these are the actual content the creator would cover.
- **Rationale:** Italicized or muted text below the bullets — visually distinct as supporting evidence, not the main message.
- **Optional fields:** `platform` and `content_format` shown as small inline labels when present (e.g., "Best for: TikTok", "Format: Short-form video"). Omitted gracefully when null.

### Subject Line and Framing
- **Subject line:** Dynamic — includes the date or week. e.g., "Your content ideas — week of March 3" or "5 content ideas for this week".
- **Email header:** Short header only — title + date, then straight into ideas. e.g., "Your Weekly Content Intel — March 3, 2026". No intro paragraph.
- **Footer:** None — no footer at the bottom of the email.

### Error and Edge Case Behavior
- **On pipeline error (no valid niches, API failure):** Send a brief error notification email. Subject: "Content agent error — [date]". Body: one-line reason (e.g., "No trending niches with named creators found this week.") — minimal, no stack trace.
- **Freshness:** Email always uses ideas just generated in the current run. Never send from a stale `ideas_output.json`. Pipeline is sequential: research → synthesize → email.
- **Delivery confirmation:** Log to console only — "Email sent to [recipient] at [time]". No delivery receipt file.

### Claude's Discretion
- Jinja2 template structure and variable naming
- Exact inline CSS values (font sizes, spacing, colors within the neutral/minimal constraint)
- Plain-text fallback formatting
- Resend API integration details (how to instantiate client, which SDK method)
- How to pass error reason string to the error email template

</decisions>

<specifics>
## Specific Ideas

- The rationale should read as evidence/proof, visually subordinate to the actionable content (angle + bullets). Italics or a muted color (#666 or similar) achieves this.
- The idea label pattern: bold number + topic name as heading, angle as a smaller subheading directly below — topic anchors the niche, angle delivers the hook.
- Subject line should convey how many ideas are included when possible: "7 content ideas for this week" > "Your content ideas — week of March 3".

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-report-and-email-delivery*
*Context gathered: 2026-03-03*
