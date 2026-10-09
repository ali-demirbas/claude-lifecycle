#!/usr/bin/env python3
"""Every pattern must instantiate into a minimal valid schema-2.0 journey (audit A25).

Reads each knowledge/journey-patterns/*.md frontmatter (stage, journey_class,
default_channels, reentry, measurement_default, depth_range), builds the
smallest journey it implies (depth_range minimum sends on the first default
channel, spaced to stay inside caps) and runs validate_output.py journey on it.
Catches vocabulary drift (in-app vs in_app), non-schema reentry values
(cooldown null, P1Y) and classes the schema doesn't know.
"""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def fm(path):
    text = open(path, encoding="utf-8").read().split("---")[1]
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def flow_map(s):
    s = s.strip().strip("{}")
    out = {}
    for part in s.split(","):
        if ":" in part:
            k, v = part.split(":", 1)
            v = v.strip()
            out[k.strip()] = None if v in ("null", "~", "") else v
    return out


def flow_list(s):
    return [x.strip() for x in s.strip().strip("[]").split(",") if x.strip()]


failed = 0
for path in sorted(glob.glob(os.path.join(ROOT, "knowledge", "journey-patterns", "*.md"))):
    name = os.path.basename(path)[:-3]
    f = fm(path)
    cls = f.get("journey_class", "")
    lo = int(re.findall(r"\d+", f.get("depth_range", "[1, 1]"))[0])
    ch = flow_list(f.get("default_channels", "[email]"))[0]
    purpose = {"marketing": "marketing", "service": "service", "transactional": "transactional"}.get(cls, cls)
    nodes = [{"id": "entry", "kind": "entry", "next": "m1"}]
    for i in range(1, lo + 1):
        n = {"id": f"m{i}", "kind": "message", "channel": ch, "purpose": purpose, "intent": f"step {i}",
             "send": {"from": "entry", "offset": f"P{(i - 1) * 4}D"}, "next": f"m{i + 1}" if i < lo else "done"}
        if ch == "in_app":
            n["delivery"] = {"mode": "next_session", "expires_after": "P3D"}
        nodes.append(n)
    nodes.append({"id": "done", "kind": "exit", "reason": "completed", "outcome": "neutral"})
    md = f.get("measurement_default")
    meas = {"design": md, "primary_outcome": {"event": "conversion", "window": "P90D"}}
    if md == "holdout":
        meas["holdout"] = {"pct": 10, "assignment": {"unit": "user", "consistent": True}, "control_excludes": ["all sends"]}
        meas["volume_note"] = "minimal instantiation"
    else:
        meas["reason"] = "minimal instantiation"
        meas["alternative"] = "minimal instantiation"
    doc = {
        "schema_version": "2.0", "id": f"test-{name}-01", "version": "1.0.0", "journey_class": cls, "readiness": "ready",
        "name": name, "pattern": name, "stage": f.get("stage"), "priority": "P1", "data_tier": "T2", "dqs": 50,
        "objective": "minimal instantiation", "trigger": {"type": "event", "value": "trigger_event"},
        "audience": {"include": "x"}, "events_available": ["trigger_event", "conversion", "consent_withdrawn"],
        "exit": {"success_event": "conversion", "success_window": "P90D", "exit_conditions": [
            {"event": "conversion", "check": ["entry", "before_each_send"]},
            {"event": "consent_withdrawn", "check": ["before_each_send"]}]},
        "reentry": {k: v for k, v in flow_map(f.get("reentry", "{}")).items() if v is not None},
        "start": "entry", "nodes": nodes, "measurement": meas,
        "kpis": [{"name": "k", "type": "primary", "definition": "d"}, {"name": "g", "type": "guardrail", "definition": "d"}],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(doc, tmp)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "validate_output.py"), "journey", tmp.name],
                       capture_output=True, text=True)
    os.unlink(tmp.name)
    if r.returncode not in (0,):
        failed += 1
        errs = [ln for ln in r.stdout.splitlines() if ln.startswith("FAIL") or "unverifiable (critical)" in ln]
        print(f"FAIL {name}: " + " | ".join(e.replace(tmp.name, '<j>')[:180] for e in errs[:3]))
    else:
        print(f"ok   {name}")
print(f"{failed} pattern(s) failed to instantiate")
sys.exit(1 if failed else 0)
