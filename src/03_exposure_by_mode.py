"""
Step 03 - exposure by mode. The denominators.

A casualty count means nothing without the travel it happened across. This step
supplies the passenger-miles that turn counts into rates.

Two of the four modes have MEASURED exposure and two do not, and that asymmetry
is the honest limit of the project:

  drive    FDOT county DVMT x 365 x vehicle occupancy   counted
  transit  NTD reported passenger-miles                 counted
  walk     nothing published for Tampa Bay              -
  bike     nothing published for Tampa Bay              -

Rather than invent a walk/bike denominator and present it beside two real ones,
this step computes the BREAK-EVEN EXPOSURE instead: how many walking miles the
region would have to produce for walking's injury cost per mile to match
driving's. That needs no estimate, and it is a stronger statement than a rate
built on a guess.

Writes: data/interim/exposure_by_mode.csv
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

INTERIM = Path(__file__).resolve().parents[1] / "data" / "interim"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (VMT_ANNUAL, OCCUPANCY, NTD_SERVICE as NTD,  # noqa: E402
                       TRANSIT_AGENCIES as AGENCIES, YEARS, USER_AGENT)


def ntd_passenger_miles():
    """Annual transit passenger-miles for the two Tampa Bay agencies."""
    total, detail = 0.0, []
    for frag in AGENCIES:
        where = urllib.parse.quote(f"agency like '%{frag}%'")
        url = f"{NTD}?$limit=200&$where={where}"
        req = urllib.request.Request(url, headers=USER_AGENT)
        with urllib.request.urlopen(req, timeout=120) as r:
            rows = json.load(r)
        if not rows:
            print(f"  !! no NTD rows for {frag!r}")
            continue
        # The year field is `report_year`, not `year`. Take the most recent.
        yr = max(int(x["report_year"]) for x in rows if x.get("report_year"))
        cur = [x for x in rows if int(x.get("report_year", 0)) == yr]
        pm = sum(float(x.get("sum_passenger_miles") or 0) for x in cur)
        upt = sum(float(x.get("sum_unlinked_passenger_trips_upt") or 0)
                  for x in cur)
        name = rows[0].get("agency", frag)
        print(f"  {name[:44]:<46}{yr}  {pm:>14,.0f} pass-mi  "
              f"{upt:>12,.0f} trips")
        detail.append((name, yr, pm))
        total += pm
    return total, detail


def main():
    cas = pd.read_csv(INTERIM / "casualties_by_mode.csv").set_index("mode")
    sld = pd.read_parquet(INTERIM / "sld.parquet")
    pop = int(sld["TotPop"].sum())

    print(f"study area population (SLD TotPop): {pop:,}\n")

    print("TRANSIT  (NTD resource 6y83-7vuw)")
    transit_pm, _ = ntd_passenger_miles()

    drive_pm = VMT_ANNUAL * OCCUPANCY

    print(f"\nMEASURED EXPOSURE, annual passenger-miles")
    print(f"  drive    {drive_pm:>18,.0f}   "
          f"({VMT_ANNUAL:,.0f} VMT x {OCCUPANCY} occupancy)")
    print(f"  transit  {transit_pm:>18,.0f}   NTD reported")
    print(f"  ratio    drive is {drive_pm / transit_pm:,.0f}x transit "
          f"passenger-miles")

    rows = [
        {"mode": "vehicle_occupant", "annual_pmt": drive_pm,
         "basis": "FDOT DVMT x 365 x NHTS occupancy", "measured": True},
        {"mode": "transit", "annual_pmt": transit_pm,
         "basis": "NTD sum_passenger_miles", "measured": True},
        {"mode": "walk", "annual_pmt": None,
         "basis": "no published Tampa Bay exposure", "measured": False},
        {"mode": "bike", "annual_pmt": None,
         "basis": "no published Tampa Bay exposure", "measured": False},
    ]

    # --- KSI rates where exposure exists -------------------------------------
    print(f"\nKSI PER BILLION PASSENGER-MILES  (annualised over {YEARS} years)")
    drive_ksi = int(cas.loc["vehicle_occupant", "KSI"]) / YEARS
    drive_rate = drive_ksi / (drive_pm / 1e9)
    print(f"  drive    {drive_rate:>8.1f}   ({drive_ksi:,.0f} KSI/yr)")

    # Transit KSI is NOT taken from the crash file - see step 02's docstring.
    # Left explicitly absent rather than filled with a wrong number.
    print(f"  transit       n/a   KSI must come from NTD safety data, not from")
    print(f"                      the crash file (no per-vehicle occupant counts)")

    # --- Break-even exposure for walk and bike --------------------------------
    # How many miles would the region have to walk for walking to be as safe
    # per mile as driving? Needs no exposure estimate.
    print(f"\nBREAK-EVEN EXPOSURE  (no walk/bike denominator required)")
    print(f"  For each mode to match driving's KSI rate of {drive_rate:.1f} per")
    print(f"  billion passenger-miles, the region would have to produce:\n")
    for mode in ("walk", "bike"):
        ksi_yr = int(cas.loc[mode, "KSI"]) / YEARS
        needed_pm = ksi_yr / drive_rate * 1e9
        per_cap_day = needed_pm / pop / 365
        print(f"  {mode:<6}{needed_pm / 1e9:>7.1f} B passenger-miles/yr "
              f"= {per_cap_day:>6.1f} miles per person per DAY")

    print(f"""
  Tampa Bay does not walk {int(cas.loc['walk', 'KSI']) / YEARS / drive_rate * 1e9 / pop / 365:.0f} miles per person per day. It is not
  close. So walking's injury rate per mile is far above driving's, and the
  size of the gap is the ratio between the real figure and these break-evens.
  This is a floor on the disparity, established without estimating exposure.
""")

    out = pd.DataFrame(rows)
    out.to_csv(INTERIM / "exposure_by_mode.csv", index=False)
    print(f"wrote {INTERIM / 'exposure_by_mode.csv'}")


if __name__ == "__main__":
    main()
