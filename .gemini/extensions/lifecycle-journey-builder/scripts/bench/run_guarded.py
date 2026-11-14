#!/usr/bin/env python3
"""Run one benchmark `claude -p` under an independent spend guard, and record everything needed to compare it.

  run_guarded.py --name A1 --cwd <plugin checkout> --cap-usd 4 --record-dir <dir>
                 [--config-dir <dir>] [--outdir <run output dir, must be empty>] -- <claude args after -p ...>

Why a guard on top of --max-budget-usd: the CLI checks its budget between
turns, so the turn in flight (and any subagent turns running in parallel)
finish after the line is crossed, and its total prices every cache write at
the 5-minute rate. This guard reads the session transcripts (parent and
subagents) every 2 s, prices 1-hour cache writes at 2x and unknown models at a
conservative fallback, and kills the whole process group when the estimate
reaches the cap. It is a stop mechanism, not a billing ceiling: requests
already in flight when it fires are still billed, and calls the CLI doesn't
write to the transcript are invisible to it. Set the cap below the real limit.

Recorded per run (record-dir/<name>.json): CLI version, git commit and plugin
version of --cwd, the exact command, config dir, model, effort flag, output
dir state before the run, the assessment cache state, the CLI result
(cost/turns/duration/modelUsage), the guard's own estimate and whether it
fired, the prompt-cache state of the first API call, and the transcript-based
per-stage breakdown reconciled against the CLI result.
"""
import argparse
import datetime as dt
import glob
import json
import os
import signal
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import measure_run as mr  # noqa: E402

FALLBACK_PRICE = (15.0, 75.0)  # deliberately high: an unpriced model must trip the guard early, not late


def guard_cost(paths):
    seen = {}
    for p in paths:
        mr.collect(sorted([r for r in mr.load(p) if r.get("timestamp")], key=lambda r: r["timestamp"]), seen, p)
    total, unpriced = 0.0, set()
    for rec in seen.values():
        u, model = rec["usage"], rec["model"]
        if mr.price_for(model):
            total += mr.cost(u, model)[1]
        else:
            unpriced.add(model)
            pin, pout = FALLBACK_PRICE[0] / 1e6, FALLBACK_PRICE[1] / 1e6
            total += (u["input_tokens"] + u["cache_creation_input_tokens"] * 2) * pin + \
                u["cache_read_input_tokens"] * pin * 0.1 + u["output_tokens"] * pout
    return total, sorted(m for m in unpriced if m)


def transcripts(config_dir, sid):
    base = os.path.join(config_dir, "projects")
    main = glob.glob(os.path.join(base, "*", f"{sid}.jsonl"))
    subs = glob.glob(os.path.join(base, "*", sid, "subagents", "*.jsonl"))
    return main, subs


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def main(argv):
    if "--" not in argv:
        print("usage: run_guarded.py [options] -- <claude -p args>", file=sys.stderr)
        return 2
    i = argv.index("--")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--cwd", required=True)
    ap.add_argument("--cap-usd", type=float, required=True)
    ap.add_argument("--record-dir", required=True)
    ap.add_argument("--config-dir")
    ap.add_argument("--outdir", help="run output dir; must be empty or absent before the run")
    ap.add_argument("--cache-dir", help="assessment cache dir to record (and require empty)")
    a = ap.parse_args(argv[:i])
    claude_args = argv[i + 1:]
    if "--no-session-persistence" in claude_args:
        print("error: the guard needs the transcript; drop --no-session-persistence", file=sys.stderr)
        return 2
    for bad in ("--session-id", "--output-format"):
        if bad in claude_args:
            print(f"error: {bad} is set by the guard", file=sys.stderr)
            return 2
    cwd = os.path.abspath(a.cwd)
    if a.outdir:
        od = os.path.join(cwd, a.outdir)
        if os.path.isdir(od) and os.listdir(od):
            print(f"error: output dir {od} is not empty; a stale run must not count as this one", file=sys.stderr)
            return 2
    cache_state = None
    if a.cache_dir:
        cd = os.path.join(cwd, a.cache_dir)
        cache_state = "absent" if not os.path.isdir(cd) else ("empty" if not os.listdir(cd) else "NOT EMPTY")
        if cache_state == "NOT EMPTY":
            print(f"error: assessment cache {cd} holds entries; clear it so the run assesses fresh", file=sys.stderr)
            return 2
    config_dir = a.config_dir or os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    env = dict(os.environ)
    if a.config_dir:
        env["CLAUDE_CONFIG_DIR"] = a.config_dir
    sid = str(uuid.uuid4())
    cmd = ["claude", "-p", *claude_args, "--session-id", sid, "--output-format", "json"]
    os.makedirs(a.record_dir, exist_ok=True)
    rec = {"name": a.name, "session_id": sid, "started": dt.datetime.now().isoformat(timespec="seconds"),
           "cli_version": sh(["claude", "--version"], cwd), "commit": sh(["git", "rev-parse", "HEAD"], cwd),
           "plugin_version": (json.load(open(os.path.join(cwd, ".claude-plugin", "plugin.json")))["version"]
                              if os.path.isfile(os.path.join(cwd, ".claude-plugin", "plugin.json")) else None),
           "cwd": cwd, "config_dir": a.config_dir or "default", "cmd": [c if len(c) < 300 else c[:120] + "…" for c in cmd],
           "model_flag": claude_args[claude_args.index("--model") + 1] if "--model" in claude_args else None,
           "effort_flag": claude_args[claude_args.index("--effort") + 1] if "--effort" in claude_args else "default",
           "cli_max_budget": claude_args[claude_args.index("--max-budget-usd") + 1]
           if "--max-budget-usd" in claude_args else None,
           "guard_cap_usd": a.cap_usd, "assessment_cache": cache_state}
    out_path = os.path.join(a.record_dir, f"{a.name}.result.json")
    t0 = time.time()
    with open(out_path, "w") as out, open(os.path.join(a.record_dir, f"{a.name}.stderr"), "w") as err:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=out, stderr=err, start_new_session=True)
        fired, peak, unpriced = False, 0.0, []
        while p.poll() is None:
            time.sleep(2)
            m, s = transcripts(config_dir, sid)
            if m:
                peak, unpriced = guard_cost(m + s)
                if peak >= a.cap_usd and not fired:
                    fired = True
                    os.killpg(p.pid, signal.SIGTERM)
                    try:
                        p.wait(10)
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
        rc = p.wait()
    rec["seconds"] = round(time.time() - t0)
    rec["exit"] = rc
    m, s = transcripts(config_dir, sid)
    if m:
        peak, unpriced = guard_cost(m + s)
    rec["guard"] = {"fired": fired, "estimate_usd_list_1h": round(peak, 4), "unpriced_models": unpriced}
    try:
        res = json.load(open(out_path))
        rec["cli"] = {k: res.get(k) for k in ("subtype", "is_error", "num_turns", "duration_ms", "total_cost_usd",
                                               "stop_reason", "terminal_reason")}
        rec["cli"]["modelUsage"] = res.get("modelUsage")
    except (json.JSONDecodeError, OSError):
        rec["cli"] = None
        out_path = None
    if m:
        rep = mr.measure(m[0], "auto", out_path)
        rec["transcript"] = m[0]
        rec["prompt_cache_at_start"] = rep["prompt_cache_at_start"]
        rec["per_model"] = rep["per_model"]
        rec["reconcile"] = rep["reconcile"]
        rec["stages"] = [{k: st[k] for k in ("stage", "seconds", "turns", "output_tokens", "cache_read_input_tokens",
                                              "cache_creation_input_tokens", "cost_cli_method", "with_subagents",
                                              "validator_runs", "validator_fails")} for st in rep["stages"]]
        rec["subagents"] = rep["subagents"]
    json.dump(rec, open(os.path.join(a.record_dir, f"{a.name}.json"), "w"), indent=1, default=str)
    cli = rec.get("cli") or {}
    print(f"{a.name}: exit {rc} · {rec['seconds']}s · CLI ${cli.get('total_cost_usd')} ({cli.get('subtype')}) · "
          f"guard est ${rec['guard']['estimate_usd_list_1h']}{' FIRED' if fired else ''}")
    return 0 if rc == 0 and not fired else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
