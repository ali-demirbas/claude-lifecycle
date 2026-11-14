#!/usr/bin/env python3
"""The generated schema digest in agent bundles must not lose any contract field.
Every non-legacy property name and every enum value in journey.schema.json must
appear in the digest; the conditional requirements must be present."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from bundle_context import LEGACY, schema_digest  # noqa: E402

schema = json.load(open(os.path.join(HERE, "..", "..", "templates", "journey.schema.json"), encoding="utf-8"))
digest = schema_digest(schema)
names, enums = set(), set()


def walk(node, legacy=False):
    if isinstance(node, dict):
        for k, v in (node.get("properties") or {}).items():
            if k in LEGACY:
                continue
            names.add(k)
            walk(v)
        for e in node.get("enum", []):
            enums.add(str(e))
        for key in ("items", "additionalProperties", "if", "then", "else", "not"):
            if isinstance(node.get(key), dict):
                walk(node[key])
        for key in ("allOf", "oneOf", "anyOf"):
            for x in node.get(key, []) or []:
                walk(x)


walk(schema)
for name, d in schema.get("$defs", {}).items():
    if name not in LEGACY:
        walk(d)
missing = sorted(n for n in names if n not in digest) + sorted(f"enum:{e}" for e in enums if e not in digest)
needed = ["requires measurement", "requires open_items", "requires channel, intent, send, next",
          "requires signal, window, branches, unmeasurable", "requires expires_after", "forbids steps, flow, experiment"]
missing += [f"condition:{c}" for c in needed if c not in digest]
print(f"digest {len(digest) // 4} tokens approx · {len(names)} fields · {len(enums)} enum values checked")
if missing:
    print("FAIL: missing from digest:", missing[:20])
    sys.exit(1)
print("ok: every contract field, enum value and key condition is in the digest")
