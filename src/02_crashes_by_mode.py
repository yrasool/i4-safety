"""
Step 02 - casualties by mode, from 602,110 police crash records.

The slow stage. One pass over a 503 MB file.

THREE THINGS THIS STEP GETS RIGHT, EACH OF WHICH WAS A TRAP:

  VINs never leave this script. V1_VIN/V2_VIN and driver ages are personally
  identifying, inside licensed Signal Four data. Only the columns listed in KEEP
  are read at all, and no identifier is among them.

  Mode is attributed by WHO WAS HURT, not by what vehicles were present. A
  pedestrian struck by a car is a walking casualty, not a driving one - the
  question the metric asks is what injury a person travelling by mode k bears.

  KSI (killed + seriously injured) is the only basis on which all modes are
  comparable, because Signal Four breaks out non-motorist casualties ONLY at
  fatality and incapacitating level. There is no pedestrian "possible injury"
  count. Full KABCO is therefore computed for motorists alone, and reported
  separately, never side by side with a KSI figure.

Transit is deliberately absent. A bus-car crash injures mostly the car's
occupants, and this file has no per-vehicle occupant injury counts, so bus
involvement cannot be turned into injuries-to-riders. Step 03 takes transit from
NTD safety data instead, which measures it directly.

Writes: data/interim/casualties_by_mode.csv
        data/interim/crashes_kabco.csv
"""

import csv
from collections import Counter
from pathlib import Path

import pandas as pd

SRC = Path(r"C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv")
OUTDIR = Path(__file__).resolve().parents[1] / "data" / "interim"

# Read only these. Nothing identifying is in the list, by construction.
KEEP = [
    "CRASH_YEAR",
    "S4_CRASH_SEVERITY_DETAIL",
    "S4_FATALITY_COUNT",
    "S4_INCAPACITATING_INJURY_COUNT",
    "S4_PEDESTRIAN_FATALITY_COUNT",
    "S4_PEDESTRIAN_INCAPACITATING_INJURY_COUNT",
    "S4_BICYCLIST_FATALITY_COUNT",
    "S4_BICYCLIST_INCAPACITATING_INJURY_COUNT",
    "S4_MOTORCYCLIST_FATALITY_COUNT",
    "S4_MOTORCYCLIST_INCAPACITATING_INJURY_COUNT",
]

# S4_CRASH_SEVERITY_DETAIL maps 1:1 onto KABCO. The coarse S4_CRASH_SEVERITY
# does not - it merges C into B - so it is not used.
KABCO = {
    "Fatal (within 30 days)": "K",
    "Incapacitating Injury": "A",
    "Non-Incapacitating Injury": "B",
    "Possible Injury": "C",
    "No Injury": "O",
    # Not a traffic fatality. Excluded from K rather than silently counted.
    "Non-Traffic Fatality": None,
}


def denul(fh):
    """Signal Four exports carry embedded NUL bytes; csv fails on them."""
    for line in fh:
        yield line.replace("\x00", "")


def num(row, col):
    v = row.get(col)
    if not v:
        return 0
    try:
        return int(float(v))
    except ValueError:
        return 0


def main():
    sev = Counter()          # crashes by KABCO
    sev_year = Counter()     # (year, kabco)
    cas = Counter()          # (mode, K|A) casualties
    unmapped = Counter()
    clamp = Counter()            # residual went negative
    clamp_magnitude = Counter()  # by how much, in persons
    excluded_nontraffic = 0
    rows = 0

    with SRC.open("r", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(denul(fh)):
            rows += 1

            detail = (row.get("S4_CRASH_SEVERITY_DETAIL") or "").strip()
            if detail in KABCO:
                k = KABCO[detail]
                if k is None:
                    excluded_nontraffic += 1
                else:
                    sev[k] += 1
                    sev_year[(row.get("CRASH_YEAR"), k)] += 1
            else:
                unmapped[detail] += 1

            # Casualties, K and A only - the basis all modes share.
            tot_k = num(row, "S4_FATALITY_COUNT")
            tot_a = num(row, "S4_INCAPACITATING_INJURY_COUNT")

            ped_k = num(row, "S4_PEDESTRIAN_FATALITY_COUNT")
            ped_a = num(row, "S4_PEDESTRIAN_INCAPACITATING_INJURY_COUNT")
            bik_k = num(row, "S4_BICYCLIST_FATALITY_COUNT")
            bik_a = num(row, "S4_BICYCLIST_INCAPACITATING_INJURY_COUNT")
            mot_k = num(row, "S4_MOTORCYCLIST_FATALITY_COUNT")
            mot_a = num(row, "S4_MOTORCYCLIST_INCAPACITATING_INJURY_COUNT")

            cas[("walk", "K")] += ped_k
            cas[("walk", "A")] += ped_a
            cas[("bike", "K")] += bik_k
            cas[("bike", "A")] += bik_a
            cas[("motorcycle", "K")] += mot_k
            cas[("motorcycle", "A")] += mot_a

            # Whoever is left is a motor-vehicle occupant. The residual can go
            # negative when non-motorist counts exceed the crash total, so it is
            # clamped - but the clamp is COUNTED, because it feeds
            # `vehicle_occupant`, which is the sole basis for r_drive, which is
            # what the step 04 acceptance test is reconciled against. Clamping
            # is one-directional: it can only undercount vehicle occupants, so
            # a high hit rate would bias r_drive LOW and could mask a method
            # error while the acceptance test still reported a pass.
            # NB: the loop variable must NOT be named `sev` - that is the
            # KABCO Counter, and shadowing it corrupts the crash totals.
            for lvl, tot, ped, bik, mot in (("K", tot_k, ped_k, bik_k, mot_k),
                                            ("A", tot_a, ped_a, bik_a, mot_a)):
                resid = tot - ped - bik - mot
                if resid < 0:
                    clamp[lvl] += 1
                    clamp_magnitude[lvl] += -resid
                cas[("vehicle_occupant", lvl)] += max(0, resid)

            if rows % 100_000 == 0:
                print(f"  {rows:,}")

    print(f"\nread {rows:,} rows")
    if unmapped:
        print("  !! severity values not in the KABCO map:")
        for k, v in unmapped.most_common():
            print(f"     {k!r:<40}{v:>8,}")
    print(f"  excluded Non-Traffic Fatality: {excluded_nontraffic:,}")
    print("\n  vehicle-occupant residual clamped at zero:")
    for lvl in ("K", "A"):
        n, mag = clamp[lvl], clamp_magnitude[lvl]
        print(f"    {lvl}  {n:,} crashes ({n / rows:.4%})  "
              f"{mag:,} persons not counted")
    if clamp["K"] / rows > 0.001 or clamp["A"] / rows > 0.001:
        print("    !! above 0.1% - investigate the source columns rather "
              "than trusting the residual")

    print("\nCRASHES BY KABCO")
    for k in "KABCO":
        print(f"  {k}  {sev[k]:>9,}")
    print(f"     {sum(sev.values()):>9,}  total")

    print("\nCASUALTIES BY MODE  (K and A only - see module docstring)")
    print(f"  {'mode':<20}{'K':>8}{'A':>10}{'KSI':>10}")
    order = ["vehicle_occupant", "motorcycle", "walk", "bike"]
    for m in order:
        k, a = cas[(m, "K")], cas[(m, "A")]
        print(f"  {m:<20}{k:>8,}{a:>10,}{k + a:>10,}")
    tk = sum(cas[(m, "K")] for m in order)
    ta = sum(cas[(m, "A")] for m in order)
    print(f"  {'':<20}{tk:>8,}{ta:>10,}{tk + ta:>10,}")

    # Cross-check the mode split against the crash-level totals. These are
    # different columns counting different things (people vs crashes), so they
    # will not match exactly - but a large gap means the split is wrong.
    print(f"\n  cross-check: {tk:,} fatalities across {sev['K']:,} fatal crashes"
          f"  ({tk / sev['K']:.3f} per crash)")

    OUTDIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        [{"mode": m, "K": cas[(m, "K")], "A": cas[(m, "A")],
          "KSI": cas[(m, "K")] + cas[(m, "A")]} for m in order]
    ).to_csv(OUTDIR / "casualties_by_mode.csv", index=False)

    pd.DataFrame(
        [{"year": y, "kabco": k, "crashes": n}
         for (y, k), n in sorted(sev_year.items())]
    ).to_csv(OUTDIR / "crashes_kabco.csv", index=False)

    print(f"\nwrote {OUTDIR / 'casualties_by_mode.csv'}")
    print(f"wrote {OUTDIR / 'crashes_kabco.csv'}")


if __name__ == "__main__":
    main()
