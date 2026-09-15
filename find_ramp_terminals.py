"""
Find the at-grade ramp terminal intersections - the surface intersections where
each ramp meets the cross street. Those are the points to centre a 250 ft radius
on when counting intersection crashes.

Method: a ramp (highway=motorway_link) has two ends. One end merges with the
freeway; the other lands at the cross street. Take every ramp endpoint and keep
the ones that are far from the motorway centerline - those are the terminals.
Cluster the survivors so both directions of a ramp pair collapse to one point.

Reads the Overpass cache written by auto_classify_ramps.py.
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "osm_ramps_cache.json")
OUT = os.path.join(HERE, "ramp_terminals.json")

LAT0 = 28.026
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))

# An endpoint this far from the freeway is a surface terminal, not a merge.
MIN_DIST_FROM_FREEWAY_M = 60.0
# Endpoints closer together than this describe the same intersection.
CLUSTER_RADIUS_M = 120.0


def to_m(lon, lat):
    return (lon * M_PER_DEG_LON, lat * M_PER_DEG_LAT)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def nearest(pt, lines):
    px, py = pt
    best = float("inf")
    for pts in lines:
        for i in range(len(pts) - 1):
            d = seg_dist(px, py, *pts[i], *pts[i + 1])
            if d < best:
                best = d
    return best


def main():
    if not os.path.exists(CACHE):
        raise SystemExit("Run auto_classify_ramps.py first to build the OSM cache.")

    with open(CACHE, encoding="utf-8") as fh:
        payload = json.load(fh)

    motorway, links = [], []
    for el in payload.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        geom = [(n["lon"], n["lat"]) for n in el["geometry"]]
        if len(geom) < 2:
            continue
        tag = el.get("tags", {}).get("highway")
        if tag == "motorway":
            motorway.append([to_m(*g) for g in geom])
        elif tag == "motorway_link":
            links.append((el.get("tags", {}), geom))

    # Candidate terminals: ramp endpoints that are well clear of the freeway.
    cands = []
    for tags, geom in links:
        for lon, lat in (geom[0], geom[-1]):
            d = nearest(to_m(lon, lat), motorway)
            if d >= MIN_DIST_FROM_FREEWAY_M:
                cands.append({"lon": lon, "lat": lat, "d_freeway_m": round(d, 1),
                              "ref": tags.get("ref") or tags.get("name") or ""})

    # Collapse endpoints that describe the same physical intersection.
    clusters = []
    for c in cands:
        cm = to_m(c["lon"], c["lat"])
        for cl in clusters:
            if math.hypot(cm[0] - cl["m"][0], cm[1] - cl["m"][1]) < CLUSTER_RADIUS_M:
                cl["members"].append(c)
                n = len(cl["members"])
                cl["lat"] += (c["lat"] - cl["lat"]) / n
                cl["lon"] += (c["lon"] - cl["lon"]) / n
                cl["m"] = to_m(cl["lon"], cl["lat"])
                break
        else:
            clusters.append({"lat": c["lat"], "lon": c["lon"], "m": cm,
                             "members": [c]})

    # West to east, and name them after the nearer interchange.
    clusters.sort(key=lambda c: c["lon"])
    out = []
    for i, cl in enumerate(clusters, 1):
        side = "McIntosh Rd" if cl["lon"] < -82.215 else "Branch Forbes Rd"
        out.append({
            "name": f"{side} terminal {i}",
            "lat": round(cl["lat"], 7),
            "lon": round(cl["lon"], 7),
            "ramps": len(cl["members"]),
        })

    print(f"{len(cands)} candidate endpoints -> {len(out)} terminal intersections\n")
    for t in out:
        print(f"  {t['name']:28s} {t['lat']:.7f}, {t['lon']:.7f}   "
              f"({t['ramps']} ramp ends)")

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
