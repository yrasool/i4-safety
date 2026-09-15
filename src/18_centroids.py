"""
Step 18 - block group centroids.  The origins every isochrone starts from.

MEP computes on a pixel grid and aggregates up with population density. This
project uses block group centroids directly, because that is the geography the
crash cost, the equity split and the EPA surface are all already on. Aggregating
pixels to block groups only to compare against block-group data would add a
resampling step with no information in it.

Source: Census TIGERweb, 2020 Census Block Groups layer, CENTLAT/CENTLON. These
are the INTERIOR points Census publishes - guaranteed to fall inside the
polygon, unlike a naive geometric centroid, which for a C-shaped block group can
land in the neighbouring one.

Writes: data/interim/centroids.csv
"""

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COUNTIES, STATE_FP, USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "centroids.csv"
LAYER = ("https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/"
         "tigerWMS_Census2020/MapServer/8")


def query(where, offset):
    params = {"where": where, "outFields": "GEOID,CENTLAT,CENTLON,AREALAND",
              "returnGeometry": "false", "resultOffset": offset,
              "resultRecordCount": 1000, "orderByFields": "GEOID", "f": "json"}
    url = f"{LAYER}/query?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def main():
    rows = []
    for fips, name in COUNTIES.items():
        where = f"STATE='{STATE_FP}' AND COUNTY='{fips}'"
        off, got = 0, []
        while True:
            page = query(where, off)
            feats = page.get("features", [])
            if not feats:
                break
            got += [f["attributes"] for f in feats]
            off += len(feats)
            if not page.get("exceededTransferLimit"):
                break
        print(f"  {name:<14}{len(got):>5} block groups")
        for a in got:
            rows.append({"GEOID20": a["GEOID"], "county": name,
                         "lat": float(a["CENTLAT"]), "lon": float(a["CENTLON"]),
                         "arealand_m2": a.get("AREALAND")})

    if len({r["GEOID20"] for r in rows}) != len(rows):
        sys.exit("FAIL: duplicate GEOID - paging overlapped")
    # Every centroid must land in the study area's bounding box. A sign error in
    # longitude puts Tampa in the Indian Ocean and nothing downstream would
    # notice, because a graph search simply returns unreachable.
    for r in rows:
        if not (27.0 < r["lat"] < 29.5 and -83.5 < r["lon"] < -82.0):
            sys.exit(f"FAIL: {r['GEOID20']} at {r['lat']},{r['lon']} is outside "
                     f"Tampa Bay. Check the CENTLAT/CENTLON sign convention.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    lats = [r["lat"] for r in rows]; lons = [r["lon"] for r in rows]
    print(f"\n  bounding box  lat {min(lats):.3f} to {max(lats):.3f}   "
          f"lon {min(lons):.3f} to {max(lons):.3f}")
    print(f"wrote {OUT}  ({len(rows):,} origins)")


if __name__ == "__main__":
    main()
