---
name: deliverability
purpose: Email deliverability floor — mailbox-provider requirements every email journey inherits. Source: Google's official Email Sender Guidelines (verified against the published doc, not vendor summaries).
---

# Deliverability — The Floor Under Every Email Journey

A journey with perfect copy and perfect timing sends nothing if the domain lands in spam. These are platform rules in the same class as iOS's review-prompt quota or GSM-7 encoding: externally enforced, non-negotiable, and cheap to comply with *before* reputation damage and near-impossible to repair after.

## Hard requirements (Google's published sender guidelines)

| Requirement | Threshold | Applies to |
|---|---|---|
| SPF **or** DKIM | required | every sender |
| SPF **and** DKIM **and** DMARC (From-domain aligned) | required | bulk senders (> 5,000 msgs/day to Gmail) |
| TLS in transit | required | every sender |
| Valid forward + reverse DNS (PTR) | required | every sender |
| DKIM key length | ≥ 1024 bits | senders to personal Gmail |
| **Spam rate in Postmaster Tools** | keep **< 0.10%**; never reach **0.30%** | every sender — the guardrail number |
| One-click unsubscribe (`List-Unsubscribe` + `List-Unsubscribe-Post` headers) + visible link | required | bulk senders' marketing/subscribed mail |

These are Google's numbers, not industry folklore; Yahoo published parallel requirements in the same cycle. When in doubt, the engine treats every client as a bulk sender — the stricter posture costs nothing.

## Design consequences for this engine

- **The 0.3% ceiling is a portfolio-level guardrail, not a per-journey one.** One aggressive journey can poison the domain every other journey sends from — which is why frequency caps, the winback sunset rule, and the re-permission step for 2-year-silent lists exist. A spam-rate spike triggers the same response as compliance rule 4: pause and diagnose, don't push through.
- **Marketing and transactional stay separated in infrastructure, not just content.** Google's own guidance: don't mix content types in one message, and separate promotional from notification sending (distinct From addresses; distinct IPs where possible). The engine's transactional/marketing split (compliance file) has an infrastructure mirror — surface it in intake when the client runs both through one stream.
- **List hygiene is a deliverability act.** Hard bounces pruned immediately, multi-year-silent segments re-permissioned instead of blasted (winback rule), and the lead-nurture sunset honored — every one of these protects the spam-rate number directly.
- **Intake question when email volume is meaningful:** is one-click unsubscribe (the header pair, not just a footer link) actually implemented in the client's ESP? Many older setups have only the visible link — that fails the bulk-sender bar on its own.

## What this file is not

Not a warm-up schedule, not an IP-reputation consultancy, and no invented "ramp by X per day" figures — warm-up specifics vary by ESP and are their documented territory. The engine's job is to keep the journeys it designs from violating the published floor, and to name the floor in the dossier when the data shows volume near the bulk threshold.
