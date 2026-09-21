"""Step 51 - what free-flow speeds are costing the answer.

THE WEAKNESS THIS CLOSES. Step 20's own docstring says it: "SPEEDS ARE
FREE-FLOW: posted limit where OSM has one, else a class default." Nobody drives
Tampa Bay at the posted limit at five o'clock. REPORT.md lists this among the
things that would move the result, predicts the DIRECTION, and says plainly
that the prediction is untested. This tests it.

It is also the experiment NREL ran for Delaware. Their 2030 scenario dropped
mean driving speed to 32.78 mph and statewide MEP fell 3.28% - "driven entirely
by network congestion", and enough to outweigh the projected growth in jobs and
land use. The same shape of question, on this network.

HOW CONGESTION IS APPLIED. A Travel Time Index: the ratio of peak travel time
to free-flow travel time, which is how FHWA's Urban Mobility Report states
congestion. TTI 1.30 means a trip takes 30% longer than it would on an empty
road. Applied to the DRIVE network only - walking and cycling are not delayed
by traffic, and transit is a schedule rather than a speed.

TTI is applied uniformly here, and that is a simplification worth naming: real
congestion falls hardest on urban arterials and barely touches rural roads, so
a uniform index understates the SPATIAL difference between a Hillsborough
origin and a Citrus one while getting the regional magnitude about right. A
per-class or per-link index would need a congested skim this project does not
have.

WHAT MOVES AND WHAT DOES NOT. Only drive travel times. The crash rates, the
networks, the opportunities and the population weights are untouched, so the
difference isolates congestion. Note both directions are reported: congestion
lowers the PUBLISHED score, and it also changes the crash-harm LOSS, because a
slower network reaches fewer opportunities to charge harm against.

Reads:  data/interim/graph_drive.npz, graph_nodes.npy, centroids.csv
Writes: data/final/congestion_scenario.csv
        data/interim/tt_drive_tti*.npy   (kept, so a run is reproducible)
"""
import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
OUT = FINAL / "congestion_scenario.csv"

# FHWA Urban Mobility Report territory. 1.15 is a mild peak, 1.30 is typical
# of a large US urban area, 1.50 is a bad peak in a congested one. Tampa is
# usually reported near the middle of that range.
TTIS = (1.15, 1.30, 1.50)
MAX_MIN = 40
CHUNK = 64
MAX_SNAP_M = 2_000


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, SRC / path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def drive_tt(tti, cent, nodes, opts, to_m):
    """Step 21's drive isochrone, with every arc slowed by `tti`."""
    z = np.load(INTERIM / "graph_drive.npz")
    G = csr_matrix((z["data"] * tti, z["indices"], z["indptr"]),
                   shape=tuple(z["shape"]))
    deg = np.diff(G.indptr) + np.bincount(G.indices, minlength=G.shape[0])
    usable = np.flatnonzero(deg > 0)
    tree = cKDTree(to_m(nodes[usable, 0], nodes[usable, 1]))
    dist, near = tree.query(opts, k=1)
    snap = usable[near]
    if int((dist > MAX_SNAP_M).sum()) > len(cent) * 0.02:
        sys.exit("FAIL: too many origins snap far from the drive network.")

    n_o = len(cent)
    tt = np.full((n_o, n_o), np.inf, dtype=np.float32)
    for i in range(0, n_o, CHUNK):
        d = dijkstra(G, directed=True, indices=snap[i:i + CHUNK],
                     limit=MAX_MIN * 60)
        tt[i:i + CHUNK] = (d[:, snap] / 60.0).astype(np.float32)
    # Intrazonal diagonal, same rule as step 21 - and it must slow too, or a
    # congested region gets instant access to its own block group.
    area = np.array([float(r["arealand_m2"] or 0) for r in cent])
    radius = np.sqrt(np.maximum(area, 1.0) / np.pi)
    intra = (2.0 / 3.0) * radius / (35.0 * 0.44704) / 60.0 * tti
    np.fill_diagonal(tt, intra.astype(np.float32))
    return tt


def main():
    v = load_mod("v26", "26_validate.py")

    cent = list(csv.DictReader(
        (INTERIM / "centroids.csv").open(encoding="utf8")))
    olat = np.array([float(r["lat"]) for r in cent])
    olon = np.array([float(r["lon"]) for r in cent])
    lat0 = np.radians(olat.mean())

    def to_m(la, lo):
        return np.column_stack([np.radians(lo) * 6_371_000 * np.cos(lat0),
                                np.radians(la) * 6_371_000])

    nodes = np.load(INTERIM / "graph_nodes.npy")
    opts = to_m(olat, olon)

    geoid, county, o, n = v.build()
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        popmap = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
    pop = np.array([popmap.get(g, 0.0) for g in geoid])
    r_drive, r_transit, R_WALK, R_BIKE = v.read_rates()

    rb = {r["GEOID20"]: r for r in csv.DictReader(
        (FINAL / "route_risk_by_origin.csv").open(encoding="utf8"))}
    bands = np.zeros((len(v.BANDS), n))
    for bi, b in enumerate(v.BANDS):
        for k, g in enumerate(geoid):
            s = rb.get(g, {}).get(f"r_band{b}", "")
            bands[bi, k] = float(s) if s else r_drive
    v.ROUTE_BANDS = bands
    real = {"drive": "route", "transit": r_transit,
            "walk": R_WALK[0], "bike": R_BIKE[0]}

    # Opportunity weights, rebuilt exactly as step 26 does, so the drive band
    # can be recomputed on a congested matrix without touching the other modes.
    rows = list(csv.DictReader(
        (INTERIM / "opportunities.csv").open(encoding="utf8")))
    acts = [c for c in rows[0] if c != "GEOID20"]
    pos = {g: i for i, g in enumerate(geoid)}
    O = np.zeros((n, len(acts)))
    for r in rows:
        i = pos.get(r["GEOID20"])
        if i is not None:
            for j, a in enumerate(acts):
                O[i, j] = float(r[a])
    fr = [r for r in csv.DictReader(
        (INTERIM / "activity_freq.csv").open(encoding="utf8"))
        if r["geography"] == "South Atlantic 2022"]
    f = np.array([float(next(x["f_share"] for x in fr if x["activity"] == a))
                  for a in acts])
    f /= f.sum()
    se = {r["activity"]: float(r["spatial_equivalency"]) for r in
          csv.DictReader(
              (INTERIM / "spatial_equivalency.csv").open(encoding="utf8"))}
    Ow = O @ (np.array([se[a] for a in acts]) * f)

    print("=" * 76)
    print("CONGESTION - what free-flow speeds are worth")
    print("=" * 76)
    base_pub = v.wmean(v.mep(o, n, {}), pop)
    base_harm = v.wmean(v.mep(o, n, real), pop)
    print(f"  {'scenario':<26}{'published':>11}{'with harm':>11}"
          f"{'loss':>8}{'vs free-flow':>14}")
    print(f"  {'free-flow (shipped)':<26}{base_pub:>11,.1f}"
          f"{base_harm:>11,.1f}{base_harm / base_pub - 1:>8.1%}{'':>14}")

    rows_out = [["scenario", "tti", "published", "with_harm", "loss",
                 "published_vs_freeflow"]]
    rows_out.append(["free_flow", "1.00", f"{base_pub:.4f}",
                     f"{base_harm:.4f}", f"{base_harm / base_pub - 1:.6f}",
                     "0"])

    for tti in TTIS:
        tag = str(tti).replace(".", "")
        tt = drive_tt(tti, cent, nodes, opts, to_m)
        np.save(INTERIM / f"tt_drive_tti{tag}.npy", tt)
        o2 = dict(o)
        o2["drive"] = np.array([(tt <= b) @ Ow for b in v.BANDS])
        pub = v.wmean(v.mep(o2, n, {}), pop)
        harm = v.wmean(v.mep(o2, n, real), pop)
        print(f"  {'TTI ' + str(tti):<26}{pub:>11,.1f}{harm:>11,.1f}"
              f"{harm / pub - 1:>8.1%}{pub / base_pub - 1:>13.2%}")
        rows_out.append([f"tti_{tag}", f"{tti}", f"{pub:.4f}", f"{harm:.4f}",
                         f"{harm / pub - 1:.6f}",
                         f"{pub / base_pub - 1:.6f}"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        csv.writer(fh).writerows(rows_out)
    print(f"\nwrote {OUT}")
    print("  NREL's Delaware 2030 scenario lost 3.28% of statewide MEP to")
    print("  congestion alone. Compare the last column against that.")


if __name__ == "__main__":
    main()
