# Data Assessment Report — Moda Nova

*Output of `/lifecycle connect` · synthetic showcase data*

## 1. Source & tier

| Field | Value |
|---|---|
| Source | GA4 property "Moda Nova — Web" (via GA4 MCP tools) |
| Tier | **T1** (live analytics connection) |
| Date range | last 90 days (2026-04-13 → 2026-07-11) |
| Industry playbook | [ecommerce](../../knowledge/industries/ecommerce.md) |
| Users in range | ≈ 118,000 (≈ 40k monthly) |

## 2. DQS breakdown

Scored per [docs/data-quality-score.md](../../docs/data-quality-score.md), against the ecommerce playbook's event expectations.

| Component | Score | Max | Reasoning |
|---|---:|---:|---|
| Event diversity | 20 | 25 | 11 meaningful events across 4+ lifecycle stages (activation, engagement, revenue-intent, revenue, retention). Low end of the 11+ band (20–25) because several events cluster in revenue-intent and there are no post-purchase engagement events beyond `refund`. |
| Conversion events | 16 | 25 | One true revenue event: `purchase` with full `value`/`currency`/`items` params (13–18 band). No second conversion type (no subscription, no lead) — that caps this component. |
| Funnel completeness | 20 | 20 | All 7 canonical funnel steps tracked consecutively: `session_start` → `view_item_list` → `view_item` → `add_to_cart` → `begin_checkout` → `add_payment_info` → `purchase`. 7/7 × 20 = 20. |
| User attributes / segments | 9 | 15 | `user_id` set on logged-in sessions (≈ 38% of sessions) and a consent-state user property is synced. No RFM-computable history queryable from GA4 (8–12 band, mid). |
| Volume sufficiency | 9 | 15 | 2,166 purchases / 90 days ≈ **722 conversions/month** — inside the 100–1k band (6–10). Enough for journey KPIs, thin for per-branch statistics. |
| **Total** | **74** | **100** | |

**Depth class: branched (DQS ≥ 70).** Journeys may use behavioral branches, value gates, and multi-channel orchestration. What would raise the score: a second conversion type (e.g. a loyalty subscription) and RFM attributes (+ up to 15 combined); volume moves to the top band at ≥ 1k purchases/month.

## 3. Event inventory (90 days)

Noise events excluded from diversity scoring (`page_view` 1.9M, `session_start` 186k, `scroll`, `first_visit`, `user_engagement`) — counted for recency only.

| Event | 90-day count | Conversion? | Mapped stage |
|---|---:|:---:|---|
| `view_item_list` | 289,400 | — | *(filled by lifecycle-map)* |
| `view_item` | 412,600 | — | |
| `add_to_wishlist` | 18,750 | — | |
| `view_cart` | 48,300 | — | |
| `add_to_cart` | 61,900 | — | |
| `remove_from_cart` | 12,480 | — | |
| `begin_checkout` | 23,700 | ✓ (key event) | |
| `add_payment_info` | 10,940 | — | |
| `purchase` | 2,166 | ✓ (revenue: `value`, `currency`, `items`) | |
| `sign_up` | 5,830 | — | |
| `refund` | 118 | — | |

## 4. Gaps

Must-have events (`view_item`, `add_to_cart`, `purchase`) are **all present** — no P0 pattern is event-blocked. Remaining gaps:

- **No `items` params on `purchase` at line-item consumption level in the CRM** — GA4 carries them, but the CRM sync drops per-item rows; blocks per-item repeat-cycle computation (replenishment) even though the category is durable anyway.
- **No inventory/price feed** (`item_back_in_stock`, `price_drop` are not emitted) — blocks back-in-stock and price-drop.
- **No `survey_response`** — feedback-nps can only run if the CRM's own survey block emits the response event.
- **No RFM attributes** — winback thresholds will be computed from raw purchase timestamps instead; segmentation depth is limited.

## 5. Next step

Proceed to `lifecycle-map` to map the 11 events onto lifecycle stages, then `lifecycle-journeys`.
