"""
Profile the full Signal Four extract against the NLR job description.

The question is not "what is in this file" - it is which of the proposed projects
the data can actually carry. So this checks the specific fields each idea needs:

  1 travel behaviour through the pandemic  -> year, hour, day-of-week, month
  2 freight energy and risk                -> CMV, heavy truck, vehicle type
  3 safety performance function            -> AADT, lanes, speed, functional class
  4 unsupervised pattern discovery         -> behavioural + environmental flags
  5 emerging technology / EV               -> nothing here; needs PennDOT EV data

Reports what is present, how well populated, and where an idea would run thin.
"""

import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv"

NEEDED = {
    "when": ["CRASH_YEAR", "CRASH_MONTH", "CRASH_DATE_AND_TIME", "DAY_OF_WEEK",
             "S4_DAY_OR_NIGHT", "CRASH_TIME", "HOUR_OF_DAY"],
    "where": ["MANAGING_DOT_DISTRICT", "COUNTY_NAME", "LATITUDE", "LONGITUDE",
              "LRS_ROADWAY", "LRS_MILEPOINT", "ON_STREET_ROAD_HIGHWAY",
              "RURAL_OR_URBAN", "FUNC_CLASS"],
    "exposure": ["DOT_AADT", "AADT", "DOT_POSTED_SPEED", "DOT_NBR_LANES",
                 "DOT_DIVIDED_UNDIVIDED", "DOT_ACCESS_CONTROL", "DOT_SURFACE_WIDTH"],
    "freight": ["S4_IS_CMV_INVOLVED", "V1_VHCL_BDY_TYP_CD", "V2_VHCL_BDY_TYP_CD",
                "TOTAL_NUMBER_OF_VEHICLES"],
    "behaviour": ["S4_IS_SPEEDING_RELATED", "S4_IS_DISTRACTED", "S4_IS_ALCOHOL_RELATED",
                  "S4_IS_DRUG_RELATED", "S4_IS_AGGRESSIVE_DRIVING",
                  "S4_IS_LANE_DEPARTURE_RELATED", "S4_IS_HIT_AND_RUN",
                  "S4_IS_INTERSECTION_RELATED"],
    "environment": ["LIGHT_CONDITION", "WEATHER_CONDITION", "ROAD_SURFACE_CONDITION",
                    "FIRST_HARMFUL_EVENT", "TYPE_OF_IMPACT"],
    "outcome": ["S4_CRASH_SEVERITY", "S4_FATALITY_COUNT", "S4_INJURY_COUNT",
                "S4_IS_PEDESTRIAN_INVOLVED", "S4_IS_BICYCLIST_INVOLVED",
                "TOTAL_NUMBER_OF_PERSONS"],
}


def main():
    with open(SRC, encoding="utf-8", errors="replace", newline="") as fh:
        header = next(csv.reader(fh))
    print(f"{len(header)} columns\n")

    have, missing = {}, {}
    for group, cols in NEEDED.items():
        have[group] = [c for c in cols if c in header]
        missing[group] = [c for c in cols if c not in header]

    # Anything AADT-ish or time-ish we did not guess the name of?
    extra_exp = [c for c in header
                 if any(k in c.upper() for k in ("AADT", "VOLUME", "TRAFFIC", "VMT"))]
    extra_time = [c for c in header
                  if any(k in c.upper() for k in ("TIME", "HOUR", "MONTH", "DATE"))]
    extra_veh = [c for c in header if "VHCL" in c.upper() or "VEH" in c.upper()]

    print("FIELDS PRESENT, BY IDEA")
    for g in NEEDED:
        print(f"\n  {g}:")
        for c in have[g]:
            print(f"      + {c}")
        for c in missing[g]:
            print(f"      - {c}   (absent)")

    print(f"\n  exposure-ish columns actually in the file: {extra_exp or 'NONE'}")
    print(f"  time-ish columns: {extra_time}")
    print(f"  vehicle columns: {extra_veh[:14]}")

    # Populate rates on a sample, which is enough to judge usability.
    watch = sorted({c for g in have for c in have[g]} | set(extra_exp))
    counts = {c: 0 for c in watch}
    years = collections.Counter()
    dist = collections.Counter()
    n = 0
    # The export contains embedded NUL bytes, which csv refuses outright.
    # Strip them per line rather than pre-cleaning a 500 MB file.
    def denul(f):
        for line in f:
            yield line.replace("\x00", "")

    with open(SRC, encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.DictReader(denul(fh)):
            n += 1
            for c in watch:
                if (row.get(c) or "").strip():
                    counts[c] += 1
            years[(row.get("CRASH_YEAR") or "").strip()] += 1
            dist[(row.get("MANAGING_DOT_DISTRICT") or "").strip()] += 1
            if n >= 120000:
                break

    print(f"\n\nPOPULATED RATE (first {n:,} rows)")
    for c in watch:
        pct = counts[c] / n * 100
        flag = "  <-- thin" if pct < 60 else ""
        print(f"  {c:<34}{pct:5.1f}%{flag}")

    print(f"\nyears: {dict(sorted(years.items()))}")
    print(f"districts: {dict(sorted(dist.items(), key=lambda kv: -kv[1])[:6])}")


if __name__ == "__main__":
    main()
