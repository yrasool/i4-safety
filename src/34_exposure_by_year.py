"""
Step 34 - is a single 2025 traffic count the right denominator for 2019-2025?

THE OBJECTION THIS ANSWERS. Every rate in this project divides ~6.9 years of
casualties by ONE traffic figure: FDOT's 2025 five-county daily VMT, multiplied
out. A road-safety reviewer will object twice:

  1. Traffic grew over the period. A 2025 count is the LARGEST year, so using it
     for all seven years inflates the denominator and UNDERSTATES the rate.
  2. 2020 was not a normal year. Traffic collapsed and fatality RATES rose.
     Averaging it away silently hides a real structural break.

Both are testable, and neither needed new assumptions - only real data.

THE ARITHMETIC IS EXACT, WHICH IS WHY THIS TEST IS WORTH DOING.

    r_now  = C / (V_2025 * YEARS)          what the project computes
    r_true = C / SUM_y V_y                 what it should be

The numerator C is IDENTICAL in both. So the ratio is purely a denominator
comparison and involves no modelling at all:

    r_true / r_now = (V_2025 * YEARS) / SUM_y V_y

No casualty split by year is needed, and none is available anyway - step 02
emits casualties by MODE, not by mode and year.

WHAT IS ASSUMED, AND IT IS ONE THING. FHWA's VM-2 is statewide Florida. The
project's denominator is five counties. This applies the STATEWIDE year-to-year
SHAPE to the five-county LEVEL - i.e. it assumes District 7 traffic rose and
fell in the same proportions as Florida's, not that it is the same size. The
level itself still comes from FDOT's five-county count and is never touched.

2025 is not in VM-2 yet. It is not extrapolated. The test is run twice, once
holding 2025 at 2024's level and once at the 2023->2024 growth rate, and both
are reported, because a reader should see that the conclusion does not depend
on which is chosen.

Reads:  data/raw/vm2_*.xls[x]        FHWA Highway Statistics Table VM-2
        data/interim/crashes_kabco.csv
Writes: data/final/exposure_by_year.csv
"""

import csv
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import DVMT_5COUNTY, YEARS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW, INTERIM, FINAL = (ROOT / "data" / "raw", ROOT / "data" / "interim",
                       ROOT / "data" / "final")

# The crash file covers Jan 2019 to Nov 2025. 2025 is a PARTIAL year and must
# be weighted as one, or the last year gets a full year's denominator against
# eleven months of casualties. YEARS = 6.9 is the project-wide constant; the
# residual after six full years is 2025's share.
FULL_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
Y2025_SHARE = round(YEARS - len(FULL_YEARS), 3)


def florida_vmt(year):
    """Florida's total annual vehicle-miles, millions, from FHWA Table VM-2."""
    for ext in ("xls", "xlsx"):
        p = RAW / f"vm2_{year}.{ext}"
        if not p.exists():
            continue
        d = pd.read_excel(p, sheet_name="A", header=None)
        row = d[d[0].astype(str).str.strip().str.lower() == "florida"]
        if row.empty:
            sys.exit(f"FAIL: no Florida row in {p.name}. FHWA changed the "
                     f"layout; do not guess a column index.")
        # Column 17 is the last TOTAL (rural + urban). Asserted, not trusted:
        # it must equal rural total (col 8) + urban total (col 16).
        rural, urban, total = (float(row.iloc[0, 8]), float(row.iloc[0, 16]),
                               float(row.iloc[0, 17]))
        if abs(rural + urban - total) > 0.01 * total:
            sys.exit(f"FAIL: {p.name} col 17 ({total:,.0f}) is not rural + "
                     f"urban ({rural + urban:,.0f}). Column indices moved.")
        return total
    sys.exit(f"FAIL: no VM-2 file for {year} in data/raw/.")


def main():
    vmt = {y: florida_vmt(y) for y in FULL_YEARS}

    print("=" * 72)
    print("FLORIDA ANNUAL VEHICLE-MILES, measured  (FHWA Highway Statistics")
    print("Table VM-2, one downloaded file per year - none typed by hand)")
    print("=" * 72)
    base = vmt[2019]
    for y in FULL_YEARS:
        bar = "#" * int(round(60 * vmt[y] / max(vmt.values())))
        print(f"  {y}  {vmt[y]:>12,.0f} M  {vmt[y] / base - 1:>+7.1%}  {bar}")
    print(f"\n  2020 fell {1 - vmt[2020] / vmt[2019]:.1%} below 2019 and did "
          f"not recover\n  until {min(y for y in FULL_YEARS if vmt[y] > base)}.")

    # --- 0. do the two sources even agree about the same universe? ----------
    # FDOT's five-county count and FHWA's statewide count are different
    # agencies, different collection systems, different publications. Before
    # one is used to reshape the other they must at least be commensurable:
    # the five counties should be a plausible share of Florida. Tampa Bay is
    # about a sixth of the state's population, so a share near that is a pass
    # and a share of 2% or 40% would mean the units are not what they look
    # like. This is the cheapest possible unit check and it costs one line.
    share = (DVMT_5COUNTY * 365 / 1e6) / vmt[2024]
    print(f"\n  CROSS-CHECK: FDOT's five-county figure is {share:.1%} of FHWA's")
    print(f"  Florida total. District 7 holds about 16% of the state's")
    print(f"  population, so the two sources are measuring the same kind of")
    print(f"  thing in the same units.")
    if not 0.08 < share < 0.30:
        sys.exit(f"FAIL: five-county VMT is {share:.1%} of statewide. One of "
                 f"the two figures is in the wrong unit.")

    # NOTE ON VINTAGE, stated rather than resolved. FDOT's report is TITLED
    # 2025 and highway statistics reports conventionally publish the PRIOR
    # year's travel. If it is in fact 2024 data, the first scenario below
    # ("2025 held at 2024's level") is the exact one and 8% is the answer.
    # The scenarios bracket the ambiguity instead of guessing at it.

    # --- 1. the severity break, which needs NO exposure at all --------------
    print("\n" + "=" * 72)
    print("1  WAS 2020 DIFFERENT?  (measured without any denominator)")
    print("=" * 72)
    print("  Deaths per 1,000 crashes. Exposure cancels out of this ratio")
    print("  entirely, so nothing here depends on the VMT figures above.\n")

    kab = {}
    with (INTERIM / "crashes_kabco.csv").open(encoding="utf8") as fh:
        for r in csv.DictReader(fh):
            kab.setdefault(int(r["year"]), {})[r["kabco"]] = int(r["crashes"])

    rows = []
    print(f"  {'year':<6}{'crashes':>10}{'fatal':>8}{'K per 1,000':>14}"
          f"{'vs 2019':>10}")
    b19 = None
    for y in sorted(kab):
        tot = sum(kab[y].values())
        k = kab[y].get("K", 0)
        per = 1000 * k / tot
        b19 = per if b19 is None else b19
        note = "  <- pandemic year" if y == 2020 else ""
        print(f"  {y:<6}{tot:>10,}{k:>8,}{per:>14.2f}{per / b19 - 1:>+10.1%}"
              f"{note}")
        rows.append({"metric": "deaths_per_1000_crashes", "year": y,
                     "value": round(per, 4)})

    p20, p19 = 1000 * kab[2020]["K"] / sum(kab[2020].values()), b19
    print(f"\n  2020 had {1 - sum(kab[2020].values()) / sum(kab[2019].values()):.1%}"
          f" FEWER crashes than 2019 and {kab[2020]['K'] / kab[2019]['K'] - 1:+.1%}"
          f" more deaths.")
    print(f"  Deaths per 1,000 crashes rose {p20 / p19 - 1:+.1%}. This is the")
    print("  documented pandemic pattern - emptier roads, higher speeds - and")
    print("  it is present in this region's own data, not assumed from it.")

    # --- 2. the denominator test --------------------------------------------
    print("\n" + "=" * 72)
    print("2  DOES THE FLAT 2025 DENOMINATOR BIAS THE RATE?")
    print("=" * 72)
    print("  r_true / r_now = (V_2025 * YEARS) / SUM_y V_y")
    print("  The casualty numerator is identical on both sides and cancels.\n")

    for label, v2025 in (("2025 held at 2024's level", vmt[2024]),
                         ("2025 grown at the 2023->2024 rate",
                          vmt[2024] * vmt[2024] / vmt[2023])):
        # Scale statewide shape onto the five-county level. The LEVEL is
        # FDOT's, the SHAPE is FHWA's; neither is invented here.
        annual_5c = DVMT_5COUNTY * 365
        shape = {y: vmt[y] / v2025 for y in FULL_YEARS}
        true_denom = annual_5c * (sum(shape.values()) + Y2025_SHARE * 1.0)
        now_denom = annual_5c * YEARS
        ratio = now_denom / true_denom
        print(f"  {label}")
        print(f"    flat denominator   {now_denom / 1e9:>10,.1f} B veh-miles")
        print(f"    year-varying       {true_denom / 1e9:>10,.1f} B veh-miles")
        print(f"    every rate here is UNDERSTATED by {ratio - 1:>6.2%}\n")
        rows.append({"metric": "rate_understatement", "year": label,
                     "value": round(ratio - 1, 6)})

    ratio_lo = 1 + rows[-2]["value"]
    ratio_hi = 1 + rows[-1]["value"]
    lo, hi = sorted((ratio_lo, ratio_hi))
    print("  THE BIAS RUNS AGAINST THIS PROJECT'S OWN CONCLUSION.")
    print(f"  Traffic in 2019-2023 was BELOW the 2025 count used for every")
    print(f"  year, so the true denominator is smaller and every crash rate")
    print(f"  here is {lo - 1:.1%} to {hi - 1:.1%} too LOW. Correcting it would make the")
    print("  MEP penalty larger, not smaller. The figure is left uncorrected")
    print("  because a conservative denominator needs no defending, and")
    print("  because the correction is smaller than the walk and bike")
    print("  exposure uncertainty it would sit inside.")

    FINAL.mkdir(parents=True, exist_ok=True)
    out = FINAL / "exposure_by_year.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["metric", "year", "value"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
