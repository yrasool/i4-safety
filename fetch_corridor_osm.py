"""
Pull a full OSM extract for the I-4 corridor: roads, buildings, water.

The existing cache holds only motorway and motorway_link - enough to classify a
crash as ramp or mainline, nowhere near enough to render a place. A scene meant
to be looked at closely needs the cross streets that give the interchanges their
names, the service roads, the buildings that make it read as somewhere, and the
water, because this corridor runs past ponds and the Hillsborough River.

Roads carry lane counts and oneway, so carriageway ribbons can be drawn at
something close to true width rather than uniform lines.
"""

import json
import os
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "corridor_osm.json")

# Generous around the study area so the interchanges are whole and there is
# context beyond the crash extent.
S, W, N, E = 28.0100, -82.2650, 28.0420, -82.1700

MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

ROADS = ("motorway|motorway_link|trunk|trunk_link|primary|primary_link|"
         "secondary|secondary_link|tertiary|tertiary_link|residential|"
         "unclassified|service")

QUERY = f"""
[out:json][timeout:180];
(
  way["highway"~"^({ROADS})$"]({S},{W},{N},{E});
  way["building"]({S},{W},{N},{E});
  way["natural"="water"]({S},{W},{N},{E});
  way["waterway"="riverbank"]({S},{W},{N},{E});
  way["landuse"~"^(forest|grass|meadow|farmland|industrial|retail)$"]({S},{W},{N},{E});
);
out geom;
"""


def fetch():
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    for url in MIRRORS:
        host = urllib.parse.urlparse(url).netloc
        try:
            print(f"  trying {host} ...", end="", flush=True)
            req = urllib.request.Request(
                url, data=data, headers={"User-Agent": "i4-corridor/1.0"})
            with urllib.request.urlopen(req, timeout=240) as r:
                payload = json.load(r)
            print(" ok")
            return payload
        except Exception as exc:
            print(f" {str(exc)[:60]}")
            time.sleep(2)
    raise SystemExit("all Overpass mirrors failed")


def main():
    if os.path.exists(OUT) and os.path.getsize(OUT) > 100_000:
        with open(OUT, encoding="utf-8") as fh:
            payload = json.load(fh)
        print(f"Cached: {len(payload['elements'])} elements")
    else:
        print("Querying Overpass ...")
        payload = fetch()
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        print(f"Wrote {OUT}  ({os.path.getsize(OUT) / 1e6:.1f} MB)")

    els = payload["elements"]
    import collections
    roads = collections.Counter()
    n_bldg = n_water = n_land = 0
    named = set()
    for e in els:
        t = e.get("tags") or {}
        if t.get("highway"):
            roads[t["highway"]] += 1
            if t.get("name"):
                named.add(t["name"])
        elif t.get("building"):
            n_bldg += 1
        elif t.get("natural") == "water" or t.get("waterway"):
            n_water += 1
        elif t.get("landuse"):
            n_land += 1

    print(f"\n{len(els):,} elements")
    print(f"  roads     {sum(roads.values()):,}")
    for k, v in roads.most_common():
        print(f"      {k:<18}{v:>5}")
    print(f"  buildings {n_bldg:,}")
    print(f"  water     {n_water:,}")
    print(f"  landuse   {n_land:,}")
    print(f"\n{len(named)} named roads, including:")
    for n in sorted(named)[:22]:
        print(f"      {n}")


if __name__ == "__main__":
    main()
