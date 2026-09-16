"""
Step 41 - the OpenStreetMap tags that Level of Traffic Stress needs.

WHY THIS EXISTS. Step 19 stored four tags per way - highway class, oneway,
maxspeed, access - which is everything routing needs and not enough to judge
whether a road is comfortable to cycle on. Level of Traffic Stress (Mekuria,
Furth and Nixon 2012) turns on three more things: how many LANES, whether there
is a BIKE LANE, and whether that lane is PROTECTED.

WHY ONLY SOME ROAD CLASSES. Local streets (residential, living_street, service)
are judged by class and speed alone in the standard method, and bike paths are
low-stress by definition, so their extra tags change nothing. Lanes and bike
facilities decide the outcome only on collectors and arterials. Fetching just
those keeps this to a small fraction of step 19's download.

THE JOIN. Ways are stored with the same 7-decimal coordinates as step 19, so
step 42 matches each way to step 20's edges by the same geometry fingerprint
step 20 uses to drop tile-boundary duplicates.

Reads:  nothing
Writes: data/raw/osm_lts/tile_*.json.gz
"""

import gzip
import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "osm_lts"
ENDPOINTS = ["https://overpass-api.de/api/interpreter",
             "https://overpass.kumi.systems/api/interpreter"]

# identical tiling to step 19, so tile names line up
S, N, W, E = 27.50, 29.15, -83.05, -81.95
STEP = 0.15

CLASSES = ("trunk|trunk_link|primary|primary_link|secondary|secondary_link"
           "|tertiary|tertiary_link|unclassified")
KEEP = ("highway", "lanes", "lanes:forward", "lanes:backward", "maxspeed",
        "oneway", "cycleway", "cycleway:both", "cycleway:left",
        "cycleway:right", "bicycle", "sidewalk")


def fetch(query, tries=4):
    last = None
    for attempt in range(tries):
        url = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            req = urllib.request.Request(
                url, data=query.encode(),
                headers={"User-Agent": "tampa-mep/1.0 (research)"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.load(r)
        except Exception as exc:
            last = exc
            wait = 30 * (attempt + 1)
            print(f"      retry {attempt + 1} in {wait}s: "
                  f"{type(exc).__name__}", flush=True)
            time.sleep(wait)
    raise SystemExit(f"FAIL: tile could not be fetched: {last}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tiles, lat = [], S
    while lat < N:
        lon = W
        while lon < E:
            tiles.append((round(lat, 3), round(lon, 3)))
            lon += STEP
        lat += STEP
    print(f"{len(tiles)} tiles", flush=True)

    total = 0
    for i, (lat, lon) in enumerate(tiles, 1):
        out = OUT / f"tile_{lat}_{lon}.json.gz"
        if out.exists():
            total += len(json.loads(gzip.decompress(out.read_bytes())))
            continue
        bbox = f"{lat},{lon},{round(lat + STEP, 3)},{round(lon + STEP, 3)}"
        q = (f'[out:json][timeout:300];'
             f'way["highway"~"^({CLASSES})$"]({bbox});out tags geom;')
        data = fetch(q)
        ways = []
        for el in data.get("elements", []):
            g = el.get("geometry")
            if not g or len(g) < 2:
                continue
            t = el.get("tags", {})
            ways.append({"t": {k: t[k] for k in KEEP if k in t},
                         "c": [[round(p["lat"], 7), round(p["lon"], 7)]
                               for p in g]})
        out.write_bytes(gzip.compress(json.dumps(ways).encode(), 6))
        total += len(ways)
        print(f"  [{i}/{len(tiles)}] {len(ways):>6,} ways", flush=True)
        time.sleep(2)
    print(f"\n{total:,} collector and arterial ways with LTS tags")
    if total == 0:
        sys.exit("FAIL: no ways fetched.")


if __name__ == "__main__":
    main()
