---
name: audience-sql
purpose: Standard GA4 BigQuery export schema reference for lifecycle-audience — the patterns every generated query must follow.
---

# Audience SQL — GA4 BigQuery Export Patterns

Reference for `lifecycle-audience`'s BigQuery mode. Everything here targets the **standard GA4 → BigQuery export schema** (Google-documented, stable); a workspace with custom/renamed tables gets asked for its schema, never guessed at. **The patterns below are fragments, not a template to fill in** — a real journey's audience is usually 2–3 of them composed (a date bound + an include condition + an exclusion CTE, sometimes a sequence or an RFM tier), not one example picked whole and bent to fit. Write the query by combining the smallest set that expresses the journey doc's §3 line.

## The tables

- `project.analytics_<property_id>.events_YYYYMMDD` — one table per day, one row per event.
- `events_intraday_YYYYMMDD` — today's streaming data; exclude from audience queries unless real-time entry is explicitly needed (rows can be revised at day close).
- **Partitioned-table variant:** some properties export to a single partitioned `events` table (`event_date`/`event_timestamp` as the partition column) instead of date-sharded `events_YYYYMMDD` tables — same data, different bound syntax (`WHERE event_date BETWEEN ...` on the partition column, not `_TABLE_SUFFIX`). The two shapes are not interchangeable; confirm which one a workspace has (same "ask for a schema" rule below) before writing the date bound.

## Identity (the decision that changes every query)

| Field | Scope | Use |
|---|---|---|
| `user_id` | Person (only where the reporting identity is implemented) | Preferred — cross-device exclusions actually hold |
| `user_pseudo_id` | Device/browser | Fallback — **always flag in a comment**: a purchase on another device will NOT exclude this pseudo-user, so recovery journeys will occasionally message buyers |

The export provides event-level rows with `user_pseudo_id` even when User-ID isn't set; `user_id` is populated only where the site/app sends it, and adds person-level cross-device stitching. Three questions stay separate: **data access** (does the export exist), **identity scope** (pseudo vs user id), and **CRM addressability** (can the CRM map this identity to a contactable customer). A query result is an audience definition, not a send list — and GA4 analytics consent is not marketing-communication consent (that is enforced downstream, rule 4). Lookback is bounded by the dataset's own table/partition expiration, not the GA4 property's retention setting; confirm both before writing a long window.

## Core patterns

Date-bounded scan (never a full-table scan):

```sql
FROM `project.analytics_XXXX.events_*`
WHERE _TABLE_SUFFIX BETWEEN FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
                        AND FORMAT_DATE('%Y%m%d', CURRENT_DATE())
```

Event param extraction (params live in a repeated record):

```sql
(SELECT value.string_value FROM UNNEST(event_params) WHERE key = 'item_id') AS item_id
-- numeric params: value.int_value / value.double_value — check the type, GA4 does not coerce
```

Items array (e-commerce events):

```sql
, UNNEST(items) AS item          -- explodes the row per item; COUNT/SUM accordingly
```

Include-with-exclude in ONE statement (the exclude must not be a separate query someone forgets):

```sql
-- journey: ecom-abandoned-cart-01 · audience: include
SELECT DISTINCT user_pseudo_id            -- FLAG: pseudo id, device-scoped (no user_id in this property)
FROM `project.analytics_XXXX.events_*` e
WHERE _TABLE_SUFFIX BETWEEN <window>
  AND event_name = 'add_to_cart'
  AND NOT EXISTS (                        -- exclude: purchased since
    SELECT 1 FROM `project.analytics_XXXX.events_*` p
    WHERE p._TABLE_SUFFIX BETWEEN <window>
      AND p.event_name = 'purchase'
      AND p.user_pseudo_id = e.user_pseudo_id
      AND p.event_timestamp > e.event_timestamp)
-- validates: journey doc §3 "added to cart, no purchase since" · consent filtering happens downstream in the CRM
```

**Exclusion at scale:** a correlated `NOT EXISTS` (above) is the clearest way to write a small include-exclude query. Correlated subqueries are not automatically slow — the engine often rewrites them into a join — so when a query stacks several exclusions or excludes against a high-volume event, write the alternative below and **compare the two plans and bytes/slot usage** before choosing; don't assume either is faster. The rewrite must keep the time condition: the purchase has to come **after that cart event, for the same identity** — excluding anyone who purchased anywhere in the window (including before the cart) is a different, wrong audience.

```sql
WITH carts AS (
  SELECT user_pseudo_id, event_timestamp AS cart_ts
  FROM `project.analytics_XXXX.events_*`
  WHERE _TABLE_SUFFIX BETWEEN <window> AND event_name = 'add_to_cart'
),
purchases AS (
  SELECT user_pseudo_id, event_timestamp AS purchase_ts
  FROM `project.analytics_XXXX.events_*`
  WHERE _TABLE_SUFFIX BETWEEN <window> AND event_name = 'purchase'
),
converted_carts AS (                       -- carts followed by a purchase from the same identity
  SELECT DISTINCT c.user_pseudo_id, c.cart_ts
  FROM carts c
  JOIN purchases p
    ON p.user_pseudo_id = c.user_pseudo_id
   AND p.purchase_ts > c.cart_ts
)
SELECT DISTINCT c.user_pseudo_id           -- FLAG: pseudo id, device-scoped (no user_id in this property)
FROM carts c
LEFT JOIN converted_carts x
  ON x.user_pseudo_id = c.user_pseudo_id
 AND x.cart_ts = c.cart_ts
WHERE x.user_pseudo_id IS NULL
-- validates: journey doc §3 "added to cart, no purchase since" · consent filtering happens downstream in the CRM
```

Like the correlated form, this keeps a person whose *latest* cart is unconverted even if an earlier cart was; if the journey means "no purchase since the most recent cart", reduce `carts` to each identity's latest cart first. Check that both forms return the same Validation B count on a sample before switching.

## Behavioral sequences (ordered-event conditions)

Not every audience is a flat threshold. "Viewed category A, then added to cart, but never viewed category B afterward" is a **pattern**, not a count — express it with `LAG()`/`ROW_NUMBER()` over `event_timestamp`, partitioned by identity, rather than stacking unordered `EXISTS` clauses that can't express order:

```sql
WITH ordered AS (
  SELECT user_pseudo_id, event_name, event_timestamp,
         LAG(event_name) OVER (PARTITION BY user_pseudo_id ORDER BY event_timestamp) AS prev_event
  FROM `project.analytics_XXXX.events_*`
  WHERE _TABLE_SUFFIX BETWEEN <window> AND event_name IN ('view_item', 'add_to_cart')
)
SELECT DISTINCT user_pseudo_id
FROM ordered
WHERE event_name = 'add_to_cart' AND prev_event = 'view_item'
-- validates: journey doc §3 "<the sequential audience line it implements>"
```

Same rules apply as any other pattern (dated bound, identity choice, decision-trace comment) — this is a shape, not an exemption. Reach for it only when the journey doc's audience line is genuinely sequential ("after viewing X" / "without doing Y since Z"); most audiences are still flat thresholds and don't need it.

## RFM tiers

`knowledge/industries/ecommerce.md`'s segmentation attributes and the DQS "user attributes" component both name RFM (recency, frequency, monetary) as a segmentation dimension — this is the SQL to actually compute it, not just cite it:

```sql
WITH rfm AS (
  SELECT user_pseudo_id,
         DATE_DIFF(CURRENT_DATE(), MAX(DATE(TIMESTAMP_MICROS(event_timestamp))), DAY) AS recency_days,
         COUNT(*) AS frequency,
         SUM((SELECT value.double_value FROM UNNEST(event_params) WHERE key = 'value')) AS monetary
  FROM `project.analytics_XXXX.events_*`
  WHERE _TABLE_SUFFIX BETWEEN <window> AND event_name = 'purchase'
  GROUP BY user_pseudo_id
)
SELECT *,
       NTILE(5) OVER (ORDER BY recency_days DESC) AS r_tile,
       NTILE(5) OVER (ORDER BY frequency)         AS f_tile,
       NTILE(5) OVER (ORDER BY monetary)          AS m_tile
FROM rfm
```

`NTILE(5)` needs a real population to bucket meaningfully — below a few hundred purchasers, fixed thresholds (from the industry playbook or the user's own figures) beat a five-way split of a tiny group; state which one was used and why.

## Rules the generator must keep

1. `event_timestamp` is **microseconds** since epoch; compare timestamps to timestamps, dates to `_TABLE_SUFFIX` (or `event_date` on the partitioned-table variant).
2. Frequency conditions ("≥ 2 view_item") are `GROUP BY identity HAVING COUNT(*) >= n` — never approximated with EXISTS.
3. Every query ends with `-- validates: <journey-doc line it implements>` (decision-trace rule) and, where pseudo-id is used, the device-scope flag comment.
4. Consent is never filtered in SQL — behavioral selection here, consent/İYS enforcement downstream in the CRM; a comment states this on every query.
5. **Costs and size are two different checks, not one — a dry run answers neither "how many" question.** State the scanned date range at the top of the file, then pair every query with BOTH:
   - **Validation A — dry run** (`bq query --dry_run` or the workspace's equivalent): confirms syntax and returns **bytes to be processed**, not a row count. Use it to catch cost/schema errors before anyone runs the real query.
   - **Validation B — size estimate**: a real `SELECT COUNT(DISTINCT <identity>) FROM (...)` run against the audience query itself is what actually tells you how many people are in it. Validation A cannot substitute for this. An unexpectedly large (near-total) or near-zero count from Validation B is a segmentation-logic bug to catch before the data team activates it, not a fact to accept silently.
   - Where an eligible population is knowable (total active users, or the broader group the audience is drawn from), express Validation B's count as **a share of it**, not just an absolute number — 400,000 people reads as plausible in isolation; 400,000 out of an eligible population of 420,000 usually means a filter condition silently failed to apply.
6. **Personalization fields travel with the identity, not separately.** If the journey's steps use item/product/discount variables (`{{product_name}}`, `{{cart_url}}`, …), the audience query selects those fields too, via the same `items`/`event_params` UNNEST the anchoring event already has — an identity-only list that forces the data team to re-derive "which cart" just moves the "designed but not activatable" gap one step downstream instead of closing it.
7. **Event params can change type mid-window** (SDK update, schema change) — a param assumed numeric can hold string values earlier in a long window. Extract with a `COALESCE(value.int_value, CAST(value.string_value AS INT64))`-style fallback when the window is long enough to plausibly cross a tracking change, not a single type access.
8. When a query stacks 2+ exclusions or excludes against a high-volume event, consider the anti-join form (see "Exclusion at scale"), keep every time condition of the original, and choose by the measured query plan and bytes, not by assumption.
