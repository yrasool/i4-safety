"""
Classify each I-4 crash as mainline or ramp from geometry alone, then score the
result against the hand-built lists in the notebook.

The idea is what every GIS package calls a spatial join. OpenStreetMap tags
through carriageways as highway=motorway and ramps as highway=motorway_link.
For each crash, measure the distance to the nearest line of each kind. Whichever
is closer is what the vehicle was on.

No API key, no shapely. Overpass responses are cached so re-runs are free.

READ-ONLY on D:. Reads the cleaned crash file, writes everything here.

Run:
    python auto_classify_ramps.py
"""

import json
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# Source lives on the SeeDrive and is never written to.
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"

CACHE = os.path.join(HERE, "osm_ramps_cache.json")
OUT_XLSX = os.path.join(HERE, "I4_AutoClassified.xlsx")
OUT_REVIEW = os.path.join(HERE, "I4_NeedsReview.xlsx")

# Generous around the study area so ramps are captured whole, not clipped.
BBOX = (28.015, -82.265, 28.042, -82.170)  # south, west, north, east

# Public instances rate-limit and periodically 504. Try them in turn.
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

QUERY = f"""
[out:json][timeout:90];
(
  way["highway"="motorway"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  way["highway"="motorway_link"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out geom;
"""

# Anything closer than this to the decision boundary is a coin flip given how
# crash coordinates are geocoded, so it gets sent to a human instead.
REVIEW_MARGIN_M = 10.0

# Local flat-earth projection. Over a 6 km corridor the error is well under a
# metre, far finer than the geocoding precision of the crash data itself.
LAT0 = 28.026
M_PER_DEG_LAT = 111_320.0
M_PER_DEG_LON = 111_320.0 * math.cos(math.radians(LAT0))


def to_m(lon, lat):
    """Longitude/latitude in degrees to a local metre grid."""
    return (lon * M_PER_DEG_LON, lat * M_PER_DEG_LAT)


def fetch_osm():
    """Ramp and mainline geometry from Overpass, cached to disk."""
    if os.path.exists(CACHE):
        print(f"Using cached OSM extract ({CACHE})")
        with open(CACHE, encoding="utf-8") as fh:
            return json.load(fh)

    data = urllib.parse.urlencode({"data": QUERY}).encode()
    last = None

    for url in OVERPASS_MIRRORS:
        host = urllib.parse.urlparse(url).netloc
        try:
            print(f"Querying {host} ...")
            req = urllib.request.Request(
                url, data=data, headers={"User-Agent": "i4-safety-analysis/1.0"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.load(resp)
        except Exception as exc:  # timeouts, 429, 504, transport errors
            print(f"  {host} failed: {exc}")
            last = exc
            time.sleep(2)
            continue

        with open(CACHE, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        print(f"  got {len(payload.get('elements', []))} ways; cached")
        return payload

    raise SystemExit(f"All Overpass mirrors failed. Last error: {last}")


def build_lines(payload):
    """Each way becomes a list of (x, y) metre coordinates."""
    mainline, ramps = [], []
    for el in payload.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        pts = [to_m(n["lon"], n["lat"]) for n in el["geometry"]]
        if len(pts) < 2:
            continue
        tag = el.get("tags", {}).get("highway")
        if tag == "motorway":
            mainline.append(pts)
        elif tag == "motorway_link":
            ramps.append(pts)
    return mainline, ramps


def seg_dist(px, py, ax, ay, bx, by):
    """Shortest distance from point P to line segment AB, all in metres."""
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    # Project P onto AB, clamped so the foot stays on the segment.
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def nearest(pt, lines):
    """Distance from a point to the closest segment of any way in `lines`."""
    px, py = pt
    best = float("inf")
    for pts in lines:
        for i in range(len(pts) - 1):
            ax, ay = pts[i]
            bx, by = pts[i + 1]
            d = seg_dist(px, py, ax, ay, bx, by)
            if d < best:
                best = d
    return best


def main():
    payload = fetch_osm()
    mainline, ramps = build_lines(payload)
    print(f"OSM geometry: {len(mainline)} mainline ways, {len(ramps)} ramp ways")

    if not ramps or not mainline:
        raise SystemExit("Missing mainline or ramp geometry - cannot classify.")

    df = pd.read_excel(SRC, engine="openpyxl").dropna(subset=["LATITUDE", "LONGITUDE"])
    print(f"Crashes: {len(df)}")

    d_main, d_ramp = [], []
    for _, row in df.iterrows():
        p = to_m(row["LONGITUDE"], row["LATITUDE"])
        d_main.append(nearest(p, mainline))
        d_ramp.append(nearest(p, ramps))

    df["dist_mainline_m"] = d_main
    df["dist_ramp_m"] = d_ramp
    # Positive margin means the ramp is the closer of the two.
    df["margin_m"] = df["dist_mainline_m"] - df["dist_ramp_m"]
    df["auto_class"] = df["margin_m"].apply(lambda m: "Ramp" if m > 0 else "Mainline")
    df["needs_review"] = df["margin_m"].abs() < REVIEW_MARGIN_M

    # The notebook's hand-built answer, collapsed to the same two labels.
    df["manual_class"] = df["Location"].apply(
        lambda z: "Ramp" if str(z).startswith("Ramp") else "Mainline"
    )

    print()
    print("=" * 64)
    print("AUTOMATIC (geometry) vs MANUAL (hand-typed lists)")
    print("=" * 64)
    print(pd.crosstab(df["manual_class"], df["auto_class"], margins=True).to_string())

    agree = int((df["auto_class"] == df["manual_class"]).sum())
    print(f"\nAgreement: {agree}/{len(df)}  ({agree / len(df) * 100:.1f}%)")

    fn = df[(df["manual_class"] == "Ramp") & (df["auto_class"] == "Mainline")]
    fp = df[(df["manual_class"] == "Mainline") & (df["auto_class"] == "Ramp")]
    print(f"  Manual said ramp, geometry says mainline: {len(fn)}")
    print(f"  Manual said mainline, geometry says ramp: {len(fp)}")

    review = df[df["needs_review"]]
    print(f"\nWithin {REVIEW_MARGIN_M:.0f} m of the decision boundary "
          f"(send to a human): {len(review)}")
    settled = len(df) - len(review)
    print(f"Settled by geometry alone: {settled} "
          f"({settled / len(df) * 100:.1f}%)")

    cols = ["REPORT_NUMBER", "Location", "auto_class", "dist_mainline_m",
            "dist_ramp_m", "margin_m", "On_Street"]
    dis = pd.concat([fn, fp])
    if len(dis):
        dis = dis.reindex(dis["margin_m"].abs().sort_values().index)
        print("\nDisagreements, closest call first:")
        print(dis[cols].head(30).to_string(
            index=False, float_format=lambda v: f"{v:8.1f}"))

    df.to_excel(OUT_XLSX, index=False, engine="openpyxl")
    review[cols].to_excel(OUT_REVIEW, index=False, engine="openpyxl")
    print(f"\nWrote {OUT_XLSX}")
    print(f"Wrote {OUT_REVIEW}")


if __name__ == "__main__":
    main()
