#!/usr/bin/env python3
"""SessionStart hook: one short orientation paragraph for the engine.

Why this exists (measured, not assumed): in a 3×2 cold-start test, agents
given only the skill list skipped the DQS gate on a bare "hoş geldin serisi
kur" request in 3/3 runs — jumping straight to journey generation, the exact
violation CLAUDE.md rule 1 exists to prevent. With this paragraph injected,
0/3 runs skipped the gate, and the copy-standalone exception kept the
counter-case (user supplies their own journey) from being over-gated.

Cost: ~120 tokens per session start. Never blocks; any failure exits 0
silently and the session starts exactly as it would without the hook.
"""
import sys

ORIENTATION = (
    "[claude-lifecycle] engine context: data-adaptive lifecycle marketing "
    "engine installed. Hard gates that bind every request: (1) never generate "
    "journeys or copy before a Data Quality Score exists — lifecycle-connect "
    "computes it from GA4/CSV, or the user explicitly declares Tier 3 "
    "(industry-only); exception: lifecycle-copy can run standalone when the "
    "user provides their own existing journey/steps. (2) Every deliverable "
    "comes from the repo's templates and must pass scripts/validate_output.py "
    "before it reaches the user. (3) If a brand config exists under "
    "knowledge/brands/ it pre-fills intake — check before asking questions. "
    "Typical sequence: lifecycle-connect → lifecycle-map → lifecycle-intake → "
    "lifecycle-journeys → lifecycle-copy; the lifecycle router sequences this "
    "automatically. A request matching several lifecycle-* skills goes to the "
    "router, not a guess."
)


def main():
    print(ORIENTATION)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
