"""What is in the OSM cache pulled during the ramp-classifier work?"""

import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "osm_ramps_cache.json")

with open(SRC, encoding="utf-8") as fh:
    data = json.load(fh)

els = data.get("elements", [])
print(f"{len(els)} elements")

kinds = collections.Counter(e.get("type") for e in els)
print(f"types: {dict(kinds)}")

hw = collections.Counter(
    (e.get("tags") or {}).get("highway") for e in els if e.get("type") == "way")
print(f"\nhighway tags: {dict(hw)}")

lat = [n["lat"] for e in els if e.get("geometry") for n in e["geometry"]]
lon = [n["lon"] for e in els if e.get("geometry") for n in e["geometry"]]
if lat:
    print(f"\nbbox lat {min(lat):.5f} .. {max(lat):.5f}")
    print(f"     lon {min(lon):.5f} .. {max(lon):.5f}")
    print(f"vertices: {len(lat):,}")

# What other attributes are available for a 3D render?
tagkeys = collections.Counter()
for e in els:
    for k in (e.get("tags") or {}):
        tagkeys[k] += 1
print("\ncommon tags: " + ", ".join(f"{k}({n})" for k, n in tagkeys.most_common(16)))

print("\nsample ways:")
for e in els[:6]:
    t = e.get("tags") or {}
    n = len(e.get("geometry") or [])
    print(f"  {t.get('highway','?'):<15} lanes={t.get('lanes','-'):<3} "
          f"oneway={t.get('oneway','-'):<4} ref={t.get('ref','-'):<10} {n} pts")
