#!/usr/bin/env python3
"""Per-stage time, token and cost breakdown of a Claude Code run, from its session transcript.

Run the pipeline with session persistence on (no --no-session-persistence), then:
  measure_run.py <session.jsonl> [--result run.json] [--split auto|skill|milestone] [--json]

What it counts, and how:
- Every API message once. One message is written as several transcript lines
  (one per content block), and a line written mid-stream can carry partial
  usage, so usage is merged per message id taking the largest value of each
  field. A message id seen in both the parent transcript and a subagent
  transcript is counted once (`duplicate_ids_across_files` in --json).
- Subagents (<session-dir>/subagents/*.jsonl) are their own rows and are also
  attributed to the parent stage that spawned them (by the spawning tool id
  in each agent's .meta.json), so a stage total includes the agents it ran.
- Stages: --split skill starts a stage at each Skill call or slash command;
  --split milestone (for runs with no Skill call) starts one at each pipeline
  milestone: input check, eligibility, bundle, run start, agent spawns,
  validator, canvas, finalize. auto = skill if the run has any, else milestone.
- Cost is computed only for models with a verified price (PRICES). Two
  figures: `cost_cli_method` prices every cache write at 1.25x input, which is
  how the CLI's own total_cost_usd came out on the preserved baseline (its
  total matches that formula to the cent); `cost_list_1h` prices 1-hour cache
  writes at 2x input, the published rate. The real invoice may be the latter.
- --result <run.json> (the `claude -p --output-format json` result) or a
  cost-state record inside the transcript is reconciled against the computed
  totals per model.
Output tokens include thinking; this tool doesn't split them. A thinking count
is shown only where the CLI itself recorded one (cost-state `thinkingTokens`).
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

USAGE_KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
CC_KEYS = ("ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens")
# USD per million tokens (input, output). Only prices checked against a CLI-reported total.
PRICES = {"claude-sonnet-4-6": (3.0, 15.0), "claude-haiku-4-5": (1.0, 5.0)}
MILESTONES = [("validate_input.py", "input check"), ("eligibility.py", "eligibility"),
              ("bundle_context.py", "bundle"), ("finalize_run.py start", "run start"),
              ("finalize_run.py finish", "finalize"), ("build_canvas.py", "canvas"),
              ("validate_output.py", "validate")]


def ts(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def load(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def price_for(model):
    for k, v in PRICES.items():
        if model and model.startswith(k):
            return v
    return None


def cost(u, model):
    p = price_for(model)
    if not p:
        return None, None
    pin, pout = p[0] / 1e6, p[1] / 1e6
    base = u["input_tokens"] * pin + u["output_tokens"] * pout + u["cache_read_input_tokens"] * pin * 0.1
    cli = base + u["cache_creation_input_tokens"] * pin * 1.25
    w1h = u.get("ephemeral_1h_input_tokens", 0)
    w5m = u["cache_creation_input_tokens"] - w1h
    return round(cli, 6), round(base + w5m * pin * 1.25 + w1h * pin * 2.0, 6)


def base_model(name):
    """claude-haiku-4-5-20251001 -> claude-haiku-4-5 (the CLI's modelUsage key has no date suffix)."""
    return re.sub(r"-\d{8}$", "", name or "")


def merge_usage(dst, u):
    for k in USAGE_KEYS:
        dst[k] = max(dst.get(k, 0), int(u.get(k) or 0))
    cc = u.get("cache_creation") or {}
    for k in CC_KEYS:
        dst[k] = max(dst.get(k, 0), int(cc.get(k) or 0))


def blocks(r):
    msg = r.get("message") or {}
    return msg.get("content") if isinstance(msg.get("content"), list) else []


def boundary(r, mode):
    """Stage name if this row starts a stage under `mode`, else None."""
    if r.get("type") == "user" and mode == "skill":
        text = json.dumps((r.get("message") or {}).get("content"))
        m = re.search(r"<command-name>/?([^<]+)</command-name>", text)
        if m:
            return m.group(1).strip()
    if r.get("type") != "assistant":
        return None
    for c in blocks(r):
        if c.get("type") != "tool_use":
            continue
        inp = c.get("input") or {}
        if mode == "skill" and c.get("name") == "Skill":
            return str(inp.get("skill", "skill"))
        if mode == "milestone":
            if c.get("name") in ("Agent", "Task"):
                return "agents"
            if c.get("name") == "Bash":
                cmd = str(inp.get("command", ""))
                for needle, label in MILESTONES:
                    if needle in cmd:
                        return label
    return None


def has_skill_calls(rows):
    return any(boundary(r, "skill") for r in rows)


def collect(rows, seen, origin, stage_of=None):
    """Merge usage per message id into `seen`; returns ids first seen here."""
    mine = []
    for r in rows:
        if r.get("type") != "assistant":
            continue
        msg = r.get("message") or {}
        mid, u = msg.get("id") or r.get("requestId"), msg.get("usage")
        if not mid or not u or msg.get("model") == "<synthetic>":
            continue
        if mid in seen:
            if seen[mid]["origin"] != origin:
                seen[mid]["dup_across_files"] = True
            merge_usage(seen[mid]["usage"], u)
            continue
        seen[mid] = {"origin": origin, "model": msg.get("model"), "usage": {}, "ts": r.get("timestamp"),
                     "stage": stage_of(r) if stage_of else None}
        merge_usage(seen[mid]["usage"], u)
        mine.append(mid)
    return mine


def zero():
    return {**{k: 0 for k in USAGE_KEYS}, **{k: 0 for k in CC_KEYS}, "turns": 0, "cost_cli_method": 0.0,
            "cost_list_1h": 0.0, "unpriced_turns": 0}


def add(tot, rec):
    for k in USAGE_KEYS + CC_KEYS:
        tot[k] += rec["usage"].get(k, 0)
    tot["turns"] += 1
    c1, c2 = cost(rec["usage"], rec["model"])
    if c1 is None:
        tot["unpriced_turns"] += 1
    else:
        tot["cost_cli_method"] += c1
        tot["cost_list_1h"] += c2


def measure(session, split="auto", result=None):
    main_rows = [r for r in load(session)]
    timed = sorted([r for r in main_rows if r.get("timestamp")], key=lambda r: r["timestamp"])
    mode = split if split != "auto" else ("skill" if has_skill_calls(timed) else "milestone")
    # stages over the parent transcript
    stages, cur, row_stage, tool_stage = [], None, {}, {}
    for r in timed:
        name = boundary(r, mode)
        if cur is None or (name and name != cur["stage"]):
            cur = {"stage": name or "start", "start": r["timestamp"], "end": r["timestamp"],
                   "validator_runs": 0, "validator_fails": 0}
            stages.append(cur)
        cur["end"] = r["timestamp"]
        row_stage[id(r)] = cur["stage"] + "#" + str(len(stages) - 1)
        for c in blocks(r):
            if c.get("type") == "tool_use":
                tool_stage[c.get("id")] = len(stages) - 1
                if c.get("name") == "Bash" and "validate_output.py" in str((c.get("input") or {}).get("command", "")):
                    cur["validator_runs"] += 1
            if c.get("type") == "tool_result":
                cur["validator_fails"] += len(re.findall(r"FAIL: ", json.dumps(c.get("content"))))
    seen = {}
    collect(timed, seen, "main", lambda r: row_stage.get(id(r)))
    # subagents
    sub_dir = os.path.join(os.path.splitext(session)[0], "subagents")
    subs = []
    for sp in sorted(glob.glob(os.path.join(sub_dir, "*.jsonl"))):
        name = os.path.basename(sp)[:-6]
        meta_p = sp[:-6] + ".meta.json"
        meta = json.load(open(meta_p, encoding="utf-8")) if os.path.isfile(meta_p) else {}
        rows = sorted([r for r in load(sp) if r.get("timestamp")], key=lambda r: r["timestamp"])
        ids = collect(rows, seen, name)
        parent_idx = tool_stage.get(meta.get("toolUseId"))
        how = "spawning tool id"
        if parent_idx is None and rows:  # older CLIs write no toolUseId: use the stage running when the agent started
            t0 = ts(rows[0]["timestamp"])
            parent_idx = next((j for j in range(len(stages) - 1, -1, -1) if ts(stages[j]["start"]) <= t0), None)
            how = "start time"
        tot = zero()
        for i in ids:
            add(tot, seen[i])
        tot.update({"agent": name, "description": meta.get("description", ""),
                    "parent_stage": (f"{stages[parent_idx]['stage']}#{parent_idx}" if parent_idx is not None
                                     else "unattributed"), "attributed_by": how,
                    "seconds": round((ts(rows[-1]["timestamp"]) - ts(rows[0]["timestamp"])).total_seconds())
                    if rows else 0})
        subs.append(tot)
    # per-stage totals
    out_stages = []
    for i, s in enumerate(stages):
        key = f"{s['stage']}#{i}"
        tot = zero()
        for rec in seen.values():
            if rec["origin"] == "main" and rec["stage"] == key:
                add(tot, rec)
        incl = dict(tot)
        for sb in subs:
            if sb["parent_stage"] == key:
                for k in ("turns", "cost_cli_method", "cost_list_1h", "output_tokens",
                          "cache_read_input_tokens", "cache_creation_input_tokens", "input_tokens"):
                    incl[k] += sb[k]
        out_stages.append({**s, **tot, "key": key,
                           "seconds": round((ts(s["end"]) - ts(s["start"])).total_seconds()),
                           "with_subagents": {k: incl[k] for k in ("turns", "output_tokens", "cost_cli_method",
                                                                    "cost_list_1h")}})
    # per-model totals over every counted message
    per_model = {}
    for rec in seen.values():
        add(per_model.setdefault(base_model(rec["model"]), zero()), rec)
    first = min((r for r in seen.values() if r["origin"] == "main"), key=lambda r: r["ts"] or "", default=None)
    report = {"session": session, "split": mode, "stages": out_stages, "subagents": subs,
              "per_model": per_model,
              "duplicate_ids_across_files": sum(1 for r in seen.values() if r.get("dup_across_files")),
              "prompt_cache_at_start": None if not first else {
                  "cache_read": first["usage"]["cache_read_input_tokens"],
                  "cache_write": first["usage"]["cache_creation_input_tokens"],
                  "state": "warm" if first["usage"]["cache_read_input_tokens"] > 0 else "cold"}}
    report["reconcile"] = reconcile(report, result, main_rows, seen)
    return report


def reconcile(report, result_path, main_rows, seen):
    """Compare computed totals with the CLI's own record (a -p result JSON, else a cost-state row)."""
    src, mu, total, window = None, None, None, None
    if result_path:
        res = json.load(open(result_path, encoding="utf-8"))
        src, mu, total = "result json", res.get("modelUsage") or {}, res.get("total_cost_usd")
    else:
        idx = [i for i, r in enumerate(main_rows) if r.get("type") == "cost-state"]
        if not idx:
            return {"source": None, "note": "no cost record to compare against"}
        cs = main_rows[idx[-1]]
        src, mu, total = "cost-state row", cs.get("modelUsage") or {}, cs.get("totalCostUSD")
        end = next((r["timestamp"] for r in reversed(main_rows[:idx[-1]]) if r.get("timestamp")), None)
        start = dt.datetime.fromtimestamp(cs["startTime"] / 1000, dt.timezone.utc).isoformat() \
            if cs.get("startTime") else None
        window = {"from": start, "to": end}
    if window:  # recompute over the cost record's own window only
        pm = {}
        for rec in seen.values():
            if rec["ts"] and (not window["from"] or ts(rec["ts"]) >= ts(window["from"])) and \
                    (not window["to"] or ts(rec["ts"]) <= ts(window["to"])):
                add(pm.setdefault(base_model(rec["model"]), zero()), rec)
    else:
        pm = report["per_model"]
    rows = []
    for model in sorted(set(mu) | set(pm)):
        cli, me = mu.get(model, {}), pm.get(model, zero())
        rows.append({"model": model,
                     "output": [cli.get("outputTokens"), me["output_tokens"]],
                     "cache_read": [cli.get("cacheReadInputTokens"), me["cache_read_input_tokens"]],
                     "cache_write": [cli.get("cacheCreationInputTokens"), me["cache_creation_input_tokens"]],
                     "input": [cli.get("inputTokens"), me["input_tokens"]],
                     "cost": [cli.get("costUSD"), round(me["cost_cli_method"], 4) if not me["unpriced_turns"] else None],
                     "thinking_recorded_by_cli": cli.get("thinkingTokens")})
    return {"source": src, "window": window, "cli_total_cost": total, "models": rows}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("session")
    ap.add_argument("--result", help="the claude -p --output-format json result file, to reconcile against")
    ap.add_argument("--split", choices=["auto", "skill", "milestone"], default="auto")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.isfile(a.session):
        print(f"error: {a.session} not found", file=sys.stderr)
        return 2
    rep = measure(a.session, a.split, a.result)
    if a.json:
        print(json.dumps(rep, indent=1, default=str))
        return 0
    print(f"split: {rep['split']} · prompt cache at start: {rep['prompt_cache_at_start']}")
    print(f"{'stage':<26}{'sec':>6}{'turns':>6}{'c.write':>10}{'c.read':>11}{'output':>9}{'$cli':>8}"
          f"{'+agents$':>9}{'val':>5}{'FAIL':>5}")
    for s in rep["stages"]:
        print(f"{s['stage'][:25]:<26}{s['seconds']:>6}{s['turns']:>6}{s['cache_creation_input_tokens']:>10}"
              f"{s['cache_read_input_tokens']:>11}{s['output_tokens']:>9}{s['cost_cli_method']:>8.3f}"
              f"{s['with_subagents']['cost_cli_method']:>9.3f}{s['validator_runs']:>5}{s['validator_fails']:>5}")
    for sb in rep["subagents"]:
        print(f"  agent {sb['agent'][-12:]} ({sb['parent_stage']}) {sb['seconds']}s turns {sb['turns']} "
              f"out {sb['output_tokens']} ${sb['cost_cli_method']:.3f}")
    print("per model:")
    for m, t in rep["per_model"].items():
        priced = f"${t['cost_cli_method']:.4f} (1h writes at 2x: ${t['cost_list_1h']:.4f})" \
            if not t["unpriced_turns"] else "no verified price"
        print(f"  {m}: turns {t['turns']} in {t['input_tokens']} c.write {t['cache_creation_input_tokens']} "
              f"(1h {t['ephemeral_1h_input_tokens']}) c.read {t['cache_read_input_tokens']} "
              f"out {t['output_tokens']} · {priced}")
    rc = rep["reconcile"]
    if rc.get("source"):
        print(f"reconcile vs {rc['source']} (CLI total ${rc['cli_total_cost']}){' window ' + str(rc['window']) if rc['window'] else ''}:")
        for r in rc["models"]:
            print(f"  {r['model']}: " + " · ".join(f"{k} cli={r[k][0]} computed={r[k][1]}"
                                                   for k in ("output", "cache_read", "cache_write", "input", "cost"))
                  + (f" · thinking (CLI) {r['thinking_recorded_by_cli']}" if r["thinking_recorded_by_cli"] else ""))
    print(f"duplicate message ids across parent/subagent files (counted once): {rep['duplicate_ids_across_files']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
