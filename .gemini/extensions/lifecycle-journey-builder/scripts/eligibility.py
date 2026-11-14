#!/usr/bin/env python3
"""Mechanical eligibility pass for lifecycle-journeys step 1.

Applies only the machine-checkable part of the contract: each pattern's
frontmatter `applicable_industries`, `required_events` and
`required_attributes` against a stage map written by lifecycle-map
(`output/<project>/stage-map.json`). Judgment (overlap with existing
automations, goal-based prioritization, depth) stays with the skill.

A named event is never enough on its own. An event counts only when the stage
map says it is mapped with confidence (`mapping: "mapped"`) AND usable
(`usable: true`, i.e. its required params were checked and are populated).
  eligible             every required event mapped + usable, every required attribute available
  blocked              a required event/attribute is absent, or present but explicitly unusable
  unknown              present but not confirmed (assumed/unmapped mapping, usability or
                       attribute availability not checked) — ask or add to open items
  playbook-recommended T3 (no data): listed in the sector playbook's pattern_priorities
  not_applicable       the pattern doesn't list this sector

stage-map.json contract:
  {"tier": "T1|T2|T2-aggregate|T3", "sector": "<slug>", "dqs": <0-100 or null for T3>,
   "volume_capped": true|false (DQS hard rule: volume too low for branched depth),
   "events": [{"name", "stage", "mapping": "mapped|assumed|unmapped",
               "source": "authoritative|behavioral|inferred|engagement",
               "usable": true|false|null, "note"?}],
   "attributes": [{"name", "available": true|false|null, "note"?}]}

Usage:
  eligibility.py <stage-map.json> [--pattern <slug> ...] [--json]
Exit: 0 ok · 2 usage/input error.
"""
import argparse
import glob
import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def frontmatter(path):
    text = open(path, encoding="utf-8").read().split("---")[1]
    fm = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def flow_list(v):
    v = (v or "").strip()
    if not (v.startswith("[") and v.endswith("]")):
        return []
    return [x.strip() for x in v[1:-1].split(",") if x.strip()]


def priorities(sector):
    p = os.path.join(ROOT, "knowledge", "industries", f"{sector}.md")
    if not os.path.isfile(p):
        return {}
    text = open(p, encoding="utf-8").read().split("---")[1]
    m = re.search(r"^pattern_priorities:\n((?:  [a-z0-9_-]+: P[0-2]\n)+)", text, re.M)
    if not m:
        return {}
    return dict(re.findall(r"^  ([a-z0-9_-]+): (P[0-2])$", m.group(1), re.M))


def assess(pattern, fm, smap, prio):
    sector = smap.get("sector")
    applicable = flow_list(fm.get("applicable_industries"))
    if sector and applicable and sector not in applicable:
        return {"pattern": pattern, "status": "not_applicable", "reasons": [f"not used for sector '{sector}'"]}
    tier = smap.get("tier", "")
    if tier == "T3" and str(fm.get("requires_feed", "")).split("#")[0].strip() == "true":
        return {"pattern": pattern, "status": "blocked",
                "reasons": ["needs a live data feed (stock, price, purchase cycle or alerts); none at T3"]}
    if tier != "T3" and not smap.get("events"):
        return {"pattern": pattern, "status": "unknown", "reasons": [f"{tier or 'tier'} stage map lists no events"]}
    if tier == "T3":
        if pattern in prio:
            return {"pattern": pattern, "status": "playbook-recommended", "priority": prio[pattern],
                    "reasons": ["T3: suggested by the sector playbook, not confirmed by data"]}
        return {"pattern": pattern, "status": "not_prioritized", "reasons": ["T3 and not in the sector playbook"]}
    events = {e.get("name"): e for e in smap.get("events", [])}
    attrs = {a.get("name"): a for a in smap.get("attributes", [])}
    blocked, unknown = [], []
    for ev in flow_list(fm.get("required_events")):
        e = events.get(ev)
        if e is None:
            blocked.append(f"event '{ev}' is not in the inventory")
        elif e.get("usable") is False:
            blocked.append(f"event '{ev}' is instrumented but unusable ({e.get('note') or 'required params missing'})")
        elif e.get("mapping") != "mapped":
            unknown.append(f"event '{ev}' mapping is '{e.get('mapping') or 'unspecified'}': confirm what it means")
        elif e.get("usable") is not True:
            unknown.append(f"event '{ev}' usability not checked (are its required params populated?)")
    for at in flow_list(fm.get("required_attributes")):
        a = attrs.get(at)
        if a is None:
            unknown.append(f"attribute '{at}' availability not reported")
        elif a.get("available") is False:
            blocked.append(f"attribute '{at}' is not available")
        elif a.get("available") is not True:
            unknown.append(f"attribute '{at}' availability not confirmed")
    status = "blocked" if blocked else ("unknown" if unknown else "eligible")
    out = {"pattern": pattern, "status": status, "reasons": blocked + unknown}
    if pattern in prio:
        out["priority"] = prio[pattern]
    opt = [o for o in flow_list(fm.get("optional_events"))
           if events.get(o, {}).get("mapping") == "mapped" and events.get(o, {}).get("usable") is True]
    if opt:
        out["optional_present"] = opt
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage_map")
    ap.add_argument("--pattern", action="append", help="assess only this pattern (repeatable): the single-journey path")
    ap.add_argument("--json", action="store_true", help="print the full JSON instead of one line per pattern")
    a = ap.parse_args(argv)
    try:
        smap = json.load(open(a.stage_map, encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"error: can't read stage map {a.stage_map}: {e}", file=sys.stderr)
        return 2
    paths = sorted(glob.glob(os.path.join(ROOT, "knowledge", "journey-patterns", "*.md")))
    names = {os.path.basename(p)[:-3]: p for p in paths}
    wanted = a.pattern or sorted(names)
    missing = [w for w in wanted if w not in names]
    if missing:
        print(f"error: unknown pattern(s) {missing}", file=sys.stderr)
        return 2
    prio = priorities(smap.get("sector", ""))
    results = [assess(n, frontmatter(names[n]), smap, prio) for n in wanted]
    if a.json:
        print(json.dumps({"stage_map": a.stage_map, "tier": smap.get("tier"), "sector": smap.get("sector"),
                          "scope": "single" if a.pattern else "all", "results": results}, ensure_ascii=False, indent=1))
    else:
        for r in results:
            if r["status"] in ("not_applicable", "not_prioritized") and not a.pattern:
                continue
            why = "; ".join(r["reasons"][:3])
            print(f"{r['status']:<20} {r.get('priority', '--')} {r['pattern']}" + (f" — {why}" if why else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
