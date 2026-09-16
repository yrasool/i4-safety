"""
Step 38 - is Tampa Bay typical for Florida, or unusual?

WHY THIS EXISTS. Every rate in this project is built from five counties. A
reviewer is entitled to ask the obvious question: is this region representative,
or did the project pick the one corner of Florida where walking and cycling are
unusually deadly? Without an answer, the result can be waved away as a local
curiosity; with one, it either generalises or it is a finding in its own right.

Rebuilding MEP for all of Florida would answer it and is not worth it: about
13,400 block groups against our 2,170, roughly 180 million routing pairs, and
some thirty transit feeds, for a number that would then be a state average
rather than a place. The cheap version is this file. Compare CASUALTY SHARES.

WHAT IS COMPARED. Pedestrian and cyclist deaths and serious injuries, 2019-2025,
our five counties against the whole state, both from Signal Four - ours from the
licensed record-level extract, Florida's from the public dashboard's emphasis
area chart. If our five counties held a share of the state's pedestrian and
cyclist deaths equal to their share of its people, the ratio below would be 1.0.

WHAT THIS CANNOT DO. It says nothing about EXPOSURE. Florida-wide walking and
cycling mileage is not published either, so this compares casualty counts to
population, not to miles travelled. A ratio above 1.0 is consistent with two
different worlds: more dangerous conditions, or more walking and cycling. It
narrows the question; it does not settle it. Saying so is the point.

Figures transcribed 2026-09-15 from the dashboard, State of Florida, All LE
Agencies, Fatalities & Serious Injuries, reading the Emphasis Areas chart for
each year. Population share uses MIDPERIOD_POP against Florida's mid-2022
population.

Writes: data/final/florida_context.csv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import MIDPERIOD_POP  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"

SNAPSHOT_DATE = "2026-09-15"
FL_POP_2022 = 22_244_823          # Census, Florida, 1 July 2022

# year -> (pedestrian & cyclist deaths, serious injuries), whole state
FLORIDA_PED_BIKE = {
    2019: (905, 2338), 2020: (892, 2061), 2021: (1045, 2200),
    2022: (1019, 2244), 2023: (1034, 2273), 2024: (897, 2345),
    2025: (861, 2369),
}


def main():
    cas = INTERIM / "casualties_by_mode.csv"
    if not cas.exists():
        sys.exit("FAIL: casualties_by_mode.csv missing. Run step 02 first.")
    with cas.open(encoding="utf8") as fh:
        rows = {r["mode"]: r for r in csv.DictReader(fh)}
    for m in ("walk", "bike"):
        if m not in rows:
            sys.exit(f"FAIL: casualties_by_mode.csv has no '{m}' row. The mode "
                     f"names in step 02 have changed, so this comparison would "
                     f"silently compare the wrong thing.")

    ours_K = sum(int(rows[m]["K"]) for m in ("walk", "bike"))
    ours_A = sum(int(rows[m]["A"]) for m in ("walk", "bike"))
    fl_K = sum(v[0] for v in FLORIDA_PED_BIKE.values())
    fl_A = sum(v[1] for v in FLORIDA_PED_BIKE.values())

    pop_share = MIDPERIOD_POP / FL_POP_2022
    k_share, a_share = ours_K / fl_K, ours_A / fl_A
    ratio = k_share / pop_share

    print(f"PEDESTRIAN AND CYCLIST CASUALTIES, 2019-2025 "
          f"(dashboard snapshot {SNAPSHOT_DATE})")
    print(f"  {'':<26}{'killed':>9}{'serious':>10}")
    print(f"  {'Florida, whole state':<26}{fl_K:>9,}{fl_A:>10,}")
    print(f"  {'our five counties':<26}{ours_K:>9,}{ours_A:>10,}")
    print(f"  {'our share of Florida':<26}{k_share:>9.1%}{a_share:>10.1%}")
    print(f"\n  our share of Florida's people: {pop_share:.1%}")
    print(f"  deaths share / population share: {ratio:.2f}")

    if ratio > 1.0:
        print(f"\n  Tampa Bay carries {ratio - 1:.0%} MORE of Florida's "
              f"pedestrian and cyclist deaths than its population share.")
    else:
        print(f"\n  Tampa Bay carries {1 - ratio:.0%} LESS than its "
              f"population share.")
    print("  This does NOT separate danger from exposure: it is consistent "
          "with\n  more dangerous conditions OR with more walking and cycling. "
          "Neither\n  Florida nor this region publishes walking and cycling "
          "mileage.")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "florida_context.csv").open("w", newline="",
                                              encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        w.writerow(["florida_ped_bike_killed_2019_2025", fl_K])
        w.writerow(["florida_ped_bike_serious_2019_2025", fl_A])
        w.writerow(["d7_ped_bike_killed_2019_2025", ours_K])
        w.writerow(["d7_ped_bike_serious_2019_2025", ours_A])
        w.writerow(["d7_share_of_florida_deaths", f"{k_share:.4f}"])
        w.writerow(["d7_share_of_florida_population", f"{pop_share:.4f}"])
        w.writerow(["concentration_ratio", f"{ratio:.3f}"])
        w.writerow(["snapshot_date", SNAPSHOT_DATE])
    print(f"\nwrote {FINAL / 'florida_context.csv'}")


if __name__ == "__main__":
    main()
