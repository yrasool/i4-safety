"""
Step 11 - the mode comparison, on counted data.

Replaces the earlier mep_combined.py, which DERIVED how many drivers died by
taking regional road deaths and assuming a statewide fraction were occupants.
That inflated occupant deaths by 68%: 384.6/yr derived against 229.3/yr
counted. Tampa Bay kills a far higher share of pedestrians than Florida
average, so a statewide split does not transfer here.

Everything below is counted from the crash file, not inferred.

FATALITY-ONLY, ALL MODES. NTD records no serious injuries for buses at all -
serious injury is a rail-only concept in their reporting. Keeping the serious
term for road modes while transit structurally cannot have one would compare
different things, so it is dropped everywhere.

OCCUPANCY comes from constants.py and is MEASURED, not inferred. An earlier
version of this docstring claimed MEP's $0.48/person-mile was AAA's $0.796
per car-mile divided by 1.67. AAA publishes no $0.796 figure; that derivation
was fabricated. Occupancy is now person-miles over vehicle-miles from NHTS 2022
driver trips, computed in step 17.
"""

import sys
from math import exp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COST_PER_PERSON, YEARS, OCCUPANCY, VMT_ANNUAL  # noqa: E402

# MEP published parameters (Hou et al. 2019; FDOT memo 2023)
A_ENERGY, B_TIME, C_COST = -0.5, -0.08, -0.5
MEP_MODE = {                       # energy kWh/PMT, operating cost $/PMT
    "drive":   (0.90, 0.48),
    "transit": (0.65, 0.86),
    "walk":    (0.00, 0.00),
    "bike":    (0.00, 0.00),
}

# Counted from signal4_district7_2019_2025.csv, 2019-2025
DEATHS = {"drive": 1582, "walk": 915, "bike": 277, "motorcycle": 697}

# Exposure, annual person-miles
PM_DRIVE = VMT_ANNUAL * OCCUPANCY                    # measured
# FHWA National Passenger OD 2022, intrazonal walk trips x NHTS mean length.
# The weakest input here - a national trip length on a regional trip count.
PM_WALK = 356_500_000 * 0.7
PM_TRANSIT_NATIONAL = 156_919_941_747 / 10           # bus, RY2015-24
TRANSIT_DEATHS_NATIONAL = 12 / 10                    # riders, collisions only


def rate(deaths_per_year, person_miles_per_year):
    return deaths_per_year * COST_PER_PERSON["K"] / person_miles_per_year


def main():
    r = {
        "drive":   rate(DEATHS["drive"] / YEARS, PM_DRIVE),
        "walk":    rate(DEATHS["walk"] / YEARS, PM_WALK),
        "transit": rate(TRANSIT_DEATHS_NATIONAL, PM_TRANSIT_NATIONAL),
    }

    print("WHAT INJURY COSTS PER MILE TRAVELLED\n")
    print(f"  {'mode':<10}{'deaths/yr':>11}{'person-miles/yr':>19}{'$ per mile':>12}")
    print(f"  {'drive':<10}{DEATHS['drive']/YEARS:>11.0f}{PM_DRIVE:>19,.0f}"
          f"{r['drive']:>12.4f}")
    print(f"  {'walk':<10}{DEATHS['walk']/YEARS:>11.0f}{PM_WALK:>19,.0f}"
          f"{r['walk']:>12.4f}")
    print(f"  {'transit':<10}{TRANSIT_DEATHS_NATIONAL:>11.1f}"
          f"{PM_TRANSIT_NATIONAL:>19,.0f}{r['transit']:>12.4f}   national bus")
    print(f"\n  walking costs {r['walk']/r['drive']:>5.0f}x driving per mile")
    print(f"  driving costs {r['drive']/r['transit']:>5.0f}x the bus per mile")

    print(f"\n{'='*64}\nWHAT HAPPENS INSIDE MEP  (30-minute trip)\n{'='*64}")
    print(f"  {'mode':<10}{'now':>11}{'with injury':>13}{'change':>10}")
    before, after = {}, {}
    for m in ("drive", "transit", "walk"):
        e, c = MEP_MODE[m]
        before[m] = exp(A_ENERGY*e + B_TIME*30 + C_COST*c)
        after[m] = exp(A_ENERGY*e + B_TIME*30 + C_COST*(c + r[m]))
        print(f"  {m:<10}{before[m]:>11.5f}{after[m]:>13.5f}"
              f"{after[m]/before[m]-1:>+10.1%}")

    print(f"\n  DRIVE vs BUS")
    for lbl, d in (("as MEP has it now", before), ("with injury priced", after)):
        lead = d["drive"] / d["transit"] - 1
        who = "driving" if lead > 0 else "the bus"
        print(f"    {lbl:<22}{who} ahead by {abs(lead):>5.1%}")

    print(f"""
  WHAT THIS SAYS
    Pricing injury does not flip the ranking. Driving still scores ahead of
    the bus, by {after['drive']/after['transit']-1:.1%} instead of {before['drive']/before['transit']-1:.1%}. The gap narrows by more than
    half and does not close.

    Walking is the mode the correction hits hardest, losing {1-after['walk']/before['walk']:.0%} of its
    score, because {DEATHS['walk']} people died walking here on a tiny number of miles.
""")


if __name__ == "__main__":
    main()
