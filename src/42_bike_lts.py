"""
Step 42 - bike reach on the LOW-STRESS network only.

WHY THIS EXISTS. Step 21 lets a cyclist ride any road except a motorway, at 12
mph, as if a six-lane 45-mph arterial were as usable as a quiet street. Most
people will not cycle there at any price, so MEP's cycling reach - which carries
three-quarters of this project's headline loss - is built on routes almost
nobody would take. That is the single most likely reason the cycling result is
too large.

Level of Traffic Stress (Mekuria, Furth and Nixon 2012) is the standard answer,
and NREL's own accessibility work uses it the same way: a bike trip counts only
if it can be made on roads an "interested but concerned" adult will ride. So
instead of PRICING stress, this step changes WHERE A BIKE CAN GO.

THE RULES, simplified from Mekuria et al. to the tags OpenStreetMap carries:

  bike path, trail, track                               low stress
  local street (residential, living_street, service,
      unclassified)                                     low stress if speed <= 30 mph
  collector / arterial with a PROTECTED bike lane       low stress
  collector / arterial with a PAINTED bike lane         low stress if speed <= 35 mph
                                                                 and lanes <= 4
  collector / arterial, no bike facility                low stress if speed <= 25 mph
                                                                 and lanes <= 2
  footway, pedestrian, steps                            excluded

Missing speeds take the class default already used for driving; missing lane
counts take a class default (2 for tertiary, 4 for secondary and above).

TWO CHOICES THAT MAKE THIS THE STRICT VERSION, stated because both push the
result the same way:
  1. SIDEWALKS ARE NOT LOW-STRESS BIKE ROUTES. Riding on the sidewalk is legal
     in Florida and common along arterials. Counting it would reconnect almost
     everything and undo the point of the test.
  2. CROSSINGS ARE NOT MODELLED. Full LTS rates each intersection approach; an
     edge-only version treats every arterial as a wall, even where a signalised
     crossing makes it passable. That fragments neighbourhoods more than a rider
     would experience.
So this is a LOWER bound on low-stress bike reach, and read as such.

NODE IDS ARE STEP 20's. Passes 1 and 2 are rerun from the same tiles, and the
junction set is checked against graph_nodes.npy before anything is written, so
snapping, travel-time matrices and every downstream index line up exactly.

Reads:  data/raw/osm/tile_*.json.gz (step 19), data/raw/osm_lts/ (step 41),
        data/interim/graph_nodes.npy, centroids.csv
Writes: data/interim/graph_bike_lts.npz, data/interim/tt_bike_lts.npy,
        data/final/bike_lts_summary.csv
"""

import csv
import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
LTS_TILES = ROOT / "data" / "raw" / "osm_lts"

spec = importlib.util.spec_from_file_location("s20", SRC / "20_build_graph.py")
s20 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s20)

MAX_MIN = 40
CHUNK = 64
MAX_SNAP_M = 2_000
CONNECTOR_M = 250.0     # about one suburban block
CONNECTOR_SLOW = 3.0    # time multiplier on those short stretches
BIKE_MPH = s20.BIKE_MPH
MPS = s20.MPS

LOCAL = ("residential", "living_street", "service", "unclassified")
PATHS = ("cycleway", "path", "track")
EXCLUDED = ("footway", "pedestrian", "steps", "motorway", "motorway_link")
MAJOR_SPEED = {"tertiary": 35, "tertiary_link": 30, "secondary": 40,
               "secondary_link": 35, "primary": 45, "primary_link": 40,
               "trunk": 55, "trunk_link": 45}
MAJOR_LANES = {"tertiary": 2, "tertiary_link": 1, "secondary": 4,
               "secondary_link": 1, "primary": 4, "primary_link": 1,
               "trunk": 4, "trunk_link": 1}


def fingerprint(c):
    # identical to step 20's tile-boundary dedupe key
    return hash((len(c), c[0][0], c[0][1], c[-1][0], c[-1][1],
                 c[len(c) // 2][0], c[len(c) // 2][1]))


def load_lts_tags():
    tiles = sorted(LTS_TILES.glob("tile_*.json.gz"))
    if not tiles:
        sys.exit("FAIL: no LTS tag tiles. Run 41_fetch_osm_lts_tags.py first.")
    tags = {}
    for t in tiles:
        for w in json.loads(gzip.decompress(t.read_bytes())):
            tags[fingerprint(w["c"])] = w["t"]
    return tags


def lanes_of(t, hw):
    for k in ("lanes",):
        v = t.get(k)
        if v:
            try:
                return int(float(str(v).split(";")[0]))
            except ValueError:
                pass
    f, b = t.get("lanes:forward"), t.get("lanes:backward")
    try:
        if f or b:
            return int(float(f or 0)) + int(float(b or 0))
    except ValueError:
        pass
    return MAJOR_LANES.get(hw, 2)


def classify(hw, speed, t):
    """Return (low_stress: bool, reason: str)."""
    if hw in EXCLUDED:
        return False, "excluded"
    if hw in PATHS:
        if (t or {}).get("bicycle") == "no":
            return False, "path, bikes prohibited"
        return True, "path"
    if hw in LOCAL:
        sp = speed if np.isfinite(speed) else 25.0
        return (sp <= 30), "local street"
    if hw in MAJOR_SPEED:
        sp = speed if np.isfinite(speed) else float(MAJOR_SPEED[hw])
        if t is None:
            return (sp <= 25), "major, no tags matched"
        cw = {str(t.get(k, "")).lower() for k in
              ("cycleway", "cycleway:both", "cycleway:left", "cycleway:right")}
        ln = lanes_of(t, hw)
        if cw & {"track", "separate"}:
            return True, "major, protected lane"
        if "lane" in cw:
            return (sp <= 35 and ln <= 4), "major, painted lane"
        return (sp <= 25 and ln <= 2), "major, mixed traffic"
    return False, "other"


def classify_walk(hw, speed, t):
    """Pedestrian stress, simplified from pedestrian LTS: walking ALONG a road
    is low-stress where there is a sidewalk and traffic is not fast, or where
    traffic is slow enough to share the street."""
    if hw in ("footway", "pedestrian", "path", "steps", "track", "cycleway"):
        return True, "footpath"
    if hw in ("motorway", "motorway_link", "trunk", "trunk_link"):
        return False, "excluded"
    if hw in LOCAL:
        sp = speed if np.isfinite(speed) else 25.0
        return (sp <= 30), "local street"
    if hw in MAJOR_SPEED:
        sp = speed if np.isfinite(speed) else float(MAJOR_SPEED[hw])
        side = str((t or {}).get("sidewalk", "")).lower()
        if t is None:
            return (sp <= 25), "major, no tags matched"
        if side in ("both", "left", "right", "yes"):
            return (sp <= 45), "major, sidewalk"
        if side == "separate":
            # the sidewalk is mapped as its own footway, which carries the
            # walking; the carriageway itself is not a walking route
            return False, "major, sidewalk mapped separately"
        return (sp <= 25), "major, no sidewalk tagged"
    return False, "other"


def main():
    tags = load_lts_tags()
    print(f"{len(tags):,} collector/arterial ways carry LTS tags")

    # ---- pass 1, exactly as step 20 ------------------------------------
    chunks, ends = [], []
    for w in s20.iter_ways():
        c = np.asarray(w["c"], dtype=np.float64)
        k = s20.pack(c[:, 0], c[:, 1])
        chunks.append(k)
        ends.append(k[[0, -1]])
    allk = np.concatenate(chunks)
    uniq, counts = np.unique(allk, return_counts=True)
    junction = np.union1d(uniq[counts >= 2], np.unique(np.concatenate(ends)))
    del allk, uniq, counts, chunks, ends

    nodes = np.load(INTERIM / "graph_nodes.npy")
    jlat, jlon = s20.unpack(junction)
    if len(junction) != len(nodes) or not (
            np.allclose(jlat, nodes[:, 0]) and np.allclose(jlon, nodes[:, 1])):
        sys.exit("FAIL: rebuilt junctions differ from graph_nodes.npy. The OSM "
                 "tiles changed since step 20 ran; rerun 20 and 21 first, or "
                 "every travel-time index will point at the wrong node.")
    idx_of = {int(k): i for i, k in enumerate(junction)}
    n = len(junction)

    # ---- pass 2 with stress ---------------------------------------------
    U, V, L, LOW, BIKE_OK, WALK_OK, WLOW = [], [], [], [], [], [], []
    reasons, wreasons = {}, {}
    major_seen = major_matched = 0
    for w in s20.iter_ways():
        hw = w["h"]
        c = np.asarray(w["c"], dtype=np.float64)
        k = s20.pack(c[:, 0], c[:, 1])
        seg = s20.haversine(c[:-1, 0], c[:-1, 1], c[1:, 0], c[1:, 1])
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        at = [i for i, kk in enumerate(k) if int(kk) in idx_of]
        sp = s20.parse_maxspeed(w.get("s"))
        t = None
        if hw in MAJOR_SPEED:
            major_seen += 1
            t = tags.get(fingerprint(w["c"]))
            major_matched += t is not None
        low, why = classify(hw, sp if sp else np.nan, t)
        bike_ok = hw not in s20.NO_BIKE
        low = low and bike_ok
        walk_ok = hw not in s20.NO_FOOT
        wlow, wwhy = classify_walk(hw, sp if sp else np.nan, t)
        wlow = wlow and walk_ok
        for a, b in zip(at[:-1], at[1:]):
            d = cum[b] - cum[a]
            if d <= 0:
                continue
            U.append(idx_of[int(k[a])])
            V.append(idx_of[int(k[b])])
            L.append(d)
            LOW.append(low)
            BIKE_OK.append(bike_ok)
            WALK_OK.append(walk_ok)
            WLOW.append(wlow)
            if bike_ok:
                key = (why, low)
                reasons[key] = reasons.get(key, 0.0) + d
            if walk_ok:
                wkey = (wwhy, wlow)
                wreasons[wkey] = wreasons.get(wkey, 0.0) + d

    U = np.asarray(U, np.int32)
    V = np.asarray(V, np.int32)
    L = np.asarray(L, np.float64)
    LOW = np.asarray(LOW, bool)
    BIKE_OK = np.asarray(BIKE_OK, bool)
    WALK_OK = np.asarray(WALK_OK, bool)
    WLOW = np.asarray(WLOW, bool)
    print(f"\n  collector/arterial ways matched to their tags: "
          f"{major_matched:,} of {major_seen:,} "
          f"({major_matched / max(major_seen, 1):.1%})")
    if major_seen and major_matched / major_seen < 0.6:
        print("  WARNING: under 60% of major roads matched their tags; OSM has "
              "changed since step 19. Unmatched majors are treated as high "
              "stress unless 25 mph or slower.")

    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    olat = np.array([float(r["lat"]) for r in cent])
    olon = np.array([float(r["lon"]) for r in cent])
    area = np.array([float(r["arealand_m2"] or 0) for r in cent])
    n_o = len(cent)
    lat0 = np.radians(olat.mean())

    def to_m(la, lo):
        return np.column_stack([np.radians(lo) * 6_371_000 * np.cos(lat0),
                                np.radians(la) * 6_371_000])

    summary = []

    def build(mode, mph, usable_edge, low_edge, why, tag="lts",
              time_mult=None):
        tot = L[usable_edge].sum()
        print(f"\n{'=' * 64}\n{mode.upper()}: low-stress share of the "
              f"{tot / 1609.344:,.0f} usable network miles is "
              f"{L[low_edge].sum() / tot:.1%}")
        print(f"  {'class':<34}{'stress':>8}{'miles':>10}{'share':>8}")
        for (w_, lo_), m in sorted(why.items(), key=lambda x: -x[1]):
            print(f"  {w_:<34}{'low' if lo_ else 'HIGH':>8}"
                  f"{m / 1609.344:>10,.0f}{m / tot:>8.1%}")

        sec = L / (mph * MPS)
        if time_mult is not None:
            sec = sec * time_mult
        u0, v0, s0 = U[low_edge], V[low_edge], sec[low_edge]
        u = np.concatenate([u0, v0])
        v = np.concatenate([v0, u0])
        s_ = np.concatenate([s0, s0])
        order = np.lexsort((s_, v, u))
        u, v, s_ = u[order], v[order], s_[order]
        first = np.ones(len(u), bool)
        first[1:] = (u[1:] != u[:-1]) | (v[1:] != v[:-1])
        G = csr_matrix((s_[first], (u[first], v[first])), shape=(n, n))
        np.savez_compressed(INTERIM / f"graph_{mode}_{tag}.npz", data=G.data,
                            indices=G.indices, indptr=G.indptr,
                            shape=np.array(G.shape))

        deg = np.diff(G.indptr) + np.bincount(G.indices, minlength=n)
        usable = np.flatnonzero(deg > 0)
        dist, near = cKDTree(to_m(nodes[usable, 0], nodes[usable, 1])).query(
            to_m(olat, olon), k=1)
        snap = usable[near]
        far = int((dist > MAX_SNAP_M).sum())
        print(f"  origins snapped: median {np.median(dist):,.0f} m, "
              f"{far} beyond {MAX_SNAP_M} m (those get no {mode} reach)")

        tt = np.full((n_o, n_o), np.inf, dtype=np.float32)
        for i0 in range(0, n_o, CHUNK):
            d = dijkstra(G, directed=True, indices=snap[i0:i0 + CHUNK],
                         limit=MAX_MIN * 60)
            tt[i0:i0 + CHUNK] = (d[:, snap] / 60.0).astype(np.float32)
        tt[dist > MAX_SNAP_M, :] = np.inf
        intra = ((2.0 / 3.0) * np.sqrt(np.maximum(area, 1.0) / np.pi)
                 / (mph * MPS) / 60.0)
        np.fill_diagonal(tt, intra.astype(np.float32))
        np.save(INTERIM / f"tt_{mode}_{tag}.npy", tt)

        full = np.load(INTERIM / f"tt_{mode}.npy")
        print(f"  {'band':>6}{'any road':>12}{'low-stress':>12}{'kept':>8}"
              f"   median block groups reached")
        summary.append([f"{mode}_{tag}_network_share",
                        f"{L[low_edge].sum() / tot:.4f}"])
        for b in (10, 20, 30, 40):
            a_ = float(np.median((full <= b).sum(1)))
            lo_ = float(np.median((tt <= b).sum(1)))
            print(f"  {b:>4}m{a_:>12,.0f}{lo_:>12,.0f}"
                  f"{lo_ / max(a_, 1):>8.0%}")
            summary.append([f"{mode}_median_reach_{b}min_any", a_])
            summary.append([f"{mode}_median_reach_{b}min_{tag}", lo_])

    build("bike", BIKE_MPH, BIKE_OK, LOW, reasons)
    # REALISTIC VARIANT. Strict LTS turns every arterial into a wall, and
    # Tampa Bay subdivisions connect only to arterials, so the strict
    # network is a set of islands. Real riders cover a block of arterial -
    # often on the sidewalk, which is legal here - to reach the next
    # entrance. So high-stress bikeable edges up to CONNECTOR_M long are
    # allowed, at CONNECTOR_SLOW times the travel time, which lets a route
    # hop a block but makes riding an arterial end to end expensive inside
    # the 40-minute limit.
    connector = BIKE_OK & ~LOW & (L <= CONNECTOR_M)
    mult = np.where(connector, CONNECTOR_SLOW, 1.0)
    print(f"\n  realistic variant: {connector.sum():,} short high-stress edges allowed "
          f"({L[connector].sum() / 1609.344:,.0f} miles) at "
          f"{CONNECTOR_SLOW:.0f}x travel time")
    build("bike", BIKE_MPH, BIKE_OK, LOW | connector, reasons,
          tag="lts_connect", time_mult=mult)
    build("walk", s20.WALK_MPH, WALK_OK, WLOW, wreasons)

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "active_lts_summary.csv").open("w", newline="",
                                                 encoding="utf8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["metric", "value"])
        wtr.writerow(["major_tag_match_share",
                      f"{major_matched / max(major_seen, 1):.4f}"])
        wtr.writerows(summary)
    print("\nwrote graph_{bike,walk}_lts.npz, tt_{bike,walk}_lts.npy, "
          "active_lts_summary.csv")


if __name__ == "__main__":
    main()
