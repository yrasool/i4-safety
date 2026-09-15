"""
How much of I-4 is outside the notebook's bounding box?

The methodology document is titled "I-4 from Bethlehem Rd to Branch Forbes Rd",
but Step 2 of the notebook sets its western limit at McIntosh Rd. This script
takes the LRS + year + district filters but drops the longitude walls, so we can
see the whole crash distribution along the route and count what the box excludes.

Reads source data read-only. Writes results here.
"""

import json
import os
import urllib.parse
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = r"D:\Yusra\I4 Safety Ana;ysis"
RAW = os.path.join(FOLDER, "crash_roadway_vehicle_driver.csv")
CLEAN = os.path.join(FOLDER, "I4_BranchForbes_Crashes_Clean.xlsx")
OUT = os.path.join(HERE, "I4_OutsideBox.xlsx")

I4_LRS_ID = "10190000"
YEARS = [2021, 2022, 2023, 2024, 2025]

BOX_WEST = -82.2446584799336
BOX_EAST = -82.18669748126841
GORE_WEST = -82.23912020511585
GORE_EAST = -82.19359219348705

# Widened well past the box on both sides; latitude band kept generous so the
# route is followed rather than clipped.
SCAN_WEST, SCAN_EAST = -82.40, -82.10
SCAN_LAT_MIN, SCAN_LAT_MAX = 28.010, 28.045

USECOLS = [
    "REPORT_NUMBER", "CRASH_YEAR", "MANAGING_DOT_DISTRICT", "LRS_ROADWAY",
    "LRS_MILEPOINT", "LATITUDE", "LONGITUDE", "ON_STREET_ROAD_HIGHWAY",
    "S4_CRASH_SEVERITY", "S4_IS_CMV_INVOLVED",
]

OVERPASS_MIRRORS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

CROSS_STREETS = ["Bethlehem Road", "McIntosh Road", "Branch Forbes Road"]


def find_cross_streets():
    """Longitude of each named cross street where it meets the corridor."""
    q = "[out:json][timeout:60];("
    for name in CROSS_STREETS:
        q += (f'way["highway"]["name"="{name}"]'
              f'({SCAN_LAT_MIN},{SCAN_WEST},{SCAN_LAT_MAX},{SCAN_EAST});')
    q += ");out geom;"

    data = urllib.parse.urlencode({"data": q}).encode()
    for url in OVERPASS_MIRRORS:
        try:
            req = urllib.request.Request(
                url, data=data, headers={"User-Agent": "i4-safety/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                payload = json.load(r)
            break
        except Exception as exc:
            print(f"  overpass {urllib.parse.urlparse(url).netloc}: {exc}")
    else:
        print("  could not reach Overpass; skipping cross-street lookup")
        return {}

    out = {}
    for el in payload.get("elements", []):
        name = el.get("tags", {}).get("name")
        if not name or "geometry" not in el:
            continue
        lons = [n["lon"] for n in el["geometry"]]
        out.setdefault(name, []).extend(lons)
    return {k: sum(v) / len(v) for k, v in out.items() if v}


def main():
    print("Locating cross streets ...")
    streets = find_cross_streets()
    for k, v in sorted(streets.items(), key=lambda kv: kv[1]):
        print(f"  {k:22s} lon {v:.6f}")

    print("\nLoading raw CSV ...")
    df = pd.read_csv(RAW, usecols=USECOLS, low_memory=False)
    df["LRS_ROADWAY"] = df["LRS_ROADWAY"].astype(str)

    scan = df[
        df["MANAGING_DOT_DISTRICT"].isin([7, 5])
        & df["CRASH_YEAR"].isin(YEARS)
        & (df["LRS_ROADWAY"] == I4_LRS_ID)
        & df["LONGITUDE"].between(SCAN_WEST, SCAN_EAST)
        & df["LATITUDE"].between(SCAN_LAT_MIN, SCAN_LAT_MAX)
    ].copy()
    print(f"I-4 crashes on the scanned stretch: {len(scan):,}")

    def band(lon):
        if lon < BOX_WEST:
            return "A. WEST of the box (never considered)"
        if lon < GORE_WEST:
            return "B. Box to west gore (trimmed away)"
        if lon <= GORE_EAST:
            return "C. Gore to gore (the kept mainline)"
        if lon <= BOX_EAST:
            return "D. East gore to box (trimmed away)"
        return "E. EAST of the box (never considered)"

    scan["band"] = scan["LONGITUDE"].apply(band)

    print("\n" + "=" * 72)
    print("CRASHES BY POSITION RELATIVE TO THE NOTEBOOK'S LIMITS")
    print("=" * 72)
    counts = scan["band"].value_counts().sort_index()
    for k, v in counts.items():
        print(f"  {k:44s} {v:5d}   ({v / len(scan) * 100:5.1f}%)")
    print(f"  {'TOTAL':44s} {len(scan):5d}")

    outside = scan[scan["band"].str.startswith(("A.", "E."))]
    print(f"\nOutside the bounding box entirely: {len(outside):,}")

    if len(outside):
        print("\n  Severity:")
        print(outside["S4_CRASH_SEVERITY"].value_counts().to_string())
        cmv = outside["S4_IS_CMV_INVOLVED"].astype(str).str.upper().eq("Y").sum()
        print(f"\n  Commercial vehicle involved: {cmv}")
        print("\n  Milepoint range of the excluded crashes:")
        print(f"    {outside['LRS_MILEPOINT'].min():.3f} "
              f"to {outside['LRS_MILEPOINT'].max():.3f}")

    print("\n  Milepoint range kept by the notebook:")
    kept = scan[scan["band"].startswith("C.") if False else
                scan["band"].str.startswith("C.")]
    print(f"    {kept['LRS_MILEPOINT'].min():.3f} "
          f"to {kept['LRS_MILEPOINT'].max():.3f}")

    # Half-mile longitude bins, so the shape of the corridor is visible.
    print("\n" + "=" * 72)
    print("DISTRIBUTION ALONG THE ROUTE (0.005 deg lon bins, ~490 m)")
    print("=" * 72)
    scan["bin"] = (scan["LONGITUDE"] / 0.005).round() * 0.005
    for b, grp in scan.groupby("bin"):
        marks = []
        if b - 0.0025 <= BOX_WEST <= b + 0.0025:
            marks.append("<< BOX WEST")
        if b - 0.0025 <= BOX_EAST <= b + 0.0025:
            marks.append("BOX EAST >>")
        for name, lon in streets.items():
            if b - 0.0025 <= lon <= b + 0.0025:
                marks.append(name)
        bar = "#" * min(int(grp.shape[0] / 2), 60)
        print(f"  {b:9.4f}  {grp.shape[0]:4d}  {bar} {' '.join(marks)}")

    outside.to_excel(OUT, index=False, engine="openpyxl")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
