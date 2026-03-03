# Phase 3: LLM Orchestrator - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

LLM synthesis pipeline that reads `ResearchFindings` (from `research_output.json`) and produces a structured list of 5–10 `ContentIdea` objects. Each idea is a topic + angle (specific hook/framing) with a data-backed rationale citing real evidence from the research. No user input required at synthesis time.

</domain>

<decisions>
## Implementation Decisions

### Idea Format
- **Angle definition:** A specific hook or framing — title-level (e.g., "Why 80% of TikTok creators are using the wrong hook format"), NOT a format recommendation or audience segment
- **Idea depth:** Title + 2–3 bullet talking points per idea — enough to act on immediately without writing a full brief
- **Platform recommendation:** Include when research clearly points to a specific platform; omit when attribution is ambiguous — not a required field
- **Content format/media type:** Include only when research surfaced a clear format signal (e.g., short-form video dominates the niche); omit otherwise — not a required field

### Rationale Evidence Standard
- **Minimum citation requirement:** Creator name + platform + metric (e.g., "GlowWithMe (850K followers, TikTok) posts daily 60-second routines and saw 3x engagement this week")
- **No speculation:** Do not include "why it works" explanations — evidence citation is sufficient, no LLM speculation about audience psychology
- **Evidence diversity:** Each idea must cite different evidence — no repeating the same creator across multiple ideas in one report
- **Timeframe language:** Always include "this week" or "recently" in the rationale — reinforces that it's fresh intel, not evergreen advice

### Thin Research Handling
- **No named creators in niche:** Skip the niche entirely — do not generate an idea without a credible creator citation
- **Fewer than 5 ideas available:** Still produce and deliver the report — quality over count, 3 strong ideas beats delaying
- **Empty research (zero niches):** Halt and log an error — do not attempt synthesis, do not generate ideas from Claude's general knowledge

### Claude's Discretion
- How to structure the multi-pass LLM prompts (trend extraction pass, creator signal pass, idea generation pass)
- Pydantic schema field names for `ContentIdea`
- Retry logic details (how many retries, what triggers a retry)
- How to batch niches for the synthesis prompt (one niche per call vs. all niches in one call)

</decisions>

<specifics>
## Specific Ideas

- The rationale should read like insider intelligence, not a blog post summary — specific numbers and names, not general claims
- "Title + 2–3 bullets" means the title is the hook and the bullets are the talking points you'd actually cover in the content, not meta-notes about the idea

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-llm-orchestrator*
*Context gathered: 2026-03-02*
