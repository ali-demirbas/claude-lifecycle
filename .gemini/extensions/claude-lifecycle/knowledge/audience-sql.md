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

**Exclusion-set cost at scale:** a correlated `NOT EXISTS` (above) is the clearest way to write a small include-exclude query, but it's a documented anti-pattern once the excluded-event table is large — restructure to a precomputed exclusion CTE with an anti-join once a query stacks multiple exclusion conditions, or excludes against a high-volume event (`page_view`, not a rarer one like `purchase`):

```sql
WITH purchasers AS (
  SELECT DISTINCT user_pseudo_id
  FROM `project.analytics_XXXX.events_*`
  WHERE _TABLE_SUFFIX BETWEEN <window> AND event_name = 'purchase'
)
SELECT DISTINCT e.user_pseudo_id
FROM `project.analytics_XXXX.events_*` e
LEFT JOIN purchasers p ON p.user_pseudo_id = e.user_pseudo_id
WHERE e._TABLE_SUFFIX BETWEEN <window> AND e.event_name = 'add_to_cart'
  AND p.user_pseudo_id IS NULL
-- validates: journey doc §3 "added to cart, no purchase since" · consent filtering happens downstream in the CRM
```

Same result, computed once instead of re-checked per candidate row. Prefer the CTE form once a query stacks 2+ exclusions or the excluded event is high-volume; the plain correlated form is fine for a single, low-volume exclusion.

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
5. Costs are real: state the scanned date range at the top of the file, and pair every query with a row-count or dry-run byte estimate — an unexpectedly large (near-total) or near-zero result is a segmentation-logic bug to catch before the data team runs it, not a fact to accept silently.
6. **Personalization fields travel with the identity, not separately.** If the journey's steps use item/product/discount variables (`{{product_name}}`, `{{cart_url}}`, …), the audience query selects those fields too, via the same `items`/`event_params` UNNEST the anchoring event already has — an identity-only list that forces the data team to re-derive "which cart" just moves the "designed but not activatable" gap one step downstream instead of closing it.
7. **Event params can change type mid-window** (SDK update, schema change) — a param assumed numeric can hold string values earlier in a long window. Extract with a `COALESCE(value.int_value, CAST(value.string_value AS INT64))`-style fallback when the window is long enough to plausibly cross a tracking change, not a single type access.
8. Prefer a precomputed exclusion CTE / anti-join (see "Exclusion-set cost at scale") over a correlated `NOT EXISTS` once a query stacks 2+ exclusions or excludes against a high-volume event.
