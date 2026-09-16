"""
What area does the crash data actually cover?

The MEP needs a study area, and the crash data should define it rather than a
guess at "Tampa". So: which counties, how many crashes in each, what spatial
extent, and how much of it is usable for a risk surface.

Also splits by year, because the pandemic years are the longitudinal spine, and
by mode-relevant flags, because the risk term has to be assigned per mode -
pedestrian and bicyclist crashes weight walking and cycling, not driving.
"""

import collections
import csv
import os

SRC = r"C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv"


def denul(f):
    for line in f:
        yield line.replace("\x00", "")


def main():
    counties = collections.Counter()
    years = collections.Counter()
    county_year = collections.Counter()
    modes = collections.Counter()
    sev = collections.Counter()
    lat_min = lon_min = 1e9
    lat_max = lon_max = -1e9
    n = geo = 0

    with open(SRC, encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(denul(fh)):
            n += 1
            c = (row.get("COUNTY_NAME") or "").strip().title()
            y = (row.get("CRASH_YEAR") or "").strip()
            counties[c] += 1
            years[y] += 1
            county_year[(c, y)] += 1
            sev[(row.get("S4_CRASH_SEVERITY") or "").strip()] += 1

            if (row.get("S4_IS_PEDESTRIAN_INVOLVED") or "").upper().startswith("Y"):
                modes["pedestrian"] += 1
            if (row.get("S4_IS_BICYCLIST_INVOLVED") or "").upper().startswith("Y"):
                modes["bicyclist"] += 1
            if (row.get("S4_IS_CMV_INVOLVED") or "").upper().startswith("Y"):
                modes["commercial vehicle"] += 1

            try:
                la = float(row["LATITUDE"]); lo = float(row["LONGITUDE"])
                if -90 < la < 90 and -180 < lo < 180 and la != 0:
                    geo += 1
                    lat_min = min(lat_min, la); lat_max = max(lat_max, la)
                    lon_min = min(lon_min, lo); lon_max = max(lon_max, lo)
            except (KeyError, TypeError, ValueError):
                pass

    print(f"{n:,} crashes\n")
    print("COUNTIES")
    for c, k in counties.most_common(12):
        print(f"  {c or '(blank)':<18}{k:>8,}  {k/n*100:5.1f}%")

    print("\nYEARS")
    base = years.get("2019", 1)
    for y in sorted(years):
        if not y:
            continue
        k = years[y]
        print(f"  {y}  {k:>8,}   {k/base*100:6.1f}% of 2019")

    print("\nTOP COUNTY BY YEAR")
    top = [c for c, _ in counties.most_common(4)]
    hdr = "  " + "county".ljust(16) + "".join(y.rjust(9) for y in sorted(years) if y)
    print(hdr)
    for c in top:
        line = "  " + c.ljust(16)
        for y in sorted(years):
            if not y:
                continue
            line += f"{county_year[(c,y)]:>9,}"
        print(line)

    print("\nMODE-RELEVANT CRASHES  (these weight the MEP risk term per mode)")
    for m, k in modes.most_common():
        print(f"  {m:<20}{k:>8,}  {k/n*100:5.2f}%")

    print("\nSEVERITY")
    for s, k in sev.most_common():
        print(f"  {s or '(blank)':<26}{k:>8,}")

    print(f"\nGEOCODED  {geo:,}  ({geo/n*100:.1f}%)")
    print(f"  lat {lat_min:.4f} .. {lat_max:.4f}")
    print(f"  lon {lon_min:.4f} .. {lon_max:.4f}")
    km_ns = (lat_max - lat_min) * 111.32
    km_ew = (lon_max - lon_min) * 111.32 * 0.883
    print(f"  extent ~{km_ew:.0f} km east-west x {km_ns:.0f} km north-south")
    print(f"  at 1 km cells that is ~{km_ew*km_ns:,.0f} cells to score")


if __name__ == "__main__":
    main()
