"""
Step 21 - isochrones by road mode.  MEP Equation 1, the reachability half.

For every block group, how long does it take to reach every other block group,
by driving, walking and cycling? That matrix is what an isochrone IS - the set
of destinations inside a time band is just a threshold on it.

MEP's default bands are 10, 20, 30 and 40 minutes, so the search is cut off at
40 and everything beyond is left unreachable rather than computed and discarded.
That cutoff is most of why this finishes: a 40-minute walk reaches a tiny
fraction of the graph, and Dijkstra stops as soon as the frontier passes it.

SNAPPING. Origins are block group interior points, which fall in the middle of a
polygon and almost never on a road. Each is snapped to the nearest node IN THAT
MODE'S OWN SUBGRAPH, not to the nearest node overall. Snapping a driving origin
onto a footpath node would strand it: the node exists, the search runs, and the
block group silently reaches nothing. That failure prints zeros, not an error.
The snap distance is reported so a bad snap is visible rather than assumed away.

Writes: data/interim/tt_{drive,walk,bike}.npy   (minutes, 2170 x 2170)
"""

import sys
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"

MAX_MIN = 40                    # MEP's widest band

# INTRAZONAL TRAVEL TIME. The diagonal of the matrix is the time to reach
# opportunities inside your OWN block group, and it must not be zero.
#
# Zero says a resident of a 200 km2 Citrus block group can reach everything in
# it instantly, on foot. 601 of 2,170 block groups here are larger than a
# ten-minute walk can cover, so a zero diagonal hands them their entire local
# opportunity count inside the shortest band, for every mode. It inflates walk
# and transit most, because those are the modes whose real reach is smallest,
# and it does it hardest in exactly the rural block groups that then show the
# largest MEP loss.
#
# Standard treatment: mean distance from the centre of a disc of equal area to
# a uniformly random point in it, which is 2R/3 for R = sqrt(area/pi).
MODE_MPH = {"drive": 25.0, "walk": 3.0, "bike": 12.0}   # local-street speeds
CHUNK = 64                      # origins per Dijkstra call; bounds peak memory
# Beyond this the interior point is not near any usable road for that mode and
# the result would be an artefact of snapping, not of the network.
MAX_SNAP_M = 2_000


def load_graph(mode):
    z = np.load(INTERIM / f"graph_{mode}.npz")
    return csr_matrix((z["data"], z["indices"], z["indptr"]),
                      shape=tuple(z["shape"]))


def main():
    import csv
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    olat = np.array([float(r["lat"]) for r in cent])
    olon = np.array([float(r["lon"]) for r in cent])
    n_o = len(cent)

    nodes = np.load(INTERIM / "graph_nodes.npy")
    print(f"{n_o:,} origins   {len(nodes):,} graph nodes")

    # Equirectangular metres about the study area. Good to well under a metre
    # over 150 km at this latitude, and it lets a KD-tree work in a flat space.
    lat0 = np.radians(olat.mean())
    to_m = lambda la, lo: np.column_stack(
        [np.radians(lo) * 6_371_000 * np.cos(lat0), np.radians(la) * 6_371_000])

    opts = to_m(olat, olon)

    for mode in ("drive", "walk", "bike"):
        G = load_graph(mode)
        # A node is usable by this mode only if it has at least one arc.
        deg = np.diff(G.indptr) + np.bincount(G.indices, minlength=G.shape[0])
        usable = np.flatnonzero(deg > 0)
        tree = cKDTree(to_m(nodes[usable, 0], nodes[usable, 1]))
        dist, near = tree.query(opts, k=1)
        snap = usable[near]

        far = int((dist > MAX_SNAP_M).sum())
        print(f"\n{mode}   {len(usable):,} usable nodes   "
              f"snap median {np.median(dist):,.0f} m, max {dist.max():,.0f} m"
              f"   {far} beyond {MAX_SNAP_M} m")
        if far > n_o * 0.02:
            sys.exit(f"FAIL: {far} of {n_o} origins snap further than "
                     f"{MAX_SNAP_M} m for {mode}. The network has holes; do "
                     f"not build isochrones on it.")

        tt = np.full((n_o, n_o), np.inf, dtype=np.float32)
        for i in range(0, n_o, CHUNK):
            src = snap[i:i + CHUNK]
            d = dijkstra(G, directed=True, indices=src, limit=MAX_MIN * 60)
            # subset to destination nodes immediately; the full array is
            # n_sources x n_nodes and must not be kept
            tt[i:i + CHUNK] = (d[:, snap] / 60.0).astype(np.float32)
            if (i // CHUNK) % 8 == 0:
                print(f"    {min(i + CHUNK, n_o):>5,}/{n_o:,}", flush=True)

        # Intrazonal diagonal, replacing whatever the graph search returned for
        # origin-to-itself (which is 0 by construction and is not a travel time).
        area = np.array([float(r["arealand_m2"] or 0) for r in cent])
        radius = np.sqrt(np.maximum(area, 1.0) / np.pi)
        mean_dist_m = (2.0 / 3.0) * radius
        intra_min = mean_dist_m / (MODE_MPH[mode] * 0.44704) / 60.0
        np.fill_diagonal(tt, intra_min.astype(np.float32))
        print(f"  intrazonal time: median {np.median(intra_min):.1f} min, "
              f"p90 {np.percentile(intra_min, 90):.1f}, "
              f"max {intra_min.max():.1f}")
        print(f"    {(intra_min > 10).sum():,} block groups cannot even be "
              f"crossed within the 10-minute band by this mode")

        np.save(INTERIM / f"tt_{mode}.npy", tt)
        finite = np.isfinite(tt)
        print(f"  reachable pairs within {MAX_MIN} min: "
              f"{finite.mean():.1%}")
        for band in (10, 20, 30, 40):
            reach = (tt <= band).sum(axis=1)
            print(f"    {band:>2} min   median {np.median(reach):>6,.0f} "
                  f"block groups reached")

    print("\nwrote tt_[drive|walk|bike].npy")


if __name__ == "__main__":
    main()
