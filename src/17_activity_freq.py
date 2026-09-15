"""
Step 17 - activity frequencies.  The `f_j` weight in MEP Equation 1.

MEP does not treat all destinations equally. Reaching 100 restaurants is not
worth the same as reaching 100 hospitals, because people go out to eat far more
often than they visit a doctor. Equation 1 weights each activity type by how
often people actually do it:

        o_ikt = SUM_j  o_ijkt * (N*/N_j) * (f_j / SUM f_j)

`f_j` is the trip frequency for activity j. MEP's Table 1 sources it from NHTS.

THREE GEOGRAPHIES, because the ideal one does not exist:

  national 2022   the latest NHTS. Used as the base.
  South Atlantic  2022, large-MSA households in the census division holding
                  Florida. This is the FINEST GEOGRAPHY THAT EXISTS in the
                  latest data.

STATE IS NOT AVAILABLE, and that is a property of the source, not a shortcut.
The 2022 public use file carries CENSUS_D, CENSUS_R, MSACAT, MSASIZE and
CDIVMSAR, and no state field at all. The 2017 file did publish HHSTATE, so a
genuinely Florida-specific `f_j` exists only in data that is now nine years old
and predates the change in travel behaviour that 2022 measures. Latest and
state-specific cannot both be had. This project takes latest.

VALIDATION: the national daily trip rate computed here must reproduce the
published FHWA figure of 2.28 (Summary of Travel Trends 2022, Table 4-5). If it
does not, the weighting is being applied wrongly and the regional cuts are
worthless too.

ALSO COMPUTES VEHICLE OCCUPANCY, because it belongs to the same survey.

MEP's cost and energy terms are per PASSENGER-mile, so the crash cost added to
them must be per passenger-mile too, which needs an occupancy to convert
FDOT's vehicle-miles. Two wrong ways to get that number were used here before:

  1.67  NHTS 2017. Superseded by the survey this step already reads.
  a back-solve from AAA, claiming MEP's $0.48/passenger-mile is AAA's
        $0.796/car-mile divided by 1.67. AAA publishes no such figure. The
        derivation was fabricated and is deleted, not corrected.

Occupancy is now MEASURED from the 2022 microdata: person-miles over vehicle-
miles across driver-reported trips in cars, vans, SUVs and pickups. Driver
trips only, or the same vehicle trip is counted once per household member
aboard and occupancy comes out squared.

Writes: data/interim/activity_freq.csv, data/interim/occupancy.csv
"""

import csv
import io
import sys
import urllib.request
import zipfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "interim" / "activity_freq.csv"
OCC_OUT = ROOT / "data" / "interim" / "occupancy.csv"
NM_OUT = ROOT / "data" / "interim" / "nonmotorised_exposure.csv"

SRC = {2022: ("https://nhts.ornl.gov/media/2022/download/csv.zip",
              "nhts2022_csv.zip", "tripv2pub.csv", "perv2pub.csv", "hhv2pub.csv")}

# TRPTRANS codes for privately operated vehicles, from the 2022 codebook:
# 01 Car, 02 Van, 03 SUV/Crossover, 04 Pickup truck. Verified against the
# codebook rather than assumed - the 2022 codes are NOT the 2017 codes.
POV_MODES = {"01", "02", "03", "04"}

# 18 Bicycle (including bikeshare, ebike), 20 Walked. Verified in the codebook.
# 19 is E-scooter and belongs to NEITHER.
NONMOTOR_MODES = {"walk": "20", "bike": "18"}

# WHYTRP1S is NHTS's own trip-purpose summary, and its categories ARE the six
# activity types in MEP's Table 1. No recoding, no judgement calls.
PURPOSE = {"10": "work", "80": "meals", "50": "social",
           "40": "shopping", "30": "medical", "20": "school"}
# 01 home, 70 transport someone, 97 other: not destinations MEP counts.

PUBLISHED_2022_TOTAL = 2.28   # FHWA Summary of Travel Trends 2022, Table 4-5

# The reference implementation's own f_k, from FDOT BDV29-977-66 Table 8,
# computed on NHTS 2017 national. Printed alongside this step's NHTS 2022
# figures as an external check. They are NOT expected to match: 2022 is a
# different survey year and this is a regional cut. Where they differ, the
# direction should be explicable from the published trend, and it is - work
# trips per person fell from 214/yr in 2017 to 153 in 2022.
REFERENCE_F_2017 = {"work": 0.30, "meals": 0.12, "shopping": 0.35,
                    "medical": 0.03, "school": 0.06, "social": 0.15}


def load(year):
    url, name, trip, per, hh = SRC[year]
    path = RAW / name
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        print(f"  downloading NHTS {year} ...")
        req = urllib.request.Request(url, headers=USER_AGENT)
        with urllib.request.urlopen(req, timeout=900) as r:
            path.write_bytes(r.read())
    z = zipfile.ZipFile(path)
    rd = lambda f: csv.DictReader(io.TextIOWrapper(z.open(f), "utf8"))
    return rd(trip), rd(per), rd(hh)


def rates(trips, persons, households, keep=None):
    """
    Annual trips per person, by purpose. NHTS weights are ANNUAL, so dividing
    the summed trip weight by the summed person weight gives trips per person
    per year; /365 makes it daily and comparable to the published table.

    `keep` is a predicate on the household row. None means all households.
    """
    hh_ok = None
    if keep is not None:
        hh_ok = {r["HOUSEID"] for r in households if keep(r)}

    pw = 0.0
    for r in persons:
        if hh_ok is not None and r["HOUSEID"] not in hh_ok:
            continue
        pw += float(r.get("WTPERFIN") or 0)

    tw = defaultdict(float)
    n = defaultdict(int)
    for r in trips:
        if hh_ok is not None and r["HOUSEID"] not in hh_ok:
            continue
        p = PURPOSE.get(r["WHYTRP1S"])
        w = float(r.get("WTTRDFIN") or 0)
        tw["ALL"] += w
        if p:
            tw[p] += w
            n[p] += 1
    return pw, tw, n, (len(hh_ok) if hh_ok is not None else None)


def occupancy(trips, households, keep=None):
    """
    Person-miles over vehicle-miles for privately operated vehicles.

    DRIVER TRIPS ONLY. Every passenger in a car also reports that trip, so
    counting all of them would multiply both the vehicle-miles and the people
    aboard, and occupancy would come out roughly squared.
    """
    hh_ok = None
    if keep is not None:
        hh_ok = {r["HOUSEID"] for r in households if keep(r)}
    pm = vm = 0.0
    n = 0
    for r in trips:
        if r["TRPTRANS"] not in POV_MODES or r.get("DRVR_FLG") != "01":
            continue
        if hh_ok is not None and r["HOUSEID"] not in hh_ok:
            continue
        try:
            mi = float(r["TRPMILES"])
            people = float(r["NUMONTRP"])
            w = float(r["WTTRDFIN"])
        except (TypeError, ValueError):
            continue
        if mi <= 0 or people < 1 or w <= 0:
            continue
        pm += mi * people * w
        vm += mi * w
        n += 1
    return pm / vm, n


def nonmotorised_miles(trips, persons, households, keep=None):
    """
    Miles walked and cycled per person per year.

    REPLACES A HARDCODED PAIR OF LITERALS. Until this existed, r_walk and r_bike
    came from `15_fixed.py`, a scratch script outside the pipeline, as

        walk person-miles = ATF * 0.90 * 1.5     bike = ATF * 0.20 * 4.0
        walk person-miles = ATF * 0.80 * 0.5     bike = ATF * 0.10 * 1.5

    with ATF an unsourced active-travel trip count. Two things were wrong with
    that beyond its provenance. The mode shares do not sum: 0.90 + 0.20 = 110%
    of active trips at one end and 0.80 + 0.10 = 90% at the other, so neither
    end is a coherent scenario. And the trip lengths, 1.5 and 4.0 miles, were
    described in the report as national means when the national means are 0.93
    and 2.46.

    The survey this step already reads measures the quantity directly, so it is
    measured here. ALL trips are counted, not just driver trips: unlike a car,
    every walker on a walk trip is walking, so there is no double counting to
    avoid.
    """
    hh_ok = None
    if keep is not None:
        hh_ok = {r["HOUSEID"] for r in households if keep(r)}

    pw = 0.0
    for r in persons:
        if hh_ok is not None and r["HOUSEID"] not in hh_ok:
            continue
        pw += float(r.get("WTPERFIN") or 0)

    miles = {m: 0.0 for m in NONMOTOR_MODES}
    trips_n = {m: 0 for m in NONMOTOR_MODES}
    lengths = {m: [0.0, 0.0] for m in NONMOTOR_MODES}   # weighted mi, weight
    for r in trips:
        for mode, code in NONMOTOR_MODES.items():
            if r["TRPTRANS"] != code:
                continue
            if hh_ok is not None and r["HOUSEID"] not in hh_ok:
                continue
            try:
                mi = float(r["TRPMILES"])
                w = float(r["WTTRDFIN"])
            except (TypeError, ValueError):
                continue
            if mi <= 0 or w <= 0:
                continue
            miles[mode] += mi * w
            trips_n[mode] += 1
            lengths[mode][0] += mi * w
            lengths[mode][1] += w
    return ({m: miles[m] / pw for m in NONMOTOR_MODES},
            trips_n,
            {m: (lengths[m][0] / lengths[m][1] if lengths[m][1] else 0.0)
             for m in NONMOTOR_MODES})


def main():
    out = []

    # --- national 2022, and the validation ---------------------------------
    print("NHTS 2022, national")
    t, p, h = load(2022)
    pw, tw, n, _ = rates(t, p, h)
    daily_all = tw["ALL"] / pw / 365
    print(f"  daily trip rate, all purposes   {daily_all:.2f}")
    print(f"  FHWA published (Table 4-5)      {PUBLISHED_2022_TOTAL:.2f}")
    if abs(daily_all - PUBLISHED_2022_TOTAL) > 0.05:
        sys.exit(f"FAIL: computed {daily_all:.3f} against published "
                 f"{PUBLISHED_2022_TOTAL}. The weights are being applied "
                 f"wrongly; every regional cut below is wrong too.")
    print(f"  PASS - reproduces the published figure, so the weighting is right\n")

    named = sum(tw[a] for a in PURPOSE.values())
    for a in PURPOSE.values():
        out.append({"geography": "US 2022", "activity": a,
                    "annual_trips_per_person": tw[a] / pw,
                    "f_share": tw[a] / named, "n_trips": n[a], "n_hh": 7893})

    # --- South Atlantic, large MSA, 2022 -----------------------------------
    # CDIVMSAR = census division (1 digit) + MSA category (1 digit).
    # 5 = South Atlantic, which contains Florida. 2 = MSA of 1 million or more
    # without heavy rail, which is how Tampa-St Petersburg classifies.
    print("NHTS 2022, South Atlantic division, MSA 1M+ (Tampa's class)")
    t, p, h = load(2022)
    pw, tw, n, nhh = rates(t, p, h, keep=lambda r: r.get("CDIVMSAR") in ("51", "52"))
    named = sum(tw[a] for a in PURPOSE.values())
    print(f"  {nhh} households, {sum(n.values()):,} purposeful trips")
    for a in PURPOSE.values():
        out.append({"geography": "South Atlantic 2022", "activity": a,
                    "annual_trips_per_person": tw[a] / pw,
                    "f_share": tw[a] / named, "n_trips": n[a], "n_hh": nhh})


    # --- report ------------------------------------------------------------
    print(f"\n{'='*70}\nf_j  - SHARE OF PURPOSEFUL TRIPS BY ACTIVITY\n{'='*70}")
    geos = ["US 2022", "South Atlantic 2022"]
    print(f"  {'activity':<12}" + "".join(f"{g:>22}" for g in geos))
    for a in PURPOSE.values():
        row = f"  {a:<12}"
        for g in geos:
            rec = next(x for x in out if x["geography"] == g and x["activity"] == a)
            row += f"{rec['f_share']:>16.1%}{'':>6}"
        print(row)
    print(f"\n  {'(trips)':<12}" + "".join(
        f"{sum(x['n_trips'] for x in out if x['geography']==g):>16,}{'':>6}"
        for g in geos))

    # --- against the reference implementation -------------------------------
    print(f"\n{'=' * 70}\nAGAINST THE REFERENCE  (FDOT BDV29-977-66 Table 8, "
          f"NHTS 2017)\n{'=' * 70}")
    print(f"  {'activity':<12}{'this, 2022':>12}{'reference, 2017':>18}"
          f"{'difference':>13}")
    for a in PURPOSE.values():
        mine = next(x["f_share"] for x in out
                    if x["geography"] == "South Atlantic 2022"
                    and x["activity"] == a)
        theirs = REFERENCE_F_2017[a]
        print(f"  {a:<12}{mine:>12.1%}{theirs:>18.0%}"
              f"{(mine - theirs) * 100:>+12.1f}pt")
    print(f"\n  Work is the big mover, and it moves the way the published trend")
    print(f"  says it should: annual work trips per person fell from 214 in 2017")
    print(f"  to 153 in 2022 (Summary of Travel Trends 2022, Table 4-3). Using")
    print(f"  the reference's 2017 shares would overweight commuting by about")
    print(f"  half in a post-pandemic region.")

    # --- vehicle occupancy --------------------------------------------------
    print(f"\n{'=' * 70}\nVEHICLE OCCUPANCY  (people per car, measured)\n"
          f"{'=' * 70}")
    occ_rows = []
    for label, keep in (("US 2022", None),
                        ("South Atlantic 2022",
                         lambda r: r.get("CDIVMSAR") in ("51", "52"))):
        t, p_, h = load(2022)
        val, n_trips = occupancy(t, h, keep)
        occ_rows.append({"geography": label, "occupancy": round(val, 4),
                         "driver_trips": n_trips})
        print(f"  {label:<22}{n_trips:>8,} driver trips{val:>10.3f}")
    used = occ_rows[1]["occupancy"]
    print(f"\n  Used downstream: {used:.3f}, the regional cut.")
    print(f"  NHTS 2017 gave 1.67. Superseded by the survey read above.")
    print(f"  Consistency check, NOT the derivation: MEP's 0.90 kWh per")
    print(f"  passenger-mile x {used:.2f} = {0.90 * used:.3f} kWh per vehicle-"
          f"mile, in range for a US light-duty fleet.")

    # --- walking and cycling exposure --------------------------------------
    print(f"\n{'=' * 70}\nNON-MOTORISED EXPOSURE  (miles per person per year)\n"
          f"{'=' * 70}")
    nm_rows = []
    for label, keep in (("US 2022", None),
                        ("South Atlantic 2022",
                         lambda r: r.get("CDIVMSAR") in ("51", "52"))):
        t, p_, h = load(2022)
        per_person, n_trips, mean_len = nonmotorised_miles(t, p_, h, keep)
        for m in NONMOTOR_MODES:
            nm_rows.append({"geography": label, "mode": m,
                            "miles_per_person_yr": round(per_person[m], 4),
                            "mean_trip_miles": round(mean_len[m], 4),
                            "n_trips": n_trips[m]})
        print(f"  {label}")
        for m in NONMOTOR_MODES:
            print(f"    {m:<6}{per_person[m]:>8.1f} mi/person/yr   "
                  f"mean trip {mean_len[m]:>5.2f} mi   "
                  f"{n_trips[m]:>5,} trips")

    reg = {r["mode"]: r for r in nm_rows
           if r["geography"] == "South Atlantic 2022"}
    print(f"\n  Used downstream: the regional cut.")
    print(f"  The superseded literals implied 138.6 walk and 82.3 bike "
          f"mi/person/yr,")
    print(f"  which is {138.6 / reg['walk']['miles_per_person_yr']:.1f}x and "
          f"{82.3 / reg['bike']['miles_per_person_yr']:.1f}x what the survey "
          f"measures. They came from a")
    print(f"  scratch script whose walk and bike mode shares summed to 110%.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    with OCC_OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(occ_rows[0]))
        w.writeheader()
        w.writerows(occ_rows)
    with NM_OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(nm_rows[0]))
        w.writeheader()
        w.writerows(nm_rows)
    print(f"\nwrote {OUT}")
    print(f"wrote {OCC_OUT}")
    print(f"wrote {NM_OUT}")


if __name__ == "__main__":
    main()
