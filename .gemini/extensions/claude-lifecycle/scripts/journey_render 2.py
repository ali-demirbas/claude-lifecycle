#!/usr/bin/env python3
"""Deterministically render a journey doc's MECHANICAL sections from the journey
JSON — the §5 step table and the §8 Mermaid `flowchart TD`. Both are pure
functions of the JSON with no model judgment, so the journey-architect agent
stops hand-writing them (and the "every branch in the table must also be in the
diagram, and vice versa" manual check disappears — there is now one authoritative
structure).

Two authoritative sources inside the journey JSON, each feeding the section it is
naturally shaped for (see templates/journey.schema.json and CLAUDE.md rule 2):
  - the flat `steps` array   -> §5 step table   (per-step wait/channel/intent/
                                                  branch_condition/copy_ref — the
                                                  linear send sequence)
  - the nested `flow` tree    -> §8 Mermaid       (the branch structure: decision
                                                  nodes emit Evet/Hayır-labeled
                                                  edges from their children labels)

`flow` is REQUIRED here: this renderer only exists for the explicit-branch-tree
path. A journey JSON without `flow` is a pre-existing/older journey that keeps its
hand-authored §5/§8 — on such input this tool exits 2 with a clear message rather
than guessing a branch structure the JSON does not carry.

The same render_* / extract_* functions are imported by
scripts/validate_output.py's consistency check, which regenerates these two
sections and compares them to what the doc actually contains (regenerate-and-diff,
not two hand-authored copies drifting apart).

Usage:
  journey_render.py <journey.json> [--section both|table|mermaid]
Exit: 0 = rendered, 2 = no `flow` field / unreadable input.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# U+2014 em dash — the empty-cell / channel-separator convention already used by
# templates/journey-doc.md and the §8 diagrams (design documentation, not
# customer-facing copy, so the no-em-dash copy rule does not apply here).
EMPTY = "—"
SEP = " — "

STEP_HEADER = "| # | Wait | Channel | Message intent | Branch condition | Copy ref |"
STEP_SEP = "|---|------|---------|----------------|------------------|----------|"

# ISO 8601 duration — mirrors ISO_WAIT in scripts/validate_output.py and the
# schema's steps[].wait pattern (week designator mutually exclusive with D/T).
_WAIT_RE = re.compile(r"^P(?:(\d+)W|(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?)$")

# Per-kind id prefixes for the Mermaid node ids; the single entry node is always T.
_KIND_PREFIX = {"message": "S", "decision": "D", "wait": "W", "exit": "X"}


# ------------------------------------------------------------------ §5 table
def _fmt_wait(iso, first):
    """ISO 8601 duration -> short form (PT1H->'1h', P2D->'2d', P1W->'1w'); step 1
    is anchored to the trigger, later steps to the previous step (journey-doc.md
    §5 rule). An unparseable value is passed through verbatim rather than dropped."""
    m = _WAIT_RE.match(iso or "")
    if not m:
        short = iso or "?"
    else:
        w, d, h, mi, s = m.groups()
        parts = []
        if w:
            parts.append(f"{w}w")
        if d:
            parts.append(f"{d}d")
        if h:
            parts.append(f"{h}h")
        if mi:
            parts.append(f"{mi}m")
        if s:
            parts.append(f"{s}s")
        short = "".join(parts) if parts else (iso or "?")
    return f"+{short} after trigger" if first else f"+{short}"


def render_step_table(doc):
    """The §5 markdown table (header + separator + one row per flat step)."""
    rows = [STEP_HEADER, STEP_SEP]
    for st in doc.get("steps", []):
        idx = st.get("index")
        wait = _fmt_wait(st.get("wait", ""), idx == 1)
        ch = st.get("channel", "")
        intent = st.get("intent", "")
        branch = st.get("branch_condition") or EMPTY
        copyref = st.get("copy_ref") or EMPTY
        rows.append(f"| {idx} | {wait} | {ch} | {intent} | {branch} | {copyref} |")
    return "\n".join(rows)


# ------------------------------------------------------------------ §8 mermaid
def _mm_text(s):
    """Sanitize a label for a double-quoted Mermaid node/edge label: collapse
    newlines and replace the literal double-quote (which would close the label)."""
    return (s or "").replace("\n", " ").replace('"', "'").strip()


def _node_decl(nid, node):
    """One Mermaid node declaration; shape encodes the kind (decision=diamond,
    message=rect, wait=parallelogram, entry/exit=stadium)."""
    title = _mm_text(node.get("title") or node.get("tag") or node.get("kind"))
    kind = node.get("kind")
    if kind == "message":
        ch = node.get("channel")
        label = f"{ch}{SEP}{title}" if ch else title
        return f'{nid}["{label}"]'
    if kind == "decision":
        return f'{nid}{{"{title}"}}'
    if kind == "wait":
        return f'{nid}[/"{title}"/]'
    return f'{nid}(["{title}"])'  # entry and exit both stadium-shaped


def render_mermaid(doc):
    """The §8 fenced ```mermaid flowchart TD``` block, generated from `flow`.

    Nodes are declared in pre-order traversal, then every parent->child edge is
    emitted (decision children carry their branch label). Declaring nodes before
    edges keeps the output unambiguous and independent of how many parents a node
    has — a plain, always-valid Mermaid shape."""
    flow = doc.get("flow")
    if not flow:
        return ""
    counters = {}
    decls, edges = [], []

    def new_id(kind):
        if kind == "entry":
            return "T"
        p = _KIND_PREFIX.get(kind, "N")
        counters[p] = counters.get(p, 0) + 1
        return f"{p}{counters[p]}"

    def walk(node, parent_id, edge_label):
        if not isinstance(node, dict):
            return
        nid = new_id(node.get("kind"))
        decls.append("    " + _node_decl(nid, node))
        if parent_id is not None:
            if edge_label:
                edges.append(f"    {parent_id} -->|{_mm_text(edge_label)}| {nid}")
            else:
                edges.append(f"    {parent_id} --> {nid}")
        for child in node.get("children", []) or []:
            walk(child.get("node"), nid, child.get("label"))

    walk(flow, None, None)
    return "\n".join(["```mermaid", "flowchart TD"] + decls + edges + ["```"])


def render(doc):
    """Both mechanical sections with their canonical journey-doc headings, ready
    to paste into (or diff against) a journey doc."""
    return (
        "## 5. Steps (required)\n\n"
        + render_step_table(doc)
        + "\n\n## 8. Flow diagram (required)\n\n"
        + render_mermaid(doc)
        + "\n"
    )


# ------------------------------------------------------- extraction (for diffs)
def _doc_section(md, heading_re):
    """Text of a `## <heading>` section up to the next `## ` heading (or EOF)."""
    m = re.search(heading_re, md, re.M)
    if not m:
        return ""
    rest = md[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def extract_step_table(md):
    """The contiguous pipe-table lines from a journey doc's §5 (prose/notes that
    don't start with '|' are ignored), so it lines up with render_step_table."""
    sec = _doc_section(md, r"^## 5\. Steps")
    tbl = [ln.rstrip() for ln in sec.splitlines() if ln.strip().startswith("|")]
    return "\n".join(tbl)


def extract_mermaid(md):
    """The fenced ```mermaid ...``` block (inclusive) from a journey doc's §8."""
    sec = _doc_section(md, r"^## 8\. Flow diagram")
    m = re.search(r"```mermaid.*?```", sec, re.S)
    return m.group(0).strip() if m else ""


def _norm(s):
    """Compare-normalize: strip the block and each line's trailing whitespace."""
    return "\n".join(ln.rstrip() for ln in (s or "").strip().splitlines())


# ------------------------------------------------------------------ main
def main(argv):
    ap = argparse.ArgumentParser(description="Render §5 step table + §8 Mermaid from a journey JSON's flow/steps.")
    ap.add_argument("journey", help="path to a journey JSON (must have a `flow` field)")
    ap.add_argument("--section", choices=["both", "table", "mermaid"], default="both")
    args = ap.parse_args(argv)

    try:
        doc = json.loads(Path(args.journey).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not isinstance(doc, dict) or "flow" not in doc:
        print(
            f"error: {args.journey} has no 'flow' field — journey_render only renders the "
            "explicit branch tree. Older journeys keep their hand-authored §5 table and §8 diagram.",
            file=sys.stderr,
        )
        return 2

    if args.section == "table":
        print(render_step_table(doc))
    elif args.section == "mermaid":
        print(render_mermaid(doc))
    else:
        print(render(doc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
