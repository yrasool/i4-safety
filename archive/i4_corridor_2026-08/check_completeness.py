"""
Two data-quality checks that would otherwise become published mistakes.

1. IS 2025 A PARTIAL YEAR?
   2025 sits at 77.1% of 2019 - almost exactly where 2020 sat. One of those is a
   pandemic, the other is probably just a truncated export. Reporting "crashes
   fell again in 2025" off an incomplete year would be a bad error, so count the
   months actually present in each year.

2. HOW FAR OUT DO THE COORDINATES GO?
   min/max spans lat 25.5-30.8, lon -87.2 to -80.1 - the whole state. District 7
   is roughly 150 km across, so there are outliers. A robust extent needs
   percentiles, not extremes.
"""

import collections
import csv
import re

SRC = r"C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv"
MONTHS = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]


def denul(f):
    for line in f:
        yield line.replace("\x00", "")


def main():
    ym = collections.Counter()
    lats, lons = [], []
    per_county_month = collections.Counter()

    with open(SRC, encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(denul(fh)):
            y = (row.get("CRASH_YEAR") or "").strip()
            dt = str(row.get("CRASH_DATE_AND_TIME") or "")
            m = re.search(r"-([A-Z]{3})-", dt.upper())
            if y and m:
                ym[(y, m.group(1))] += 1
            try:
                la = float(row["LATITUDE"]); lo = float(row["LONGITUDE"])
                if la != 0 and -90 < la < 90:
                    lats.append(la); lons.append(lo)
            except (KeyError, TypeError, ValueError):
                pass

    print("CRASHES BY YEAR AND MONTH")
    years = sorted({y for y, _ in ym})
    print("       " + "".join(mm.rjust(7) for mm in MONTHS) + "     total")
    for y in years:
        row = [ym.get((y, mm), 0) for mm in MONTHS]
        present = sum(1 for v in row if v > 0)
        flag = "   <-- PARTIAL" if present < 12 else ""
        print(f"  {y}  " + "".join(f"{v:>7,}" for v in row) +
              f"{sum(row):>10,}{flag}")

    last = years[-1]
    got = [mm for mm in MONTHS if ym.get((last, mm), 0) > 0]
    print(f"\n  {last} has {len(got)} months: {', '.join(got)}")
    if len(got) < 12:
        full = [y for y in years if sum(1 for mm in MONTHS if ym.get((y,mm),0)) == 12]
        if full:
            base = sum(ym.get((full[-1], mm), 0) for mm in got)
            cur = sum(ym.get((last, mm), 0) for mm in got)
            print(f"  Like-for-like on those months vs {full[-1]}: "
                  f"{cur:,} vs {base:,}  ({cur/base*100:.1f}%)")
            print("  ^ THIS is the comparable figure. The raw year total is not.")

    lats.sort(); lons.sort()
    def pct(a, p):
        return a[int(len(a) * p)]
    print(f"\nCOORDINATE SPREAD  ({len(lats):,} points)")
    for p in (0.001, 0.01, 0.5, 0.99, 0.999):
        print(f"  p{p*100:<6.1f}  lat {pct(lats,p):9.4f}   lon {pct(lons,p):10.4f}")
    lo, hi = pct(lats,0.001), pct(lats,0.999)
    lo2, hi2 = pct(lons,0.001), pct(lons,0.999)
    print(f"\n  robust extent (p0.1-p99.9): "
          f"{(hi2-lo2)*111.32*0.883:.0f} km E-W x {(hi-lo)*111.32:.0f} km N-S")
    out = sum(1 for la, lo3 in zip(lats, lons)
              if not (lo <= la <= hi and lo2 <= lo3 <= hi2))
    print(f"  points outside that box: {out:,} ({out/len(lats)*100:.2f}%)")


if __name__ == "__main__":
    main()
