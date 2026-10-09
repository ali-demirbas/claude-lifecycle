#!/usr/bin/env python3
"""Regression for knowledge/audience-sql.md's exclusion rule (audit A18).

An include-with-exclude audience ("added to cart, no purchase since") must keep
the time condition when the exclusion is rewritten as a precomputed anti-join:
a purchase BEFORE the cart must not exclude the user. Portable SQL on SQLite;
this checks audience meaning, not BigQuery performance.
Exit 0 when the temporal anti-join matches the correlated reference query, the
naive anti-join is shown to differ, AND every "no purchase since" SQL block in
knowledge/audience-sql.md itself returns the reference audience on the same
fixture (BigQuery-only table/suffix syntax is rewritten for SQLite). The doc
check is what makes this a regression test of the doc, not of a private copy.
"""
import os
import re
import sqlite3
import sys

DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "knowledge", "audience-sql.md")

db = sqlite3.connect(":memory:")
db.execute("CREATE TABLE events (user_id TEXT, event_name TEXT, ts INTEGER)")
db.executemany("INSERT INTO events VALUES (?,?,?)", [
    ("u1", "purchase", 1), ("u1", "add_to_cart", 5),     # bought before the cart -> include
    ("u2", "add_to_cart", 1), ("u2", "purchase", 5),     # bought after the cart -> exclude
    ("u3", "add_to_cart", 3),                            # cart only -> include
    ("u4", "add_to_cart", 1), ("u4", "purchase", 2), ("u4", "add_to_cart", 6),  # new cart after a purchase -> include
])
reference = """SELECT DISTINCT e.user_id FROM events e WHERE e.event_name='add_to_cart'
  AND NOT EXISTS (SELECT 1 FROM events p WHERE p.event_name='purchase' AND p.user_id=e.user_id AND p.ts > e.ts)"""
naive = """WITH purchasers AS (SELECT DISTINCT user_id FROM events WHERE event_name='purchase')
  SELECT DISTINCT e.user_id FROM events e LEFT JOIN purchasers p ON p.user_id=e.user_id
  WHERE e.event_name='add_to_cart' AND p.user_id IS NULL"""
temporal = """WITH carts AS (SELECT user_id, ts FROM events WHERE event_name='add_to_cart'),
  purchases AS (SELECT user_id, ts FROM events WHERE event_name='purchase')
  SELECT DISTINCT c.user_id FROM carts c LEFT JOIN purchases p ON p.user_id=c.user_id AND p.ts > c.ts
  WHERE p.user_id IS NULL"""
q = lambda s: sorted(r[0] for r in db.execute(s))  # noqa: E731
ref, nai, tem = q(reference), q(naive), q(temporal)
print(f"reference {ref} · temporal anti-join {tem} · naive anti-join {nai}")
if tem != ref:
    print("FAIL: the temporal anti-join does not match the reference audience")
    sys.exit(1)
if nai == ref:
    print("FAIL: fixture no longer distinguishes the naive anti-join")
    sys.exit(1)
print("ok: temporal anti-join keeps 'purchase after cart'; the naive one drops u1/u4")

# the doc's own SQL, on the same fixture
doc = open(DOC, encoding="utf-8").read()
blocks = [b for b in re.findall(r"```sql\n(.*?)```", doc, re.S) if "no purchase since" in b]
if not blocks:
    print("FAIL: no 'no purchase since' SQL block found in knowledge/audience-sql.md")
    sys.exit(1)
gdb = sqlite3.connect(":memory:")
gdb.execute("CREATE TABLE events (user_pseudo_id TEXT, event_name TEXT, event_timestamp INTEGER)")
gdb.executemany("INSERT INTO events VALUES (?,?,?)", db.execute("SELECT user_id, event_name, ts FROM events").fetchall())
bad = 0
for i, b in enumerate(blocks):
    s = b.replace("`project.analytics_XXXX.events_*`", "events")
    s = re.sub(r"(\w+\.)?_TABLE_SUFFIX BETWEEN <window>\s+AND", "", s)
    s = re.sub(r"WHERE\s+(\w+\.)?_TABLE_SUFFIX BETWEEN <window>\s*$", "", s, flags=re.M)
    try:
        got = sorted(r[0] for r in gdb.execute(s))
    except sqlite3.Error as e:
        got = f"error: {e}"
    ok = got == ref
    bad += not ok
    print(f"doc block {i}: {'ok' if ok else 'FAIL'} got {got} want {ref}")
sys.exit(1 if bad else 0)
