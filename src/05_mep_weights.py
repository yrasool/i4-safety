"""
Step 05 - the bus injury rate, and the term folded into MEP's weighting factor.

FATALITY-ONLY, ON BOTH SIDES. That is forced, not chosen.

All fourteen NTD serious-injury columns are zero for Bus and Ferry in every year
2014-2026, while bus rider INJURIES run to 22,054 over 2019-2024. Serious injury
is a rail-only concept in NTD, inherited from the State Safety Oversight regime
(49 CFR Part 674), which covers rail fixed-guideway. There is no alternative
field and no defensible imputation, so the A term is dropped from BOTH modes.
Since A supplies 47% of the drive side's cost, keeping it while bus structurally
cannot have it inflated the ratio by 1.89x on that basis alone.

Three further corrections, all of which had been SUPPRESSING transit's
advantage rather than flattering it:

  MODE      the previous version applied no mode filter, so rail was included -
            and rail supplies 59% of rider fatalities and 100% of rider serious
            injuries while bus is only 41% of the transit denominator.
  CRIME     57.8% of rider fatalities are `Security` events (assault, homicide,
            robbery). The drive side is police-reported traffic crashes. Crime
            was being priced on one side of the comparison only.
  DENOMINATOR  all-transit passenger-miles where bus passenger-miles belong.
            NTD_SERVICE has no `mode` field at all, so NTD_PMT_BY_MODE is a
            required substitution rather than a preference.

Then: what the term does inside MEP.

    M_k = ALPHA*e_k + BETA*t + SIGMA*c_k + DELTA*r_k

Time is unchanged by adding injury, so the change in M is exactly DELTA*r_k and
the multiplier on a mode's opportunities is exp(DELTA*r_k). No travel time is
needed for that, which is why this step needs no routing.

Writes: data/final/mep_weights.csv, data/final/injury_rate_by_mode.csv
"""

import json
import sys
import urllib.parse
import urllib.request
from math import exp
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (NTD_SAFETY, NTD_PMT_BY_MODE, BUS_MODES,  # noqa: E402
                       COLLISION_CATEGORIES, TRANSIT_SPAN, TRANSIT_R_CI,
                       COST_PER_PERSON, YEARS, MEP_DEFAULTS as MEP,
                       TRANSIT_K_OBSERVED,
                       ALPHA, GAMMA, SCENARIOS, USER_AGENT,
                       SAVAGE_BUS_PER_BN_PMT, SAVAGE_CAR_PER_BN_PMT)

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
LO, HI = TRANSIT_SPAN


def get(url):
    req = urllib.request.Request(url, headers=USER_AGENT)
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.load(r)


def page(base, where, limit=50000, order=":id"):
    """
    Paged fetch with an EXPLICIT SORT. Without `$order`, Socrata offset paging
    is not stable: the same query run twice returned 237 duplicated rows and
    silently omitted 237 real events, with no error and the correct row count.

    That is not cosmetic here. The bus numerator is 12 deaths from 8 events,
    one of which carries 4. Losing that single event prints 72x instead of 48x.
    """
    rows, off = [], 0
    while True:
        chunk = get(f"{base}?$limit={limit}&$offset={off}"
                    f"&$order={urllib.parse.quote(order)}"
                    f"&$where={urllib.parse.quote(where)}")
        if not chunk:
            break
        rows.extend(chunk)
        off += len(chunk)
        if len(chunk) < limit:
            break
    return rows


def aggregate(base, where, expr):
    """Server-side sum. No paging, so no paging bug. Used to CHECK page()."""
    url = (f"{base}?$select={urllib.parse.quote(expr)}"
           f"&$where={urllib.parse.quote(where)}")
    return get(url)[0]


def bus_fatalities():
    """Rider fatalities on fixed-route bus, traffic collisions only."""
    modes = ",".join(f"'{m}'" for m in BUS_MODES)
    cats = ",".join(f"'{c}'" for c in COLLISION_CATEGORIES)
    where = (f"year >= {LO} AND year <= {HI} AND mode IN ({modes}) "
             f"AND event_category IN ({cats})")
    rows = page(NTD_SAFETY, where)
    k = sum(int(float(x.get("transit_vehicle_rider") or 0)) for x in rows)
    a = sum(int(float(x.get("transit_vehicle_rider_serious") or 0))
            for x in rows)

    # Cross-check the paged numerator against a server-side aggregate, which
    # cannot be affected by paging at all. If these disagree, the paged read
    # dropped or duplicated events and the rate is not reproducible.
    agg = aggregate(NTD_SAFETY, where,
                    "sum(transit_vehicle_rider) as k,"
                    "sum(transit_vehicle_rider_serious) as a")
    k_srv = int(float(agg.get("k") or 0))
    if k != k_srv:
        raise SystemExit(
            f"FAIL: paged read gives {k} rider fatalities, server-side "
            f"aggregate gives {k_srv}. Socrata paging dropped or duplicated "
            f"rows; the rate is not reproducible. Do not use this run.")

    # The numerator is a handful of events, not a large sample. Guard the
    # count so a silent change cannot pass as a new result.
    if k != TRANSIT_K_OBSERVED:
        raise SystemExit(
            f"FAIL: {k} rider fatalities, expected {TRANSIT_K_OBSERVED}. The "
            f"published CI is computed on {TRANSIT_K_OBSERVED}. Recompute the "
            f"interval before changing this constant.")

    print(f"  {len(rows):,} fixed-route bus collision events {LO}-{HI}")
    print(f"  {k} rider fatalities (server-side check: {k_srv})   "
          f"{a} rider serious injuries")
    if a == 0:
        print(f"    ^ zero is STRUCTURAL, not missing: serious injury is a")
        print(f"      rail-only concept in NTD. This is why the comparison")
        print(f"      must be fatality-only on both sides.")
    return k


def bus_passenger_miles():
    """
    Bus passenger-miles over the same span.

    NTD_SERVICE is aggregated by agency and carries NO `mode` column, so it
    cannot be filtered to bus at all - this resource is required, not preferred.
    It is LONG format: `field` names the metric and `value` holds the number, so
    it must be filtered to 'Passenger Miles Traveled' or every metric in the
    dataset gets summed together.
    """
    modes = ",".join(f"'{m}'" for m in BUS_MODES)
    where = (f"report_year >= '{LO}' AND report_year <= '{HI}' "
             f"AND mode IN ({modes}) AND field = 'Passenger Miles Traveled'")
    rows = page(NTD_PMT_BY_MODE, where)
    pm = sum(float(x.get("value") or 0) for x in rows)
    yrs = sorted({int(x["report_year"]) for x in rows if x.get("report_year")})
    print(f"  {len(rows):,} agency-mode-year rows, {yrs[0]}-{yrs[-1]}")
    print(f"  {pm:,.0f} bus passenger-miles")
    return pm


def main():
    cas = pd.read_csv(INTERIM / "casualties_by_mode.csv").set_index("mode")
    exp_df = pd.read_csv(INTERIM / "exposure_by_mode.csv").set_index("mode")

    print(f"FIXED-ROUTE BUS, COLLISION-ONLY, FATALITIES  (NTD 9ivb-8ae9)")
    k_bus = bus_fatalities()
    print(f"\nBUS PASSENGER-MILES  (NTD npsm-38gk, by mode)")
    pm_bus = bus_passenger_miles()

    span = HI - LO + 1
    r_transit = (k_bus / span) * COST_PER_PERSON["K"] / (pm_bus / span)

    # Drive, FATALITY ONLY, to match.
    drive_pmt = float(exp_df.loc["vehicle_occupant", "annual_pmt"])
    k_drive_yr = cas.loc["vehicle_occupant", "K"] / YEARS
    r_drive = k_drive_yr * COST_PER_PERSON["K"] / drive_pmt

    print(f"\n{'=' * 66}\nFATALITY-ONLY INJURY COST PER PASSENGER-MILE\n{'=' * 66}")
    print(f"  drive    ${r_drive:.6f}   {k_drive_yr:,.0f} occupant deaths/yr")
    print(f"  bus      ${r_transit:.6f}   {k_bus} deaths over {span} years")
    print(f"           95% CI ${TRANSIT_R_CI[0]:.6f} - ${TRANSIT_R_CI[1]:.6f}"
          f"   (Poisson on k={k_bus})")
    print(f"\n  Driving carries {r_drive / r_transit:.0f}x the fatality cost per")
    print(f"  passenger-mile that riding a fixed-route bus does.")
    print(f"  Range across the CI: "
          f"{r_drive / TRANSIT_R_CI[1]:.0f}x to {r_drive / TRANSIT_R_CI[0]:.0f}x")

    # --- Literature check ----------------------------------------------------
    bus_per_bn = k_bus / (pm_bus / 1e9)
    drive_per_bn = k_drive_yr / (drive_pmt / 1e9)
    print(f"\nAGAINST SAVAGE (2013), fatalities per billion passenger-miles")
    print(f"  bus     this {bus_per_bn:>6.3f}   Savage {SAVAGE_BUS_PER_BN_PMT}"
          f"   (collision-only here; Savage also counts in-vehicle falls)")
    print(f"  car     this {drive_per_bn:>6.3f}   Savage {SAVAGE_CAR_PER_BN_PMT}"
          f"   (Tampa Bay occupants vs his 2000-2009 national)")
    print(f"  ratio   this {r_drive / r_transit:>6.0f}x  Savage "
          f"{SAVAGE_CAR_PER_BN_PMT / SAVAGE_BUS_PER_BN_PMT:.0f}x")

    # --- The term inside MEP -------------------------------------------------
    print(f"\n{'=' * 66}\nEFFECT ON THE MEP MODAL WEIGHTING FACTOR\n{'=' * 66}")
    rows = []
    for name, delta in SCENARIOS.items():
        print(f"\n{name}   delta = {delta:.3f}")
        print(f"  {'mode':<9}{'sigma*c':>10}{'delta*r':>11}"
              f"{'% of cost':>11}{'weight x':>10}")
        for mode, r in (("drive", r_drive), ("transit", r_transit)):
            gc = GAMMA * MEP[mode]["c"]
            dr = delta * r
            rows.append({"scenario": name, "mode": mode, "sigma_c": gc,
                         "delta_r": dr, "pct_of_cost_term": abs(dr / gc),
                         "weight_multiplier": exp(dr)})
            print(f"  {mode:<9}{gc:>10.4f}{dr:>11.5f}"
                  f"{abs(dr / gc):>10.1%}{exp(dr):>10.4f}")

    base = {r["mode"]: r for r in rows if r["scenario"] == "base"}
    print(f"""
  The injury term is {base['drive']['pct_of_cost_term']:.1%} of the cost MEP already charges driving and
  {base['transit']['pct_of_cost_term']:.2%} of transit's - an asymmetry of {base['drive']['pct_of_cost_term'] / base['transit']['pct_of_cost_term']:.0f}x. Omitting it does not
  treat the modes equally; it flatters the car.
""")

    FINAL.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(FINAL / "mep_weights.csv", index=False)
    pd.DataFrame([
        {"mode": "drive", "r": r_drive, "basis": "fatality-only, occupants",
         "ci_lo": None, "ci_hi": None},
        {"mode": "transit", "r": r_transit,
         "basis": f"fixed-route bus, collision-only, RY{LO}-{HI}",
         "ci_lo": TRANSIT_R_CI[0], "ci_hi": TRANSIT_R_CI[1]},
    ]).to_csv(FINAL / "injury_rate_by_mode.csv", index=False)
    print(f"wrote {FINAL / 'injury_rate_by_mode.csv'}")


if __name__ == "__main__":
    main()
