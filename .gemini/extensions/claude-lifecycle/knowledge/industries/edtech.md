---
name: edtech
display_name: EdTech (courses / learning apps)
funnel: [first_visit, sign_up, course_start, lesson_complete, purchase]
conversion_events: [purchase, subscription_start]
activation_definition: First lesson completed (lesson_complete) within 72 hours of sign_up — enrollment alone is not activation; starting to learn is.
churn_signal: Broken learning rhythm — no lesson_complete for 5–7 days after a period of regular activity (a broken streak precedes uninstall/cancellation by weeks).
pattern_priorities:
  welcome-onboarding: P0
  activation: P0
  churn-prevention: P0
  milestone: P1
  trial-conversion: P1
  payment-failure: P1
  winback: P1
  feature-adoption: P1
  progressive-profiling: P2
  upsell-cross-sell: P2
  abandoned-cart: P2
  referral: P2
  feedback-nps: P2
  reactivation: P2
  channel-opt-in: P2
  gamified-rewards: P2
  lead-nurture: P1
typical_channels: [push, email, in-app, whatsapp]
---

# EdTech Playbook

Learning products sell a transformation, but retention lives or dies on a habit: **the completion-rate crisis is THE retention problem** — most learners who enroll never finish, and every dropout is future churn, a lost renewal, and a silent detractor. Lifecycle marketing in edtech is therefore closer to a coaching program than a promo calendar: the core journeys protect the learning rhythm (streaks), rescue it when it breaks, and celebrate progress — because celebrated progress is the product's proof of value. Monetization (course purchase, subscription) converts most reliably from users who are actively learning, so engagement journeys are revenue journeys here. Push and in-app do the daily-rhythm work; email carries progress summaries and monetization.

## Canonical funnel

| Step | Expected event | Notes |
|---|---|---|
| Visit | `first_visit` / `session_start` | |
| Register | `sign_up` | Freemium or trial entry in most apps |
| Enroll / begin | `course_start` (or `tutorial_begin` in app conventions) | Choosing a course is commitment, not yet activation |
| Learn | `lesson_complete` | The heartbeat event; the biggest drop-off is between course_start and a *second/third* lesson_complete |
| Pay | `purchase` / `subscription_start` | Course sales and/or subscription; must carry `value` |

## Event expectations

**Must-have** (missing any of these blocks P0 journeys): `sign_up`, `course_start`, `lesson_complete` (with course/lesson identifiers), a revenue event (`purchase` or `subscription_start`).
**Nice-to-have** (unlocks depth/branches): streak/`unlock_achievement`-style events, course_complete, quiz/assessment results, `trial_start`/`trial_end`, `payment_failed`, learning-goal or level as user property, time-of-day usage pattern, `add_to_cart` (course marketplaces).

## Pattern priorities — rationale

- **welcome-onboarding P0** — goal-setting and first-lesson push in the first session; learners who articulate a goal and start immediately form the habit. Onboarding ends at the first `lesson_complete`, not at profile completion.
- **activation P0** — distinct from welcome here: the enrollment→learning gap is the sector's biggest leak. A user with `course_start` but no `lesson_complete` within 72h needs a dedicated rescue with the friction removed ("your first lesson is 4 minutes").
- **churn-prevention P0** — streak-break rescue: the broken learning rhythm is the earliest, most reliable churn signal, and the intervention window is days, not weeks. Tone is critical — encouraging re-entry, never guilt (see lexicon); one missed day is normal, the message's job is to make returning feel small and easy.
- **milestone P1 (deliberately promoted)** — progress celebration is unusually high-value in edtech, worth far more than its usual P2: completed units, streak records, course completion are the moments the product's value becomes visible to the learner. These messages retain, convert to paid, and are the natural referral trigger. Kept at P1 only because the P0 slots protect the habit itself; promote to P0 for gamified daily-practice apps.
- **trial-conversion P1** — for subscription learning apps; conversion messaging should lead with the learner's own progress data ("you've completed 12 lessons this week") rather than feature lists. P0 if the business is trial-led.
- **payment-failure P1** — wherever subscription billing exists; transactional, cheap, and protects learners mid-course from involuntary lockout. P0 if subscriptions dominate revenue.
- **winback P1** — lapsed learners left mid-course; "resume where you left off" with concrete position ("Unit 3, lesson 2 is waiting") outperforms generic comebacks.
- **feature-adoption P1** — reminders, offline lessons, practice modes: each adopted study feature reinforces the habit loop.
- **abandoned-cart P2** — applicable only to course-marketplace models with carts; N/A for pure subscription apps.
- **browse-abandonment, replenishment, back-in-stock, price-drop, post-purchase, loyalty, anniversary — not applicable (default)**: no catalog/stock mechanics; post-purchase is subsumed by activation/engagement (the "purchase" is a commitment to learn, and the follow-up is getting them learning); marketplace-model accounts may re-enable browse-abandonment and price-drop at intake, with the caveat that perpetual discounting trains users to never pay full price.

- **lead-nurture P1** — course/program decisions are researched long before enrollment; leads from syllabus downloads and info sessions convert on education and proof, not product tours.

## Sector-specific timing & cadence

- First lesson nudge: same session if possible (in-app), else within 24h of sign_up.
- Daily practice reminder: user-chosen time where possible; otherwise anchor to the user's own observed study time — a fixed 19:00 blast ignores the habit you're building.
- Streak-break rescue: first touch within 24–48h of the first missed day (gentle), escalating usefulness — a shorter/easier re-entry lesson — rather than escalating pressure.
- Milestones: send at the moment of achievement (in-app/push), with a weekly email progress digest as the summary layer.
- Respect study-hour reality: learners are often students — evening engagement is normal, but quiet hours per channel rules still bind.
- Seasonality: new-year resolutions, back-to-school, and exam calendars (TR: YKS/LGS/KPSS periods for test-prep products) drive both acquisition waves and churn cliffs after them.

## Seasonality

- The **academic calendar** is the metronome: back-to-school brings acquisition waves, term breaks bring rhythm breaks (a streak lost to a holiday is not a churn signal — adjust churn-prevention sensitivity around known breaks).
- **Exam seasons** (TR: YKS/LGS/KPSS) create intense pre-exam engagement and a predictable post-exam churn cliff; a post-exam journey ("what's next") converts a cliff into a transition.
- **New-year resolutions** are the sector's biggest motivation spike — onboarding and reactivation both work harder in January, and the follow-through problem (resolution abandonment) makes streak-protection journeys more valuable than acquisition messaging in February.
- Seasonal windows modify existing journeys (timing, framing, churn thresholds) — they are not a separate journey type. Peak-season attributed numbers inflate with the motivational baseline; holdouts matter more (see [measurement](../measurement.md)).

## Segmentation attributes that matter

Learning goal and course category, streak status / days-since-last-lesson (the operative segment), progress-through-course percentage, free vs trial vs paying, study-time-of-day pattern, learner type where known (student, professional, hobbyist — changes tone and timing).

## Intake questions (sector-specific)

1. What is the business model — course marketplace (one-off purchases), subscription, freemium, B2B/school licenses, or mixed?
2. Is there a streak/daily-goal mechanic in the product, and is streak state available as an event or user property?
3. What does course structure look like (lesson length, expected pace) — what is a realistic "regular" learning rhythm to protect?
4. Do you know learners' goals (exam prep, career, hobby) at sign-up? Is the goal stored where messaging can use it?
5. Are there live components (cohorts, deadlines, classes) that create real time pressure, or is everything self-paced?
