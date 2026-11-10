#!/usr/bin/env python3
"""Write the context bundle one journey-architect needs, as a single file.

The orchestrator used to paste ~10k tokens of shared rules into every agent
prompt (paid as orchestrator output, then carried in its context for the rest
of the run), or the instruction was skipped and every agent re-read the same
files one tool call at a time. This script assembles exactly the files one
journey needs, with no model tokens; the agent reads one file.

Only what the task needs: the journey's own pattern, the sector playbook and
lexicon, the brand config if there is one, the consent/frequency rules,
segmentation and measurement guidance, the doc template and the schema.
Never the whole knowledge base.

Usage:
  bundle_context.py --pattern winback --sector ecommerce [--brand acme] --out output/<project>/_bundle/<id>.md
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _first_sentence(s, limit=220):
    s = " ".join((s or "").split()).replace("e.g.", "e\u2024g\u2024").replace("i.e.", "i\u2024e\u2024")
    m = re.match(r"(.+?[.;])(\s|$)", s)
    s = (m.group(1) if m else s).replace("\u2024", ".")
    return s if len(s) <= limit else s[:limit - 1] + "…"


def _type(node):
    if "$ref" in node:
        return node["$ref"].split("/")[-1]
    if "enum" in node:
        return " | ".join(map(str, node["enum"]))
    if "const" in node:
        return f"= {node['const']}"
    if "oneOf" in node:
        return " or ".join(_type(x) for x in node["oneOf"])
    t = node.get("type")
    if t == "array":
        items = node.get("items", {})
        return f"array of {_type(items) if isinstance(items, dict) else 'items'}"
    if isinstance(t, list):
        return " | ".join(t)
    return t or "object"


def _constraints(v):
    """Machine constraints the architect must respect, in the same line as the field."""
    bits = []
    if v.get("pattern"):
        bits.append(f"pattern /{v['pattern']}/")
    for key, label in (("minimum", "≥"), ("maximum", "≤"), ("exclusiveMinimum", ">"), ("exclusiveMaximum", "<")):
        if key in v:
            bits.append(f"{label} {v[key]}")
    if "maxLength" in v:
        bits.append(f"len ≤ {v['maxLength']}")
    if "minLength" in v and v["minLength"] > 1:
        bits.append(f"len ≥ {v['minLength']}")
    if "minItems" in v:
        bits.append(f"items ≥ {v['minItems']}")
    if "maxItems" in v:
        bits.append(f"items ≤ {v['maxItems']}")
    if isinstance(v.get("contains"), dict) and "const" in v["contains"]:
        bits.append(f"must contain {v['contains']['const']}")
    items = v.get("items") if isinstance(v.get("items"), dict) else {}
    if items.get("pattern"):
        bits.append(f"each /{items['pattern']}/")
    if v.get("additionalProperties") is False:
        bits.append("no other fields")
    if v.get("uniqueItems"):
        bits.append("unique")
    return (" [" + "; ".join(bits) + "]") if bits else ""


def _conditions(node):
    out = []
    for c in node.get("allOf", []):
        cond = c.get("if", {})
        props = cond.get("properties", {})
        test = ", ".join(f"{k} {'= ' + str(v['const']) if 'const' in v else 'in ' + str(v.get('enum'))}"
                         for k, v in props.items()) or ("has " + ", ".join(cond.get("required", [])))
        then = c.get("then", {})
        bits = []
        if then.get("required"):
            bits.append("requires " + ", ".join(then["required"]))
        if then.get("not"):
            bits.append("forbids " + ", ".join(r for x in then["not"].get("anyOf", []) for r in x.get("required", [])))
        for k, v in (then.get("properties") or {}).items():
            if v.get("required"):
                bits.append(f"{k} requires " + ", ".join(v["required"]))
            if "minItems" in v or "maxItems" in v:
                bits.append(f"{k} items {v.get('minItems', 0)}..{v.get('maxItems', 'n')}")
        for inner in _conditions({"allOf": then.get("allOf", [])}):
            bits.append("and " + inner.strip())
        else_ = c.get("else", {})
        if else_.get("required"):
            bits.append("otherwise requires " + ", ".join(else_["required"]))
        if bits:
            out.append(f"  if {test}: " + "; ".join(bits))
    return out


LEGACY = {"steps", "flow", "experiment", "flowNode", "flowChild"}  # 1.x only; forbidden in 2.0 files


def _object(name, node, lines):
    req = set(node.get("required", []))
    lines.append(f"{name}" + (f" — {_first_sentence(node.get('description'))}" if node.get("description") else ""))
    for k, v in (node.get("properties") or {}).items():
        if k in LEGACY:
            continue
        flag = " (required)" if k in req else ""
        desc = _first_sentence(v.get("description")) if v.get("description") else ""
        lines.append(f"  {k}: {_type(v)}{flag}{_constraints(v)}" + (f" — {desc}" if desc else ""))
        if v.get("type") == "object" and v.get("properties"):
            sub = []
            _object(f"  {k} fields", v, sub)
            lines.extend("  " + s for s in sub[1:])
        addl = v.get("additionalProperties") if isinstance(v.get("additionalProperties"), dict) else None
        if addl and addl.get("properties"):
            sub = []
            _object(f"  {k} values", addl, sub)
            lines.append(f"    each {k} value:")
            lines.extend("  " + s for s in sub[1:])
            for alt in addl.get("oneOf", []):
                lines.append(f"      one of: requires {', '.join(alt.get('required', []))}")
        items = v.get("items") if isinstance(v.get("items"), dict) else None
        if items and items.get("properties"):
            sub = []
            _object(f"  {k}[] fields", items, sub)
            lines.extend("  " + s for s in sub[1:])
    lines.extend(_conditions(node))


def schema_digest(schema):
    """Compact, generated digest of journey.schema.json: every field, type, enum,
    required flag and conditional requirement, with each description's first
    sentence. Derived from the canonical schema on every bundle build, so it
    can't drift; the validator remains the source of truth."""
    lines = [f"Journey JSON schema {schema.get('x-schema-version', '')} — generated digest. "
             "The validator (scripts/validate_output.py) enforces the full schema. Legacy 1.x fields "
             "(steps, flow, experiment) are omitted: a 2.0 file must not carry them."]
    _object("journey (root)", schema, lines)
    for name, node in (schema.get("$defs") or {}).items():
        if name in LEGACY:
            continue
        lines.append("")
        if node.get("oneOf") and not node.get("properties"):
            lines.append(f"$defs/{name}: one of the forms below")
            for i, alt in enumerate(node["oneOf"], 1):
                if alt.get("properties"):
                    _object(f"  form {i}" + (f" — {' '.join(alt['description'].split())}" if alt.get("description") else ""),
                            {k: v for k, v in alt.items() if k != "description"}, lines)
                    for k, v in alt["properties"].items():
                        items = v.get("items") if isinstance(v.get("items"), dict) else None
                        if items and items.get("properties"):
                            lines.append(f"    {k}: each member is a simple {name} with the fields of form 1")
        elif node.get("properties"):
            _object(f"$defs/{name}", node, lines)
        else:
            lines.append(f"$defs/{name}: {_type(node)}" + (f" — {_first_sentence(node.get('description'))}"
                                                          if node.get("description") else ""))
            if node.get("pattern"):
                lines.append(f"  pattern: {node['pattern']}")
    return "\n".join(lines)


def parts(pattern, sector, brand):
    out = [
        ("Pattern", f"knowledge/journey-patterns/{pattern}.md"),
        ("Sector playbook", f"knowledge/industries/{sector}.md"),
        ("Sector lexicon", f"knowledge/lexicons/{sector}.md"),
    ]
    if brand:
        out.append(("Brand config", f"knowledge/brands/{brand}.md"))
    out += [
        ("Consent, frequency, quiet hours", "knowledge/compliance/consent-and-quiet-hours.md"),
        ("Segmentation", "knowledge/segmentation.md"),
        ("Measurement", "knowledge/measurement.md"),
        ("Journey doc template", "templates/journey-doc.md"),
        ("Journey JSON schema 2.0", "templates/journey.schema.json"),
        ("Passing example (schema 2.0)", "examples/ecommerce-full-ga4/05-journey-cart-recovery.json"),
    ]
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pattern", required=True)
    ap.add_argument("--sector", required=True)
    ap.add_argument("--brand")
    ap.add_argument("--out", required=True)
    ap.add_argument("--schema", choices=["digest", "full"], default="digest",
                    help="digest (default): generated compact schema + a passing example; full: the raw schema")
    a = ap.parse_args(argv)
    for name, val in (("pattern", a.pattern), ("sector", a.sector), ("brand", a.brand)):
        if val is not None and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", val):
            print(f"error: --{name} must be a slug (lowercase letters, digits, dashes), got {val!r}", file=sys.stderr)
            return 2
    chunks, missing = [], []
    for title, rel in parts(a.pattern, a.sector, a.brand):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        body = open(p, encoding="utf-8").read().rstrip()
        if rel == "templates/journey.schema.json" and a.schema == "digest":
            body = schema_digest(json.loads(body))
            title = "Journey JSON schema 2.0 (generated digest)"
            chunks.append(f"# {title} — `{rel}`\n\n```text\n{body}\n```")
            continue
        if rel.startswith("examples/"):
            body = json.dumps(json.loads(body), ensure_ascii=False, separators=(",", ":"))
        fence = "```json" if rel.endswith(".json") else ""
        chunks.append(f"# {title} — `{rel}`\n\n" + (f"{fence}\n{body}\n```" if fence else body))
    required_missing = [m for m in missing if "brands/" not in m]
    if required_missing:
        print(f"error: missing {required_missing}", file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    text = "\n\n---\n\n".join(chunks) + "\n"
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"ok: {a.out} ({len(text) // 4} tokens approx, {len(chunks)} files)"
          + (f"; no brand config: {missing}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
