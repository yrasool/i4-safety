"""
Step 40 - crash risk along the ROUTE ACTUALLY DRIVEN, origin by destination.

WHY THIS EXISTS. Step 30 gives each origin one driving crash cost, built as a
traffic-weighted average of segments NEAR it, discounted by travel time. Its own
docstring names what that is: "exposure-weighted proximity, not route
assignment". A driver from a quiet suburb who reaches every job along one deadly
arterial gets the suburb's number, because proximity cannot see which roads a
trip uses. That is the limitation a transport modeller asks about first.

This step does the assignment properly:

    for each origin block group
        build the shortest-time tree over the drive network (40-minute limit)
        for each reachable destination block group
            walk the tree back along the route actually taken
            sum  (segment crash cost per passenger-mile x miles)  on that route
            divide by route miles on the state system
    weight each destination by its MEP opportunities and MEP's own time decay

HOW IT STAYS TRACTABLE. 2,170 x 2,170 routes, each hundreds of edges, cannot be
walked one at a time in Python. It does not have to be. A shortest-path tree
stores one predecessor per node, so a quantity summed along a route is a
quantity summed up a tree, and POINTER JUMPING does that for every node at once
in about log2(depth) vectorised passes:

    value[v] += value[jump[v]];   jump[v] = jump[jump[v]]

After about 13 passes every node holds the sum over its whole route. One
Dijkstra and a dozen numpy operations per origin, instead of millions of walks.

HOW FDOT SEGMENTS ARE LAID ON THE GRAPH. The crash rates live on FDOT
straight-line-diagram segments; the routes live on an OpenStreetMap junction
graph. They share no keys. A graph edge is assigned to a segment when BOTH of its
junctions lie within TOL_M of that segment's polyline. Requiring both ends is
what stops a side street that merely touches a state road at one junction from
inheriting that road's crash rate. The segment cache in step 30 stored only
midpoints, which cannot do this; full polylines are fetched and cached here.

The FDOT county highway maps (PDF) show the same roads, but as rendered images
with no recoverable coordinates, so the geometry comes from FDOT's own RCI
feature service instead.

WHAT IS AND IS NOT ON A ROUTE'S RISK.
  * Only STATE-SYSTEM miles carry a measured rate - FDOT publishes AADT, and so
    Empirical Bayes rates, for those roads alone. They carry 78.5% of driving.
  * Local streets carry no rate. A route's cost is the length-weighted mean over
    its state-system miles. A route with NO state-system miles - a short trip on
    neighbourhood streets - falls back to the regional driving rate, and how
    often that happens is reported, not hidden.
  * Edge length is the straight chord between junctions. Curved roads are longer
    than their chords, but the same length sits in numerator and denominator, so
    the bias is second-order on a length-weighted MEAN.

Reads:  data/interim/graph_drive.npz, graph_nodes.npy, centroids.csv, tt_drive.npy,
        opportunities.csv, spatial_equivalency.csv, activity_freq.csv
        data/final/segment_eb.csv, injury_cost_by_mode.csv, origin_risk.csv
Writes: data/raw/fdot_segment_paths.json          (cached polylines)
        data/interim/route_risk_od.npy            (2,170 x 2,170, $/pmt, NaN if unreachable)
        data/final/route_risk_by_origin.csv       (per origin: overall and per 10-min band)
"""

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import BETA, USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
RAW = ROOT / "data" / "raw"
RCI = "https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/FeatureServer/0"
COUNTY_DOT = ("10", "15", "14", "08", "02")
PATH_CACHE = RAW / "fdot_segment_paths.json"

MAX_MIN = 40
BANDS = (10, 20, 30, 40)
TOL_M = 25.0          # junction-to-polyline tolerance for edge matching
DENSIFY_M = 10.0      # polyline resampling step before building the KD-tree
MI_PER_M = 1 / 1609.344


def fetch_paths():
    if PATH_CACHE.exists():
        return json.loads(PATH_CACHE.read_text())
    where = "COUNTYDOT IN (" + ",".join(f"'{c}'" for c in COUNTY_DOT) + ")"
    out, off = {}, 0
    while True:
        url = (f"{RCI}/query?where={urllib.parse.quote(where)}"
               f"&outFields=ROADWAY,BEGIN_POST,END_POST"
               f"&returnGeometry=true&outSR=4326"
               f"&resultOffset={off}&resultRecordCount=1000&f=json")
        req = urllib.request.Request(url, headers=USER_AGENT)
        with urllib.request.urlopen(req, timeout=300) as r:
            d = json.load(r)
        feats = d.get("features", [])
        if not feats:
            break
        for feat in feats:
            a = feat["attributes"]
            parts = (feat.get("geometry") or {}).get("paths") or []
            if parts:
                key = f"{a['ROADWAY']}|{a['BEGIN_POST']}|{a['END_POST']}"
                # [lon, lat] as returned; each part kept separate so a
                # multipart segment is never bridged across its gap
                out.setdefault(key, []).extend(parts)
        off += len(feats)
        print(f"    {off:,} segment polylines", flush=True)
        if not d.get("exceededTransferLimit"):
            break
    PATH_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PATH_CACHE.write_text(json.dumps(out))
    return out


def read_csv(path):
    with path.open(encoding="utf8") as fh:
        return list(csv.DictReader(fh))


def main():
    bench = "--bench" in sys.argv
    t0 = time.time()

    # ---- segments and their polylines -----------------------------------
    segs = read_csv(FINAL / "segment_eb.csv")
    print(f"{len(segs):,} segments with Empirical Bayes rates")
    paths = fetch_paths()

    cent = read_csv(INTERIM / "centroids.csv")
    olat = np.array([float(r["lat"]) for r in cent])
    olon = np.array([float(r["lon"]) for r in cent])
    lat0 = np.radians(olat.mean())

    def to_m(lat, lon):
        return np.column_stack([np.radians(lon) * 6_371_000 * np.cos(lat0),
                                np.radians(lat) * 6_371_000])

    pts, owner, seg_r = [], [], []
    for s in segs:
        key = f"{s['roadway']}|{float(s['begin_post'])}|{float(s['end_post'])}"
        parts = paths.get(key)
        if not parts:
            continue
        sid = len(seg_r)
        seg_r.append(float(s["r_per_pmt"]))
        for part in parts:
            xy = to_m(np.array([p[1] for p in part]),
                      np.array([p[0] for p in part]))
            for a, b in zip(xy[:-1], xy[1:]):
                k = max(1, int(np.hypot(*(b - a)) // DENSIFY_M))
                t = np.linspace(0.0, 1.0, k + 1)[:, None]
                pts.append(a + t * (b - a))
                owner.append(np.full(k + 1, sid, dtype=np.int32))
    seg_r = np.array(seg_r)
    print(f"  {len(seg_r):,} of {len(segs):,} segments have a polyline "
          f"({len(seg_r) / len(segs):.1%})")
    if len(seg_r) < 0.8 * len(segs):
        sys.exit("FAIL: under 80% of segments matched a polyline. The key "
                 "(roadway|begin|end) is not joining; check float formatting.")
    pts = np.vstack(pts)
    owner = np.concatenate(owner)
    seg_tree = cKDTree(pts)
    print(f"  {len(pts):,} densified polyline points")

    # ---- graph, and each edge's segment ---------------------------------
    z = np.load(INTERIM / "graph_drive.npz")
    G = csr_matrix((z["data"], z["indices"], z["indptr"]),
                   shape=tuple(z["shape"]))
    N = G.shape[0]
    nodes = np.load(INTERIM / "graph_nodes.npy")
    nxy = to_m(nodes[:, 0], nodes[:, 1])

    src = np.repeat(np.arange(N, dtype=np.int64), np.diff(G.indptr))
    dst = G.indices.astype(np.int64)
    E = len(dst)
    edge_len_mi = np.hypot(*(nxy[src] - nxy[dst]).T) * MI_PER_M

    # nearest polyline point to every junction, once
    dn, pn = seg_tree.query(nxy, k=1, distance_upper_bound=TOL_M)
    node_seg = np.where(np.isfinite(dn),
                        owner[np.minimum(pn, len(owner) - 1)], -1)
    # both ends on the SAME segment
    edge_seg = np.where((node_seg[src] >= 0) & (node_seg[src] == node_seg[dst]),
                        node_seg[src], -1)
    on_state = edge_seg >= 0
    edge_state_mi = np.where(on_state, edge_len_mi, 0.0)
    edge_risk = np.where(on_state,
                         edge_len_mi * seg_r[np.maximum(edge_seg, 0)], 0.0)
    used = len(np.unique(edge_seg[on_state]))
    print(f"  {on_state.sum():,} of {E:,} graph edges on a state segment "
          f"({on_state.mean():.1%} of edges, "
          f"{edge_state_mi.sum() / edge_len_mi.sum():.1%} of network miles); "
          f"{used:,} of {len(seg_r):,} segments received at least one edge")
    if used < 0.7 * len(seg_r):
        sys.exit(f"FAIL: only {used} of {len(seg_r)} segments matched any "
                 f"graph edge. The OSM network and the FDOT polylines are not "
                 f"lining up; check TOL_M and the projection.")

    # (source, target) -> edge index, for predecessor lookups
    ekey = src * N + dst
    order = np.argsort(ekey)
    ekey_sorted = ekey[order]

    def edge_of(p, v):
        k = p.astype(np.int64) * N + v.astype(np.int64)
        return order[np.searchsorted(ekey_sorted, k)]

    # ---- origins, snapped exactly as step 21 does ------------------------
    deg = np.diff(G.indptr) + np.bincount(G.indices, minlength=N)
    usable = np.flatnonzero(deg > 0)
    _, near = cKDTree(nxy[usable]).query(to_m(olat, olon), k=1)
    snap = usable[near]
    n = len(cent)

    T = np.load(INTERIM / "tt_drive.npy")
    r_reg = float(next(x["cost_per_pmt"]
                       for x in read_csv(FINAL / "injury_cost_by_mode.csv")
                       if x["mode"] == "vehicle_occupant"))

    # ---- per-origin trees ----------------------------------------------
    R = np.full((n, n), np.nan, dtype=np.float32)   # $/pmt along the route
    S = np.zeros((n, n), dtype=np.float32)           # state share of route miles
    todo = range(8) if bench else range(n)
    t1 = time.time()
    for i in todo:
        dist, pred = dijkstra(G, directed=True, indices=int(snap[i]),
                              limit=MAX_MIN * 60, return_predecessors=True)
        reach = np.flatnonzero(np.isfinite(dist))
        cid = np.full(N, -1, dtype=np.int64)
        cid[reach] = np.arange(len(reach))
        root = cid[snap[i]]
        p = pred[reach]
        has = p >= 0
        jump = np.full(len(reach), root, dtype=np.int64)
        jump[has] = cid[p[has]]
        risk = np.zeros(len(reach))
        ln = np.zeros(len(reach))
        sl = np.zeros(len(reach))
        e = edge_of(p[has], reach[has])
        risk[has] = edge_risk[e]
        ln[has] = edge_len_mi[e]
        sl[has] = edge_state_mi[e]
        # pointer jumping: after k passes each node holds the sum over its
        # first 2^k hops toward the root; the root carries zero
        for _ in range(40):
            live = jump != root
            if not live.any():
                break
            risk = risk + np.where(live, risk[jump], 0.0)
            ln = ln + np.where(live, ln[jump], 0.0)
            sl = sl + np.where(live, sl[jump], 0.0)
            jump = np.where(live, jump[jump], root)
        else:
            sys.exit(f"FAIL: pointer jumping did not converge for origin {i}. "
                     f"The predecessor array contains a cycle.")

        dcid = cid[snap]
        okj = (dcid >= 0) & np.isfinite(T[i]) & (T[i] <= MAX_MIN)
        okj[i] = False
        j = np.flatnonzero(okj)
        rk, sm, tl = risk[dcid[j]], sl[dcid[j]], ln[dcid[j]]
        R[i, j] = np.where(sm > 0, rk / np.maximum(sm, 1e-12), r_reg)
        S[i, j] = np.where(tl > 0, sm / np.maximum(tl, 1e-12), 0.0)

        if bench or i % 100 == 0:
            el = time.time() - t1
            left = el / (i + 1) * (n - i - 1) / 60
            print(f"    origin {i + 1:>5,}/{n:,}   {len(reach):>7,} nodes "
                  f"reached   {el:6.0f}s   ~{left:5.1f} min left", flush=True)

    if bench:
        k = np.isfinite(R[:8])
        print(f"\nBENCH: {time.time() - t1:.1f}s for 8 origins; full run "
              f"~{(time.time() - t1) / 8 * n / 60:.0f} min")
        print(f"  route $/pmt: median {np.nanmedian(R[:8]):.4f}  "
              f"p10 {np.nanpercentile(R[:8], 10):.4f}  "
              f"p90 {np.nanpercentile(R[:8], 90):.4f}")
        print(f"  state-system share of route miles: median "
              f"{np.median(S[:8][k]):.1%}")
        return

    np.save(INTERIM / "route_risk_od.npy", R)

    # ---- opportunity weights, exactly as step 23 builds them -------------
    opp = read_csv(INTERIM / "opportunities.csv")
    acts = [c for c in opp[0] if c != "GEOID20"]
    freq = [r for r in read_csv(INTERIM / "activity_freq.csv")
            if r["geography"] == "South Atlantic 2022"]
    f = np.array([float(next(x["f_share"] for x in freq
                             if x["activity"] == a)) for a in acts])
    f = f / f.sum()
    se = {r["activity"]: float(r["spatial_equivalency"])
          for r in read_csv(INTERIM / "spatial_equivalency.csv")}
    w_act = np.array([se[a] for a in acts]) * f
    byid = {r["GEOID20"]: sum(float(r[a]) * w_act[k]
                              for k, a in enumerate(acts)) for r in opp}
    O = np.array([byid.get(c["GEOID20"], 0.0) for c in cent])

    Tf = np.where(np.isfinite(T), T, 1e9)
    W = O[None, :] * np.exp(BETA * Tf)
    W[~np.isfinite(R)] = 0.0
    Rz = np.nan_to_num(R, nan=0.0)

    def wmean(mask):
        ww = np.where(mask, W, 0.0)
        den = ww.sum(axis=1)
        return np.divide((ww * Rz).sum(axis=1), den,
                         out=np.full(n, np.nan), where=den > 0)

    overall = wmean(np.ones(W.shape, dtype=bool))
    per_band, lo = [], 0.0
    for b in BANDS:
        per_band.append(wmean((T > lo) & (T <= b)))
        lo = b

    fin = np.isfinite(R)
    fallback = float(((S == 0) & fin).sum() / fin.sum())
    print(f"\nROUTE-ASSIGNED DRIVING CRASH COST, {fin.sum():,} "
          f"origin-destination pairs")
    print(f"  per pair    median ${np.nanmedian(R):.4f}   "
          f"p10 ${np.nanpercentile(R, 10):.4f}   "
          f"p90 ${np.nanpercentile(R, 90):.4f}")
    print(f"  state-system share of route miles: median "
          f"{np.median(S[fin]):.1%}")
    print(f"  pairs with NO state-system miles (regional fallback): "
          f"{fallback:.1%}")
    ok = np.isfinite(overall)
    print(f"\n  per origin  median ${np.median(overall[ok]):.4f}   "
          f"p10 ${np.percentile(overall[ok], 10):.4f}   "
          f"p90 ${np.percentile(overall[ok], 90):.4f}   "
          f"min ${overall[ok].min():.4f}   max ${overall[ok].max():.4f}")

    prox = {r["GEOID20"]: r["r_drive_local"]
            for r in read_csv(FINAL / "origin_risk.csv")}
    px = np.array([float(prox.get(c["GEOID20"]) or "nan") for c in cent])
    both = ok & np.isfinite(px)
    rho = spearmanr(overall[both], px[both]).correlation
    print(f"\n  vs step 30 proximity: Spearman {rho:.3f} over {both.sum():,} "
          f"origins; route / proximity median ratio "
          f"{np.median(overall[both] / px[both]):.2f}")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "route_risk_by_origin.csv").open("w", newline="",
                                                   encoding="utf8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["GEOID20", "county", "r_route", "r_band10", "r_band20",
                      "r_band30", "r_band40", "r_proximity"])

        def fmt(v):
            return f"{v:.6f}" if np.isfinite(v) else ""

        for i, c in enumerate(cent):
            wtr.writerow([c["GEOID20"], c["county"], fmt(overall[i])]
                         + [fmt(pb[i]) for pb in per_band] + [fmt(px[i])])
    print(f"\nwrote {FINAL / 'route_risk_by_origin.csv'}   "
          f"({(time.time() - t0) / 60:.1f} min)")


if __name__ == "__main__":
    main()
