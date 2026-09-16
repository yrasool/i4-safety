"""
Step 37 - check our licensed crash extract against S4's PUBLIC dashboard.

WHY THIS EXISTS. Every casualty number in this project comes from ONE source:
the Signal Four Analytics record-level extract. That extract is licensed, so no
reviewer can open it and check the totals. A single source that nobody else can
inspect is exactly the shape of an error that survives to an interview.

Signal Four also publishes a PUBLIC dashboard (signal4analytics.com) with no
login: fatalities and serious injuries, by county, by year, 2014 to date. It is
built from the same database, but it is a DIFFERENT PRODUCT, reached a different
way, and anybody can reproduce it in a browser in two minutes.

So the two must agree. If they do not, one of these is true and all of them
matter: the extract is filtered in a way this project did not account for, the
county set is wrong, the year range is wrong, or the person-versus-crash
distinction has been mixed up somewhere.

WHAT IS COMPARED. People, not crashes. The dashboard counts PEOPLE killed and
PEOPLE seriously injured, which is what this project prices; step 02's
casualties_by_mode.csv counts the same. crashes_kabco.csv counts CRASHES by
their worst injury and is NOT comparable - reading that file here would be the
unit error this project has already made twice.

TOLERANCE. 5%. Our extract ends in November 2025 while the dashboard runs to
July 2026, so our 2025 is short by about six weeks and our totals should come
in SLIGHTLY LOW. A ratio above 1.0, or below 0.95, means something is wrong.

Figures transcribed 2026-09-15 from the dashboard's own chart labels, county by
county, with no filters set other than the county and Fatalities & Serious
Injuries. They are a fixed snapshot: the dashboard is revised as reports are
filed, so a rerun years from now may differ slightly. That is a reason to record
the date, not a reason to skip the check.

Writes: data/final/s4_public_check.csv
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"

SNAPSHOT_DATE = "2026-09-15"
YEARS = list(range(2014, 2027))
STUDY_YEARS = range(2019, 2026)          # our extract's coverage
TOLERANCE = 0.05

# county -> {"K": fatalities by year, "A": serious injuries by year}
S4_PUBLIC = {
    "Hillsborough": {
        "A": [1693, 1411, 1373, 1378, 1228, 1207, 1089, 1032, 1065, 1026, 932,
              798, 344],
        "K": [158, 190, 227, 191, 176, 219, 213, 272, 225, 230, 180, 176, 70]},
    "Pinellas": {
        "A": [1105, 1200, 1222, 991, 859, 805, 792, 840, 697, 639, 686, 628,
              296],
        "K": [116, 103, 127, 119, 129, 108, 108, 158, 124, 112, 108, 96, 33]},
    "Pasco": {
        "A": [1114, 1306, 1188, 1149, 915, 1047, 999, 836, 755, 639, 478, 419,
              195],
        "K": [71, 70, 86, 108, 99, 99, 108, 104, 105, 92, 111, 84, 39]},
    "Hernando": {
        "A": [241, 252, 266, 268, 328, 337, 252, 362, 323, 211, 277, 205, 113],
        "K": [20, 35, 25, 34, 31, 25, 44, 33, 45, 45, 44, 48, 14]},
    "Citrus": {
        "A": [219, 252, 224, 258, 219, 225, 239, 190, 165, 111, 127, 93, 50],
        "K": [27, 29, 24, 31, 37, 22, 39, 37, 25, 26, 32, 29, 20]},
}


def main():
    for c, v in S4_PUBLIC.items():
        for k in ("K", "A"):
            if len(v[k]) != len(YEARS):
                sys.exit(f"FAIL: {c}/{k} has {len(v[k])} values, "
                         f"expected {len(YEARS)}")

    idx = {y: i for i, y in enumerate(YEARS)}
    pub = {y: (sum(S4_PUBLIC[c]["K"][idx[y]] for c in S4_PUBLIC),
               sum(S4_PUBLIC[c]["A"][idx[y]] for c in S4_PUBLIC))
           for y in YEARS}

    cas = INTERIM / "casualties_by_mode.csv"
    if not cas.exists():
        sys.exit("FAIL: casualties_by_mode.csv missing. Run step 02 first.")
    with cas.open(encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    ours_K = sum(int(r["K"]) for r in rows)
    ours_A = sum(int(r["A"]) for r in rows)

    pub_K = sum(pub[y][0] for y in STUDY_YEARS)
    pub_A = sum(pub[y][1] for y in STUDY_YEARS)

    print(f"S4 PUBLIC DASHBOARD, snapshot {SNAPSHOT_DATE}, five D7 counties")
    print(f"  {'year':<6}{'killed':>9}{'serious':>10}")
    for y in YEARS:
        note = "  <- partial" if y == 2026 else ""
        print(f"  {y:<6}{pub[y][0]:>9,}{pub[y][1]:>10,}{note}")

    print(f"\n{'':<24}{'killed':>9}{'serious':>10}")
    print(f"  {'public dashboard':<22}{pub_K:>9,}{pub_A:>10,}")
    print(f"  {'our extract':<22}{ours_K:>9,}{ours_A:>10,}")
    rK, rA = ours_K / pub_K, ours_A / pub_A
    print(f"  {'ratio, ours/public':<22}{rK:>9.3f}{rA:>10.3f}")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "s4_public_check.csv").open("w", newline="",
                                              encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "public_dashboard", "our_extract", "ratio"])
        w.writerow(["killed 2019-2025", pub_K, ours_K, f"{rK:.4f}"])
        w.writerow(["serious 2019-2025", pub_A, ours_A, f"{rA:.4f}"])
        w.writerow(["snapshot_date", SNAPSHOT_DATE, "", ""])

    bad = [n for n, r in (("killed", rK), ("serious", rA))
           if not (1 - TOLERANCE) <= r <= 1.0]
    if bad:
        sys.exit(f"\nFAIL: {', '.join(bad)} outside 0.95-1.00 of the public "
                 f"dashboard. Our extract ends Nov 2025, so it should be a "
                 f"little LOW; above 1.0 means double counting, far below "
                 f"means a filter or county set is wrong.")
    print(f"\nPASS - within {TOLERANCE:.0%}, and low as expected "
          f"(our extract stops in November 2025).")


if __name__ == "__main__":
    main()
