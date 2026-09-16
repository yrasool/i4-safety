"""
Step 39 - what does a BUS cause, locally?

WHY THIS EXISTS. The transit rate in this project ($0.00105 per passenger-mile)
is harm to bus RIDERS, pooled from ten years of national NTD data because the
local count was two deaths. It is the smallest number in the model and it makes
transit look almost free, which is convenient for a project arguing that MEP
flatters driving. A reviewer is entitled to ask the obvious question: fine, but
what does a bus do to everyone ELSE?

Step 35 answers that question for cars and not for buses. That asymmetry is
exactly the shape of a result chosen to flatter the argument, so it is closed
here, with LOCAL data, from the same licensed extract.

HOW A TRANSIT BUS IS IDENTIFIED, AND WHY IT MATTERS ENORMOUSLY.

A first pass took every crash whose body type was "Bus" or "Motor Coach":
4,019 crashes, and an externality of $0.1532 per passenger-mile - THREE TIMES a
car's. That number was wrong, and wrong in this project's most familiar way: the
numerator counted every bus on the road - charter coaches, hotel shuttles, tour
buses, church buses - while the denominator was HART and PSTA passenger-miles
alone. A denominator that does not cover its own numerator.

Narrowing to vehicle special function code 13 gives 1,464 crashes and $0.0647,
1.26x a car rather than 3x. Code 13 is read as transit because 93% of its
crashes fall in Pinellas and Hillsborough, the only two counties with fixed-route
service, while school buses (code 12, 90% school-bus-related, the anchor that
identifies it) spread evenly across all five. That is inference from the data,
not a code book, so it is stated as inference.

WHAT THE ANSWER IS. Buses here are roughly as dangerous to other people as cars,
per passenger-mile. Not because buses are reckless, but because ridership is so
low that each passenger-mile carries a great deal of vehicle. In a city where
buses were full the same arithmetic would favour them heavily.

THREE REASONS NOT TO PUT THIS IN THE HEADLINE.
  1. THREE deaths. One crash either way moves it by a third.
  2. Per PASSENGER-mile flatters cars here. Per VEHICLE-mile a bus replacing
     many cars looks very different, and neither figure is the whole truth.
  3. It is a Tampa Bay finding about Tampa Bay ridership, not about buses.

Reads:  the Signal Four crash export (licensed, not redistributable)
Writes: data/final/bus_externality.csv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COST_PER_PERSON, YEARS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
SRC = Path(r"C:\Users\yusra\claude\traffic-data"
           r"\signal4_district7_2019_2025.csv")

BUS_BODIES = {"Bus", "Motor Coach"}
TRANSIT_FN = "13"          # inferred, see docstring
SCHOOL_FN = "12"
CAR_EXTERNALITY = 0.051373  # step 35, data/final/externality.csv


def num(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def main():
    if not SRC.exists():
        sys.exit(f"FAIL: {SRC} not found. This step needs the licensed "
                 f"Signal Four extract.")

    fields = {"K": "S4_FATALITY_COUNT",
              "A": "S4_INCAPACITATING_INJURY_COUNT",
              "pK": "S4_PEDESTRIAN_FATALITY_COUNT",
              "pA": "S4_PEDESTRIAN_INCAPACITATING_INJURY_COUNT",
              "bK": "S4_BICYCLIST_FATALITY_COUNT",
              "bA": "S4_BICYCLIST_INCAPACITATING_INJURY_COUNT",
              "mK": "S4_MOTORCYCLIST_FATALITY_COUNT"}
    groups = {"transit": dict.fromkeys(fields, 0),
              "school": dict.fromkeys(fields, 0),
              "other bus": dict.fromkeys(fields, 0)}
    counts = dict.fromkeys(groups, 0)
    counties = {g: {} for g in groups}

    with SRC.open(encoding="utf8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            fn = None
            for v in ("V1", "V2"):
                if row.get(f"{v}_VHCL_BDY_TYP_CD", "").strip() in BUS_BODIES:
                    f = row.get(f"{v}_VHCL_SPCL_FNC_CD", "").strip()
                    fn = TRANSIT_FN if f == TRANSIT_FN else (fn or f)
            if fn is None:
                continue
            g = ("transit" if fn == TRANSIT_FN
                 else "school" if fn == SCHOOL_FN else "other bus")
            counts[g] += 1
            c = row.get("COUNTY_NAME", "").strip()
            counties[g][c] = counties[g].get(c, 0) + 1
            for k, col in fields.items():
                groups[g][k] += num(row.get(col))

    exp = INTERIM / "exposure_by_mode.csv"
    if not exp.exists():
        sys.exit("FAIL: exposure_by_mode.csv missing. Run step 03 first.")
    with exp.open(encoding="utf8") as fh:
        pmt = next(float(r["annual_pmt"]) for r in csv.DictReader(fh)
                   if r["mode"] == "transit")

    t = groups["transit"]
    caused_K = t["pK"] + t["bK"] + t["mK"]
    caused_A = t["pA"] + t["bA"]
    cost = (caused_K * COST_PER_PERSON["K"]
            + caused_A * COST_PER_PERSON["A"]) / YEARS
    rate = cost / pmt

    print("BUS CRASHES, FDOT DISTRICT 7, 2019-2025")
    print(f"  {'':<12}{'crashes':>9}{'killed':>8}{'serious':>9}"
          f"{'ped K':>7}{'bike K':>8}")
    for g in ("transit", "school", "other bus"):
        v = groups[g]
        print(f"  {g:<12}{counts[g]:>9,}{v['K']:>8}{v['A']:>9}"
              f"{v['pK']:>7}{v['bK']:>8}")

    tot = sum(counties["transit"].values())
    urban = sum(n for c, n in counties["transit"].items()
                if c in ("Pinellas", "Hillsborough"))
    print(f"\n  transit-coded crashes in the two counties with fixed-route "
          f"service: {urban / tot:.0%}")
    if urban / tot < 0.80:
        sys.exit(f"FAIL: only {urban / tot:.0%} of special-function-{TRANSIT_FN} "
                 f"bus crashes are in Pinellas or Hillsborough. The reading of "
                 f"that code as 'transit bus' is inference from exactly this "
                 f"pattern, so if the pattern is gone the inference is void.")

    print(f"\n  TRANSIT BUS, harm caused to people OUTSIDE the bus")
    print(f"    killed {caused_K}, seriously injured {caused_A}")
    print(f"    ${cost / 1e6:.1f}M per year over {pmt / 1e6:,.0f}M "
          f"passenger-miles")
    print(f"    per passenger-mile   ${rate:.4f}")
    print(f"    car, same convention ${CAR_EXTERNALITY:.4f}"
          f"   ratio {rate / CAR_EXTERNALITY:.2f}x")
    print(f"\n  Rests on {caused_K} deaths. One crash either way moves it by "
          f"about {1 / caused_K:.0%}.")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "bus_externality.csv").open("w", newline="",
                                              encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        for g in groups:
            w.writerow([f"{g}_crashes", counts[g]])
            w.writerow([f"{g}_killed", groups[g]["K"]])
            w.writerow([f"{g}_serious", groups[g]["A"]])
        w.writerow(["transit_caused_killed", caused_K])
        w.writerow(["transit_caused_serious", caused_A])
        w.writerow(["transit_externality_per_pmt", f"{rate:.6f}"])
        w.writerow(["car_externality_per_pmt", f"{CAR_EXTERNALITY:.6f}"])
        w.writerow(["bus_over_car", f"{rate / CAR_EXTERNALITY:.3f}"])
    print(f"\nwrote {FINAL / 'bus_externality.csv'}")


if __name__ == "__main__":
    main()
