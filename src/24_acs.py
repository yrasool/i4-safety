"""
Step 24 - population and vehicle access on 2020 block groups.

RUN THIS BEFORE STEP 16. It is numbered 24 because it was written last, not
because it runs last.

WHY THIS EXISTS. Steps 01 to 07 take population and vehicle ownership from
EPA's Smart Location Database. The SLD field is called `GEOID20`, which reads
like 2020 census geography. It is not. EPA's own layer metadata says:

    GEOID20 - Census block group 12-digit FIPS code (2018)

and the values behind it are ACS 2014-2018. So the SLD sits on 2018 block
groups while LODES 2023, the TIGERweb centroids and the crash data all sit on
2020 ones. For these five counties that is 2,098 rows against 2,170, and only
1,670 GEOIDs appear in both. Five hundred block groups exist in one map and not
the other, and a join across them succeeds silently on whatever matches.

This step replaces the SLD demographics with ACS 2023 five-year estimates on
2020 block groups, so the whole pipeline sits on one geography.

SOURCE. The Census summary files, not the API - the API now demands a key for
block group queries, and a pipeline that needs a secret is a pipeline nobody
else can run. The summary files are plain pipe-delimited text over HTTPS.

    B01003   total population
    B25044   tenure by vehicles available; zero-vehicle households are
             owner-occupied-with-none plus renter-occupied-with-none

B08201 would be the more natural vehicle table but it is NOT PUBLISHED at
block group level, only to tract. B25044 is the block group table.

Writes: data/interim/acs_blockgroups.csv
"""

import csv
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COUNTIES, STATE_FP, USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "interim" / "acs_blockgroups.csv"

YEAR = 2023
BASE = ("https://www2.census.gov/programs-surveys/acs/summary_file/"
        f"{YEAR}/table-based-SF/data/5YRData/acsdt5y{YEAR}-{{}}.dat")

BG_LEVEL = "1500000US"                       # summary level for block groups
KEEP = tuple(BG_LEVEL + STATE_FP + c for c in COUNTIES)


def fetch(table):
    path = RAW / f"acs{YEAR}_{table}.dat"
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(BASE.format(table), headers=USER_AGENT)
        with urllib.request.urlopen(req, timeout=900) as r:
            path.write_bytes(r.read())
    lines = path.read_text(encoding="utf8", errors="replace").splitlines()
    head = lines[0].split("|")
    rows = {}
    for ln in lines[1:]:
        if not ln.startswith(KEEP):
            continue
        f = ln.split("|")
        rows[f[0].split("US")[1]] = dict(zip(head, f))
    print(f"  {table}  {len(rows):,} block groups in the five counties")
    return rows


def num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


def main():
    print(f"ACS {YEAR} five-year estimates, 2020 block groups")
    pop = fetch("b01003")
    veh = fetch("b25044")

    ids = sorted(set(pop) | set(veh))
    if set(pop) != set(veh):
        print(f"  NOTE {len(set(pop) ^ set(veh))} block groups appear in one "
              f"table and not the other")

    rows = []
    for gid in ids:
        p, v = pop.get(gid, {}), veh.get(gid, {})
        hh = num(v.get("B25044_E001"))
        # E003 owner-occupied with no vehicle, E010 renter-occupied with none
        zero = num(v.get("B25044_E003")) + num(v.get("B25044_E010"))
        rows.append({"GEOID20": gid,
                     "county": COUNTIES[gid[2:5]],
                     "pop": num(p.get("B01003_E001")),
                     "households": hh,
                     "zero_vehicle_hh": zero,
                     "zero_vehicle_share": round(zero / hh, 6) if hh else ""})

    # A share above 1 means the two components are not subsets of the total,
    # which would mean the column mapping is wrong. This has to be impossible,
    # not merely unlikely.
    bad = [r for r in rows if r["zero_vehicle_share"] != ""
           and r["zero_vehicle_share"] > 1]
    if bad:
        sys.exit(f"FAIL: {len(bad)} block groups report more zero-vehicle "
                 f"households than households. Check the B25044 column map.")

    total_pop = sum(r["pop"] for r in rows)
    total_hh = sum(r["households"] for r in rows)
    total_zero = sum(r["zero_vehicle_hh"] for r in rows)
    print(f"\n  {len(rows):,} block groups")
    print(f"  population        {total_pop:>12,}")
    print(f"  households        {total_hh:>12,}")
    print(f"  zero-vehicle      {total_zero:>12,}  ({total_zero/total_hh:.1%})")
    print(f"\n  {'county':<15}{'BGs':>6}{'population':>13}{'zero-car hh':>13}"
          f"{'share':>8}")
    for c in sorted(COUNTIES.values()):
        sub = [r for r in rows if r["county"] == c]
        z = sum(r["zero_vehicle_hh"] for r in sub)
        h = sum(r["households"] for r in sub)
        print(f"  {c:<15}{len(sub):>6}{sum(r['pop'] for r in sub):>13,}"
              f"{z:>13,}{z/h:>8.1%}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
