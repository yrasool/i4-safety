"""
Turn the OSM extract into a compact, pre-projected scene payload.

Projection happens here rather than in the browser so the page ships numbers it
can draw directly. Local metres, corridor centred, Y up, so the scene is in the
same space as the crash markers.

Roads keep their class and lane count because the point of zooming in is to see
that a ramp is a ramp: a one-lane motorway_link peeling off a four-lane
carriageway should look like that, not like two identical strokes.
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OSM = os.path.join(HERE, "corridor_osm.json")
CRASHES = os.path.join(HERE, "i4_crashes_3d.json")
OUT = os.path.join(HERE, "corridor_scene.json")

UNIT = 0.1          # 1 scene unit = 10 m, matching the existing crash scene

# Road classes, ordered by how wide they draw. Width is in scene units.
ROAD_CLASS = {
    "motorway":       {"w": 1.55, "z": 6, "k": "mainline"},
    "motorway_link":  {"w": 0.85, "z": 5, "k": "ramp"},
    "trunk":          {"w": 1.25, "z": 4, "k": "major"},
    "trunk_link":     {"w": 0.75, "z": 4, "k": "ramp"},
    "primary":        {"w": 1.05, "z": 4, "k": "major"},
    "primary_link":   {"w": 0.7,  "z": 4, "k": "ramp"},
    "secondary":      {"w": 0.9,  "z": 3, "k": "major"},
    "secondary_link": {"w": 0.65, "z": 3, "k": "ramp"},
    "tertiary":       {"w": 0.75, "z": 3, "k": "minor"},
    "tertiary_link":  {"w": 0.6,  "z": 3, "k": "ramp"},
    "residential":    {"w": 0.5,  "z": 2, "k": "local"},
    "unclassified":   {"w": 0.45, "z": 2, "k": "local"},
    "service":        {"w": 0.26, "z": 1, "k": "service"},
}


def main():
    with open(OSM, encoding="utf-8") as fh:
        els = json.load(fh)["elements"]
    with open(CRASHES, encoding="utf-8") as fh:
        crashes = json.load(fh)

    # Centre on the crash extent so roads and markers share an origin.
    lats = [c["lat"] for c in crashes]
    lons = [c["lon"] for c in crashes]
    lat0 = (min(lats) + max(lats)) / 2
    lon0 = (min(lons) + max(lons)) / 2
    m_lat = 111320.0
    m_lon = 111320.0 * math.cos(math.radians(lat0))

    def proj(lon, lat):
        return [round((lon - lon0) * m_lon * UNIT, 2),
                round(-(lat - lat0) * m_lat * UNIT, 2)]

    roads, buildings, water, land = [], [], [], []

    for e in els:
        t = e.get("tags") or {}
        geom = e.get("geometry")
        if not geom or len(geom) < 2:
            continue
        pts = [proj(n["lon"], n["lat"]) for n in geom]

        hw = t.get("highway")
        if hw and hw in ROAD_CLASS:
            spec = ROAD_CLASS[hw]
            lanes = t.get("lanes")
            try:
                lanes = int(str(lanes).split(";")[0])
            except (TypeError, ValueError):
                lanes = None
            # A carriageway with more lanes really is wider; scale gently so a
            # 4-lane motorway does not swamp everything around it.
            w = spec["w"] * (1.0 + 0.16 * ((lanes or 2) - 2)) if lanes else spec["w"]
            roads.append({
                "p": pts, "w": round(max(0.2, w), 2), "z": spec["z"],
                "k": spec["k"],
                "n": t.get("name") or t.get("ref") or "",
                "b": t.get("bridge") == "yes",
            })
            continue

        if t.get("building"):
            closed = pts[0] == pts[-1]
            ring = pts[:-1] if closed else pts
            if len(ring) < 3:
                continue
            h = None
            if t.get("height"):
                try:
                    h = float(str(t["height"]).replace("m", "").strip())
                except ValueError:
                    h = None
            if h is None and t.get("building:levels"):
                try:
                    h = float(t["building:levels"]) * 3.2
                except ValueError:
                    h = None
            if h is None:
                h = 4.5
            buildings.append({"p": ring, "h": round(h * UNIT, 2)})
            continue

        if t.get("natural") == "water" or t.get("waterway") == "riverbank":
            ring = pts[:-1] if pts[0] == pts[-1] else pts
            if len(ring) >= 3:
                water.append({"p": ring})
            continue

        if t.get("landuse"):
            ring = pts[:-1] if pts[0] == pts[-1] else pts
            if len(ring) >= 3:
                land.append({"p": ring, "t": t["landuse"]})

    # crash markers, in the same projected space
    marks = []
    for c in crashes:
        x, z = proj(c["lon"], c["lat"])
        marks.append({**{k: c[k] for k in
                         ("id","k","f","n","sev","dir","yr","dt","typ","hrm",
                          "lgt","surf","mp","veh","inj","cmv","spd","ldp")},
                      "x": x, "z": z})

    xs = [p[0] for r in roads for p in r["p"]]
    zs = [p[1] for r in roads for p in r["p"]]
    scene = {
        "roads": roads, "buildings": buildings, "water": water, "land": land,
        "marks": marks,
        # The projection origin and metres-per-degree, so anything else that has
        # to line up with this scene - basemap imagery especially - can be placed
        # by computation instead of nudged by eye.
        "origin": {"lat0": lat0, "lon0": lon0,
                   "mLat": m_lat, "mLon": m_lon, "unit": UNIT},
        "bbox": {"x0": min(xs), "x1": max(xs), "z0": min(zs), "z1": max(zs)},
        "meta": {
            "n": len(marks),
            "coords": len({(m["x"], m["z"]) for m in marks}),
            "tallest": max(m["n"] for m in marks),
            "stacked": sum(1 for m in marks if m["n"] > 1),
        },
    }

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(scene, fh, separators=(",", ":"))

    byk = {}
    for r in roads:
        byk[r["k"]] = byk.get(r["k"], 0) + 1
    print(f"roads      {len(roads):,}  {byk}")
    print(f"buildings  {len(buildings):,}")
    print(f"water      {len(water):,}   landuse {len(land):,}")
    print(f"marks      {len(marks):,}")
    print(f"extent     {scene['bbox']['x1']-scene['bbox']['x0']:.0f} x "
          f"{scene['bbox']['z1']-scene['bbox']['z0']:.0f} units "
          f"({(scene['bbox']['x1']-scene['bbox']['x0'])*10/1000:.1f} km long)")
    print(f"\nWrote {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
