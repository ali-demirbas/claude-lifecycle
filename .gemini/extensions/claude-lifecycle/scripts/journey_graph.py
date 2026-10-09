#!/usr/bin/env python3
"""Journey graph analysis for schema 2.0 journeys (and a best-effort read of 1.x).

Pure functions, no I/O beyond what the caller passes in. Used by
validate_output.py (rules), journey_render.py (tables/diagrams) and
build_canvas.py (canvas tree), so all three read a journey the same way.

What it computes for a 2.0 journey:
  - graph structure: duplicate ids, broken links, unreachable nodes, cycles
  - every path from the entry node to an exit
  - per path, the time of every send and decision relative to journey entry,
    from each node's explicit anchor (entry / another node / an event or
    attribute with a declared relation to entry)
  - per path, the most sends that fall inside any rolling window, per channel

Findings are returned as (level, message, critical) tuples. level is one of
"error", "warning", "unverifiable". A critical unverifiable item means a
safety-relevant fact (timing, frequency, event existence) could not be
established, so the caller must not report an unconditional pass.
"""
import re

GRAPH_VERSION = "2.0.0"
DUR = re.compile(r"^(-)?P(?!$)(?:(\d+)W|(?:(\d+)D)?(?:T(?=\d)(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?)$")
DAY = 86400
MAX_PATHS = 2000
CONSENT_EXIT = re.compile(r"consent|unsub|opt_?out|optout|withdraw|izin", re.I)
CONSENT_GRANT = re.compile(r"consent_?grant|re_?consent|opt_?in|subscribe|izin_?ver", re.I)
CONSENT_NEGATIVE = re.compile(r"unsub|opt_?out|optout|withdr|revok|denied|declin|reject|iptal|geri_?cek", re.I)
CHANNEL_TOKENS = {"email": r"e_?mail", "sms": r"sms", "push": r"push", "whatsapp": r"whats_?app|\bwa_", "in_app": r"in_?app"}


def granted_channel(sig):
    """The one channel an authoritative consent grant reopens, or None (not a grant, or no channel named)."""
    name = str(sig.get("name", ""))
    if sig.get("source") != "authoritative" or not CONSENT_GRANT.search(name) or CONSENT_NEGATIVE.search(name):
        return None
    if sig.get("channel"):
        return sig["channel"]
    named = [ch for ch, rx in CHANNEL_TOKENS.items() if re.search(rx, name, re.I)]
    return named[0] if len(named) == 1 else None
LEGACY_OPEN = re.compile(r"\bopen(ed|s)?\b|\bnot opened\b|açıl|açmad|açmay|okunmad", re.I)
MARKETING_PURPOSES = {None, "marketing", "reconsent_request"}


def dur_seconds(s):
    """Signed ISO 8601 duration (no months/years) -> seconds, or None."""
    if not isinstance(s, str):
        return None
    m = DUR.match(s)
    if not m:
        return None
    neg, w, d, h, mi, se = m.groups()
    total = int(w or 0) * 7 * DAY + int(d or 0) * DAY + int(h or 0) * 3600 + int(mi or 0) * 60 + int(se or 0)
    return -total if neg else total


def fmt(sec):
    """Seconds -> compact ISO duration ('P3D', 'P6DT21H', 'PT5H', '-P2D')."""
    if sec is None:
        return "?"
    neg = sec < 0
    sec = abs(int(sec))
    d, rem = divmod(sec, DAY)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    out = "P" + (f"{d}D" if d else "")
    t = (f"{h}H" if h else "") + (f"{m}M" if m else "") + (f"{s}S" if s else "")
    if t:
        out += "T" + t
    if out == "P":
        out = "P0D"
    return ("-" if neg else "") + out


def is_v2(doc):
    return isinstance(doc, dict) and doc.get("schema_version") == "2.0"


class Findings:
    def __init__(self):
        self.items = []
        self._seen = set()

    def add(self, level, msg, critical=True):
        key = (level, msg)
        if key not in self._seen:
            self._seen.add(key)
            self.items.append((level, msg, critical))

    def error(self, msg):
        self.add("error", msg)

    def warn(self, msg):
        self.add("warning", msg, False)

    def unverifiable(self, msg, critical=True):
        self.add("unverifiable", msg, critical)


# ---------------------------------------------------------------- structure
def successors(node):
    """[(label, target_id)] for a node's outgoing edges."""
    k = node.get("kind")
    if k in ("entry", "message"):
        return [(None, node["next"])] if node.get("next") else []
    if k == "decision":
        out = [(b.get("label") or b.get("when"), b.get("next")) for b in node.get("branches") or []]
        if node.get("default"):
            out.append(("default", node["default"]))
        if node.get("unmeasurable"):
            out.append(("unmeasurable", node["unmeasurable"]))
        return out
    return []


def build(doc, F):
    """Index nodes and check structure. Returns (by_id, ok_for_paths)."""
    nodes = doc.get("nodes") or []
    by_id = {}
    for n in nodes:
        nid = n.get("id")
        if nid in by_id:
            F.error(f"duplicate node id '{nid}'")
        by_id[nid] = n
    start = doc.get("start")
    if start not in by_id:
        F.error(f"start '{start}' is not a node id")
        return by_id, False
    if by_id[start].get("kind") != "entry":
        F.error(f"start node '{start}' must be kind 'entry'")
    entries = [n["id"] for n in nodes if n.get("kind") == "entry"]
    if len(entries) != 1:
        F.error(f"exactly one entry node expected, found {len(entries)}: {entries}")
    ok = True
    for n in nodes:
        k = n.get("kind")
        if k in ("entry", "message") and not n.get("next"):
            F.error(f"node '{n.get('id')}' ({k}) has no 'next'")
            ok = False
        if k == "exit" and n.get("next"):
            F.error(f"exit node '{n.get('id')}' must not have 'next'")
        for _, tgt in successors(n):
            if tgt not in by_id:
                F.error(f"node '{n.get('id')}' points to '{tgt}', which does not exist (broken link)")
                ok = False
    if not ok:
        return by_id, False
    # reachability
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(t for _, t in successors(by_id[cur]))
    for nid in by_id:
        if nid not in seen:
            F.error(f"node '{nid}' is unreachable from the entry node")
    # cycles (journeys are DAGs: re-entry is a policy, not a loop in the graph)
    color = {}

    def dfs(u, trail):
        color[u] = 1
        for _, v in successors(by_id[u]):
            if color.get(v) == 1:
                F.error(f"cycle: {' -> '.join(trail + [u, v])} (loops are not supported; use reentry policy)")
                return False
            if color.get(v) is None and not dfs(v, trail + [u]):
                return False
        color[u] = 2
        return True

    if not dfs(start, []):
        return by_id, False
    return by_id, True


def enumerate_paths(by_id, start, F):
    paths = []

    def walk(nid, path):
        if len(paths) > MAX_PATHS:
            return
        node = by_id[nid]
        succ = successors(node)
        if not succ:
            paths.append(path)
            return
        for label, tgt in succ:
            walk(tgt, path + [(tgt, label)])

    walk(start, [(start, None)])
    if len(paths) > MAX_PATHS:
        F.unverifiable(f"more than {MAX_PATHS} paths; timeline and frequency were not fully computed")
    return paths[:MAX_PATHS]


# ---------------------------------------------------------------- timing
def resolve(anchor, times_on_path, doc, F, where):
    """Anchor -> seconds from entry, or None if not computable."""
    if not isinstance(anchor, dict):
        F.error(f"{where}: missing timing anchor")
        return None
    off = anchor.get("offset", "P0D")
    off_s = dur_seconds(off)
    if off_s is None:
        F.error(f"{where}: offset '{off}' is not a supported duration (ISO 8601, no months/years)")
        return None
    cal = anchor.get("calendar")
    if cal is not None:
        tz = str(cal.get("timezone", "")).strip()
        if not tz:
            F.error(f"{where}: calendar time '{cal.get('time_of_day')}' has no timezone (use 'user_local' or an IANA zone)")
        elif tz != "user_local":
            try:
                from zoneinfo import ZoneInfo  # noqa: PLC0415
                ZoneInfo(tz)
            except Exception:  # noqa: BLE001
                F.error(f"{where}: timezone '{tz}' is not a valid IANA zone (or 'user_local')")
    src = anchor.get("from")
    if src == "entry":
        base = 0
    elif src == "node":
        ref = anchor.get("node")
        if ref not in times_on_path:
            F.error(f"{where}: anchored to node '{ref}', which does not precede it on every path that reaches it")
            return None
        base = times_on_path[ref]
        if base is None:
            return None
    elif src in ("event", "attribute"):
        name = anchor.get(src)
        rel = (doc.get("time_anchors") or {}).get(name)
        if rel and "relative_to_entry" not in rel and rel.get("range"):
            rel = {"relative_to_entry": rel["range"][0]}  # analyze() substitutes each end; this is a fallback
        if not rel:
            F.unverifiable(f"{where}: anchored to {src} '{name}' with no declared relation to entry (time_anchors); "
                           f"its place on the timeline can't be computed")
            return None
        base = dur_seconds(rel.get("relative_to_entry"))
        if base is None:
            F.error(f"{where}: time_anchors['{name}'] has an invalid duration")
            return None
    else:
        F.error(f"{where}: anchor 'from' must be entry|node|event|attribute, got {src!r}")
        return None
    return base + off_s


def timeline(doc, by_id, path, F):
    """[(node_id, label, seconds|None)] for every timed node on the path."""
    times, out, last_known = {}, [], (None, 0)
    for nid, label in path:
        n = by_id[nid]
        k = n.get("kind")
        t = None
        if k == "entry":
            t = 0
        elif k == "message":
            t = resolve(n.get("send"), times, doc, F, f"node '{nid}' send")
        elif k == "decision":
            w = n.get("window") or {}
            t_from = resolve(w.get("from"), times, doc, F, f"node '{nid}' window.from")
            t = resolve(w.get("to"), times, doc, F, f"node '{nid}' window.to")
            if t is not None and t_from is not None and t < t_from:
                F.error(f"node '{nid}': decision window ends ({fmt(t)}) before it starts ({fmt(t_from)})")
            lat = max([dur_seconds(m.get("latency")) or 0 for m in signal_members(n.get("signal") or {})] or [0])
            if lat and t is not None and t_from is not None and (t - t_from) < lat:
                F.warn(f"node '{nid}': decision window ({fmt(t - t_from)}) is shorter than the signal's "
                       f"latency ({fmt(lat)}); late data will read as 'not occurred'")
        if k in ("entry", "message", "decision"):
            if t is not None:
                if t < 0:
                    F.error(f"node '{nid}' is scheduled at {fmt(t)}, before the user entered the journey")
                prev_id, prev_t = last_known
                if prev_id is not None and t < prev_t:
                    F.error(f"node '{nid}' is scheduled at {fmt(t)}, before '{prev_id}' at {fmt(prev_t)} "
                            f"which precedes it on this path")
                last_known = (nid, t)
            times[nid] = t
            out.append((nid, label, t))
    return out


# ---------------------------------------------------------------- frequency
def window_max(times, window):
    """Most items whose times fall inside any half-open window of this length."""
    ts = sorted(times)
    best, j = 0, 0
    for i in range(len(ts)):
        while ts[i] - ts[j] >= window:
            j += 1
        best = max(best, i - j + 1)
    return best


def path_frequency(by_id, tl, window):
    """Per channel: worst count inside the window on this path, plus unknown-time sends."""
    known, unknown = {}, {}
    for nid, _, t in tl:
        n = by_id[nid]
        if n.get("kind") != "message" or n.get("purpose") not in MARKETING_PURPOSES:
            continue
        ch = n.get("channel")
        (known.setdefault(ch, []).append(t) if t is not None else unknown.__setitem__(ch, unknown.get(ch, 0) + 1))
    res = {}
    for ch in set(known) | set(unknown):
        res[ch] = window_max(known.get(ch, []), window) + unknown.get(ch, 0)
    all_known = [t for v in known.values() for t in v]
    res["total"] = window_max(all_known, window) + sum(unknown.values())
    return res, bool(unknown)


# ---------------------------------------------------------------- analysis
def analyze(doc, inventory=None, window=7 * DAY):
    """Full analysis of a 2.0 journey. Returns a dict (see module docstring).

    When a time anchor is a range (a date whose distance from entry varies per
    user), the journey is analyzed at both ends; findings are merged and the
    worse frequency is kept."""
    ranged = {k: v for k, v in (doc.get("time_anchors") or {}).items()
              if isinstance(v, dict) and v.get("range") and "relative_to_entry" not in v}
    if not ranged:
        return _analyze_once(doc, inventory, window)
    import copy as _copy  # noqa: PLC0415
    results = []
    for end in (0, 1):
        d = _copy.deepcopy(doc)
        for k, v in ranged.items():
            d["time_anchors"][k] = {"relative_to_entry": v["range"][end]}
        results.append(_analyze_once(d, inventory, window))
    short, long_ = results
    merged = Findings()
    # At the shortest runway, a send landing before entry or out of order is what the
    # pattern's short-runway compression rule must handle (skip/merge); the graph
    # can't express "this node exists only at long runways", so it is reported as
    # unverifiable, not passed. At the longest runway the same findings are errors.
    chrono = ("before the user entered", "which precedes it on this path")
    for level, msg, crit in short["findings"].items:
        if level == "error" and any(c in msg for c in chrono):
            merged.unverifiable(msg + " [at the shortest end of the date range: the short-runway compression rule "
                                      "must drop or merge this step]")
        else:
            merged.add(level, msg, crit)
    for level, msg, crit in long_["findings"].items:
        if (level, msg) not in merged._seen:
            merged.add(level, msg + " [at the longest end of the date range]", crit)
    short["findings"] = merged
    for ch, v in long_["freq"].items():
        short["freq"][ch] = max(short["freq"].get(ch, 0), v)
    short["freq_has_unknown"] |= long_["freq_has_unknown"]
    return short


def _analyze_once(doc, inventory=None, window=7 * DAY):
    F = Findings()
    for legacy_key in ("steps", "flow", "experiment"):
        if legacy_key in doc:
            F.error(f"schema 2.0 file also carries legacy '{legacy_key}': one file, one authority; migrate it into "
                    f"nodes/measurement or keep the file as legacy 1.x")
    if doc.get("readiness") == "ready" and doc.get("open_items"):
        F.error(f"readiness is 'ready' but open_items lists {len(doc['open_items'])} unconfirmed fact(s)")
    if doc.get("readiness") == "draft":
        F.unverifiable(f"draft: {len(doc.get('open_items') or [])} open item(s) must be confirmed before this journey "
                       f"is ready to implement: {doc.get('open_items')}")
    for n in doc.get("nodes") or []:
        if n.get("kind") == "message" and n.get("channel") == "in_app":
            dv = n.get("delivery") or {}
            if dv.get("mode") != "next_session" or not dv.get("expires_after"):
                F.error(f"node '{n.get('id')}': in-app content is shown at a session, so it needs delivery "
                        f"{{mode: next_session, expires_after}}; later anchors use its scheduled time")
    by_id, ok = build(doc, F)
    res = {"findings": F, "paths": [], "timelines": [], "freq": {}, "freq_has_unknown": False,
           "max_msgs_on_path": 0, "by_id": by_id, "structure_ok": ok}
    if not ok:
        return res
    paths = enumerate_paths(by_id, doc["start"], F)
    res["paths"] = paths
    sw = dur_seconds((doc.get("exit") or {}).get("success_window"))
    if sw is None and (doc.get("exit") or {}).get("success_window_days"):
        sw = int(doc["exit"]["success_window_days"]) * DAY
    allowed = set((doc.get("constraints") or {}).get("allowed_channels") or [])
    withdrawn = set((doc.get("constraints") or {}).get("withdrawn_channels") or [])
    worst = {}
    for p in paths:
        tl = timeline(doc, by_id, p, F)
        res["timelines"].append(tl)
        nmsg = sum(1 for nid, _ in p if by_id[nid].get("kind") == "message")
        res["max_msgs_on_path"] = max(res["max_msgs_on_path"], nmsg)
        fr, unk = path_frequency(by_id, tl, window)
        res["freq_has_unknown"] |= unk
        for ch, v in fr.items():
            worst[ch] = max(worst.get(ch, 0), v)
        # sends vs success window, consent per path
        reconsented = set()
        prev_label = {}
        for idx, (nid, label) in enumerate(p):
            n = by_id[nid]
            if idx + 1 < len(p):
                prev_label[p[idx + 1][0]] = (nid, p[idx + 1][1])
            if n.get("kind") == "decision":
                sig = n.get("signal") or {}
                nxt_label = p[idx + 1][1] if idx + 1 < len(p) else None
                gch = granted_channel(sig)
                if gch and gch in withdrawn and nxt_label == "occurred":
                    reconsented.add(gch)
            if n.get("kind") == "message":
                ch = n.get("channel")
                if allowed and ch not in allowed:
                    F.error(f"node '{nid}': channel '{ch}' is not in constraints.allowed_channels {sorted(allowed)} "
                            f"(Channel Consent Violation)")
                if ch in withdrawn and ch not in reconsented:
                    F.error(f"node '{nid}': sends on '{ch}', which the user withdrew; a journey never reopens a "
                            f"closed channel on its own (route through an authoritative consent-granted decision for "
                            f"'{ch}' on this path: signal.channel '{ch}', or the channel in the event name)")
                t = next((t for i2, _, t in tl if i2 == nid), None)
                dl = (n.get("delivery") or {}).get("deadline")
                if dl and t is not None:
                    times_here = {i2: t2 for i2, _, t2 in tl}
                    dl_t = resolve(dl, times_here, doc, F, f"node '{nid}' delivery.deadline")
                    if dl_t is not None and t > dl_t:
                        F.error(f"node '{nid}' is scheduled at {fmt(t)}, after its own deadline {fmt(dl_t)}")
                if sw is not None and t is not None and t > sw:
                    F.error(f"node '{nid}' is sent at {fmt(t)}, outside the success window ({fmt(sw)})")
    res["freq"] = worst
    if res["freq_has_unknown"]:
        F.unverifiable("some sends have no computable time; frequency is a conservative upper bound "
                       "(unknown-time sends counted inside every window)", critical=False)
    check_decisions(doc, by_id, F)
    check_review_gating(by_id, F)
    check_exits_and_reentry(doc, by_id, F)
    check_measurement(doc, F)
    check_events(doc, by_id, inventory, F)
    return res


def signal_members(sig):
    """A simple signal -> [sig]; a composite any_of/all_of -> its members."""
    if not isinstance(sig, dict):
        return []
    for k in ("any_of", "all_of"):
        if isinstance(sig.get(k), list):
            return [m for m in sig[k] if isinstance(m, dict)]
    return [sig]


def check_decisions(doc, by_id, F):
    for nid, n in by_id.items():
        if n.get("kind") != "decision":
            continue
        sig = n.get("signal") or {}
        members = signal_members(sig)
        types = {m.get("type") for m in members}
        st = next(iter(types)) if len(types) == 1 else ("event" if types & {"event", "click"} else "attribute")
        if "open" in types:
            F.error(f"node '{nid}': branches on an email open. Opens are inflated by mail privacy protection and "
                    f"image proxies and are not a reliable signal, alone or inside a composite; branch on a click "
                    f"or a product event")
        for m in members:
            if m.get("type") == "click" and not m.get("bot_filtered"):
                F.warn(f"node '{nid}': click signal without bot_filtered: security scanners click links; state "
                       f"whether bot clicks are filtered before this decision reads them")
            lat = dur_seconds(m.get("latency"))
            if lat is not None and lat < 0:
                F.error(f"node '{nid}': signal latency {m.get('latency')} is negative")
        if not n.get("unmeasurable"):
            F.error(f"node '{nid}': no 'unmeasurable' route. 'Not measured' must never be treated as 'did not happen'")
        else:
            tgt = by_id.get(n["unmeasurable"]) or {}
            if tgt.get("kind") == "exit" and tgt.get("reason") in ("disengaged", "suppressed"):
                F.error(f"node '{nid}': the unmeasurable route ends in a '{tgt.get('reason')}' exit. A signal that "
                        f"can't be measured is not evidence of disinterest")
        whens = {b.get("when") for b in n.get("branches") or []}
        if st in ("event", "click") and not ({"occurred", "not_occurred"} & whens):
            F.error(f"node '{nid}': event/click decisions branch on 'occurred' / 'not_occurred'")
        if st == "attribute" and not n.get("default"):
            F.error(f"node '{nid}': attribute decision has no 'default' route for values no branch matches")


SCORE_SIGNAL = re.compile(r"nps|csat|ces\b|score|rating|satisf|sentiment|memnuniyet|puan", re.I)
REVIEW_ASK = re.compile(r"review|store rating|rating prompt|app ?store|play ?store|trustpilot|google (my business|maps)|"
                        r"değerlendirme|yorum (yap|bırak|yaz)|puan ver", re.I)


def check_review_gating(by_id, F):
    """A public/store review request must not depend on the satisfaction score (review gating):
    if some branches of a score decision lead to a review request and others don't, that is gating.
    The review request is recognised from the message's `intent` text."""
    def reaches_review(start, seen):
        stack = [start]
        while stack:
            nid = stack.pop()
            if nid in seen or nid not in by_id:
                continue
            seen.add(nid)
            n = by_id[nid]
            if n.get("kind") == "message" and REVIEW_ASK.search(str(n.get("intent", ""))):
                return nid
            stack.extend(t for _, t in successors(n))
        return None
    for nid, n in by_id.items():
        if n.get("kind") != "decision":
            continue
        names = [str(m.get("name", "")) for m in signal_members(n.get("signal") or {})]
        if not any(SCORE_SIGNAL.search(x) for x in names):
            continue
        hits = {label: reaches_review(target, set()) for label, target in successors(n)}
        with_review = sorted(f"{lbl} → {hit}" for lbl, hit in hits.items() if hit)
        without = sorted(str(lbl) for lbl, hit in hits.items() if not hit)
        if with_review and without:
            F.error(f"decision '{nid}' reads a satisfaction score ({', '.join(names)}) and only some branches lead to "
                    f"a review request ({'; '.join(with_review)}; not: {', '.join(without)}). That is review gating: "
                    f"ask everyone or no one, and keep the score for routing private follow-up")


def check_exits_and_reentry(doc, by_id, F):
    ex = doc.get("exit") or {}
    conds = ex.get("exit_conditions") or []
    pre = {c.get("event") for c in conds if "before_each_send" in (c.get("check") or [])}
    if ex.get("success_event") and ex["success_event"] not in pre:
        F.error(f"success event '{ex['success_event']}' is not re-checked before each send "
                f"(exit_conditions check: before_each_send); a user who converts keeps getting queued messages")
    mkt_channels = {n.get("channel") for n in by_id.values()
                    if n.get("kind") == "message" and n.get("purpose") in MARKETING_PURPOSES}
    consent_conds = [c for c in conds if CONSENT_EXIT.search(str(c.get("event")))
                     and "before_each_send" in (c.get("check") or [])]
    journey_wide = any(c.get("scope", "instance") != "channel" for c in consent_conds)
    covered = {c.get("channel") for c in consent_conds if c.get("scope") == "channel"}
    if mkt_channels and not journey_wide and not mkt_channels <= covered:
        missing = sorted(ch for ch in mkt_channels - covered if ch)
        F.error(f"marketing sends on {missing or sorted(c for c in mkt_channels if c)} have no consent-withdrawal / "
                f"unsubscribe exit checked before each send (journey-wide, or channel-scoped per channel); this "
                f"applies to every marketing-purpose send, whatever the journey's class")
    for c in conds:
        if c.get("same_instance") and not doc.get("instance_key"):
            F.error(f"exit condition '{c.get('event')}' is limited to the same instance, but the journey declares no "
                    f"instance_key")
        if c.get("scope") == "channel" and not c.get("channel"):
            F.error(f"exit condition '{c.get('event')}' is channel-scoped but names no channel")
    for nid, n in by_id.items():
        if n.get("kind") == "exit" and n.get("reason") == "handoff":
            h = n.get("handoff")
            if not h:
                F.error(f"exit '{nid}' is a handoff but names no target")
            elif not h.get("suppress_queued"):
                F.error(f"exit '{nid}': handoff to '{h.get('to')}' without suppress_queued; queued sends from this "
                        f"journey would still go out alongside the next one")
    re_ = doc.get("reentry") or {}
    pol, dup, cd = re_.get("policy"), re_.get("on_duplicate_trigger"), re_.get("cooldown")
    cds = dur_seconds(cd)
    if pol == "after_cooldown" and (cds is None or cds <= 0):
        F.error("reentry policy 'after_cooldown' needs a positive cooldown duration")
    elif cds is not None and cds < 0:
        F.error(f"reentry cooldown {cd} is negative")
    if dup == "new_instance" and pol != "after_cooldown":
        F.error("a repeated trigger starts a new instance with no cooldown: one user can receive the same "
                "sequence again and again (set a cooldown, or ignore/restart the active instance)")
    if dup == "restart" and pol == "each_trigger":
        F.warn("repeated triggers restart the instance with no cooldown; early steps can be re-sent repeatedly")


def check_measurement(doc, F):
    cls = doc.get("journey_class")
    m = doc.get("measurement")
    has_mkt = any(n.get("kind") == "message" and n.get("purpose") in MARKETING_PURPOSES
                  for n in doc.get("nodes") or [])
    if not m:
        if cls == "marketing" or has_mkt:
            F.error("journey has marketing-purpose sends but no measurement plan (design + primary outcome + "
                    "window); a service/transactional class doesn't exempt its marketing steps")
        return
    d = m.get("design")
    if d == "holdout":
        h = m.get("holdout") or {}
        a = h.get("assignment") or {}
        if not h:
            F.error("measurement design is 'holdout' but no holdout is specified")
        else:
            if a.get("unit") not in ("user", "account", "household"):
                F.error("holdout assignment unit must be user, account or household")
            if a.get("consistent") is not True:
                F.error("holdout assignment must be consistent per unit (the same user always in the same group)")
            if not h.get("control_excludes"):
                F.error("holdout must state which new communications the control group does not receive")
        if not m.get("volume_note"):
            F.warn("holdout without a volume note: state what the expected volume can and cannot detect; "
                   "a holdout alone does not make a result statistically reliable")
    elif d in ("none_low_volume", "none_service", "pre_post", "other"):
        if not m.get("reason"):
            F.error(f"measurement design '{d}' needs a reason")
        if d != "none_service" and not m.get("alternative"):
            F.error(f"measurement design '{d}' needs the alternative measurement used instead of a holdout")


def referenced_events(doc, by_id):
    refs = set()
    tr = doc.get("trigger") or {}
    if tr.get("type") == "event" and tr.get("value"):
        refs.add(tr["value"])
    ex = doc.get("exit") or {}
    if ex.get("success_event"):
        refs.add(ex["success_event"])
    for c in ex.get("exit_conditions") or []:
        refs.add(c.get("event"))
    po = ((doc.get("measurement") or {}).get("primary_outcome") or {}).get("event")
    if po:
        refs.add(po)
    for n in by_id.values():
        for sig in signal_members(n.get("signal") or {}):
            if sig.get("type") in ("event", "attribute") and sig.get("name"):
                refs.add(sig["name"])
        for key in ("send",):
            a = n.get(key) or {}
            if a.get("from") in ("event", "attribute"):
                refs.add(a.get(a["from"]))
        w = n.get("window") or {}
        for a in (w.get("from") or {}, w.get("to") or {}):
            if a.get("from") in ("event", "attribute"):
                refs.add(a.get(a["from"]))
    return {r for r in refs if r}


def check_events(doc, by_id, inventory, F):
    inv = inventory if inventory is not None else doc.get("events_available")
    refs = referenced_events(doc, by_id)
    if inv is None:
        F.unverifiable(f"event existence not checked: no events_available inventory "
                       f"({len(refs)} referenced: {sorted(refs)[:6]})")
        return
    for r in sorted(refs - set(inv)):
        F.error(f"event/attribute '{r}' is not in the mapped inventory (events_available); "
                f"a journey can't read a signal that isn't tracked")


# ---------------------------------------------------------------- legacy 1.x
def legacy_timelines(doc):
    """Two readings of 1.x waits: every wait from entry, or each from the previous step."""
    steps = doc.get("steps") or []
    from_entry, chained, acc = [], [], 0
    for s in steps:
        w = dur_seconds(s.get("wait")) or 0
        acc += w
        from_entry.append((s, w))
        chained.append((s, acc))
    return from_entry, chained


def legacy_frequency(doc, window=7 * DAY):
    """(lower, upper) per-channel bounds over both readings. lower counts only
    unconditioned steps (branch steps may be mutually exclusive)."""
    lower, upper = {}, {}
    readings = legacy_timelines(doc)
    for reading in readings:
        lo_c, up_c = {}, {}
        for s, t in reading:
            up_c.setdefault(s.get("channel"), []).append(t)
            if not s.get("branch_condition"):
                lo_c.setdefault(s.get("channel"), []).append(t)
        for ch, ts in up_c.items():
            upper[ch] = max(upper.get(ch, 0), window_max(ts, window))
        for ch in set(up_c):
            v = window_max(lo_c.get(ch, []), window)
            lower[ch] = v if ch not in lower else min(lower[ch], v)
    return lower, upper


def analyze_legacy(doc):
    F = Findings()
    for s in doc.get("steps") or []:
        bc = s.get("branch_condition") or ""
        if LEGACY_OPEN.search(bc):
            F.error(f"step {s.get('index')}: branch condition depends on an email open ('{bc}'); opens are not a "
                    f"reliable branching signal on their own")
    fe, ch = legacy_timelines(doc)
    last_fe = max((t for _, t in fe), default=0)
    last_ch = max((t for _, t in ch), default=0)
    sw = (doc.get("exit") or {}).get("success_window_days")
    msg = (f"legacy 1.x journey: step waits have no stated anchor. Read from entry, the last send is at "
           f"{fmt(last_fe)}; read as from the previous step, at {fmt(last_ch)}")
    if sw:
        swd = int(sw) * DAY
        if last_fe > swd and last_ch > swd:
            F.error(msg + f"; both readings exceed the {sw}-day success window")
            return F
        if last_ch > swd:
            msg += f" (outside the {sw}-day success window under that reading)"
    F.unverifiable(msg + ". Timing, branch exclusivity and frequency can't be verified until migrated to schema 2.0")
    return F
