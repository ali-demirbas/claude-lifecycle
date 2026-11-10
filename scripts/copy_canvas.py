#!/usr/bin/env python3
"""Build the copy-canvas JOURNEYS object from reviewed copy docs, in code.

  copy_canvas.py <output/<project>/_copy/<id>.md> [...] --out <journeys.json>

The reviewed markdown (templates/copy-output.md) is the source of truth. The
canvas object used to be written by hand, which let it drift from the reviewed
text (swapped variant bodies, a stale count, an extra CTA) and let raw HTML from
the copy reach the page. Generating it here makes the two equal by construction:
every field text is HTML-escaped, `{{variables}}` get the canvas's variable
wrapper, counts are the doc's own `chars/limit`, and the review badge follows the
doc's Review status. Feed the output to:

  build_canvas.py --template templates/copy-canvas.html --journeys <journeys.json> --meta <meta.json> --out ...

`validate_output.py copy-canvas <md> <canvas.json>` compares a canvas object with
what this script derives from the md, step by step and variant by variant.
"""
import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate_output as vo  # noqa: E402

H1 = re.compile(r"^# .*?\(`([^`]+)`\)\s*$", re.M)
H1_NAME = re.compile(r"^# (?:Copy|İletişim Metinleri|Message copy)?\s*[—:-]?\s*(.+?)\s*\(`", re.M)
INTENT = re.compile(r"^\*\*(?:Intent|Niyet):\*\*\s*(.+?)(?:\s*·\s*\*\*|$)", re.M)


def _field_html(text):
    esc = html.escape(text, quote=False)
    return re.sub(r"\{\{[^}]+\}\}", lambda m: f'<code class="variable">{m.group(0)}</code>', esc)


def _review(text):
    m = vo.REVIEW_STATUS_RE.search(text)
    s = m.group(1) if m else ""
    if "⚖" in s:
        return "legal"
    if "⚠" in s:
        return "notes"
    if "✅" in s:
        return "pass"
    return "pending"


def _rows(section):
    out = []
    for ln in section.splitlines():
        m = vo.ROW.match(ln)
        if m and m.group(1).strip().lower() not in ("field", "alan"):
            out.append([m.group(1).strip(), _field_html(m.group(2).strip()), f"{m.group(3)}/{m.group(5)}"])
    return out


def derive(md_path):
    text = open(md_path, encoding="utf-8").read()
    jid_m = H1.search(text)
    jid = jid_m.group(1) if jid_m else os.path.splitext(os.path.basename(md_path))[0]
    name_m = H1_NAME.search(text)
    review = _review(text)
    starts = [m.start() for m in vo.STEP_HEAD.finditer(text)]
    steps = []
    for k, s in enumerate(starts):
        block = text[s: starts[k + 1] if k + 1 < len(starts) else len(text)]
        head = block.split("\n", 1)[0]
        tag = re.sub(r"^##\s*", "", head)
        tag = re.sub(r"\s*\(`[^`]*`\)\s*$", "", tag).strip()
        intent_m = INTENT.search(block)
        fb = re.search(r"^### (?:Fallback|Yedek)\b.*$", block, re.M)
        variants = []
        vheads = list(vo.VARIANT_HEAD.finditer(block))
        for vi, vm in enumerate(vheads):
            end = vheads[vi + 1].start() if vi + 1 < len(vheads) else (fb.start() if fb and fb.start() > vm.start()
                                                                      else len(block))
            label = re.sub(r"^###\s*", "", vm.group(0)).strip()
            variants.append({"label": label, "fields": _rows(block[vm.end():end])})
        if not vheads:
            variants.append({"label": "", "fields": _rows(block[: fb.start()] if fb else block)})
        step = {"tag": tag, "intent": intent_m.group(1).strip() if intent_m else "", "review": review,
                "variants": variants}
        if fb:
            rest = block[fb.end():]
            nxt = re.search(r"^#{2,3} |^\*\*(Personalization variables used|Reviewer notes|Kullanılan değişkenler|"
                            r"İnceleme notları):\*\*", rest, re.M)
            body = rest[: nxt.start()] if nxt else rest
            rows = _rows(body)
            if rows:
                step["fallback"] = " · ".join(f"{r[0]}: {r[1]}" for r in rows)
            else:
                prose = " ".join(ln.strip() for ln in body.splitlines() if ln.strip() and not ln.startswith("|"))
                if prose:
                    step["fallback"] = _field_html(prose)
        steps.append(step)
    return {"id": jid, "label": name_m.group(1).strip() if name_m else jid, "steps": steps}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    journeys = [derive(p) for p in a.docs]
    ids = [j["id"] for j in journeys]
    if len(set(ids)) != len(ids):
        print(f"error: duplicate journey ids {ids}", file=sys.stderr)
        return 2
    json.dump(journeys, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"ok: {a.out} ({len(journeys)} journey(s), {sum(len(j['steps']) for j in journeys)} step(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
