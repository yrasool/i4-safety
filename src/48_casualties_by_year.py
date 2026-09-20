"""Step 48 - casualties by mode and year, because the rate is a mean of a
series that moved.

WHY THIS EXISTS. Every rate in this project divides seven years of casualties
by seven years of exposure, which assumes the underlying risk is roughly flat
across the window. For cycling it is not. Bicycle deaths in these five counties
rose about a third between 2019 and 2022-24 while serious injuries did not move
at all, so r_bike is a seven-year mean of a rising series and a rate built on
the recent years alone would be materially higher.

That is a limitation the project should state with its own number rather than
cite from elsewhere. A May 2026 analysis by Santini Research, built from FLHSMV
and UF BEBR figures, reports Florida bicycle fatalities up 46.6% from a 2017-19
baseline to 2022-25. This step does not adopt that figure - the window and the
geography both differ - it reproduces the QUESTION on the licensed extract and
reports what Tampa Bay actually shows.

WHAT IT DOES NOT CLAIM. Not a rate. There is no denominator here - these are
counts, and exposure by year is step 34's job. A count going up can mean more
risk or more riding, and this file cannot separate them. It also cannot isolate
e-bikes: Florida's crash reports fold them into the bicycle category, and
SB 382, which would have required e-bike classification on crash reports, was
vetoed in June 2026.

2025 IS A PARTIAL YEAR. The extract runs to November, so the last row is not
comparable to a full one and is excluded from the change calculation. Step 34
quantifies the same effect for the all-mode rate.

PROVENANCE. Reads the licensed Signal Four extract and writes counts by year
only - the same scale the public dashboard publishes, which step 37 checks
against. No record-level field leaves this step.

Reads:  the Signal Four extract named in step 02
Writes: data/final/casualties_by_year.csv
"""
import csv
import io
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "final" / "casualties_by_year.csv"

# Same source as step 02. Named once there and once here; if it moves, both
# fail loudly rather than one silently reading an older extract.
SRC = Path(r"C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv")

FIELDS = {
    "bike_K": "S4_BICYCLIST_FATALITY_COUNT",
    "bike_A": "S4_BICYCLIST_INCAPACITATING_INJURY_COUNT",
    "ped_K": "S4_PEDESTRIAN_FATALITY_COUNT",
    "ped_A": "S4_PEDESTRIAN_INCAPACITATING_INJURY_COUNT",
}
PARTIAL_YEAR = "2025"          # extract ends in November
BASELINE = ("2019",)
RECENT = ("2022", "2023", "2024")


def num(row, key):
    v = (row.get(key) or "").strip()
    try:
        return int(float(v))
    except ValueError:
        return 0


def main():
    if not SRC.exists():
        sys.exit(f"FAIL: {SRC.name} not found. This step needs the licensed "
                 "Signal Four extract, same file step 02 reads.")

    counts = {k: Counter() for k in FIELDS}
    crashes = Counter()
    with io.open(SRC, encoding="utf8", errors="replace", newline="") as fh:
        # The extract carries embedded NULs; step 02 strips them the same way.
        rdr = csv.DictReader(line.replace("\0", "") for line in fh)
        for row in rdr:
            y = (row.get("CRASH_YEAR") or "").strip()
            if not y:
                continue
            crashes[y] += 1
            for k, col in FIELDS.items():
                counts[k][y] += num(row, col)

    years = sorted(crashes)
    if not years:
        sys.exit("FAIL: no CRASH_YEAR values parsed. Check the extract.")

    print("=" * 68)
    print("CASUALTIES BY YEAR - counts, not rates")
    print("=" * 68)
    print(f"  {'year':<8}{'bike K':>8}{'bike A':>9}{'ped K':>8}"
          f"{'ped A':>9}{'crashes':>11}")
    for y in years:
        mark = "  *" if y == PARTIAL_YEAR else ""
        print(f"  {y:<8}{counts['bike_K'][y]:>8}{counts['bike_A'][y]:>9}"
              f"{counts['ped_K'][y]:>8}{counts['ped_A'][y]:>9}"
              f"{crashes[y]:>11,}{mark}")
    print(f"  {'TOTAL':<8}{sum(counts['bike_K'].values()):>8}"
          f"{sum(counts['bike_A'].values()):>9}"
          f"{sum(counts['ped_K'].values()):>8}"
          f"{sum(counts['ped_A'].values()):>9}"
          f"{sum(crashes.values()):>11,}")
    print(f"  * {PARTIAL_YEAR} is a partial year and is excluded below.")

    rows = [["metric", "year", "value"]]
    for k in FIELDS:
        for y in years:
            rows.append([k, y, counts[k][y]])
    for y in years:
        rows.append(["crashes", y, crashes[y]])

    print("\n  change from baseline, partial year excluded")
    for k in ("bike_K", "bike_A", "ped_K", "ped_A"):
        base = statistics.mean(counts[k][y] for y in BASELINE)
        recent = statistics.mean(counts[k][y] for y in RECENT)
        if base == 0:
            continue
        chg = recent / base - 1
        print(f"    {k:<8}{'-'.join(BASELINE)} {base:>6.1f}  ->  "
              f"{RECENT[0]}-{RECENT[-1][-2:]} {recent:>6.1f}   {chg:>+7.1%}")
        rows.append([f"{k}_change_{'-'.join(BASELINE)}_to_"
                     f"{RECENT[0]}-{RECENT[-1]}", "", f"{chg:.6f}"])

    print("\n  Deaths and serious injuries move differently: that gap is the")
    print("  severity signal, and it is why a seven-year mean rate carries a")
    print("  caveat rather than an error. A count is not a rate - exposure by")
    print("  year is step 34's job, and this step does not divide by it.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
