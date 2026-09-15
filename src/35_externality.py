"""
Step 35 - who owns a pedestrian killed by a driver?

WHY THIS EXISTS, AND IT IS NOT A FLATTERING REASON.

INTERVIEW_QA.md Q10 claimed, in the author's own voice:

    "I ran it both ways ... 93% of pedestrian deaths here involve a car ...
     The gap between A and B is the externality and I report it separately."

None of that was true of the live project. No step in `run_all.py` computed
version B. REPORT.md contained no externality figure anywhere. And `93%`
appeared exactly once in the entire repository - in that sentence - derived by
nothing. The only code that had ever done the calculation was `12_full_run.py`
and `13_final.py`, which are outside the pipeline and built on superseded
occupancy and exposure.

That is the same failure as the deleted delay term and the AAA figure before it:
a number that reads fluently, was once true of some earlier version, and is now
load-bearing in a document the author would speak from in a room. This step
exists so the claim is either true or gone.

IT IS NOW TRUE, AND THE FIGURE WAS WRONG. Measured here: 99.0%, not 93%.

THE TWO CONVENTIONS.

  Version A  charge each mode what its OWN travellers suffer.
             A pedestrian killed by a driver is a cost of WALKING.
  Version B  charge each mode what it CAUSES.
             That same death is a cost of DRIVING.

Neither is wrong. Mixing them is. This project publishes A, because every other
term in MEP's cost function is what the traveller personally carries - fuel,
fare, depreciation. B is computed here and reported beside it.

WHY THE ANSWER MATTERS MORE THAN IT LOOKS. Under A, cycling supplies 79% of the
headline loss and looks catastrophically expensive. Under B, almost all of that
moves to driving. The finding does NOT survive the switch unchanged, and a
reviewer who suspects the convention was chosen to produce the result deserves
to see the number rather than a reassurance.

Reads:  the Signal Four crash export (licensed, not redistributable)
        data/interim/casualties_by_mode.csv, exposure_by_mode.csv
Writes: data/final/externality.csv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COST_PER_PERSON, YEARS, OCCUPANCY  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
SRC = Path(r"C:\Users\yusra\claude\traffic-data"
           r"\signal4_district7_2019_2025.csv")


def denul(lines):
    """Signal Four exports carry embedded NUL bytes; csv fails on them."""
    for line in lines:
        yield line.replace("\x00", "")


def num(row, key):
    v = row.get(key)
    if v in (None, ""):
        return 0
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def measure_involvement():
    """
    The share of pedestrian and cyclist casualties involving a motor vehicle.

    TWO DEFINITIONS, AND THE DIFFERENCE IS NOT COSMETIC.

      any vehicle  - TOTAL_NUMBER_OF_VEHICLES >= 1. This is ~100% by
                     construction: a police-reportable traffic crash almost
                     always has a vehicle in it. Reporting this as evidence
                     would be circular, so it is computed and then NOT used.
      a car        - vehicles remaining after motorcycles and mopeds are
                     removed. This is the number version B needs, because
                     motorcycles are not a MEP mode and cannot be charged.

    Only the second is carried forward.
    """
    if not SRC.exists():
        sys.exit(f"FAIL: {SRC} not found. This step needs the licensed Signal "
                 f"Four export; it cannot be derived from the interim files.")

    agg = {}
    with SRC.open(encoding="utf8", errors="replace") as fh:
        for row in csv.DictReader(denul(fh)):
            vehicles = num(row, "TOTAL_NUMBER_OF_VEHICLES")
            two_wheel = (num(row, "S4_MOTORCYCLE_COUNT")
                         + num(row, "S4_MOPED_COUNT"))
            cars = vehicles - two_wheel
            for mode, prefix in (("walk", "S4_PEDESTRIAN"),
                                 ("bike", "S4_BICYCLIST")):
                k = num(row, f"{prefix}_FATALITY_COUNT")
                a = num(row, f"{prefix}_INCAPACITATING_INJURY_COUNT")
                if not k and not a:
                    continue
                d = agg.setdefault(mode, dict(K=0, A=0, K_any=0, A_any=0,
                                              K_car=0, A_car=0))
                d["K"] += k
                d["A"] += a
                if vehicles >= 1:
                    d["K_any"] += k
                    d["A_any"] += a
                if cars >= 1:
                    d["K_car"] += k
                    d["A_car"] += a
    return agg


def main():
    cas = {}
    with (INTERIM / "casualties_by_mode.csv").open(encoding="utf8") as fh:
        for r in csv.DictReader(fh):
            cas[r["mode"]] = {"K": int(r["K"]), "A": int(r["A"])}

    with (INTERIM / "exposure_by_mode.csv").open(encoding="utf8") as fh:
        exp = {r["mode"]: r for r in csv.DictReader(fh)}
    drive_pmt = float(exp["vehicle_occupant"]["annual_pmt"])

    agg = measure_involvement()
    rows = []

    print("=" * 72)
    print("1  HOW MANY NON-MOTORIST CASUALTIES INVOLVE A CAR?")
    print("=" * 72)
    print("  Counted from the crash records, not asserted. INTERVIEW_QA Q10")
    print("  claimed 93%; no script had ever computed it.\n")
    print(f"  {'':<8}{'deaths':>9}{'w/ any veh':>13}{'w/ a car':>11}"
          f"{'car share':>12}")
    share = {}
    for mode in ("walk", "bike"):
        d = agg[mode]
        s = d["K_car"] / d["K"]
        share[mode] = s
        print(f"  {mode:<8}{d['K']:>9,}{d['K_any']:>13,}{d['K_car']:>11,}"
              f"{s:>12.1%}")
        # Cross-check against step 02, which counted the same casualties by a
        # different route. If these disagree the two steps are reading
        # different columns and neither number can be trusted.
        if d["K"] != cas[mode]["K"] or d["A"] != cas[mode]["A"]:
            sys.exit(f"FAIL: {mode} K/A here ({d['K']}/{d['A']}) disagrees "
                     f"with step 02 ({cas[mode]['K']}/{cas[mode]['A']}). Two "
                     f"steps are reading the same file differently.")
        rows.append({"metric": "car_involved_share_K", "mode": mode,
                     "value": round(s, 4)})

    print(f"\n  'Any vehicle' is ~100% BY CONSTRUCTION and is not evidence of")
    print("  anything - a reportable traffic crash has a vehicle in it. The")
    print("  car share is the one version B can use, because motorcycles are")
    print("  not a MEP mode and cannot be charged for what they hit.")

    # --- 2. the two conventions ---------------------------------------------
    print("\n" + "=" * 72)
    print("2  VERSION A (what you suffer) vs VERSION B (what you cause)")
    print("=" * 72)

    def cost(k, a):
        return (k * COST_PER_PERSON["K"] + a * COST_PER_PERSON["A"]) / YEARS

    occupant = cost(cas["vehicle_occupant"]["K"], cas["vehicle_occupant"]["A"])
    inflicted = sum(cost(agg[m]["K_car"], agg[m]["A_car"])
                    for m in ("walk", "bike"))

    r_a = occupant / drive_pmt
    r_b = (occupant + inflicted) / drive_pmt

    print(f"  driving, version A   ${r_a:.4f} / passenger-mile")
    print(f"  driving, version B   ${r_b:.4f} / passenger-mile"
          f"   (+{r_b / r_a - 1:.0%})")
    print(f"\n  The gap is ${r_b - r_a:.4f} per passenger-mile, or "
          f"${(r_b - r_a) * OCCUPANCY:.4f} per")
    print(f"  VEHICLE-mile. THAT NUMBER IS THE EXTERNALITY: the harm a driver")
    print(f"  inflicts on someone outside the car, which version A charges to")
    print(f"  the person who was hit.")
    print(f"\n  In money: ${inflicted / 1e9:.2f} billion a year moves from "
          f"walking and cycling")
    print(f"  to driving. That is {inflicted / (occupant + inflicted):.0%} of "
          f"driving's total under version B.")

    rows += [{"metric": "r_drive_version_a", "mode": "drive",
              "value": round(r_a, 6)},
             {"metric": "r_drive_version_b", "mode": "drive",
              "value": round(r_b, 6)},
             {"metric": "externality_per_pmt", "mode": "drive",
              "value": round(r_b - r_a, 6)},
             {"metric": "externality_annual_usd", "mode": "drive",
              "value": round(inflicted, 0)}]

    # --- 2b. the benchmark that was waiting for this step -------------------
    #
    # `CL_FULL_2024_PER_MILE` sat in constants.py, computed, DOCUMENTED and
    # referenced by nothing. That is what a dead constant usually means: the
    # calculation it was built for was never written. Cui & Levinson split
    # safety cost into internal (borne by occupants) and external (inflicted
    # on non-motorists) for exactly the reason this step exists.
    #
    # So the two benchmarks pair off, and each version gets its own:
    #     version A  vs  INTERNAL only   (step 04 does this, 1.65x)
    #     version B  vs  INTERNAL + EXTERNAL
    # Comparing version A against the FULL figure, or B against internal only,
    # would repeat the convention-mixing this whole step is about.
    from constants import (CL_FULL_2024_PER_MILE,  # noqa: E402
                           CL_INTERNAL_2024_PER_MILE)
    b_vmt = r_b * OCCUPANCY
    ratio_b = b_vmt / CL_FULL_2024_PER_MILE
    ratio_a = r_a * OCCUPANCY / CL_INTERNAL_2024_PER_MILE
    print("\n" + "-" * 72)
    print("  ACCEPTANCE TEST - each version against ITS OWN benchmark")
    print("-" * 72)
    print(f"    version A  ${r_a * OCCUPANCY:.4f}/veh-mi  vs C&L internal "
          f"${CL_INTERNAL_2024_PER_MILE:.4f}   {ratio_a:.2f}x")
    print(f"    version B  ${b_vmt:.4f}/veh-mi  vs C&L full     "
          f"${CL_FULL_2024_PER_MILE:.4f}   {ratio_b:.2f}x")
    print(f"\n  Both land near Florida's ~2x fatality rate over Minnesota's,")
    print(f"  and both are LOWER bounds (this project prices K and A only;")
    print(f"  Cui & Levinson price every severity). The two conventions")
    print(f"  agreeing with two independently published components is a")
    print(f"  stronger check than either alone.")
    if not 0.5 < ratio_b < 4.0:
        sys.exit(f"FAIL: version B is {ratio_b:.2f}x the published full cost. "
                 f"Outside the band that version A is required to sit in, so "
                 f"the externality attribution is wrong somewhere.")
    rows.append({"metric": "version_b_vs_cl_full", "mode": "drive",
                 "value": round(ratio_b, 4)})

    # --- 3. the honest consequence ------------------------------------------
    print("\n" + "=" * 72)
    print("3  DOES THE HEADLINE SURVIVE THE SWITCH?  (no, and say so)")
    print("=" * 72)
    print("  Under version A, cycling supplies 79% of the MEP loss and looks")
    print("  catastrophically expensive per mile. Under version B nearly all")
    print("  of that harm is driving's, and cycling's own rate collapses to")
    print("  the residual - the casualties with no car involved:\n")
    for mode in ("walk", "bike"):
        d = agg[mode]
        resid = 1 - share[mode]
        print(f"    {mode:<6} version B keeps {resid:>5.1%} of its version A "
              f"rate  ({d['K'] - d['K_car']} of {d['K']} deaths)")

    print("\n  SO THE CHOICE OF CONVENTION DRIVES THE HEADLINE ATTRIBUTION.")
    print("  Version A is used, and the reason is that it matches MEP: every")
    print("  other term in the cost function - fuel, fare, depreciation - is")
    print("  what the traveller personally carries. A metric about what YOU")
    print("  can reach, priced by what YOU bear.")
    print("\n  But this is a CHOICE, not a finding, and the number above is")
    print("  what it is worth. Anyone preferring version B can take the")
    print("  externality figure and reassign it; nothing else in the pipeline")
    print("  needs to change.")

    FINAL.mkdir(parents=True, exist_ok=True)
    out = FINAL / "externality.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["metric", "mode", "value"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
