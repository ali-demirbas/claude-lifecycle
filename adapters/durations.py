#!/usr/bin/env python3
"""Convert an ISO 8601 wait duration (steps[].wait, e.g. PT1H, P2D, P3DT12H)
to a target tool's native integer+unit delay input. Deterministic counterpart
of docs/crm-export-mapping.md's Wait-duration conversion section — same
rationale as variables.py: the doc's own rule ("round to the nearest
supported unit") is arithmetic a model can get wrong or apply inconsistently
across a portfolio; a function doesn't.

Usage:  durations.py <braze|klaviyo|iterable|insider> <ISO8601 duration> [...]
        (prints "<duration> -> <value> <unit>" per input, to stdout)
Exit:   0 = ok, 2 = usage error / unknown tool / unparseable duration.
"""
import re
import sys

# Mirrors the same exclusive W-vs-D/T structure as templates/journey.schema.json's
# steps[].wait pattern and scripts/validate_output.py's ISO_WAIT (kept in sync
# deliberately, same class of duplication this repo already guards elsewhere —
# a week-only duration is mutually exclusive with D/T per the ISO 8601 standard).
ISO_WAIT = re.compile(r"^P(?!$)(?:(\d+)W|(?:(\d+)D)?(?:T(?=\d)(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?)$")


def to_seconds(duration):
    m = ISO_WAIT.match(duration)
    if not m:
        return None
    w, d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    if w:
        return w * 604800
    return d * 86400 + h * 3600 + mi * 60 + s


def _round_to_unit(seconds):
    """Coarsest whole unit that exactly represents the value — whole days
    first (journeys are usually day-paced), else whole hours, else whole
    minutes; a sub-minute remainder rounds to the nearest minute, since no
    documented tool exposes a finer delay-step granularity than minutes."""
    if seconds >= 86400 and seconds % 86400 == 0:
        return seconds // 86400, "days"
    if seconds >= 3600 and seconds % 3600 == 0:
        return seconds // 3600, "hours"
    if seconds % 60 == 0:
        return seconds // 60, "minutes"
    return round(seconds / 60), "minutes"


def _uniform(seconds):
    value, unit = _round_to_unit(seconds)
    return f"{value} {unit}"


# One entry per documented tool (docs/crm-export-mapping.md, Wait-duration
# section: "All four tools take integer + unit inputs"). Every entry maps to
# the same rounding today — kept as a dict, not one shared call, so a future
# tool with different delay-step granularity is a one-line addition here, not
# a rewrite. Mirrors variables.py's TOOLS dict for the same reason.
TOOLS = {
    "braze": _uniform,
    "klaviyo": _uniform,
    "iterable": _uniform,
    "insider": _uniform,
}


def convert(duration, tool):
    seconds = to_seconds(duration)
    if seconds is None:
        return None
    return TOOLS[tool](seconds)


def main(argv):
    if len(argv) < 2 or argv[0] not in TOOLS:
        print(__doc__)
        print(f"known tools: {', '.join(sorted(TOOLS))}")
        return 2
    tool = argv[0]
    ok = True
    for duration in argv[1:]:
        result = convert(duration, tool)
        if result is None:
            print(f"error: {duration}: not a valid ISO 8601 wait duration", file=sys.stderr)
            ok = False
            continue
        print(f"{duration} -> {result}")
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
