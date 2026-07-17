---
name: calendar-rules
purpose: Temporal conflict rules — what evergreen journeys do when a campaign period (Black Friday, seasonal sale, launch) is running. Consumed by lifecycle-journeys' conflict review.
---

# Calendar Rules — Campaigns vs Evergreen

The portfolio's frequency math is correct on an average week and silently wrong on a campaign week: Black Friday adds 3-4 campaign sends on top of every evergreen journey, and nobody declared that anywhere. CRM is temporal; the conflict review must be too.

## The declaration

Campaign windows come from intake ("known campaign calendar" question) or the brand config's `campaign_windows` list — real dated windows, never guessed. No declared windows → these rules stay dormant and the portfolio says so in one line ("campaign-period behavior undeclared — revisit before the next peak").

## Behavior classes during a declared campaign window

| Class | Patterns | Behavior in-window |
|---|---|---|
| **Never pauses** | payment-failure (dunning), transactional layer | Runs untouched — a lapsed card during Black Friday is MORE urgent, not less |
| **Runs, incentive-suppressed** | abandoned-cart, browse-abandonment, back-in-stock, price-drop | The journey runs (recovery matters most at peak volume) but its own incentive steps are suppressed while a deeper campaign offer is live — two competing discounts in one inbox is offer cannibalization, and the journey's smaller coupon *undercuts* the campaign anchor |
| **Pauses, resumes with cool-down** | winback, reactivation, feedback-nps, referral, anniversary, milestone, gamified-rewards, progressive-profiling, channel-opt-in, lead-nurture | Relationship touches drown at peak and their metrics poison (open rates crater against campaign volume). Pause at window start, resume **48–72h after** window end — the inbox needs to cool before a "we miss you" reads as anything but noise |
| **Judgment per run** | welcome-onboarding, activation, trial-conversion, post-purchase, churn-prevention, upsell-cross-sell, feature-adoption, account-onboarding | Time-sensitive to the USER's clock, not the calendar's — default: keep running but drop to the essential steps (a trial expiring during the campaign still expires); the portfolio states the choice per journey |

## Cap math on campaign weeks

Weekly frequency caps (compliance file) do **not** grow because it's a campaign week — campaign sends count toward the same 8/week total. The conflict review's worst case on a declared campaign week = evergreen worst case + declared campaign sends; over cap → evergreen yields (that's what the pause classes above implement), the campaign never silently steals the budget. The declared sends go into the registry as `campaign_msgs_per_week` — `validate_output.py` re-runs the cap math with them included, so this rule is enforced in code, not just prose.

## Post-window rule

Paused journeys resume from their **entry gate**, not mid-sequence — a user who entered winback 3 weeks ago doesn't get step 4 cold after a two-week gap; they re-qualify or exit. Measurement note: windows overlapping a campaign period inherit the seasonality caution in [measurement.md](measurement.md) — attributed numbers inflate on elevated baselines.
