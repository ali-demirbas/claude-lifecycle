-- scanned range: last 30 days
-- journey: ecom-abandoned-cart-01 · audience: include
SELECT DISTINCT user_id FROM `p.analytics_1.events_*` WHERE event_name = 'add_to_cart'
-- validates: journey doc §3 "added to cart, no purchase since" · consent filtering happens downstream in the CRM
-- activation_status: ready

-- journey: ecom-winback-01 · audience: include
SELECT DISTINCT user_pseudo_id FROM `p.analytics_1.events_*` WHERE event_name = 'purchase'
-- validates: journey doc §3 "last purchase 90+ days ago"
-- activation_status: conditional (suppression list enforcement location not confirmed)
