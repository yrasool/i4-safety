"""
Step 30 - place-varying crash risk. The half that makes the map real.

Step 29 gives every FDOT segment its own Empirical-Bayes crash cost per
passenger-mile, and they span a factor of 8 from p10 to p90. Step 23 still
applies ONE regional number to every block group, which is why step 26 proves
the surface is an identity: four scalars cannot make a map.

This step attaches the segments to origins.

WEIGHTING, AND WHY IT IS NOT A SIMPLE AVERAGE INSIDE A BAND.
A 40-minute drive from almost anywhere in Tampa Bay reaches almost the same
road network, so an unweighted mean over an isochrone returns nearly the same
number everywhere and the identity survives in all but name. Nearby roads have
to count for more, and MEP already says by how much: its own time decay.

    r_i = SUM_s  VMT_s * exp(BETA * t_is) * r_s
        / SUM_s  VMT_s * exp(BETA * t_is)

`exp(BETA*t)` is the same discount MEP applies to distant opportunities, with
the same BETA. Weighting by VMT as well means a busy arterial counts for more
than a quiet one, which is what "the roads you actually use" means in the
absence of an assignment model.

THIS IS AN APPROXIMATION AND THE HONEST NAME FOR IT IS EXPOSURE-WEIGHTED
PROXIMITY, NOT ROUTE ASSIGNMENT. A real assignment would route each
origin-destination pair over the network and accumulate risk along the path
actually taken. That needs an OD matrix this project does not have. What this
does capture is the thing that varies: whether the roads near you are the ones
that kill people.

TRAVEL TIME TO A SEGMENT is taken as the drive time to the block group holding
the segment's midpoint, from `tt_drive.npy`. Segment midpoints are matched to
the nearest block group centroid.

Writes: data/final/origin_risk.csv
"""

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import BETA, USER_AGENT, COUNTIES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
RAW = ROOT / "data" / "raw"
RCI = "https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/FeatureServer/0"
COUNTY_DOT = {"10": "Hillsborough", "15": "Pinellas", "14": "Pasco",
              "08": "Hernando", "02": "Citrus"}
GEOM_CACHE = RAW / "fdot_segment_geometry.json"


def fetch_geometry():
    """Segment centroids, keyed by (roadway, begin_post, end_post)."""
    if GEOM_CACHE.exists():
        return json.loads(GEOM_CACHE.read_text())
    where = "COUNTYDOT IN (" + ",".join(f"'{c}'" for c in COUNTY_DOT) + ")"
    rows, off = {}, 0
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
        for f in feats:
            a = f["attributes"]
            paths = (f.get("geometry") or {}).get("paths") or []
            pts = [p for path in paths for p in path]
            if not pts:
                continue
            # Midpoint by vertex count is close enough for a block-group match;
            # these segments average 1.5 miles and block groups are larger.
            lon = float(np.mean([p[0] for p in pts]))
            lat = float(np.mean([p[1] for p in pts]))
            key = f"{a['ROADWAY']}|{a['BEGIN_POST']}|{a['END_POST']}"
            rows[key] = [lat, lon]
        off += len(feats)
        print(f"    {off:,} segment geometries", flush=True)
        if not d.get("exceededTransferLimit"):
            break
    GEOM_CACHE.parent.mkdir(parents=True, exist_ok=True)
    GEOM_CACHE.write_text(json.dumps(rows))
    return rows


def main():
    with (FINAL / "segment_eb.csv").open(encoding="utf8") as fh:
        segs = list(csv.DictReader(fh))
    print(f"{len(segs):,} segments with EB rates")

    print("fetching FDOT segment geometry")
    geom = fetch_geometry()
    print(f"  {len(geom):,} geometries cached")

    lat, lon, r_s, vmt_s, matched = [], [], [], [], 0
    for s in segs:
        key = f"{s['roadway']}|{float(s['begin_post'])}|{float(s['end_post'])}"
        g = geom.get(key)
        if g is None:
            continue
        matched += 1
        lat.append(g[0])
        lon.append(g[1])
        r_s.append(float(s["r_per_pmt"]))
        vmt_s.append(float(s["vmt_period"]))
    lat = np.array(lat); lon = np.array(lon)
    r_s = np.array(r_s); vmt_s = np.array(vmt_s)
    print(f"  {matched:,} of {len(segs):,} segments matched to a geometry "
          f"({matched / len(segs):.1%})")
    if matched < 0.8 * len(segs):
        sys.exit("FAIL: fewer than 80% of segments have geometry. The join key "
                 "(roadway|begin|end) is not matching; check float formatting.")

    # --- attach segments to block groups ------------------------------------
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    olat = np.array([float(c["lat"]) for c in cent])
    olon = np.array([float(c["lon"]) for c in cent])
    n = len(cent)

    lat0 = np.radians(olat.mean())
    to_m = lambda la, lo: np.column_stack(
        [np.radians(lo) * 6_371_000 * np.cos(lat0),
         np.radians(la) * 6_371_000])
    tree = cKDTree(to_m(olat, olon))
    dist, bg_of_seg = tree.query(to_m(lat, lon), k=1)
    print(f"  segment midpoint to nearest block group centroid: "
          f"median {np.median(dist):,.0f} m, p90 {np.percentile(dist, 90):,.0f} m")

    # --- weighted risk per origin -------------------------------------------
    T = np.load(INTERIM / "tt_drive.npy")          # minutes, origins x origins
    t_is = T[:, bg_of_seg]                          # time from each origin
    decay = np.exp(BETA * t_is)                     # MEP's own time discount
    decay[~np.isfinite(t_is)] = 0.0

    w = decay * vmt_s[None, :]
    denom = w.sum(axis=1)
    r_i = np.divide((w * r_s[None, :]).sum(axis=1), denom,
                    out=np.zeros(n), where=denom > 0)

    reachable = (np.isfinite(t_is)).sum(axis=1)
    print(f"\n  origins with at least one reachable segment: "
          f"{(denom > 0).sum():,} of {n:,}")
    print(f"  segments reachable per origin: median {np.median(reachable):,.0f}"
          f" of {matched:,}")

    ok = denom > 0
    print(f"\nPLACE-VARYING r_drive")
    print(f"  median   ${np.median(r_i[ok]):.4f}")
    print(f"  p10      ${np.percentile(r_i[ok], 10):.4f}")
    print(f"  p90      ${np.percentile(r_i[ok], 90):.4f}")
    print(f"  min-max  ${r_i[ok].min():.4f} to ${r_i[ok].max():.4f}")
    print(f"  spread   {np.percentile(r_i[ok], 90) / np.percentile(r_i[ok], 10):.2f}x "
          f"p90 over p10")

    # The regional figure this must stay near, or the weighting is distorting.
    with (FINAL / "injury_cost_by_mode.csv").open(encoding="utf8") as fh:
        r_reg = float(next(x["cost_per_pmt"] for x in csv.DictReader(fh)
                           if x["mode"] == "vehicle_occupant"))
    print(f"\n  regional r_drive  ${r_reg:.4f}")
    print(f"  mean of r_i       ${r_i[ok].mean():.4f}   "
          f"{r_i[ok].mean() / r_reg:.2f}x")

    # A DEGENERATE RESULT IS THE FAILURE MODE HERE. If every origin gets nearly
    # the same number, r has not become spatial and the identity survives with
    # extra steps. Say so rather than shipping a map that only looks varied.
    cv = r_i[ok].std() / r_i[ok].mean()
    print(f"\n  coefficient of variation {cv:.3f}")
    if cv < 0.05:
        print(f"  WARNING: r_i is nearly constant across origins. The time "
              f"decay is not\n  separating places, so substituting this will "
              f"NOT break the identity.")
    else:
        print(f"  r_i genuinely varies by place, so substituting it into MEP "
              f"gives the\n  cost term a spatial component it did not have. "
              f"Step 26 Test 1 decides\n  whether that is enough to break the "
              f"identity.")

    by_county = {}
    for i, c in enumerate(cent):
        if ok[i]:
            by_county.setdefault(c["county"], []).append(r_i[i])
    print(f"\n  {'county':<15}{'median r_i':>12}{'p10':>10}{'p90':>10}")
    for c in sorted(by_county):
        v = np.array(by_county[c])
        print(f"  {c:<15}{np.median(v):>12.4f}{np.percentile(v, 10):>10.4f}"
              f"{np.percentile(v, 90):>10.4f}")

    with (FINAL / "origin_risk.csv").open("w", newline="",
                                          encoding="utf8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["GEOID20", "county", "r_drive_local",
                      "segments_reachable"])
        for i, c in enumerate(cent):
            wtr.writerow([c["GEOID20"], c["county"],
                          f"{r_i[i]:.6f}" if ok[i] else "",
                          int(reachable[i])])
    print(f"\nwrote {FINAL / 'origin_risk.csv'}")


if __name__ == "__main__":
    main()
