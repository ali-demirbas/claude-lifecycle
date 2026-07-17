# CRM Export Mapping

`lifecycle-export` emits CRM-agnostic JSON validating against [`templates/journey.schema.json`](../templates/journey.schema.json). This document maps those fields onto the four most common CRM tools. The JSON never changes per tool — these tables are the bridge a human (or importer script) uses.

## Concept mapping

| journey.schema.json | Braze | Klaviyo | Iterable | Insider |
|---|---|---|---|---|
| Journey (whole file) | Canvas | Flow | Journey | Architect journey |
| `trigger.type: event` | Canvas entry: action-based | Flow trigger: metric | Journey trigger: event | Trigger: event-based |
| `trigger.type: time` | Scheduled entry | Date-property trigger | Scheduled/recurring | Time-based trigger |
| `trigger.type: segment_entry` | Audience entry | Segment trigger (list/segment join) | Segment entry | Segment-based |
| `trigger.entry_conditions` | Entry audience filters | Flow filters | Entry rules | Audience conditions |
| `trigger.reentry_policy` | Re-eligibility settings | Smart Sending / re-entry toggle | Journey re-entry | Re-entry rules |
| `audience.exclude` | Exception audiences | Flow filters (NOT conditions) | Exclusion lists | Exclude segments |
| `exit.success_event` | Exit: conversion event | Flow exit: metric | Exit criteria | Conversion goal |
| `steps[].wait` (ISO 8601) | Delay step | Time delay | Wait node | Wait node |
| `steps[].channel` | Message step (channel) | Email/SMS/Push action | Message node | Channel node |
| `steps[].branch_condition` | Decision split / Audience path | Conditional split | Yes/No split node | Conditional split |
| `kpis` + `experiment.holdout_pct` | Canvas analytics + Control group | Flow analytics + A/B | Journey analytics + holdout | Journey analytics + control |
| Copy `{{first_name}}` vars | Liquid: `{{${first_name}}}` | `{{ first_name }}` (profile) | Handlebars: `{{firstName}}` | `[%first_name%]` |
| Copy `**Image:**` (push, optional) | Push message's image/rich-media field | Push action's image field | Push message's image field | Rich push image field |

## Wait-duration conversion

Schema waits are ISO 8601 durations. `PT1H` = 1 hour, `P1D` = 1 day, `P3DT12H` = 3.5 days. All four tools take integer + unit inputs; round to the nearest supported unit and keep quiet-hour windows from the journey doc's §2 as the tool's send-time settings.

## Rich media (push image)

Push copy's optional `**Image:**` line ([templates/copy-output.md](../templates/copy-output.md)) is an HTTPS URL, never a binary upload — every one of the four tools expects a hosted image URL for a push/rich-push message, not raw file bytes. `scripts/validate_output.py` checks the line is well-formed (HTTPS, non-empty alt text); it cannot verify the actual downloaded file size, so apply [knowledge/channels/push.md](../knowledge/channels/push.md)'s ≤1MB ceiling by hand before import — that number is Android/FCM's own limit, the tighter of the two OS platforms (iOS/APNs tolerates far more).

## Personalization variable conventions

Exported copy uses `{{snake_case}}` variables. Map to each tool's syntax at import time (table row above). The copy output's variable list plus the fallback block gives you everything needed to configure default values — tools differ in where fallbacks live (Braze: Liquid default filter; Klaviyo: default in tag; Iterable: merge params; Insider: fallback field).

## Snippets and live data

Any tool-specific snippet (Liquid, personalization syntax) shown during export or setup is **illustrative, not literal**. Treat placeholders like `${...}` as placeholders, and adapt every snippet to the workspace's actual attribute names and syntax before use. If a tool's templating convention isn't well known, describe the logic in prose instead of fabricating syntax — an illustrative-but-wrong snippet is worse than an honest prose description, because it gets pasted verbatim.

Messages that reference live price or stock values must pull that data **at send time** (e.g. Braze Connected Content-class mechanisms in whatever tool is in use), not at journey-entry time. If the tool cannot fetch live data, the journey design must state the staleness risk explicitly — a "price dropped to X" message rendered from hours-old data is a broken promise.

## Trigger health after launch

A live journey whose trigger event breaks does not error — **it goes silent**, which is indistinguishable from a journey working perfectly with no one to message. Two obligations:

- **Pre-launch**: verify the trigger event and attribute names against the *current* schema in the destination tool — not against the tracking plan or an old export; names drift.
- **Post-launch**: wire a volume-anomaly alert on the entry trigger (e.g. daily entries falling below half of the trailing 7-day average → internal alert). If the tool cannot alert on entry volume, state that gap in the handoff so the marketer knows to spot-check entry counts manually.

## What does NOT export

- Frequency caps and quiet hours are journey-doc *requirements* but live in tool-level settings — configure them once per workspace, not per journey.
- The tracking plan is for your analytics team, not the CRM.
- Review-pending copy: `lifecycle-export` refuses to embed copy that has not passed copy-reviewer; it exports `copy_ref` pointers instead.
