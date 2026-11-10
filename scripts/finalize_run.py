#!/usr/bin/env python3
"""Run bookkeeping for lifecycle-journeys, done by code instead of model turns.

  start  <outdir> --scope <journey-id> [...] [--mode single|portfolio]
      Archives the previous run (its manifest, dossier, canvas and every file its
      manifest listed) into <outdir>/runs/<old-run-id>/, then opens a new run:
      a unique run id and the list of journeys in scope.

  finish <outdir> [--max-discount N] [--sector SLUG]
      For the journeys in scope only (nothing else in the folder leaks in):
        1. validates each journey JSON (the canonical artifact);
        2. renders the mechanical doc sections (§5 table, §8 diagram) from it,
           leaving narrative sections untouched;
        3. refreshes the registry's mechanical fields from the journey files
           (file, pattern, stage, priority, channels, computed weekly load),
           keeping the judgment fields the model wrote (audience groups,
           overlaps, existing journeys, breach policy); entries outside the
           scope are dropped;
        4. validates registry, dossier and copy;
        5. builds the canvas only if nothing failed;
        6. writes run-manifest.json with sha256 of every delivered file,
           readiness per journey and the validator result.
      Exit 0 passed · 3 delivered but unverified/draft · 1 failed (no canvas,
      manifest status "failed") · 2 usage error.

It never edits a journey's design: JSON content is read, not rewritten.
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import journey_graph as jg  # noqa: E402
import journey_render as jr  # noqa: E402

VO = os.path.join(HERE, "validate_output.py")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_validator(*args):
    r = subprocess.run([sys.executable, VO, *args], capture_output=True, text=True)
    summary = next((ln for ln in r.stdout.splitlines() if ln.startswith("validator ")), "")
    problems = [ln.strip() for ln in r.stdout.splitlines()
                if ln.startswith("FAIL") or "unverifiable (critical)" in ln]
    if r.returncode not in (0, 3) and not problems:
        # a traceback or a usage error: never silently a pass
        tail = (r.stderr.strip() or r.stdout.strip()).splitlines()[-1:] or ["no output"]
        problems = [f"FAIL: validator exited {r.returncode} without findings: {tail[0][:200]}"]
        r.returncode = 1
    return r.returncode, summary, problems


def load_manifest(outdir):
    p = os.path.join(outdir, "run-manifest.json")
    return (json.load(open(p, encoding="utf-8")), p) if os.path.isfile(p) else (None, p)


ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*-[0-9]{2}$")
RUN_ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{4}$")


def cmd_start(a):
    bad = [s for s in a.scope if not ID_RE.match(s)]
    if bad:
        print(f"error: journey ids must match <sector>-<pattern>-<nn>: {bad}", file=sys.stderr)
        return 2
    os.makedirs(a.outdir, exist_ok=True)
    old, mpath = load_manifest(a.outdir)
    if old:
        old_id = str(old.get("run_id", ""))
        if not RUN_ID_RE.match(old_id):
            # a manifest from before the run-id format: archive it under a safe name instead of refusing
            old_id = "legacy-" + (re.sub(r"[^A-Za-z0-9-]", "-", old_id).strip("-")[:40] or
                                  hashlib.sha256(json.dumps(old, sort_keys=True).encode()).hexdigest()[:8])
        dest = os.path.join(a.outdir, "runs", old_id)
        os.makedirs(dest, exist_ok=True)
        listed = [f["path"] for f in old.get("files", [])] + ["dossier.md", "canvas.html", "_meta.json",
                                                              "iletisim-metinleri.html", "message-copy.html",
                                                              "run-manifest.json"]
        listed = [p for p in listed if not os.path.isabs(p) and ".." not in p.split("/")]
        moved = 0
        for rel in dict.fromkeys(listed):
            src = os.path.join(a.outdir, rel)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
                shutil.move(src, os.path.join(dest, rel))
                moved += 1
        print(f"archived run {old.get('run_id')} ({moved} files) -> runs/{old.get('run_id')}/")
    run_id = dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)
    manifest = {"run_id": run_id, "started_at": dt.datetime.now().isoformat(timespec="seconds"),
                "scope": {"mode": a.mode, "journeys": a.scope}, "status": "in_progress"}
    if a.mode == "single":
        manifest["scope"]["note"] = ("single-journey run: other patterns' eligibility and portfolio coverage "
                                     "were not reviewed")
    json.dump(manifest, open(mpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"run {run_id} · scope {a.mode}: {', '.join(a.scope)}")
    return 0


def replace_section(md, heading_re, body):
    m = re.search(heading_re, md, re.M)
    if not m:
        return md, False
    start = m.end()
    nxt = re.search(r"^## ", md[start:], re.M)
    end = start + nxt.start() if nxt else len(md)
    return md[:start] + "\n\n" + body.strip() + "\n\n" + md[end:].lstrip("\n"), True


def cmd_finish(a):
    manifest, mpath = load_manifest(a.outdir)
    if not manifest:
        print("error: no run-manifest.json — run `finalize_run.py start` first", file=sys.stderr)
        return 2
    scope = manifest["scope"]["journeys"]
    failures, unverified, files, journeys = [], [], [], {}
    for jid in scope:
        jp, mp = os.path.join(a.outdir, f"{jid}.json"), os.path.join(a.outdir, f"{jid}.md")
        if not os.path.isfile(jp):
            failures.append(f"{jid}: journey JSON missing ({jid}.json)")
            continue
        code, summary, probs = run_validator("journey", jp)
        try:
            doc = json.load(open(jp, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            failures.append(f"{jid}: journey JSON unreadable: {e}")
            files.append(jp)
            continue
        journeys[jid] = {"readiness": doc.get("readiness"), "open_items": doc.get("open_items", []),
                         "validator": summary, "exit": code}
        (failures if code == 1 else unverified if code == 3 else []).extend(f"{jid}: {p}" for p in probs)
        files.append(jp)
        if not os.path.isfile(mp):
            failures.append(f"{jid}: journey doc missing ({jid}.md)")
            continue
        try:
            if jg.is_v2(doc) and code != 1:
                md = open(mp, encoding="utf-8").read()
                md, ok5 = replace_section(md, r"^## 5\. Steps[^\n]*$", jr.render_step_table(doc))
                md, ok8 = replace_section(md, r"^## 8\. Flow diagram[^\n]*$", jr.render_mermaid(doc))
                if not (ok5 and ok8):
                    failures.append(f"{jid}: doc lacks the '## 5. Steps' / '## 8. Flow diagram' headings the "
                                    f"template requires; the mechanical sections could not be rendered")
                open(mp, "w", encoding="utf-8").write(md)
            if code != 1:  # a failed journey's doc was not re-rendered; its consistency verdict would only mislead
                ccode, _, cprobs = run_validator("consistency", mp, jp)
                if ccode == 1:
                    failures.extend(f"{jid}: {p}" for p in cprobs)
        except Exception as e:  # noqa: BLE001  a render crash is a failed run, not a traceback
            failures.append(f"{jid}: rendering the doc failed: {type(e).__name__}: {e}")
        files.append(mp)
    # registry: mechanical fields from the journey files, judgment fields kept
    ppath = os.path.join(a.outdir, "portfolio.json")
    reg = json.load(open(ppath, encoding="utf-8")) if os.path.isfile(ppath) else {}
    reg.setdefault("schema_version", "2.0")
    reg.setdefault("frequency_policy", {"window": "P7D", "on_breach": "defer"})
    reg.setdefault("external_journeys_status", "unknown")
    reg["scope"] = manifest["scope"]["mode"]
    old = {j.get("id"): j for j in reg.get("journeys", [])}
    entries = []
    for jid in scope:
        jp = os.path.join(a.outdir, f"{jid}.json")
        if not os.path.isfile(jp):
            continue
        try:
            doc = json.load(open(jp, encoding="utf-8"))
            res = jg.analyze(doc)
        except Exception as e:  # noqa: BLE001
            failures.append(f"{jid}: registry refresh failed: {type(e).__name__}: {e}")
            continue
        e = dict(old.get(jid, {}))
        e.update({"id": jid, "file": f"{jid}.json", "pattern": doc.get("pattern"), "stage": doc.get("stage"),
                  "priority": doc.get("priority"),
                  "channels": sorted({n.get("channel") for n in doc.get("nodes", [])
                                      if n.get("kind") == "message" and n.get("channel")}),
                  "est_msgs_per_week": {k: v for k, v in res["freq"].items() if k != "total"}})
        e.setdefault("audience_group", jid)
        entries.append(e)
    reg["journeys"] = entries
    json.dump(reg, open(ppath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    code, summary, probs = run_validator("portfolio", ppath)
    (failures if code == 1 else unverified if code == 3 else []).extend(f"portfolio: {p}" for p in probs)
    files.append(ppath)
    dpath = os.path.join(a.outdir, "dossier.md")
    if os.path.isfile(dpath):
        code, _, probs = run_validator("dossier", dpath)
        (failures if code == 1 else unverified if code == 3 else []).extend(f"dossier: {p}" for p in probs)
        files.append(dpath)
    else:
        failures.append("dossier: dossier.md is missing; write it before finish so it is validated and hashed")
    copies = [cp for cp in sorted(glob.glob(os.path.join(a.outdir, "_copy", "*.md")))
              if os.path.basename(cp)[:-3] in scope]
    if copies and (a.max_discount is None or not a.sector):
        failures.append("copy: finish needs --max-discount and --sector when copy is in scope; without them the "
                        "discount ceiling and the sector's banned words are not checked")
    for cp in sorted(glob.glob(os.path.join(a.outdir, "_copy", "*.md"))):
        jid = os.path.basename(cp)[:-3]
        if jid not in scope:
            continue
        args = ["copy", cp] + (["--max-discount", str(a.max_discount)] if a.max_discount is not None else []) \
            + (["--sector", a.sector] if a.sector else [])
        code, _, probs = run_validator(*args)
        (failures if code == 1 else unverified if code == 3 else []).extend(f"copy {jid}: {p}" for p in probs)
        files.append(cp)
    for name in ("iletisim-metinleri.html", "message-copy.html"):
        cc = os.path.join(a.outdir, name)
        if os.path.isfile(cc):
            ccode, _, cprobs = run_validator("canvas", cc, "--template", os.path.join(ROOT, "templates", "copy-canvas.html"))
            if ccode == 1:
                failures.extend(f"{name}: {p}" for p in cprobs)
            files.append(cc)
    for cj in sorted(glob.glob(os.path.join(a.outdir, "_copy", "*.canvas.json"))):
        jid = os.path.basename(cj)[: -len(".canvas.json")]
        md = os.path.join(a.outdir, "_copy", f"{jid}.md")
        if jid in scope and os.path.isfile(md):
            ccode, _, cprobs = run_validator("copy-canvas", md, cj)
            if ccode == 1:
                failures.extend(f"copy canvas {jid}: {p}" for p in cprobs)
            files.append(cj)
    canvas = "skipped (validation failed)" if failures else "not built"
    stale = os.path.join(a.outdir, "canvas.html")
    if failures and os.path.isfile(stale):
        os.replace(stale, stale + ".stale")  # never leave a previous canvas next to a failed run
    if not failures:
        meta_path = os.path.join(a.outdir, "_meta.json")
        if not os.path.isfile(meta_path):
            json.dump({"title": "Lifecycle journeys", "eyebrow": "Journey canvas", "h1": "Journeys",
                       "lede": f"{len(scope)} journey(s) for review.", "holdout_tip": "",
                       "data_note": ""}, open(meta_path, "w", encoding="utf-8"))
        out = os.path.join(a.outdir, "canvas.html")
        r = subprocess.run([sys.executable, os.path.join(HERE, "build_canvas.py"), "--template",
                            os.path.join(ROOT, "templates", "canvas.html"), "--from-journeys",
                            *[os.path.join(a.outdir, f"{j}.json") for j in scope], "--meta", meta_path,
                            "--out", out], capture_output=True, text=True)
        canvas = "built" if r.returncode == 0 and os.path.isfile(out) else f"failed: {r.stderr.strip()[:200]}"
        if os.path.isfile(out) and r.returncode == 0:
            files.append(out)
        else:
            failures.append(f"canvas: {canvas}")
    status = "failed" if failures else ("unverified" if unverified or
                                        any(j["readiness"] == "draft" for j in journeys.values()) else "passed")
    vline = subprocess.run([sys.executable, VO, "dossier", "/dev/null"], capture_output=True, text=True).stdout
    vver = next((ln for ln in vline.splitlines() if ln.startswith("validator ")), "").split(" · ")[:2]
    manifest.update({"finished_at": dt.datetime.now().isoformat(timespec="seconds"), "status": status,
                     "validator": " · ".join(vver), "journeys": journeys, "canvas": canvas,
                     "failures": failures, "unverified": unverified,
                     "files": [{"path": os.path.relpath(f, a.outdir), "sha256": sha(f)} for f in files]})
    json.dump(manifest, open(mpath, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"run {manifest['run_id']}: {status} · {len(journeys)} journey(s) · canvas {canvas}")
    for f in failures[:6]:
        print(f"  FAIL {f}")
    for u in unverified[:6]:
        print(f"  UNVERIFIED {u}")
    return 1 if failures else (3 if status == "unverified" else 0)


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("outdir")
    s.add_argument("--scope", nargs="+", required=True)
    s.add_argument("--mode", choices=["single", "portfolio"], default="portfolio")
    f = sub.add_parser("finish")
    f.add_argument("outdir")
    f.add_argument("--max-discount", type=float)
    f.add_argument("--sector")
    a = ap.parse_args(argv)
    return cmd_start(a) if a.cmd == "start" else cmd_finish(a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
