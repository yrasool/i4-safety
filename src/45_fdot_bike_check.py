"""Step 45 - is the bike-lane tag right?  FDOT's inventory against OSM's.

WHY THIS EXISTS. Cycling supplies the largest single share of this project's
loss, and step 42 decides a major road's stress almost entirely on one OSM tag:

    cycleway = track|separate  -> low stress at ANY speed
    cycleway = lane            -> low stress if <= 35 mph and <= 4 lanes
    no cycleway tag            -> low stress only if <= 25 mph and <= 2 lanes

So a 40 mph four-lane arterial is HIGH stress without the tag and LOW stress
with it. The tag is there because a volunteer added it. FDOT's Roadway
Characteristics Inventory is the state's own record of what it built. Every
other input to this project has an external check; the one that moves the
answer most had none. This is that check.

WHAT IT MEASURES, AND WHAT IT DOES NOT. Not "is OSM wrong" - the two describe
different things. FDOT inventories the state-maintained system; OSM holds every
road, including the city and county streets FDOT never records. So a lane FDOT
has and OSM lacks is a probable OSM gap, while a lane OSM has and FDOT lacks is
usually a local facility outside FDOT's remit. Both directions are reported,
separately, in miles, and neither is called an error on its own.

METHOD. FDOT polylines are densified to a point every DENSIFY_M metres, each
carrying the local bearing. Each OSM way segment is matched to the nearest FDOT
point within TOL_M, and accepted only if the two bearings agree within
BEARING_TOL degrees modulo 180. Without the bearing test a cross street passing
under an arterial matches it, which would inflate agreement. Coordinates are
projected to metres on a local equirectangular grid centred on the region; over
five counties the scale error is far below the tolerance.

ONLY MAJOR ROADS ARE COMPARED. On a local street the cycleway tag does not
change step 42's classification - speed decides - so a disagreement there
cannot move the model. Restricting to the classes where the tag is load-bearing
is what makes the count mean something.

Reads:  data/raw/fdot_bikeped/bike_lane_tda_d7.geojson,
        data/raw/osm/tile_*.json.gz (step 19), data/raw/osm_lts/ (step 41)
Writes: data/final/fdot_bike_check.csv
"""
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]

OSM = ROOT / "data" / "raw" / "osm"
LTS_TILES = ROOT / "data" / "raw" / "osm_lts"
FDOT = ROOT / "data" / "raw" / "fdot_bikeped" / "bike_lane_tda_d7.geojson"
OUT = ROOT / "data" / "final" / "fdot_bike_check.csv"
GAP_OUT = ROOT / "data" / "interim" / "fdot_lane_gap_ways.txt"

DENSIFY_M = 10.0        # spacing of FDOT sample points
TOL_M = 25.0            # how far an OSM segment may sit from an FDOT lane
BEARING_TOL = 30.0      # degrees, modulo 180
LAT0, LON0 = 28.2, -82.5
M_PER_DEG = 111_320.0

# the classes where the cycleway tag decides the answer - step 42's MAJOR_SPEED
MAJOR = ("trunk", "trunk_link", "primary", "primary_link",
         "secondary", "secondary_link", "tertiary", "tertiary_link")


def to_m(lon, lat):
    return ((lon - LON0) * M_PER_DEG * math.cos(math.radians(LAT0)),
            (lat - LAT0) * M_PER_DEG)


def bearing(dx, dy):
    return math.degrees(math.atan2(dy, dx)) % 180.0


def densify(coords):
    """Line vertices -> points every DENSIFY_M metres, with local bearing."""
    pts, brs = [], []
    for (x1, y1), (x2, y2) in zip(coords[:-1], coords[1:]):
        dx, dy = x2 - x1, y2 - y1
        d = math.hypot(dx, dy)
        if d == 0:
            continue
        b = bearing(dx, dy)
        n = max(int(d // DENSIFY_M), 1)
        for k in range(n + 1):
            f = k * DENSIFY_M / d
            if f > 1:
                break
            pts.append((x1 + dx * f, y1 + dy * f))
            brs.append(b)
    return pts, brs


def load_fdot():
    if not FDOT.exists():
        sys.exit(f"FAIL: {FDOT.name} missing. Fetch the FDOT bike layers first.")
    gj = json.loads(FDOT.read_text(encoding="utf8"))
    pts, brs, miles = [], [], 0.0
    for f in gj["features"]:
        g = f.get("geometry") or {}
        parts = g.get("coordinates") or []
        if g.get("type") == "LineString":
            parts = [parts]
        for line in parts:
            c = [to_m(p[0], p[1]) for p in line]
            if len(c) < 2:
                continue
            miles += sum(math.dist(a, b)
                         for a, b in zip(c[:-1], c[1:])) / 1609.344
            p, b = densify(c)
            pts += p
            brs += b
    if not pts:
        sys.exit("FAIL: no FDOT geometry parsed.")
    return np.asarray(pts), np.asarray(brs), miles


def fingerprint(c):
    # steps 20 and 42 use this same key; kept identical on purpose
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


def osm_has_lane(t):
    """Exactly what step 42 reads. Returns 'protected', 'painted' or ''."""
    keys = ("cycleway", "cycleway:both", "cycleway:left", "cycleway:right")
    cw = {str((t or {}).get(k, "")).lower() for k in keys}
    if cw & {"track", "separate"}:
        return "protected"
    if "lane" in cw:
        return "painted"
    return ""


def compare(tree, fbrs, tags):
    tiles = sorted(OSM.glob("tile_*.json.gz"))
    if not tiles:
        sys.exit("FAIL: no OSM tiles. Run 19_fetch_osm.py first.")
    seen, gap = set(), set()
    m = {(a, b): 0.0
         for a in ("protected", "painted", "none")
         for b in ("lane", "no lane")}
    for t in tiles:
        for w in json.loads(gzip.decompress(t.read_bytes())):
            if w["h"] not in MAJOR:
                continue
            fp = fingerprint(w["c"])
            if fp in seen:          # tiles overlap; same dedupe as step 20
                continue
            seen.add(fp)
            osm = osm_has_lane(tags.get(fp)) or "none"
            # THE TWO SOURCES ORDER COORDINATES OPPOSITELY. FDOT's GeoJSON is
            # [lon, lat]; the OSM tiles steps 19-20 write are [lat, lon]. Read
            # the same way, every OSM road lands in the Indian Ocean and the
            # comparison returns zero matches over 1,782 miles of bike lane -
            # which is what this file printed, without error, the first time.
            c = [to_m(p[1], p[0]) for p in w["c"]]
            for a, b in zip(c[:-1], c[1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                d = math.hypot(dx, dy)
                if d == 0:
                    continue
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                br = bearing(dx, dy)
                hit = False
                for i in tree.query_ball_point(mid, TOL_M):
                    diff = abs(br - fbrs[i])
                    if min(diff, 180 - diff) <= BEARING_TOL:
                        hit = True
                        break
                m[(osm, "lane" if hit else "no lane")] += d / 1609.344
                if osm == "none" and hit:
                    gap.add(fp)
    print(f"  major OSM ways compared: {len(seen):,}")
    print(f"  ways FDOT records a lane on and OSM does not tag: {len(gap):,}")
    # WRITTEN SO THE SCENARIO CAN USE IT. These are the ways where the state
    # says a bike lane exists and the tag is missing, which is the difference
    # between step 42 calling the road high stress and low stress. Step 42
    # reads this file to build the `lts_fdot` network.
    GAP_OUT.parent.mkdir(parents=True, exist_ok=True)
    with GAP_OUT.open("w", encoding="utf8") as fh:
        for f in sorted(gap):
            fh.write(f"{f}\n")
    print(f"  wrote {GAP_OUT.name}")
    return m


def report(m, fdot_miles):
    tot = sum(m.values())
    osm_any = sum(v for (o, _), v in m.items() if o != "none")
    fdot_any = sum(v for (_, f), v in m.items() if f == "lane")
    both = sum(v for (o, f), v in m.items() if o != "none" and f == "lane")

    print(f"\nMAJOR-ROAD MILES COMPARED: {tot:,.0f}\n")
    print(f"  {'OSM says':<12}{'FDOT: lane':>14}{'FDOT: no lane':>16}")
    for o in ("protected", "painted", "none"):
        print(f"  {o:<12}{m[(o, 'lane')]:>14,.0f}{m[(o, 'no lane')]:>16,.0f}")
    print(f"\n  both agree a lane exists          {both:>9,.0f} mi")
    print(f"  OSM only, FDOT has none           {osm_any - both:>9,.0f} mi"
          f"   (local facility, or an OSM error)")
    print(f"  FDOT only, OSM untagged           {fdot_any - both:>9,.0f} mi"
          f"   (probable OSM gap)")
    if fdot_any:
        print(f"\n  FDOT lane miles OSM also tags:    {both / fdot_any:>9.1%}")
    print("\n  A mile in the last row is a road step 42 may be calling HIGH")
    print("  stress that the state records as having a bike lane. That is the")
    print("  direction which would make the cycling loss too large.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        fh.write("osm,fdot,miles\n")
        for (o, f), v in sorted(m.items()):
            fh.write(f"osm_{o},fdot_{f.replace(' ', '_')},{v:.2f}\n")
        fh.write(f"summary,fdot_total_centreline_miles,{fdot_miles:.2f}\n")
        fh.write(f"summary,major_road_miles_compared,{tot:.2f}\n")
        fh.write(f"summary,agreed_lane_miles,{both:.2f}\n")
    print(f"\nwrote {OUT}")


def check_overlap(fpts, tags):
    """The two sides must occupy the same patch of ground before any distance
    is computed. A silent axis swap is the failure this guards: it produces a
    complete, plausible table of zeros rather than an error."""
    tile = sorted(OSM.glob("tile_*.json.gz"))[0]
    w = json.loads(gzip.decompress(tile.read_bytes()))[0]
    o = np.asarray([to_m(p[1], p[0]) for p in w["c"]])
    lo, hi = fpts.min(0) - 200_000, fpts.max(0) + 200_000
    if not (np.all(o.min(0) > lo) and np.all(o.max(0) < hi)):
        sys.exit("FAIL: OSM ways fall outside the FDOT extent by more than "
                 "200 km. Check the coordinate order on both sides - FDOT "
                 "GeoJSON is [lon, lat], the OSM tiles are [lat, lon].")


def main():
    fpts, fbrs, fdot_miles = load_fdot()
    print(f"FDOT bike lanes: {len(fpts):,} sample points, "
          f"{fdot_miles:,.0f} centreline miles")
    tags = load_lts_tags()
    check_overlap(fpts, tags)
    tree = cKDTree(fpts)
    report(compare(tree, fbrs, tags), fdot_miles)


if __name__ == "__main__":
    main()
