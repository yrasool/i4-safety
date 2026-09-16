"""
Step 43 - is low-stress cycling in Tampa Bay really a set of islands, and where?

WHY THIS EXISTS. Step 42 found that strict low-stress bike reach falls from 162
block groups in 40 minutes to 3, and the explanation offered was that suburban
subdivisions connect only to arterials. That explanation fitted the numbers but
was not measured. This step measures it, two ways, and splits both by county.

  1. ISLANDS. Connected components of the bike network. If the explanation is
     right, removing high-stress roads should shatter one connected network into
     many small pieces, and a block group should find few others in its piece.

  2. SHORT HOPS REJOIN THEM. If the pieces are separated by a block or so of
     arterial - the subdivision pattern - then adding back only high-stress edges
     of 250 m or less should merge most of them again. If the pieces are instead
     separated by long stretches (rivers, interstates, rural gaps), short hops
     will not help, and the explanation is wrong.

And the county split of the MEP drop under all three bike networks, because a
regional average can hide an older grid city and a new suburb pulling in
opposite directions.

Reads:  data/interim/graph_bike.npz, graph_bike_lts.npz, graph_bike_lts_connect.npz,
        graph_nodes.npy, centroids.csv, acs_blockgroups.csv
        MEP_DUMP arrays produced here by running step 23 three ways
Writes: data/final/bike_islands_by_county.csv
"""

import csv
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
COUNTIES = ("Hillsborough", "Pinellas", "Pasco", "Hernando", "Citrus")
MAX_SNAP_M = 2_000


def load(name):
    z = np.load(INTERIM / f"graph_{name}.npz")
    return csr_matrix((z["data"], z["indices"], z["indptr"]),
                      shape=tuple(z["shape"]))


def main():
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    olat = np.array([float(r["lat"]) for r in cent])
    olon = np.array([float(r["lon"]) for r in cent])
    county = np.array([r["county"] for r in cent])
    geoid = [r["GEOID20"] for r in cent]
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        popmap = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
    pop = np.array([popmap.get(g, 0.0) for g in geoid])
    nodes = np.load(INTERIM / "graph_nodes.npy")
    lat0 = np.radians(olat.mean())

    def to_m(la, lo):
        return np.column_stack([np.radians(lo) * 6_371_000 * np.cos(lat0),
                                np.radians(la) * 6_371_000])

    rows = []
    print(f"{'network':<22}{'islands with a BG':>18}{'BGs alone':>11}"
          f"{'median BGs in own island':>26}")
    stats = {}
    for name, label in (("bike", "any road"),
                        ("bike_lts_connect", "realistic"),
                        ("bike_lts", "strict")):
        G = load(name)
        n = G.shape[0]
        ncomp, comp = connected_components(G, directed=False)
        deg = np.diff(G.indptr) + np.bincount(G.indices, minlength=n)
        usable = np.flatnonzero(deg > 0)
        dist, near = cKDTree(to_m(nodes[usable, 0], nodes[usable, 1])).query(
            to_m(olat, olon), k=1)
        c = comp[usable[near]].astype(np.int64)
        c[dist > MAX_SNAP_M] = -1 - np.arange((dist > MAX_SNAP_M).sum())
        ids, sizes = np.unique(c, return_counts=True)
        size_of = dict(zip(ids.tolist(), sizes.tolist()))
        island = np.array([size_of[x] for x in c])
        stats[label] = island
        print(f"{label:<22}{len(ids):>18,}{(island == 1).sum():>11,}"
              f"{np.median(island):>26,.0f}")

    # does allowing short hops rejoin what strict removal split apart?
    strict, realistic, anyroad = (stats["strict"], stats["realistic"],
                                  stats["any road"])
    print(f"\n  block groups in an island of 10 or fewer:  "
          f"strict {(strict <= 10).mean():.1%}   realistic "
          f"{(realistic <= 10).mean():.1%}   any road {(anyroad <= 10).mean():.1%}")

    # ---- MEP by county under three bike networks ------------------------
    dumps = {}
    for label, env in (("any road", "any"), ("realistic", "lts_connect"),
                       ("strict", "lts")):
        tmp = Path(tempfile.gettempdir()) / f"mep43_{env}.npz"
        e = dict(os.environ, MEP_BIKE_NETWORK=env, MEP_DUMP=str(tmp),
                 PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "src" / "23_mep.py")],
                           env=e, capture_output=True, text=True)
        if not tmp.exists():
            print(r.stdout[-1500:], r.stderr[-1500:])
            sys.exit(f"FAIL: step 23 did not dump arrays for '{label}'.")
        dumps[label] = np.load(tmp)

    print(f"\n  {'county':<14}{'pop':>11}"
          f"{'drop: any road':>16}{'realistic':>11}{'strict':>9}"
          f"{'bike reach kept':>17}{'median island':>15}")
    full_tt = np.load(INTERIM / "tt_bike.npy")
    conn_tt = np.load(INTERIM / "tt_bike_lts_connect.npy")
    for cn in COUNTIES + ("REGION",):
        m = np.ones(len(county), bool) if cn == "REGION" else county == cn
        drops = []
        for label in ("any road", "realistic", "strict"):
            d = dumps[label]
            b, lo = d["base"][m], d["lo"][m]
            w = pop[m]
            drops.append(1 - np.sum(lo * w) / np.sum(b * w))
        kept = (np.median((conn_tt[m] <= 40).sum(1))
                / max(np.median((full_tt[m] <= 40).sum(1)), 1))
        print(f"  {cn:<14}{pop[m].sum():>11,.0f}{drops[0]:>16.1%}"
              f"{drops[1]:>11.1%}{drops[2]:>9.1%}{kept:>17.0%}"
              f"{np.median(strict[m]):>15,.0f}")
        rows.append([cn, int(pop[m].sum()), f"{drops[0]:.4f}",
                     f"{drops[1]:.4f}", f"{drops[2]:.4f}", f"{kept:.4f}",
                     int(np.median(strict[m])),
                     f"{(strict[m] <= 10).mean():.4f}"])

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "bike_islands_by_county.csv").open("w", newline="",
                                                     encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["county", "population", "drop_any_road", "drop_realistic",
                    "drop_strict", "bike_reach_kept_realistic",
                    "median_island_strict", "share_island_le10_strict"])
        w.writerows(rows)
    print(f"\nwrote {FINAL / 'bike_islands_by_county.csv'}")


if __name__ == "__main__":
    main()
