#!/usr/bin/env python3
"""Per-stage time and token breakdown of a Claude Code run, from its session transcript.

Run the pipeline with session persistence on (no --no-session-persistence), then:
  measure_run.py <session.jsonl> [--json]
Subagent transcripts in <session-dir>/subagents/*.jsonl are included as their
own rows. A stage starts at each Skill call (the skill's name) and runs until
the next one; work before the first Skill call is "start".

Per stage: wall-clock, API turns (distinct message ids), fresh input, cache
write, cache read and output tokens, validator runs and validator FAIL lines
seen in tool results. Usage is de-duplicated by message id: one API message is
written as several transcript lines. Output tokens include thinking; this tool
does not split them, so don't label the difference between file size and
output as thinking without separate evidence.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return [r for r in rows if r.get("timestamp")]


def new_stage(name, t0):
    return {"stage": name, "start": t0, "end": t0, "msg_ids": set(), "validator_runs": 0, "validator_fails": 0,
            **{k: 0 for k in USAGE_KEYS}}


def measure(rows, first_stage="start"):
    rows = sorted(rows, key=lambda r: r["timestamp"])
    stages, cur, seen = [], None, {}
    for r in rows:
        t = ts(r["timestamp"])
        if cur is None:
            cur = new_stage(first_stage, t)
            stages.append(cur)
        msg = r.get("message") or {}
        content = msg.get("content") if isinstance(msg.get("content"), list) else []
        if r.get("type") == "assistant":
            for c in content:
                if c.get("type") == "tool_use" and c.get("name") == "Skill":
                    cur["end"] = t
                    cur = new_stage(str((c.get("input") or {}).get("skill", "skill")), t)
                    stages.append(cur)
                if c.get("type") == "tool_use" and c.get("name") == "Bash" and \
                        "validate_output.py" in str((c.get("input") or {}).get("command", "")):
                    cur["validator_runs"] += 1
            mid = msg.get("id") or r.get("requestId")
            u = msg.get("usage") or {}
            if mid and u and mid not in seen:
                seen[mid] = True
                cur["msg_ids"].add(mid)
                for k in USAGE_KEYS:
                    cur[k] += int(u.get(k) or 0)
        elif r.get("type") == "user":
            for c in content:
                if c.get("type") == "tool_result":
                    text = json.dumps(c.get("content"))
                    cur["validator_fails"] += len(re.findall(r"FAIL: ", text))
        cur["end"] = t
    for s in stages:
        s["seconds"] = round((s["end"] - s["start"]).total_seconds())
        s["turns"] = len(s.pop("msg_ids"))
        s["start"], s["end"] = s["start"].isoformat(), s["end"].isoformat()
    return stages


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.session):
        print(f"error: {a.session} not found", file=sys.stderr)
        return 2
    report = {"session": a.session, "main": measure(load(a.session)), "subagents": []}
    sub_dir = os.path.join(os.path.splitext(a.session)[0], "subagents")
    for sp in sorted(glob.glob(os.path.join(sub_dir, "*.jsonl"))):
        rows = load(sp)
        if rows:
            st = measure(rows, first_stage="agent:" + os.path.basename(sp)[:-6])
            total = {k: sum(s[k] for s in st) for k in USAGE_KEYS + ("turns", "validator_runs", "validator_fails")}
            total.update({"stage": st[0]["stage"], "start": st[0]["start"], "end": st[-1]["end"],
                          "seconds": round((ts(st[-1]["end"]) - ts(st[0]["start"])).total_seconds())})
            report["subagents"].append(total)
    if a.json:
        print(json.dumps(report, indent=1))
        return 0
    hdr = f"{'stage':<34}{'sec':>6}{'turns':>6}{'input':>8}{'c.write':>10}{'c.read':>11}{'output':>9}{'val.runs':>9}{'FAILs':>6}"
    print(hdr)
    for s in report["main"] + report["subagents"]:
        print(f"{s['stage'][:33]:<34}{s['seconds']:>6}{s['turns']:>6}{s['input_tokens']:>8}"
              f"{s['cache_creation_input_tokens']:>10}{s['cache_read_input_tokens']:>11}{s['output_tokens']:>9}"
              f"{s['validator_runs']:>9}{s['validator_fails']:>6}")
    allr = report["main"] + report["subagents"]
    print(f"{'TOTAL (subagent time overlaps main)':<34}{'':>6}{sum(s['turns'] for s in allr):>6}"
          f"{sum(s['input_tokens'] for s in allr):>8}{sum(s['cache_creation_input_tokens'] for s in allr):>10}"
          f"{sum(s['cache_read_input_tokens'] for s in allr):>11}{sum(s['output_tokens'] for s in allr):>9}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
