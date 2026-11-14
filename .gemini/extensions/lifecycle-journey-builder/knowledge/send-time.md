---
name: send-time
purpose: Within-window send-time optimization for email, push, and SMS. Referenced from channel files' quiet_hours field.
---

# Send-Time Optimization

This is a different layer from **quiet hours**. Quiet hours (`knowledge/channels/*.md`, `knowledge/compliance/consent-and-quiet-hours.md`) are a hard floor — never send inside them, no exceptions. Send-time optimization is a soft preference for *when inside the allowed window* a message is most likely to land well. Never use anything in this file to justify sending inside a channel's quiet hours.

## Rule 1 — real data beats every heuristic below

If the connected source (GA4, CRM export) has engagement-by-hour signal for this specific account — open/click/session timestamps — use that over any generic pattern. This is CLAUDE.md rule 9's trust hierarchy applied to timing: **account's own data > sector heuristic > this file**. `event-analyst` should surface an engagement-by-hour distribution when the source data supports it; when it does, the heuristics below don't apply.

## Rule 2 — everything past this point is an unsourced starting hypothesis, not a fact

No source found for send-time optimization had citations, named studies, or reproducible methodology. What follows is drawn from uncited marketing vendor guides with no data behind their specific claims. Treat every clock time below as a first guess to A/B test, never a measured result. Per `agents/copy-writer.md`'s existing convention, any of this surfaced to a user must be framed as "sektör pratiği olarak" / "as a common practice" — never as this account's reality.

### Reasoning framework: habitual-checking moments

Rather than memorizing clock times, reason from moments a user is likely to check their device on their own: waking up, commuting, a work break, winding down before bed. A trigger-relevant message timed near one of these moments has a plausible mechanism for working, independent of which exact hour a blog post names.

### Starting heuristics by segment (unsourced, test before trusting)

- **B2B:** weekday mid-morning or just after lunch; Monday mornings and Friday afternoons tend to underperform (catch-up / wind-down).
- **B2C:** evenings and weekends outperform weekday daytime; Friday afternoon can work for weekend-planning-relevant offers.
- **Push specifically:** morning (~8–10), lunch (~12–14), and evening (~19–21) are commonly cited windows — three separate hypotheses to test, not three guaranteed slots.
- **Decision fatigue** (avoid stacking asks late in the day) is a popular but empirically contested idea — the underlying "ego depletion" research has had major replication failures. Treat it as a weak prior at most, not a rule to encode with any confidence.

### What's a verified fact, not a heuristic

Platform push-permission mechanics are not a "best time" question and don't need A/B testing: iOS requires explicit opt-in, Android 13+ also requires explicit runtime opt-in (older Android defaulted on). Already captured in `knowledge/channels/push.md`'s `consent_required` field — noted here only so it isn't confused with the soft heuristics above.

## SMS — checked, nothing to add

A third vendor guide was checked specifically for SMS. It doesn't add anything past what's already in `knowledge/channels/sms.md` and `knowledge/compliance/consent-and-quiet-hours.md` — and in one place it's actively misleading to import: it frames "business hours, 10am–8pm" as a discovered optimization insight, but that's US-centric TCPA framing, not a within-window signal. This repo's actual default (TR/İYS: 10:00–20:00 allowed) is already stricter and already documented, deliberately, in the compliance file. No SMS-specific heuristic added here; the allowed window is narrow enough that Rule 1 (real data) matters more than any generic guess for the channel with the least room to guess in.

## Never do

- Never state a specific send hour as measured fact for an account that hasn't been tested.
- Never let this file override a channel's quiet_hours.
- Never fabricate a citation for the heuristics above — if asked for a source, name the actual one (an uncited vendor blog), don't dress it up as research.
