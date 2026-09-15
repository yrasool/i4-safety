"""
Step 20 - turn the OSM tiles into a routable graph, one per road mode.

FOUR THINGS HERE ARE NOT OBVIOUS AND ALL FOUR ARE LOAD-BEARING.

1. WAYS ARE DEDUPLICATED FIRST.
   An Overpass bbox query returns the WHOLE geometry of any way that touches
   the box, so a road crossing a tile edge comes back complete in both tiles.
   Left alone, every interior point of every boundary-crossing way appears
   twice, which makes it look like a junction, which defeats step 2 entirely
   and inflates the graph by roughly an order of magnitude.

2. THE GRAPH IS CONTRACTED TO JUNCTIONS.
   OSM stores a curve as dozens of points. For routing, only the points where
   ways MEET matter; the rest just add length. A coordinate is a junction if it
   appears in two or more distinct ways, or is a way endpoint. Everything
   between two junctions collapses to one edge carrying the summed length.
   This is what makes 2,170 shortest-path searches finish.

3. COORDINATES ARE THE JOIN KEY, PACKED INTO INT64.
   Ways that meet share a coordinate, so rounding to 7dp (about 1 cm) joins
   them without a second pass to resolve OSM node ids, and stitches tile
   boundaries for free. A Python dict over ~20 million points would not fit in
   memory, so keys are packed into int64 and counted with numpy.

4. PARALLEL EDGES TAKE THE MINIMUM, NOT THE SUM.
   Two nodes are often joined by more than one way - a road and the footpath
   beside it, a slip road doubling back. scipy's coo -> csr conversion SUMS
   duplicate entries, which would make the two-minute path between them take
   four minutes and would never raise. Duplicates are reduced by minimum before
   the matrix is built.

SPEEDS ARE FREE-FLOW: posted limit where OSM has one, else a class default.
Stated plainly because it is exactly what the MEP authors would ask. These
isochrones contain NO congestion, so a crash-delay term added on top is not
double counting. Against a congested skim it would be.

Writes: data/interim/graph_{drive,walk,bike}.npz, data/interim/graph_nodes.npy
"""

import gzip
import json
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[1]
OSM = ROOT / "data" / "raw" / "osm"
INTERIM = ROOT / "data" / "interim"

# Free-flow mph by OSM highway class, used when the way carries no maxspeed.
DRIVE_MPH = {"motorway": 65, "trunk": 55, "primary": 45, "secondary": 40,
             "tertiary": 35, "unclassified": 30, "residential": 25,
             "living_street": 10, "service": 15, "track": 10,
             "motorway_link": 45, "trunk_link": 40, "primary_link": 35,
             "secondary_link": 30, "tertiary_link": 25}
NO_DRIVE = ("pedestrian", "footway", "path", "cycleway", "steps")
NO_FOOT = ("motorway", "motorway_link", "trunk", "trunk_link")
NO_BIKE = ("motorway", "motorway_link", "steps")

# 12 mph bike is the reference implementation's base assumption
# (FDOT BDV29-977-66 s4.1: "bikeable with a speed of 12 mph").
WALK_MPH, BIKE_MPH = 3.0, 12.0
MPS = 0.44704                   # mph -> metres per second

LAT_SCALE = 10_000_000          # 7 decimal places
LON_OFFSET = 4_000_000_000      # exceeds any packed longitude, so keys are unique


def pack(lat, lon):
    a = np.rint((np.asarray(lat) + 90.0) * LAT_SCALE).astype(np.int64)
    b = np.rint((np.asarray(lon) + 180.0) * LAT_SCALE).astype(np.int64)
    return a * LON_OFFSET + b


def unpack(key):
    a, b = np.divmod(np.asarray(key), LON_OFFSET)
    return a / LAT_SCALE - 90.0, b / LAT_SCALE - 180.0


def haversine(lat1, lon1, lat2, lon2):
    R = 6_371_000.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def parse_maxspeed(v):
    """OSM maxspeed is free text: '45 mph', '45', 'signals', 'RU:urban'."""
    if not v:
        return None
    t = str(v).lower().replace("mph", " ").strip()
    try:
        n = float(t.split()[0])
    except (ValueError, IndexError):
        return None
    return n if 3 <= n <= 85 else None


def iter_ways(report=False):
    """Stream every way once, deduplicated across tiles."""
    tiles = sorted(OSM.glob("tile_*.json.gz"))
    if not tiles:
        sys.exit("FAIL: no OSM tiles. Run 19_fetch_osm.py first.")
    seen, dup = set(), 0
    for t in tiles:
        for w in json.loads(gzip.decompress(t.read_bytes())):
            c = w["c"]
            h = hash((len(c), c[0][0], c[0][1], c[-1][0], c[-1][1],
                      c[len(c) // 2][0], c[len(c) // 2][1]))
            if h in seen:
                dup += 1
                continue
            seen.add(h)
            yield w
    if report:
        print(f"  {len(seen):,} distinct ways, {dup:,} tile-boundary "
              f"duplicates dropped ({dup / (len(seen) + dup):.1%})")


def main():
    # --- pass 1: which coordinates are junctions --------------------------
    print("pass 1  finding junctions", flush=True)
    chunks, ends = [], []
    for w in iter_ways(report=True):
        c = np.asarray(w["c"], dtype=np.float64)
        k = pack(c[:, 0], c[:, 1])
        chunks.append(k)
        ends.append(k[[0, -1]])
    allk = np.concatenate(chunks)
    uniq, counts = np.unique(allk, return_counts=True)
    junction = np.union1d(uniq[counts >= 2],
                          np.unique(np.concatenate(ends)))
    print(f"  {len(allk):,} points -> {len(uniq):,} distinct -> "
          f"{len(junction):,} junctions", flush=True)
    del allk, uniq, counts, chunks, ends

    idx_of = {int(k): i for i, k in enumerate(junction)}
    jlat, jlon = unpack(junction)

    # --- pass 2: split ways at junctions, emit edges ----------------------
    print("pass 2  building edges", flush=True)
    U, V, L, CLASS, ONEWAY, MAXSPD = [], [], [], [], [], []
    n_ways = 0
    for w in iter_ways():
        n_ways += 1
        c = np.asarray(w["c"], dtype=np.float64)
        k = pack(c[:, 0], c[:, 1])
        seg = haversine(c[:-1, 0], c[:-1, 1], c[1:, 0], c[1:, 1])
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        at = [i for i, kk in enumerate(k) if int(kk) in idx_of]
        hw = w["h"]
        ow = str(w.get("o") or "").lower() in ("yes", "true", "1", "-1")
        sp = parse_maxspeed(w.get("s"))
        for a, b in zip(at[:-1], at[1:]):
            d = cum[b] - cum[a]
            if d <= 0:
                continue
            U.append(idx_of[int(k[a])])
            V.append(idx_of[int(k[b])])
            L.append(d)
            CLASS.append(hw)
            ONEWAY.append(ow)
            MAXSPD.append(sp if sp else np.nan)

    U = np.asarray(U, np.int32)
    V = np.asarray(V, np.int32)
    L = np.asarray(L, np.float64)
    ONEWAY = np.asarray(ONEWAY, bool)
    MAXSPD = np.asarray(MAXSPD, np.float64)
    CLASS = np.asarray(CLASS)
    n = len(junction)
    tagged = np.isfinite(MAXSPD).mean()
    print(f"  {len(U):,} edges from {n_ways:,} ways   "
          f"{tagged:.1%} carry a posted speed", flush=True)

    # --- pass 3: per-mode traversal seconds --------------------------------
    print("pass 3  per-mode travel times", flush=True)
    for mode in ("drive", "walk", "bike"):
        if mode == "drive":
            mph = np.array([DRIVE_MPH.get(c, 25) for c in CLASS], float)
            mph = np.where(np.isfinite(MAXSPD), MAXSPD, mph)
            ok = ~np.isin(CLASS, NO_DRIVE)
            oneway = ONEWAY
        elif mode == "walk":
            mph = np.full(len(CLASS), WALK_MPH)
            ok = ~np.isin(CLASS, NO_FOOT)
            oneway = np.zeros(len(CLASS), bool)      # walking ignores one-way
        else:
            mph = np.full(len(CLASS), BIKE_MPH)
            ok = ~np.isin(CLASS, NO_BIKE)
            oneway = np.zeros(len(CLASS), bool)      # contraflow lanes are common

        sec = L / (mph * MPS)
        u0, v0, s0, d0 = U[ok], V[ok], sec[ok], oneway[ok]
        # forward arcs always; reverse arcs only where the edge is two-way
        u = np.concatenate([u0, v0[~d0]])
        v = np.concatenate([v0, u0[~d0]])
        s = np.concatenate([s0, s0[~d0]])

        # Reduce parallel edges by MINIMUM. coo -> csr would sum them.
        order = np.lexsort((s, v, u))
        u, v, s = u[order], v[order], s[order]
        first = np.ones(len(u), bool)
        first[1:] = (u[1:] != u[:-1]) | (v[1:] != v[:-1])
        u, v, s = u[first], v[first], s[first]

        M = csr_matrix((s, (u, v)), shape=(n, n))
        np.savez_compressed(INTERIM / f"graph_{mode}.npz",
                            data=M.data, indices=M.indices,
                            indptr=M.indptr, shape=np.array(M.shape))
        print(f"  {mode:<6}{int(ok.sum()):>10,} usable edges  "
              f"{M.nnz:>10,} arcs after dedup", flush=True)

    np.save(INTERIM / "graph_nodes.npy",
            np.column_stack([jlat, jlon]).astype(np.float64))
    print(f"\nwrote graph_[drive|walk|bike].npz and graph_nodes.npy "
          f"({n:,} nodes)")


if __name__ == "__main__":
    main()
