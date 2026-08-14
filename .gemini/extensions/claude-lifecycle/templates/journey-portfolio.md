# Journey Portfolio Template

The portfolio is the top-level deliverable of `lifecycle-journeys`. It always precedes individual journey docs.

**Multi-vertical brands** (brand config has `verticals` set): the header's Industry/DQS/Activation line and the stage-coverage table (section 3) repeat once per vertical, and section 3 opens with a cross-vertical summary rollup before the per-vertical detail; the portfolio table (section 2) gains a Vertical column; conflict & frequency review (section 4) stays **one shared section for the whole portfolio**, never split per vertical — a user eligible for journeys in two verticals is still one person subject to one set of caps.

---

# Lifecycle Journey Portfolio — <Company / Project>

**Generated:** <date> · **Data tier:** T1 | T2 | T3
**Goal weighting:** <user goal from intake, e.g. "retention-first">

**Single-industry brands:** **Industry:** <sector> · **DQS:** <n>/100 · **Activation:** ready | **blocked — <reason, e.g. no per-user identity>** *(mandatory when the DQS activation flag is set; see docs/data-quality-score.md hard rule 3)*

**Multi-vertical brands** — one row per vertical instead of the line above:

| Vertical | Industry | DQS | Activation |
|---|---|---|---|
| <name> | <sector> | <n>/100 | ready \| blocked — <reason> |

## 1. Executive summary (required)

3–5 sentences: what data was available, how many journeys were generated (across which verticals, if multi-vertical), which lifecycle stages they cover, and the single most important journey to launch first.

## 2. Portfolio table (required)

| # | Journey | Vertical *(multi-vertical brands only)* | ID | Stage | Priority | Depth | Channels | Status |
|---|---------|---|----|----|----------|-------|----------|--------|
| 1 | <name> | <vertical name> | `<id>` | Activation | P0 | 7 steps, branched | email+push | ✅ generated |
| 2 | <name> | <vertical name> | `<id>` | Revenue | P0 | 5 steps | email | ✅ generated |
| … | | | | | | | | |
| n | <name> | <vertical name> | `<id>` | Winback | P1 | — | — | 🔒 blocked — missing `<event>` |

Status values: `✅ generated` · `🔒 blocked — missing <event>` (goes to tracking plan) · `⏸ deferred` (low priority for stated goal).

The Vertical column (multi-vertical brands only) and each row's Depth carry into `portfolio.json`'s `vertical` and the journey JSON's `depth_class` fields respectively — this table is not the only place either fact lives, and the two must agree (see `scripts/validate_output.py consistency`, and the portfolio registry's `vertical` field per journey).

## 3. Lifecycle stage coverage (required)

**Multi-vertical brands only — cross-vertical summary first:** one compact rollup row per vertical, before the detailed per-vertical tables below. This is the "shape of the whole portfolio" view — a reader shouldn't have to scan every vertical's full stage table just to see which vertical is furthest along or which has the most gaps.

| Vertical | DQS | Activation | Journeys generated | Blind stages |
|---|---|---|---|---|
| <name> | <n>/100 | ready \| blocked | <n> | <n> (<list, or "none">) |

**Single-industry brands:** one table. **Multi-vertical brands:** one table per vertical, each labeled with its vertical name, after the summary above — coverage in one product line never offsets a blind stage in another, which is exactly why the summary row's "Blind stages" count exists: it surfaces the gap at a glance without pretending it's fixable by looking at a different vertical's numbers.

| Stage | Journeys | Coverage verdict |
|---|---|---|
| Acquisition | <ids or —> | covered / gap / not applicable |
| Activation | | |
| Engagement | | |
| Revenue | | |
| Retention | | |
| Winback | | |

Every gap gets one sentence: why it exists (missing data vs. low priority) and what unblocks it.

## 4. Conflict & frequency review (required)

One shared section across the whole portfolio, always — including for multi-vertical brands. Vertical boundaries are an internal planning split, not an exemption from frequency caps.

- Journeys sharing a trigger or audience, and which wins.
- Worst-case messages/user/week if all journeys run; flag if it exceeds the cap in [consent-and-quiet-hours.md](../knowledge/compliance/consent-and-quiet-hours.md).

## 5. Launch roadmap (required)

Ordered list: which journeys to launch in week 1 / month 1 / later, with one-line rationale each.

## 6. Tracking plan summary *(if applicable)*

Count of blocked journeys and the top 3 missing events by unlocked value. Full detail in [tracking-plan.md](tracking-plan.md) output.
