"""
Step 19 - the road and path network.  What the isochrones are computed on.

MEP's Table 1 lists OpenStreetMap as a source for isochrones. This pulls it.

TILED, because one query for the whole region times out and, worse, can return
a TRUNCATED result that still parses as valid JSON. Each tile is fetched and
cached separately, and a tile is only written once it has come back complete, so
an interrupted run resumes instead of silently producing a network with holes in
it. A hole in a walking network does not raise - it just makes a neighbourhood
look unreachable, which is exactly what this project is trying to measure.

NODES ARE KEYED BY ROUNDED COORDINATE rather than OSM node id. Ways that meet at
a junction share the coordinate, so rounding to 7 decimal places (about 1 cm)
joins them. This avoids a second pass to resolve node ids, and it also stitches
tile boundaries automatically, because a way crossing a tile edge appears in
both tiles with identical coordinates.

Writes: data/raw/osm/tile_*.json.gz
"""

import gzip
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OSM = ROOT / "data" / "raw" / "osm"
ENDPOINTS = ["https://overpass-api.de/api/interpreter",
             "https://overpass.kumi.systems/api/interpreter"]

# From step 18's centroid bounding box, padded so a trip can leave the region.
S, N, W, E = 27.50, 29.15, -83.05, -81.95
STEP = 0.15   # degrees; ~16 km, sized so a dense urban tile stays under ~50 MB

# Everything routable by car, bike or foot. `service` covers car parks and
# driveways, which matter for the last 100 m of a walk trip.
HIGHWAYS = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential"
            "|living_street|service|motorway_link|trunk_link|primary_link"
            "|secondary_link|tertiary_link|pedestrian|footway|path|cycleway"
            "|steps|track")


def fetch(query, tries=4):
    last = None
    for attempt in range(tries):
        url = ENDPOINTS[attempt % len(ENDPOINTS)]
        try:
            req = urllib.request.Request(
                url, data=query.encode(),
                headers={"User-Agent": "tampa-mep/1.0 (research)"})
            with urllib.request.urlopen(req, timeout=900) as r:
                return json.load(r)
        except Exception as exc:
            last = exc
            wait = 30 * (attempt + 1)
            print(f"      retry {attempt+1} in {wait}s: {type(exc).__name__}",
                  flush=True)
            time.sleep(wait)
    raise SystemExit(f"FAIL: tile could not be fetched: {last}")


def main():
    OSM.mkdir(parents=True, exist_ok=True)
    tiles = []
    lat = S
    while lat < N:
        lon = W
        while lon < E:
            tiles.append((round(lat, 3), round(lon, 3)))
            lon += STEP
        lat += STEP
    print(f"{len(tiles)} tiles of {STEP} degrees", flush=True)

    total_ways = 0
    for i, (lat, lon) in enumerate(tiles, 1):
        out = OSM / f"tile_{lat}_{lon}.json.gz"
        if out.exists():
            n = len(json.loads(gzip.decompress(out.read_bytes())))
            total_ways += n
            print(f"  [{i}/{len(tiles)}] cached  {n:>7,} ways", flush=True)
            continue

        bbox = f"{lat},{lon},{round(lat+STEP,3)},{round(lon+STEP,3)}"
        q = (f'[out:json][timeout:600];'
             f'way["highway"~"^({HIGHWAYS})$"]({bbox});out geom;')
        data = fetch(q)

        ways = []
        for el in data.get("elements", []):
            g = el.get("geometry")
            if not g or len(g) < 2:
                continue
            t = el.get("tags", {})
            ways.append({
                "h": t.get("highway"),
                "o": t.get("oneway"),
                "s": t.get("maxspeed"),
                "a": t.get("access"),
                # rounded to 7dp; this is the join key used in step 20
                "c": [[round(p["lat"], 7), round(p["lon"], 7)] for p in g],
            })
        # Write only after the whole tile parsed, so a partial file cannot be
        # mistaken for a complete one on the next run.
        out.write_bytes(gzip.compress(json.dumps(ways).encode(), 6))
        total_ways += len(ways)
        print(f"  [{i}/{len(tiles)}] fetched {len(ways):>7,} ways  "
              f"{out.stat().st_size/1e6:>5.1f} MB", flush=True)
        time.sleep(3)   # be polite to a free public endpoint

    print(f"\n{total_ways:,} way segments across {len(tiles)} tiles", flush=True)
    print(f"cached in {OSM}", flush=True)


if __name__ == "__main__":
    main()
