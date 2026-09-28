-- journey: ecom-abandoned-cart-01 · audience: include
SELECT DISTINCT user_id FROM `p.analytics_1.events_*` WHERE event_name = 'add_to_cart'
-- validates: journey doc §3 "added to cart"

-- journey: ecom-winback-01 · audience: include
SELECT DISTINCT user_pseudo_id FROM `p.analytics_1.events_*` WHERE event_name = 'purchase'
-- activation_status: conditional
