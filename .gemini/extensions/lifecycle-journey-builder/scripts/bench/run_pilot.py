#!/usr/bin/env python3
"""Run the pilot in scripts/bench/pilot.json: A1, A2, B once each, in order, each in its own fresh worktree.

  run_pilot.py --work <dir outside the repo> [--only A1 ...]            dry run: prints what would run
  run_pilot.py --work <dir> --execute                                  spends money

After each run: the scope check, then the comparability verdict over the runs
done so far. It stops at the first run that is out of scope or hit a budget
stop, and never starts repeats; that is a separate decision.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def verdict(records, cfg):
    reasons = []
    if len({r.get("cli_version") for r in records}) > 1:
        reasons.append("CLI version differs between runs")
    for r in records:
        if r["guard"]["fired"] or (r.get("cli") or {}).get("subtype") == "error_max_budget_usd":
            reasons.append(f"{r['name']}: stopped on budget")
        if cfg["fixed"]["model"] not in json.dumps((r.get("cli") or {}).get("modelUsage") or {}):
            reasons.append(f"{r['name']}: main model is not {cfg['fixed']['model']}")
        for m in (r.get("reconcile") or {}).get("models", []):
            if any(m[k][0] != m[k][1] for k in ("output", "cache_read", "cache_write", "input")):
                reasons.append(f"{r['name']}: transcript does not reconcile with the CLI result for {m['model']}")
        if not r["scope_check"]["in_scope"]:
            reasons.append(f"{r['name']}: out of scope: {r['scope_check']['problems']}")
    states = {(r.get("prompt_cache_at_start") or {}).get("state") for r in records}
    if len(states) > 1:
        reasons.append(f"first-call prompt cache differs between runs: {states}")
    return reasons


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--work", required=True)
    ap.add_argument("--only", nargs="+")
    ap.add_argument("--execute", action="store_true")
    a = ap.parse_args(argv)
    cfg = json.load(open(os.path.join(HERE, "pilot.json"), encoding="utf-8"))
    fx = cfg["fixed"]
    work = os.path.abspath(a.work)
    if work.startswith(ROOT + os.sep):
        print("error: --work must be outside the repo", file=sys.stderr)
        return 2
    head = git("rev-parse", "HEAD")
    records = []
    for name in a.only or fx["order"]:
        run = cfg["runs"][name]
        commit = head if run["commit"] == "HEAD" else git("rev-parse", run["commit"])
        wt = os.path.join(work, f"wt-{name}")
        claude_args = [cfg["prompts"][run["prompt"]], "--plugin-dir", wt, "--model", fx["model"],
                       "--max-budget-usd", str(fx["cli_max_budget_usd"]), "--permission-mode", fx["permission_mode"],
                       "--allowedTools", *fx["allowed_tools"]]
        guard = [sys.executable, os.path.join(HERE, "run_guarded.py"), "--name", name, "--cwd", wt,
                 "--cap-usd", str(fx["guard_cap_usd"]), "--record-dir", os.path.join(work, "records"),
                 "--outdir", fx["outdir"], "--cache-dir", "output", "--", *claude_args]
        print(f"{name}: commit {commit[:7]} · scope {run['scope']} · worktree {wt}")
        if not a.execute:
            print("  would run: run_guarded.py --name", name, "... -- <prompt", run["prompt"] + ">",
                  " ".join(claude_args[1:]))
            continue
        if os.path.isdir(wt):
            subprocess.run(["git", "worktree", "remove", "--force", wt], cwd=ROOT)
            shutil.rmtree(wt, ignore_errors=True)
        git("worktree", "add", "--detach", wt, commit)
        subprocess.run(guard)
        rec_path = os.path.join(work, "records", f"{name}.json")
        rec = json.load(open(rec_path))
        sc = subprocess.run([sys.executable, os.path.join(HERE, "check_scope.py"), os.path.join(wt, fx["outdir"]),
                             "--scope", run["scope"], "--json"], capture_output=True, text=True)
        rec["scope_check"] = json.loads(sc.stdout) if sc.stdout.strip().startswith("{") else \
            {"in_scope": False, "problems": [sc.stdout.strip() or sc.stderr.strip()]}
        json.dump(rec, open(rec_path, "w"), indent=1, default=str)
        records.append(rec)
        reasons = verdict(records, cfg)
        if reasons:
            print("NOT COMPARABLE — stopping, no further runs:")
            for r in reasons:
                print("  -", r)
            return 1
    if a.execute:
        print("pilot comparable on every check; repeats need a separate go-ahead")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
