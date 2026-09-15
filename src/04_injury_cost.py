"""
Step 04 - injury cost per passenger-mile, by mode. The term MEP is missing.

THIS STEP HAS AN ACCEPTANCE TEST, and it is not "did it produce a number".

Cui & Levinson (2019) measured internal safety cost at $0.040 per vehicle-km,
about $0.064 per vehicle-mile, in the Twin Cities - roughly 6% of full travel
cost. An earlier pass here landed near $0.505/mile, eight times that, which
would have been embarrassing to defend and was a signal that something was
wrong with the method rather than with Minnesota.

The error was mixing conventions. Three separate choices each inflate the
figure, and they compound:

  1. FHWA's comprehensive costs attach to a CRASH; this project counts
     CASUALTIES. Per-crash values applied to person counts overcount.
  2. All five KABCO levels were priced, but non-motorist casualties only exist
     at K and A, so the modes were never comparable in the first place.
  3. Dividing by VEHICLE-miles rather than PASSENGER-miles ignores occupancy.

This step fixes all three by construction:
  - USDOT BCA Table A-1a, value per INJURED PERSON, matching the numerator
  - KSI only, the one basis all four modes share
  - per PASSENGER-mile, matching the denominator MEP uses ($/PMT)

If the result still lands far from $0.064 after that, the method is still wrong
and the number must not be published.

Writes: data/final/injury_cost_by_mode.csv
"""

from pathlib import Path

import csv
import sys

import pandas as pd

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from constants import (COST_PER_PERSON, YEARS,  # noqa: E402
                       CL_INTERNAL_2024_PER_MILE, CL_INTERNAL_PER_VEHKM,
                       DEFLATOR_2010_2024, ACCEPT_LO, ACCEPT_HI, OCCUPANCY,
                       MIDPERIOD_POP)

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"




# Florida's fatality rate per VMT runs roughly double Minnesota's. Used only to
# say whether the residual points the right way, never to adjust the result.
FL_MN_FATALITY_RATIO = 2.0


def main():
    cas = pd.read_csv(INTERIM / "casualties_by_mode.csv").set_index("mode")
    exp = pd.read_csv(INTERIM / "exposure_by_mode.csv").set_index("mode")
    sld = pd.read_parquet(INTERIM / "sld.parquet")
    # SLD TotPop is pre-2020 and BELOW the 2020 census count for these five
    # counties. Using it against a 2019-2025 numerator overstated cost per
    # resident by 9.3%. Census PEP July 2022 is the study midpoint almost
    # exactly, so no interpolation is needed.
    pop = MIDPERIOD_POP
    sld_pop = int(sld["TotPop"].sum())

    print("ANNUAL KSI COST BY MODE  (USDOT per-person values, 2024 $)")
    print(f"  {'mode':<20}{'K/yr':>8}{'A/yr':>9}{'$B/yr':>10}")
    rows = []
    for mode in cas.index:
        k = cas.loc[mode, "K"] / YEARS
        a = cas.loc[mode, "A"] / YEARS
        cost = k * COST_PER_PERSON["K"] + a * COST_PER_PERSON["A"]
        rows.append({"mode": mode, "K_per_yr": k, "A_per_yr": a,
                     "cost_per_yr": cost})
        print(f"  {mode:<20}{k:>8.0f}{a:>9.0f}{cost / 1e9:>10.2f}")
    df = pd.DataFrame(rows).set_index("mode")
    total = df["cost_per_yr"].sum()
    print(f"  {'':<20}{'':>8}{'':>9}{total / 1e9:>10.2f}   "
          f"= ${total / pop:,.0f} per resident per year")

    # --- r_k, the term that goes into MEP -----------------------------------
    print("\nINJURY COST PER PASSENGER-MILE  (r_k)")
    pmt = exp["annual_pmt"]
    drive_r = None
    for mode in df.index:
        if mode in pmt.index and pd.notna(pmt.get(mode)):
            r = df.loc[mode, "cost_per_yr"] / pmt[mode]
            print(f"  {mode:<20}${r:>7.3f} / passenger-mile")
            if mode == "vehicle_occupant":
                drive_r = r
        else:
            print(f"  {mode:<20}      no measured exposure "
                  f"(see break-even below)")

    # --- ACCEPTANCE TEST -----------------------------------------------------
    print("\n" + "=" * 68)
    print("ACCEPTANCE TEST - reconcile against Cui & Levinson (2019)")
    print("=" * 68)
    # THE UNITS MUST MATCH BEFORE DIVIDING. An earlier version printed
    # "$/passenger-mile" and "$/vehicle-mile" on adjacent lines and then divided
    # them anyway, reporting 1.49x where the answer is 2.49x - the same
    # vehicle-versus-passenger-mile confusion this step exists to catch, living
    # inside the test written to catch it. Convert first, then compare.
    drive_r_vmt = drive_r * OCCUPANCY
    ratio = drive_r_vmt / CL_INTERNAL_2024_PER_MILE
    print(f"  this analysis   ${drive_r:.4f} / passenger-mile")
    print(f"                  ${drive_r_vmt:.4f} / vehicle-mile   "
          f"(x {OCCUPANCY} occupancy)")
    print(f"  Cui & Levinson  ${CL_INTERNAL_PER_VEHKM:.4f} / vehicle-KM, 2010 $"
          f"   internal only")
    print(f"                  ${CL_INTERNAL_2024_PER_MILE:.4f} / vehicle-mile, "
          f"2024 $   (x{DEFLATOR_2010_2024})")
    print(f"  ratio           {ratio:.2f}x   <- vehicle-mile vs vehicle-mile")
    print(f"\n  Florida's fatality rate per VMT is about "
          f"{FL_MN_FATALITY_RATIO:.0f}x Minnesota's, so a correct")
    print(f"  method should land near that. Note this project prices K and A")
    print(f"  ONLY while Cui & Levinson include all severities, so a fully")
    print(f"  unit-matched ratio would be HIGHER still - this is a lower bound.")

    if ratio > ACCEPT_HI:
        print("\n  FAIL - still far above the published figure. Do not publish "
              "a dollar\n  value from this run; the convention is still mixed.")
    elif ratio < ACCEPT_LO:
        print("\n  FAIL - implausibly low. Check that KSI counts and exposure "
              "cover\n  the same period and geography.")
    else:
        print(f"\n  PASS - {ratio:.2f}x sits where a more dangerous state should "
              f"sit against\n  a published US baseline. The earlier 8x came from "
              f"mixing per-crash\n  costs with person counts and vehicle-miles "
              f"with passenger-miles.")
    print("=" * 68)

    # --- Walk and bike, now MEASURED ----------------------------------------
    #
    # These used to be declared as literals in `23_mep.py`, traced back to a
    # scratch script whose walk and bike mode shares summed to 110% at one end
    # of its "range" and 90% at the other. They carried 79% of the headline.
    # Step 17 now measures the exposure from the same NHTS 2022 file it already
    # reads for f_k and occupancy, so they are computed here like every other
    # rate and written to the same CSV.
    #
    # THE RANGE IS NOW TWO REAL MEASUREMENTS, national and regional, rather than
    # two arbitrary mode-share guesses. The regional bike cell rests on 35
    # surveyed trips, so the national figure is not the weaker end of that pair
    # and both are reported.
    nm = {}
    with (INTERIM / "nonmotorised_exposure.csv").open(encoding="utf8") as fh:
        for r in csv.DictReader(fh):
            nm[(r["geography"], r["mode"])] = r

    print("\nWALK AND BIKE  (NHTS 2022 exposure x ACS 2023 population)")
    print(f"  {'mode':<6}{'geography':<22}{'mi/person/yr':>13}"
          f"{'region PMT/yr':>16}{'$ per mile':>12}{'trips':>8}")
    nm_out = {}
    for mode in ("walk", "bike"):
        c = df.loc[mode, "cost_per_yr"]
        vals = []
        for geo in ("US 2022", "South Atlantic 2022"):
            rec = nm[(geo, mode)]
            per_person = float(rec["miles_per_person_yr"])
            # NB: must NOT be named `pmt` - that is the exposure Series read
            # above, and shadowing it makes `pmt.index` a float attribute
            # lookup fifty lines later. Same bug class as the `sev` Counter
            # in step 02.
            mode_pmt = per_person * pop
            r = c / mode_pmt
            vals.append(r)
            print(f"  {mode:<6}{geo:<22}{per_person:>13.1f}"
                  f"{mode_pmt / 1e6:>15,.0f}M{r:>12.2f}"
                  f"{int(rec['n_trips']):>8,}")
        nm_out[mode] = (min(vals), max(vals))

    print(f"\n  {'mode':<6}{'range used downstream':>28}{'vs driving':>14}")
    for mode in ("walk", "bike"):
        lo, hi = nm_out[mode]
        print(f"  {mode:<6}{f'${lo:.2f} to ${hi:.2f}':>28}"
              f"{f'{lo / drive_r:.0f}x to {hi / drive_r:.0f}x':>14}")

    # The break-even remains, because it is the one statement about walking and
    # cycling that needs NO exposure estimate at all, and so survives any
    # objection to the numbers above.
    print(f"\n  BREAK-EVEN, which needs no exposure estimate:")
    for mode in ("walk", "bike"):
        c = df.loc[mode, "cost_per_yr"]
        print(f"    {mode:<6}the region would have to travel "
              f"{c / drive_r / 1e9:.1f} B passenger-miles/yr by this mode")
        print(f"    {'':<6}for its injury cost per mile to equal driving's. "
              f"It travels "
              f"{float(nm[('South Atlantic 2022', mode)]['miles_per_person_yr']) * pop / 1e9:.2f} B.")

    FINAL.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["annual_pmt"] = [pmt.get(m) if m in pmt.index else None
                         for m in out.index]
    out["cost_per_pmt"] = out["cost_per_yr"] / out["annual_pmt"]
    # FATALITY-ONLY drive rate, emitted so that any sentence comparing driving
    # to TRANSIT can be like-for-like. NTD records no bus serious injuries at
    # all - serious injury is a rail-only concept there under 49 CFR 674 - so
    # r_transit is structurally fatality-only. Comparing it against the KSI
    # drive rate roughly doubles the apparent asymmetry, and a draft of the
    # report did exactly that. Serious injuries are 47% of the drive rate.
    out["cost_per_pmt_fatal_only"] = (
        out["K_per_yr"] * COST_PER_PERSON["K"] / out["annual_pmt"])
    # walk and bike now have a measured range; carry both ends so no downstream
    # step has to declare them
    out["cost_per_pmt_lo"] = [nm_out.get(m, (None, None))[0] for m in out.index]
    out["cost_per_pmt_hi"] = [nm_out.get(m, (None, None))[1] for m in out.index]
    out["cost_per_resident"] = out["cost_per_yr"] / pop
    out.to_csv(FINAL / "injury_cost_by_mode.csv")
    print(f"wrote {FINAL / 'injury_cost_by_mode.csv'}")


if __name__ == "__main__":
    main()
