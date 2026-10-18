#!/usr/bin/env python3
"""Convert a Kaluza .composite / .protocol template to a FlowNg (FlowNG.html) v3 template.

The output is the JSON the viewer's "Import Template" button reads (``*_FlowNgtmplt.json``).
Kaluza datasets (tubes) are identified only by position (dataset index 0, 1, 2...), so the
output file entries follow that order. Use --tube-names / --lmd to label them, and match each
entry to the right physical tube in FlowNg's import dialog.

Usage:
  uv run scripts/kaluza_to_flowng.py "BTM Triage Template v10.composite" --list
  uv run scripts/kaluza_to_flowng.py "BTM Triage Template v10.composite" \
      --tube-names "B tube,T tube,M tube" -o btm.FlowNgtmplt.json
  uv run scripts/kaluza_to_flowng.py "BTM Triage Template v10.composite" \
      --lmd B.LMD --lmd T.LMD --lmd M.LMD
"""
import argparse
import datetime
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

BIG = 1e12
DEFAULT_COLOR = "#808080"
SCALE_MAP = {"I": "lin", "O": "log", "C": "asinh"}
QUAD_CORNERS = {"UR": 1, "LR": 2, "LL": 3, "UL": 4}   # FlowNg quad.q numbering
LEGACY_LOG = (104.8576, 4.0, 1024.0)                    # min, decades, bins (Kaluza legacy bin units)

warnings = []


def warn(msg):
    if msg not in warnings:
        warnings.append(msg)


# ── loading ──────────────────────────────────────────────────────────────────

def load_root(path):
    p = Path(path)
    if p.suffix.lower() == ".xml":
        return ET.parse(p).getroot()
    with zipfile.ZipFile(p) as zf:
        names = sorted(n for n in zf.namelist() if n.lower().endswith(".xml"))
        if not names:
            sys.exit(f"no XML found in {path}")
        return ET.fromstring(zf.read(names[0]).lstrip(b"\xef\xbb\xbf"))


def find_protocol(root):
    protos = root.findall(".//Protocol")
    for pr in protos:
        gates = pr.find("Gates")
        if gates is not None and len(gates) > 0:
            return pr
    sys.exit("no Protocol with gates found in template")


PARAM_NAMES = {}      # dataset index -> {kaluza channel key -> FlowNg parameter name}
_CUR_D = [0]


def lmd_param_names(path):
    """Names FlowNg gives an LMD's channels: the FCS2.0 header's $PnS stain label (else $PnN) for
    FLn / SS / TIME, and FSC-A / FSC-H for forward scatter (see FlowNG.html LMD loader)."""
    raw = Path(path).read_bytes()
    ts, te = int(raw[10:18]), int(raw[18:26])
    text = raw[ts:te + 1].decode("latin1")
    parts = text[1:].split(text[0])
    kv = {parts[i].strip().upper(): parts[i + 1].strip() for i in range(0, len(parts) - 1, 2)}
    out = {"FS INT": "FSC-A", "FS PEAK": "FSC-H"}
    for i in range(1, int(kv.get("$PAR", "0")) + 1):
        n, st = kv.get(f"$P{i}N", ""), kv.get(f"$P{i}S", "")
        m = re.match(r"FL(\d+)", n, re.I)
        key = f"FL{m.group(1)} INT" if m else ("SS INT" if n.upper().startswith("SS") else
                                                "TIME" if "TIME" in n.upper() else None)
        if key:
            out[key] = st or n
    return out


def map_param(m, d=None):
    """Kaluza measurement name -> FlowNg parameter name for dataset d."""
    d = _CUR_D[0] if d is None else d
    if d in PARAM_NAMES and m in PARAM_NAMES[d]:
        return PARAM_NAMES[d][m]
    if m == "TIME":
        return "TIME"
    if m == "FS INT":
        return "FSC-A"
    if m == "FS PEAK":
        return "FSC-H"
    if d not in PARAM_NAMES:
        warn(f"D={d}: no --lmd given, so '{m}' cannot be mapped to the tube's stain name; "
             f"kept as '{m}' (FlowNg will skip it). Pass --lmd for every tube.")
    else:
        warn(f"D={d}: parameter '{m}' not found in the LMD; kept as-is")
    return m


def argb_to_hex(c):
    if not c:
        return None
    c = c[1:] if c[0] == "S" else c
    return "#" + c[-6:].lower()


# ── gates ────────────────────────────────────────────────────────────────────

class Gate:
    def __init__(self, el):
        self.el = el
        self.tag = el.tag                      # R, P, B
        self.name = el.get("N")
        self.d = int(el.get("D") or 0)
        pj = el.get("J")
        self.parent = el.get("G")
        self.pd = int(pj) if pj is not None else self.d
        self.axes = [(a.get("M"), a.get("S")) for a in el.findall("./A/A")]
        self.pts = [tuple(float(v) for v in p.get("O").split(",")) for p in el.findall("./P/P")]
        self.color = argb_to_hex(el.get("C"))
        # Kaluza paints events by gate colour only for gates that have one AND are not "structural"
        # gates (Time / Singlets / Viable and friends carry C in U with F=8 and never colour events;
        # confirmed against the Kaluza-rendered reference sheets).
        self.structural = "C" in (el.get("U") or "") and el.get("F") == "8"
        if self.structural:
            self.color = None
        self.expr = (el.findtext("ExpressionText") or "").strip()
        self.quad = None                       # filled by quad detection

    @property
    def key(self):
        return (self.name, self.d)


def legacy_to_raw(val, scale):
    if scale == "O":
        mn, dec, bins = LEGACY_LOG
        return mn * 10 ** (dec * val / bins)
    warn("legacy bin-unit gate on a non-log axis converted linearly (bin/1024 * 2^20); check it")
    return val / 1024.0 * 1048576.0


def parse_bool(expr, resolve):
    """OR/AND/NOT/parens over quoted or bare gate names -> {op,args} with leaves from resolve(name)."""
    quoted = []

    def stash(m):
        quoted.append(m.group(1))
        return f"\x00{len(quoted) - 1}\x00"

    text = re.sub(r'"([^"]*)"', stash, expr)
    parts = [t for t in re.split(r"(\(|\)|\bAND\b|\bOR\b|\bNOT\b)", text, flags=re.I) if t and t.strip()]
    toks = []
    for t in parts:
        s = t.strip()
        u = s.upper()
        if s in "()" or u in ("AND", "OR", "NOT"):
            toks.append(u if u in ("AND", "OR", "NOT") else s)
        else:
            m = re.fullmatch(r"\x00(\d+)\x00", s)
            toks.append(("N", quoted[int(m.group(1))] if m else s))
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def p_or():
        args = [p_and()]
        while peek() == "OR":
            take()
            args.append(p_and())
        return args[0] if len(args) == 1 else {"op": "or", "args": args}

    def p_and():
        args = [p_not()]
        while peek() == "AND":
            take()
            args.append(p_not())
        return args[0] if len(args) == 1 else {"op": "and", "args": args}

    def p_not():
        if peek() == "NOT":
            take()
            return {"op": "not", "args": [p_not()]}
        return p_atom()

    def p_atom():
        t = take()
        if t == "(":
            e = p_or()
            if peek() == ")":
                take()
            return e
        if isinstance(t, tuple):
            return resolve(t[1])
        raise ValueError(f"unexpected token {t!r}")

    return p_or()


def build_datasets(proto, root):
    gates = [Gate(g) for g in proto.find("Gates")]
    legacy = (proto.get("C") or "") == "Legacy"
    by_key = {g.key: g for g in gates}

    # Linked copies -> canonical (first listed) gate
    canon = {}
    gc = proto.find("GateConstraints")
    if gc is not None:
        for lk in gc.findall("Linked"):
            members = [(x.get("G"), int(x.get("J") or 0)) for x in lk.findall("Gate")]
            for m in members[1:]:
                canon[m] = members[0]

    def cname(name, d):
        return canon.get((name, d), (name, d))[0]

    dropped_copies = {g.key for g in gates if g.key in canon}
    # A linked copy's colour fills in when its original has none (e.g. Blasts / 45-neg are only
    # coloured on the Initial Gating copies); an original's own colour always wins.
    for g in gates:
        if g.key in canon:
            orig = by_key.get(canon[g.key])
            if orig and orig.color is None and not orig.structural and g.color and not g.structural:
                orig.color = g.color
    gates = [g for g in gates if g.key not in dropped_copies]
    if dropped_copies:
        warn(f"{len(dropped_copies)} linked copy gates merged into their originals")

    # legacy bin units -> raw
    if legacy:
        for g in gates:
            if g.tag == "B" or not g.axes or not g.pts:
                continue
            if all(0 <= v <= 1024 for p in g.pts for v in p) and any(s == "O" for _, s in g.axes):
                g.pts = [tuple(legacy_to_raw(v, g.axes[i][1]) for i, v in enumerate(p)) for p in g.pts]
                warn("legacy bin-unit gate coordinates converted to raw units")

    # Quadrants
    quad_groups = []
    if gc is not None:
        for tag in ("Staggered", "Hinged"):
            for st in gc.findall(tag):
                grp = {}
                for corner in QUAD_CORNERS:
                    nm, dj = st.get(f"{corner}G"), int(st.get(f"{corner}J") or 0)
                    if nm is None:
                        break
                    grp[corner] = by_key.get((nm, dj))
                if len(grp) == 4 and all(grp.values()):
                    quad_groups.append((tag, st, grp))
    gid = 0
    for tag, st, grp in quad_groups:
        gid += 1
        cx = cy = None
        if tag == "Hinged":
            cx, cy = (float(v) for v in st.get("CT").split(","))
            warn("hinged quadrant tilt ignored (using centre point only)")
        else:
            ll = grp["LL"].pts
            if ll:
                cx, cy = max(p[0] for p in ll), max(p[1] for p in ll)
                ok = True
                tol = lambda a, b: abs(a - b) <= 1e-3 * max(1.0, abs(a), abs(b))
                chk = [("LR", 0, "min", cx), ("UL", 1, "min", cy), ("UR", 0, "min", cx), ("UR", 1, "min", cy),
                       ("UL", 0, "max", cx), ("LR", 1, "max", cy)]
                for corner, ax, mm, ref in chk:
                    pts = grp[corner].pts
                    if not pts:
                        ok = False
                        break
                    val = (min if mm == "min" else max)(p[ax] for p in pts)
                    ok &= tol(val, ref)
                if not ok:
                    warn(f"staggered quadrant ({grp['LL'].name}…) kept as 4 separate polygons")
                    cx = cy = None
        if cx is None:
            continue
        for corner, g in grp.items():
            g.quad = {"gid": f"kq{gid}", "q": QUAD_CORNERS[corner], "cx": cx, "cy": cy}

    return gates, cname, legacy


def rect_pts(g):
    (x1, y1), (x2, y2) = g.pts[0], g.pts[1]
    lx, hx, ly, hy = min(x1, x2), max(x1, x2), min(y1, y2), max(y1, y2)
    return [(lx, hy), (hx, hy), (hx, ly), (lx, ly)]


def quad_pts(q, cx, cy):
    x0, x1 = (cx, BIG) if q in (1, 2) else (-BIG, cx)
    y0, y1 = (cy, BIG) if q in (1, 4) else (-BIG, cy)
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# ── plots ────────────────────────────────────────────────────────────────────

def collect_plots(proto, sheet_filter, sheet_exclude):
    plots = []
    for ps in proto.find("Sheets").findall("PlotSheet"):
        sname = ps.get("N")
        if sheet_filter and sname not in sheet_filter:
            continue
        if sname in sheet_exclude:
            continue
        for node in ps.findall("Node"):
            s = node.find("S")
            if s is None:
                continue
            x, y = s.find("X"), s.find("Y")
            if x is None or y is None or not x.get("M") or not y.get("M"):
                continue
            plots.append({
                "sheet": sname, "d": int(s.get("D") or 0), "g": s.get("G"),
                "gd": int(s.get("J") or s.get("D") or 0),
                "x": (x.get("M"), x.get("S"), x.get("W")), "y": (y.get("M"), y.get("S"), y.get("W")),
            })
    return plots


def infer_tube_labels(proto, n):
    labels = {}
    for ps in proto.find("Sheets").findall("PlotSheet"):
        ds = {int(n_.find("S").get("D") or 0) for n_ in ps.findall("Node")
              if n_.find("S") is not None and n_.find("S/X") is not None}
        mt = re.match(r"^([A-Za-z0-9]+)\s+(Gating|comp)\b", ps.get("N") or "", re.I)
        if len(ds) == 1 and mt:
            labels.setdefault(next(iter(ds)), f"{mt.group(1).upper()} tube")
    return {i: labels.get(i, f"Tube {i + 1}") for i in range(n)}


# ── conversion ───────────────────────────────────────────────────────────────

def convert(path, args):
    root = load_root(path)
    proto = find_protocol(root)
    gates, cname, legacy = build_datasets(proto, root)
    plots = collect_plots(proto, set(args.sheets or []), set(args.exclude_sheets or []))
    n_tubes = max([g.d for g in gates] + [p["d"] for p in plots] + [0]) + 1

    labels = infer_tube_labels(proto, n_tubes)
    if args.tube_names:
        for i, nm in enumerate(args.tube_names.split(",")):
            labels[i] = nm.strip()
    for spec in args.tube or []:
        k, _, v = spec.partition("=")
        labels[int(k)] = v
    for i, lmd in enumerate(args.lmd or []):
        labels[i] = Path(lmd).name
    if args.list:
        print(f"Protocol: {proto.get('N')!r}  datasets: {n_tubes}")
        for d in range(n_tubes):
            sheets = sorted({p["sheet"] for p in plots if p["d"] == d})
            print(f"  D={d}  {labels[d]!r}: {sum(1 for g in gates if g.d == d)} gates, "
                  f"{sum(1 for p in plots if p['d'] == d)} plots, sheets: {', '.join(sheets)}")
        return None

    files = []
    for i, lmd in enumerate(args.lmd or []):
        PARAM_NAMES[i] = lmd_param_names(lmd)
    for d in range(n_tubes):
        _CUR_D[0] = d
        dg = [g for g in gates if g.d == d]
        names = {g.name for g in dg}
        # unique names within the tube
        seen = {}
        for g in dg:
            if g.name in seen:
                seen[g.name] += 1
                new = f"{g.name} ({seen[g.name]})"
                warn(f"D={d}: duplicate gate name '{g.name}' renamed '{new}'")
                g.name = new
            else:
                seen[g.name] = 1
        kids = defaultdict(list)      # parent name (canonical) -> gates
        bools = {g.name: g for g in dg if g.tag == "B"}
        for g in dg:
            if g.tag == "B":
                continue
            kids[cname(g.parent, g.pd) if g.parent else None].append(g)

        def gate_node(g, parent_label):
            node = {"name": g.name, "color": g.color or DEFAULT_COLOR, "noColor": g.color is None,
                    "parentName": parent_label}
            if g.color and args.dots:
                node["dots"] = True      # draw coloured populations as exact events, like Kaluza
            if not g.axes or len(g.axes) < 2:
                return None
            (xm, xs), (ym, ys) = g.axes[:2]
            node.update(xParamName=map_param(xm), yParamName=map_param(ym),
                        xScale=SCALE_MAP.get(xs, "lin"), yScale=SCALE_MAP.get(ys, "lin"))
            if g.quad:
                q = g.quad
                node["rawPts"] = [{"rx": a, "ry": b} for a, b in quad_pts(q["q"], q["cx"], q["cy"])]
                node["quad"] = dict(q)
            else:
                pts = rect_pts(g) if g.tag == "R" and len(g.pts) == 2 else g.pts
                if len(pts) < 3:
                    warn(f"D={d}: gate '{g.name}' has no usable geometry; skipped")
                    return None
                node["rawPts"] = [{"rx": a, "ry": b} for a, b in pts]
            node["children"] = [c for c in (gate_node(k, g.name) for k in kids.get(g.name, [])) if c]
            return node

        top = [c for c in (gate_node(k, "All Events") for k in kids.get(None, [])) if c]

        # orphans (parent missing)
        known = {g.name for g in dg}
        for pname, lst in kids.items():
            if pname is not None and pname not in known:
                warn(f"D={d}: parent '{pname}' not found; {len(lst)} gate(s) moved to the top level")
                top += [c for c in (gate_node(k, "All Events") for k in lst) if c]

        booleans = []
        for b in bools.values():
            try:
                expr = parse_bool(b.expr, lambda nm: cname(nm, d) if (cname(nm, d), d) in {(x.name, x.d) for x in dg}
                                  else (_ for _ in ()).throw(KeyError(nm)))
            except (KeyError, ValueError) as e:
                warn(f"D={d}: boolean '{b.name}' skipped ({e!r})")
                continue
            if isinstance(expr, str):
                expr = {"op": "or", "args": [expr]}
            booleans.append({"name": b.name, "color": b.color or DEFAULT_COLOR, "noColor": b.color is None,
                             "expr": expr,
                             "children": [c for c in (gate_node(k, b.name) for k in kids.get(b.name, [])) if c]})

        # param ranges from plot windows
        pr = {}
        for p in plots:
            if p["d"] != d:
                continue
            for m, s, w in (p["x"], p["y"]):
                nm = map_param(m)
                ent = pr.setdefault(nm, {})
                if w:
                    lo, hi = (float(v) for v in w.split(";"))
                    ent["rawMin"] = min(ent.get("rawMin", lo), lo)
                    ent["rawMax"] = max(ent.get("rawMax", hi), hi)
                if s == "C":
                    ent["asinhCofactor"] = args.cofactor
        files.append({"sourceFile": labels[d], "gates": top, "booleans": booleans,
                      "colorPrecedence": [], "paramRanges": pr})

    # plots
    out_plots = []
    for p in plots:
        d = p["d"]
        f_names = {n["name"] for n in files[d]["gates"]}

        def collect(nodes):
            for n in nodes:
                f_names.add(n["name"])
                collect(n.get("children", []))
        collect(files[d]["gates"])
        for b in files[d]["booleans"]:
            f_names.add(b["name"])
            collect(b["children"])
        inp = cname(p["g"], p["gd"]) if p["g"] else "All Events"
        if inp != "All Events" and inp not in f_names:
            warn(f"plot on sheet '{p['sheet']}' uses missing population '{inp}'; using All Events")
            inp = "All Events"
        (xm, xs, _), (ym, ys, _) = p["x"], p["y"]
        out_plots.append({
            "fileIndex": d, "xParamName": map_param(xm, d), "yParamName": map_param(ym, d),
            "inputPopName": inp, "xLog": xs == "O", "yLog": ys == "O",
            "xAsinh": xs == "C", "yAsinh": ys == "C", "dotSize": 1.5, "bins": 256, "tabName": p["sheet"],
        })

    name = args.name or proto.get("N") or Path(path).stem
    tmpl = {"version": 3, "name": name, "exported": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "files": files, "plots": out_plots}
    self_check(tmpl)
    return tmpl


def self_check(tmpl):
    for fi, f in enumerate(tmpl["files"]):
        names, boolnames = [], {b["name"] for b in f["booleans"]}

        def walk(nodes, parent):
            for n in nodes:
                names.append(n["name"])
                walk(n["children"], n["name"])
        walk(f["gates"], None)
        for b in f["booleans"]:
            names.append(b["name"])
            walk(b["children"], b["name"])
        if len(set(names)) != len(names):
            warn(f"file {fi}: gate names are not unique")

        def leaves(e):
            return [e] if isinstance(e, str) else [l for a in e["args"] for l in leaves(a)]
        for b in f["booleans"]:
            for l in leaves(b["expr"]):
                if l not in names:
                    warn(f"file {fi}: boolean '{b['name']}' references unknown '{l}'")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("template", help="Kaluza .composite / .protocol (zip) or raw Analysis .xml")
    ap.add_argument("-o", "--output", help="output JSON (default: <name>_FlowNgtmplt.json in cwd)")
    ap.add_argument("--name", help="template name (default: Kaluza protocol name)")
    ap.add_argument("--tube-names", help="comma-separated labels for dataset 0,1,2... e.g. 'B tube,T tube,M tube'")
    ap.add_argument("--tube", action="append", metavar="IDX=NAME", help="label one dataset (repeatable)")
    ap.add_argument("--lmd", action="append", help="LMD/FCS file for dataset 0,1,2... (repeat in dataset order); "
                    "its basename becomes sourceFile so FlowNg auto-matches it")
    ap.add_argument("--sheets", action="append", help="only include these plot sheets (repeatable)")
    ap.add_argument("--exclude-sheets", action="append", help="skip these plot sheets (repeatable)")
    ap.add_argument("--cofactor", type=float, default=300.0, help="asinh cofactor for logicle axes (default 300)")
    ap.add_argument("--dots", action="store_true",
                    help="draw coloured populations as exact coloured events (Kaluza style) instead of "
                         "FlowNg's density blend (default)")
    ap.add_argument("--list", action="store_true", help="list datasets / sheets and exit")
    args = ap.parse_args()

    tmpl = convert(args.template, args)
    if tmpl is None:
        for w in warnings:
            print("warning:", w)
        return
    out = Path(args.output) if args.output else Path(
        re.sub(r"[^\w.\- ]", "_", tmpl["name"]) + "_FlowNgtmplt.json")
    out.write_text(json.dumps(tmpl, indent=2))
    print(f"wrote {out}")
    for i, f in enumerate(tmpl["files"]):
        def count(nodes):
            return sum(1 + count(n["children"]) for n in nodes)
        ng = count(f["gates"]) + sum(count(b["children"]) for b in f["booleans"])
        npl = sum(1 for p in tmpl["plots"] if p["fileIndex"] == i)
        print(f"  file {i}: {f['sourceFile']!r}: {ng} gates, {len(f['booleans'])} booleans, {npl} plots")
    print(f"  tabs: {', '.join(dict.fromkeys(p['tabName'] for p in tmpl['plots']))}")
    print("NOTE: template files are tube-specific. In FlowNg's import dialog, match each entry above "
          "to the correct loaded tube (dataset order comes from the Kaluza template).")
    for w in warnings:
        print("warning:", w)


if __name__ == "__main__":
    main()
