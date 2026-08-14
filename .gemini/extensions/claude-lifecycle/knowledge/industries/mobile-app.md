---
name: mobile-app
display_name: Mobile app (consumer apps & games)
funnel: [first_open, session_start, tutorial_begin, tutorial_complete, feature_used, purchase]
conversion_events: [purchase]
activation_definition: tutorial_complete (or the app's equivalent first-success event) within 24 hours of first_open.
churn_signal: No session for 3 consecutive days in the first month, or 7+ days thereafter; app_remove is hard churn (push channel lost).
pattern_priorities:
  welcome-onboarding: P0
  activation: P0
  churn-prevention: P0
  reactivation: P0
  milestone: P1
  feature-adoption: P1
  upsell-cross-sell: P1
  winback: P1
  progressive-profiling: P2
  loyalty: P2
  referral: P2
  feedback-nps: P2
  payment-failure: P2
  anniversary: P2
  channel-opt-in: P1
  gamified-rewards: P2
typical_channels: [push, in_app, email]
---

# Mobile App Playbook

Session-based economics: no cart, no contract — just the daily question of whether the app gets opened. Decision cycles are minutes (install to first session), relationships live or die inside the first week, and value is framed as day-1 / day-7 / day-30 retention rather than a purchase funnel. Most installs churn within days, so lifecycle work front-loads brutally: activate on day 0, build a session habit by day 7, and re-engage lapses within hours-to-days, not weeks. Push is the dominant channel and also the scarcest resource — permission is revocable and `app_remove` ends the relationship on the highest-reach channel, so every send is a retention bet. Email is the fallback for lapsed and uninstalled users; in-app messages carry monetization and feature discovery.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Install & open | `first_open` | Day-0 clock starts here |
| Return visit | `session_start` | Frequency/recency source for all retention math |
| Onboarding begins | `tutorial_begin` | |
| Onboarding done | `tutorial_complete` | Activation event; biggest drop-off is first_open → tutorial_complete |
| Habitual use | `feature_used` / `level_up` / `post_score` | App-specific engagement vocabulary |
| Monetization | `purchase` (IAP or subscription) | Ad-monetized apps: retention *is* revenue — sessions proxy conversion |
| Loss | `app_remove` (Android only) | iOS uninstall is inferred from push token death |

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `first_open`, `session_start`, `tutorial_complete` (or a designated first-success event).
**Nice-to-have** (unlocks depth/branches): `tutorial_begin`, `feature_used`, `level_up`/`unlock_achievement`, `purchase` with `value`, `spend_virtual_currency`, `app_remove`, push-permission status as an attribute, `share`, notification-open tracking.

## Pattern priorities — rationale

- **welcome-onboarding P0** — the day-0 session decides everything; users who don't finish onboarding in the first session rarely return for a second.
- **activation P0** — tutorial_complete is the strongest single predictor of day-7 retention; every un-activated install is a countdown to uninstall.
- **churn-prevention P0** — engagement decays in days, not months; a 2–3 day session gap in month one is already an emergency, and push can still reach the user.
- **reactivation P0** — dormant-but-installed users are the cheapest audience the app will ever have; once `app_remove` fires, only email/SMS remain and win rates collapse.
- **channel-opt-in P1** — push permission is the app's highest-reach channel and a one-shot OS resource; the soft-ask → native-prompt sequencing in this pattern is the difference between owning the channel and losing it on day 0.
- **milestone P1** — streaks, levels, and achievement notifications are the habit engine for games and habit apps; promote to P0 for streak-mechanic products.
- **upsell-cross-sell P1** — IAP/subscription offers timed to engagement peaks (post level-up, post streak), never to lapses.
- **payment-failure P2** — only relevant for subscription apps; app-store billing handles most dunning, so this is P2 unless direct billing exists.
- **trial-conversion — contextual, not scored** — applies only to subscription apps with an explicit trial; if present, treat with trial mechanics from the SaaS playbook.
- **abandoned-cart, browse-abandonment, replenishment, back-in-stock, price-drop, post-purchase — not applicable** (no cart, no catalog, no inventory; post-IAP care is handled by milestone and feature-adoption). Shopping apps are e-commerce with an app shell — use the ecommerce playbook instead.

## Sector-specific timing & cadence

- Day-0: onboarding push only if the user stalled mid-tutorial; wait at least 2–4 hours after first_open before the first push.
- Days 1–7: this is the habit window; one well-timed push per day is the ceiling, and it must reference something real (progress, content, streak) — generic "come back" pushes burn permission.
- Lapse response: first re-engagement touch within 24–48h of a broken pattern in month one; 3–7 days for established users.
- Send at the user's own historical session time-of-day when known; never default to morning blasts.
- Quiet hours are absolute (respect knowledge/channels/push.md); games skew evening, utility apps skew commute hours.
- Uninstall (`app_remove` / dead token): switch to email within days while the app is still remembered.

## Seasonality

- **Holiday periods** shift usage patterns hard in both directions — games and entertainment apps spike, utility and commute-tied apps dip; know which side the app is on before scheduling around holidays.
- **Platform sale/featuring seasons** (app-store seasonal promotions, new-device gift waves around year-end) bring install surges of low-intent users — day-0 onboarding journeys carry more weight, and cohort comparisons across these windows mislead.
- **New-year resolution waves** matter for habit/fitness/learning apps: big January cohorts with steep drop-off; streak-protection journeys earn a temporary promotion.
- Seasonal windows modify existing journeys (push timing, day-0 emphasis, re-engagement framing) — they are not a separate journey type. Surge-window attributed retention inflates with the baseline; holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

Days since install (day-0/1–7/8–30/30+ cohorts), activation state (tutorial done or not), session frequency tier (daily / weekly / lapsing), push permission status, payer vs non-payer (and spend tier), platform (iOS/Android — differs in both reachability and uninstall visibility).

## Intake questions (sector-specific)

1. What is your first-success moment — tutorial completion, first level cleared, first item created — and which event marks it?
2. How do you monetize: IAP, subscription, ads, or a mix? (Determines whether `purchase` or session frequency is the revenue KPI.)
3. Roughly what share of users grants push permission, and do you track permission status per user?
4. What are your current day-1 and day-7 retention rates, even approximately?
5. Do you have email addresses for a meaningful share of users, or is push the only owned channel?
