#!/usr/bin/env python3
"""Deterministically build a canvas HTML from its template by copying the
template and substituting ONLY the swappable regions — the exact cp-then-edit
mechanism CLAUDE.md rule 2 mandates, done in code so it is correct every run.

Why a script: doing the substitution by hand (regex in a model's head) is
error-prone in two specific ways that both silently break the skeleton check:
  1. The template's SWAPPABLE comment contains a literal `<title>`, so a
     dot-matches-newline title regex swallows the comment and the real title.
  2. The JOURNEYS array must end with a bare `];` line (check_canvas's boundary
     marker); emitting it on one line breaks where the neutralizer resumes.
This tool encodes both fixes once. It also self-verifies: after writing, it
runs the same skeleton neutralizer check_canvas uses and refuses to emit a file
that drifted from the template outside the swappable regions.

Two ways to supply the journeys (exactly one is required):

  --from-journeys <a.json> <b.json> ...   PREFERRED. The per-journey schema JSONs
        this run already wrote. Each canvas journey object — including its node
        tree `root` — is DERIVED deterministically here: `root` is the journey's
        own explicit `flow` tree when present (used directly, branch-faithful, no
        approximation), otherwise a flat linear fallback (trigger -> steps -> exit)
        built in code so pre-`flow` journeys still get a canvas. The wrapper fields
        (skill/label/purpose/segment/goal/primaryMetric) come from the journey's
        pattern/name/trigger/audience/objective/primary-KPI. This is the wiring
        that removes the orchestrator's hand-built flat->linear node tree: the
        agent emits `flow` in the JSON, this tool turns the JSONs into the canvas.

  --journeys <j.json>                     A pre-built array of canvas node-tree
        objects (id/skill/label/.../root). The lower-level primitive, kept for
        callers that already hold canvas objects and for regression tests.

Usage:
  build_canvas.py --template templates/canvas.html \
                  --from-journeys output/<project>/*.json \
                  --meta meta.json --out output/<project>/canvas.html

  --meta     : JSON file with any of: title, eyebrow, h1, lede, holdout_tip,
               data_note. Each replaces its swappable region if present in BOTH
               the meta and the template. holdout_tip/data_note are the full JS
               right-hand side (e.g. 'tip("a","b")' or a quoted string) WITHOUT
               the trailing semicolon.
Exit: 0 = built and self-verified, 2 = usage error / drift detected.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_output import _canvas_skeleton  # reuse the authoritative neutralizer
from journey_render import _fmt_wait  # reuse the ISO-duration -> short-form formatter


def _sub_once(text, pattern, repl, flags=0):
    """re.sub with count=1; returns (new_text, n_replacements)."""
    new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=flags)
    return new, n


# --------------------------------------------- journey JSON -> canvas journey obj
_CHANNEL_ICON = {"email": "mail", "push": "bell", "sms": "chat", "in_app": "bolt", "whatsapp": "chat"}
# The canvas keys its channel styles by these ids (templates/canvas.html CHANNELS).
_CANVAS_CHANNEL = {"in_app": "inapp"}
_EDGE_LABEL = {"occurred": "Oldu", "not_occurred": "Olmadı", "default": "Varsayılan", "unmeasurable": "Ölçülemedi"}
_EXIT_TITLE = {"completed": "Tamamlandı", "converted": "Dönüştü", "expired": "Süre doldu", "handoff": "Devir",
               "suppressed": "Bastırıldı", "unsubscribed": "Abonelikten çıktı", "ineligible": "Uygun değil"}
_UNIT_TR = {"W": "hafta", "D": "gün", "H": "saat", "M": "dakika"}


def _esc(s):
    """Journey data that lands inside a `rows[].html` string: it is rendered with
    innerHTML, so event names, anchors and signal names are escaped here. Only
    the model-authored `display.rows` keep their HTML, like copy bodies."""
    return html.escape(str(s if s is not None else ""), quote=True)


def _js_safe(s):
    """A JSON text embedded in a <script> block must not contain `</`: a
    `</script>` inside any string would close the block and run what follows."""
    return s.replace("</", "<\\/")


def _dur_tr(iso):
    """'P1D' -> '1 gün', 'PT1H' -> '1 saat', 'P1DT12H' -> '1 gün 12 saat'."""
    m = re.fullmatch(r"-?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", iso or "")
    if not m or not iso or iso in ("P0D", "PT0H", "PT0M"):
        return "hemen" if iso in ("P0D", "PT0H", "PT0M") else (iso or "?")
    parts = [f"{v} {_UNIT_TR[u]}" for v, u in zip(m.groups(), "WDHM") if v and int(v)]
    return " ".join(parts) or "hemen"


def anchor_text_tr(a):
    """Anchor -> Turkish text for the canvas: 'Girişten 1 gün sonra', 'trial_end 2 gün önce', 'd1 sonrası hemen'."""
    if not isinstance(a, dict):
        return "?"
    off = a.get("offset", "P0D")
    src = a.get("from")
    ref = {"entry": "Giriş", "node": a.get("node"), "event": a.get("event"), "attribute": a.get("attribute")}.get(src) or "?"
    neg = str(off).startswith("-")
    d = _dur_tr(str(off).lstrip("-"))
    if d == "hemen":
        txt = f"{ref} anında" if src == "entry" else f"{ref} sonrası hemen"
    else:
        txt = f"{ref} {d} {'önce' if neg else 'sonra'}"
    cal = a.get("calendar")
    if cal:
        txt += f", saat {cal.get('time_of_day')} ({cal.get('timezone') or 'saat dilimi yok'})"
    return txt


def _signal_text(sig):
    import journey_graph as jg  # noqa: PLC0415
    members = jg.signal_members(sig or {})
    if not members:
        return "?", "?"
    if len(members) == 1:
        m = members[0]
        return str(m.get("name", "?")), str(m.get("source", "?"))
    joiner = " veya " if "any_of" in sig else " ve "
    names = joiner.join(str(m.get("name", "?")) for m in members)
    sources = ", ".join(sorted({str(m.get("source", "?")) for m in members}))
    return names, sources


def _primary_metric(doc):
    for k in doc.get("kpis", []):
        if k.get("type") == "primary":
            return k.get("name", "—")
    return "—"


def _flat_root(doc):
    """Deterministic LINEAR fallback used when a journey JSON has no `flow` tree —
    the same trigger -> step1 -> ... -> exit chain the orchestrator used to build
    by hand, now produced in code so pre-`flow` journeys still get a canvas that
    can't drift. It is linear by construction: a flat `steps` array carries no
    branch structure, so branch_condition is surfaced as a card row rather than as
    an actual fork (that is exactly what the `flow` path exists to fix)."""
    trig = doc.get("trigger") or {}
    entry = {
        "kind": "entry",
        "tag": "Giriş",
        "title": trig.get("value", doc.get("id", "Giriş")),
        "rows": [{"icon": "clock", "html": f"<b>Tetikleyici:</b> {_esc(trig.get('value', ''))}"}],
        "children": [],
    }
    tail = entry  # node whose children we append the next node to
    for st in doc.get("steps", []):
        ch = st.get("channel", "")
        rows = [{"icon": _CHANNEL_ICON.get(ch, "mail"), "html": f"Bekleme: {_esc(_fmt_wait(st.get('wait', ''), st.get('index') == 1))}"}]
        if st.get("branch_condition"):
            rows.append({"icon": "filter", "html": f"Koşul: {_esc(st['branch_condition'])}"})
        node = {
            "kind": "message",
            "channel": _CANVAS_CHANNEL.get(ch, ch),
            "tag": f"Adım {st.get('index')} · {ch}",
            "title": st.get("intent", ""),
            "rows": rows,
            "children": [],
        }
        tail["children"] = [{"label": None, "node": node}]
        tail = node
    exit_ev = (doc.get("exit") or {}).get("success_event", "Çıkış")
    tail["children"] = [{"label": None, "node": {"kind": "exit", "exit": "good", "title": exit_ev}}]
    return entry


def _v2_root(doc):
    """Schema 2.0 graph -> canvas tree. A node reached from several branches
    (a merge) is drawn under each parent, tagged as shared, so the tree stays
    faithful without the canvas needing a graph renderer."""
    import journey_graph as jg  # noqa: PLC0415
    res = jg.analyze(doc)
    if not res["structure_ok"]:
        errs = [m for lvl, m, _ in res["findings"].items if lvl == "error"]
        raise ValueError(f"{doc.get('id')}: journey graph is broken: {errs[:3]}")
    by_id = res["by_id"]
    first_t = {}
    for tl in res["timelines"]:
        for nid, _, tsec in tl:
            if tsec is not None:
                first_t[nid] = min(first_t.get(nid, tsec), tsec)
    incoming = {}
    for n in by_id.values():
        for _, tgt in jg.successors(n):
            incoming[tgt] = incoming.get(tgt, 0) + 1

    def day(nid):
        tsec = first_t.get(nid)
        return f"Gün {tsec // jg.DAY}" if tsec is not None else "Zaman: olaya bağlı"

    drawn = set()

    def exit_node(n, disp):
        reason = n.get("reason") or ""
        title = disp.get("title") or _EXIT_TITLE.get(reason, reason or "Çıkış")
        hand = n.get("handoff") or {}
        if hand.get("to") and not disp.get("title"):
            title = f"Devir: {hand['to']}"
        outcome = n.get("outcome")
        pill = "good" if outcome == "good" else ("neutral" if outcome == "neutral" or hand else "bad")
        return {"kind": "exit", "exit": pill, "title": title}

    def to_node(nid):
        n = by_id[nid]
        disp = n.get("display") or {}
        k = n.get("kind")
        is_shared = incoming.get(nid, 0) > 1
        shared = " · ortak adım" if is_shared else ""
        if k == "entry":
            trig = doc.get("trigger") or {}
            node = {"kind": "entry", "tag": disp.get("tag") or "Giriş",
                    "title": disp.get("title") or trig.get("value", doc.get("id", "")),
                    "rows": disp.get("rows") or [{"icon": "clock", "html": f"<b>Tetikleyici:</b> {_esc(trig.get('value', ''))}"}]}
        elif k == "message":
            ch = n.get("channel", "")
            rows = disp.get("rows")
            if not rows:
                rows = [{"icon": _CHANNEL_ICON.get(ch, "mail"), "html": f"Zamanlama: {_esc(anchor_text_tr(n.get('send')))}"}]
                dl = n.get("delivery") or {}
                if dl.get("mode") == "next_session":
                    rows.append({"icon": "clock", "html": "Gösterim: sonraki oturumda"
                                 + (f", {_esc(_dur_tr(dl['expires_after']))} içinde görülmezse düşer" if dl.get("expires_after") else "")})
                if dl.get("deadline"):
                    rows.append({"icon": "clock", "html": f"Son gönderim: {_esc(anchor_text_tr(dl['deadline']))}"})
                if n.get("purpose") and n.get("purpose") != "marketing":
                    rows.append({"icon": "gear", "html": f"Amaç: {_esc(n['purpose'])} (pazarlama sıklığına sayılmaz)"})
                if n.get("recipient_role"):
                    rows.append({"icon": "user", "html": f"Alıcı: {_esc(n['recipient_role'])}"})
            node = {"kind": "message", "channel": _CANVAS_CHANNEL.get(ch, ch),
                    "tag": disp.get("tag") or f"{day(nid)} · {ch.replace('_', '-')}{shared}",
                    "title": disp.get("title") or n.get("intent", ""),
                    "rows": rows}
        elif k == "decision":
            names, sources = _signal_text(n.get("signal"))
            node = {"kind": "decision", "tag": disp.get("tag") or f"{day(nid)} · Yol ayrımı{shared}",
                    "title": disp.get("title") or f"{names}?",
                    "rows": disp.get("rows") or [{"icon": "filter", "html": f"Sinyal: {_esc(names)} ({_esc(sources)})"}]}
        else:
            node = exit_node(n, disp)
        if disp.get("extra"):
            node["extra"] = disp["extra"]
        if is_shared and nid in drawn:
            # a merge node is drawn in full once; later parents get a pointer, so a
            # graph with several merges doesn't multiply into hundreds of cards
            node["tag"] = (node.get("tag") or "") + " (yukarıda çizildi)"
            return node
        drawn.add(nid)
        kids = [{"label": _EDGE_LABEL.get(str(lab), lab) if lab is not None else None, "node": to_node(tgt)}
                for lab, tgt in jg.successors(n)]
        if kids:
            node["children"] = kids
        return node

    return to_node(doc["start"])


def journey_to_canvas(doc):
    """Map a per-journey schema JSON onto one canvas journey object
    ({id, skill, label, purpose, segment, goal, primaryMetric, root}). The node
    tree (`root`) is the journey's explicit `flow` when present — used DIRECTLY,
    no linear approximation — otherwise the deterministic flat fallback above."""
    trig = doc.get("trigger") or {}
    ex = doc.get("exit") or {}
    purpose = trig.get("value", "")
    if ex.get("success_event"):
        purpose = f"{purpose} → {ex['success_event']}" if purpose else ex["success_event"]
    return {
        "id": doc.get("id", ""),
        "skill": doc.get("pattern", ""),
        "label": doc.get("name", doc.get("id", "")),
        "purpose": purpose,
        "segment": (doc.get("audience") or {}).get("include", ""),
        "goal": doc.get("objective", ""),
        "primaryMetric": _primary_metric(doc),
        "root": _v2_root(doc) if doc.get("schema_version") == "2.0" else (doc["flow"] if doc.get("flow") else _flat_root(doc)),
    }


def meta_count_mismatch(meta, n):
    """Header text like 'N journey' that disagrees with the actual journey count
    is almost always a stale/reused --meta: the lede/h1 is substituted VERBATIM
    (never counted), so a meta written for a 6-journey run reused on a 3-journey
    build silently claims '6 journey' over 3 tabs. Return a warning string (this
    is cosmetic, so it warns — never blocks a build), or None when they agree."""
    blob = " ".join(str(meta.get(k, "")) for k in ("lede", "h1", "eyebrow", "title"))
    m = re.search(r"(\d+)\s*journey", blob, re.I)
    if m and int(m.group(1)) != n:
        return (
            f"--meta header says '{m.group(0)}' but {n} journey(s) were supplied "
            f"— stale/reused meta? header text is substituted verbatim, not counted"
        )
    return None


def build(template_path, journeys, meta):
    t = Path(template_path).read_text(encoding="utf-8")

    # Header texts — NO DOTALL so the `<title>` inside the SWAPPABLE comment
    # (which has no closing `</title>` on its own line) is never matched.
    if "title" in meta:
        t, _ = _sub_once(t, r"<title>.*?</title>", f"<title>{_esc(meta['title'])}</title>")
    if "eyebrow" in meta:
        t, _ = _sub_once(t, r'<p class="eyebrow">.*?</p>', f'<p class="eyebrow">{_esc(meta["eyebrow"])}</p>')
    if "h1" in meta:
        t, _ = _sub_once(t, r"<h1>.*?</h1>", f"<h1>{_esc(meta['h1'])}</h1>")
    if "lede" in meta:
        t, _ = _sub_once(t, r'<p class="lede">.*?</p>', f'<p class="lede">{_esc(meta["lede"])}</p>')

    # HOLDOUT_TIP / DATA_NOTE — whole line (no DOTALL), so an inner ';' inside
    # the string literal doesn't truncate the match. Only if the template has them.
    if "holdout_tip" in meta and "const HOLDOUT_TIP" in t:
        t, _ = _sub_once(t, r"const HOLDOUT_TIP = .*", f"const HOLDOUT_TIP = {meta['holdout_tip']};")
    if "data_note" in meta and "const DATA_NOTE" in t:
        t, _ = _sub_once(t, r"const DATA_NOTE = .*", f"const DATA_NOTE = {meta['data_note']};")

    # JOURNEYS — multi-line, one journey object per line, closed by a bare `];`
    # line. json.dumps produces valid JS string literals (double-quoted); a
    # journey object serialized compact never contains a bare `];` line, so the
    # only `];` is the intended closer.
    lines = ["const JOURNEYS = ["]
    for i, jj in enumerate(journeys):
        comma = "," if i < len(journeys) - 1 else ""
        lines.append("  " + _js_safe(json.dumps(jj, ensure_ascii=False)) + comma)
    lines.append("];")
    block = "\n".join(lines)
    t, n = _sub_once(t, r"const JOURNEYS = \[.*?\n\];", block, flags=re.S)
    if n != 1:
        raise ValueError(
            f"could not locate the 'const JOURNEYS = [ ... \\n];' region in "
            f"{template_path} — is this a canvas template?"
        )
    return t


def self_verify(built_text, template_path):
    """Refuse to emit a file whose boilerplate drifted from the template."""
    tmpl = Path(template_path).read_text(encoding="utf-8")
    a = _canvas_skeleton(tmpl)
    b = _canvas_skeleton(built_text)
    if a != b:
        # find first differing line for a useful message
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return False, f"skeleton drift at neutralized line {i}: template={x!r} built={y!r}"
        return False, f"skeleton length differs (template {len(a)} vs built {len(b)} lines)"
    return True, "skeleton matches the template outside swappable regions"


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--journeys", help="JSON file: a pre-built array of canvas node-tree objects (id/skill/label/.../root)")
    src.add_argument(
        "--from-journeys", nargs="+", dest="from_journeys", metavar="JOURNEY.json",
        help="one or more per-journey schema JSONs; the canvas object (incl. root) is derived from each — "
             "root = its `flow` tree when present, else a deterministic flat linear fallback",
    )
    ap.add_argument("--meta", required=True, help="JSON file: title/eyebrow/h1/lede/holdout_tip/data_note")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    try:
        meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
        if args.from_journeys:
            journeys = []
            for jp in args.from_journeys:
                doc = json.loads(Path(jp).read_text(encoding="utf-8"))
                if not isinstance(doc, dict) or "id" not in doc:
                    print(f"error: {jp} is not a journey JSON object (no 'id')", file=sys.stderr)
                    return 2
                try:
                    journeys.append(journey_to_canvas(doc))
                except ValueError as e:
                    print(f"error: {e} — refusing to write a canvas for an invalid journey; "
                          f"the validated JSON/markdown outputs remain the deliverable", file=sys.stderr)
                    return 1
        else:
            journeys = json.loads(Path(args.journeys).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    ids = [j.get("id") for j in journeys] if isinstance(journeys, list) else []
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"error: duplicate journey id(s) {dup}: the canvas keys its tabs by id, a second tab could never be shown",
              file=sys.stderr)
        return 2
    if not isinstance(journeys, list) or not journeys:
        print("error: no journeys to build (empty --journeys array or no --from-journeys inputs)", file=sys.stderr)
        return 2

    count_warn = meta_count_mismatch(meta, len(journeys))
    if count_warn:
        print(f"warning: {count_warn}", file=sys.stderr)

    try:
        built = build(args.template, journeys, meta)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    ok, msg = self_verify(built, args.template)
    if not ok:
        print(f"FAIL: {msg}", file=sys.stderr)
        print("Refusing to write a drifted canvas. This is a bug in build_canvas.py, not your data.", file=sys.stderr)
        return 2
    Path(args.out).write_text(built, encoding="utf-8")
    print(f"ok: wrote {args.out} ({len(journeys)} journeys) — {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
