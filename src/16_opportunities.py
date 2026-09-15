"""
Step 16 - opportunities by activity type.  MEP Equation 1, the `o_ijkt` counts.

MEP does not count "jobs". It counts SIX kinds of destination, because a trip to
work and a trip for lunch are not the same opportunity:

    work | meals | social & recreational | shopping & errands |
    medical & dental | school, daycare & religious

Source: LEHD LODES 8 Workplace Area Characteristics, Florida, 2023 - the latest
release. WAC counts jobs at the WORKPLACE census block, which is what an
opportunity is: somewhere you can go and find that activity.

WHY JOBS AS A PROXY FOR DESTINATIONS. MEP's own Table 1 lists CoStar, Google
Places and Foursquare as the alternatives. All three are commercial and none is
reproducible by a reader. LODES is free, federal and versioned. The cost is that
a big-box store and a corner shop are one job count, not one destination each,
so this measures the SIZE of an opportunity rather than the NUMBER. Stated here
because it biases toward dense employment centres.

NAICS -> activity mapping. Each is the closest single sector, not a blend:
    work                       C000   all jobs
    meals                      CNS18  Accommodation and Food Services
    social & recreational      CNS17  Arts, Entertainment, and Recreation
    shopping & errands         CNS07  Retail Trade
    medical & dental           CNS16  Health Care and Social Assistance
    school/daycare/religious   CNS15  Educational Services
                             + CNS19  Other Services - the ONLY sector holding
                               religious organisations (NAICS 8131), but it also
                               holds repair and personal services, so this
                               category is the loosest of the six.

Writes: data/interim/opportunities.csv   (one row per block group)
"""

import csv
import gzip
import io
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COUNTIES, STATE_FP, USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fl_wac_2023.csv.gz"
OUT = ROOT / "data" / "interim" / "opportunities.csv"

YEAR = 2023
URL = (f"https://lehd.ces.census.gov/data/lodes/LODES8/fl/wac/"
       f"fl_wac_S000_JT00_{YEAR}.csv.gz")

# activity -> the WAC columns that are summed for it
ACTIVITY = {
    "work":       ["C000"],
    "meals":      ["CNS18"],
    "social":     ["CNS17"],
    "shopping":   ["CNS07"],
    "medical":    ["CNS16"],
    "school":     ["CNS15", "CNS19"],
}

# The five study counties as 5-digit state+county FIPS.
KEEP = {STATE_FP + c for c in COUNTIES}


def download():
    if RAW.exists():
        return RAW.read_bytes()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(URL, headers=USER_AGENT)
    with urllib.request.urlopen(req, timeout=300) as r:
        blob = r.read()
    RAW.write_bytes(blob)
    return blob


def main():
    blob = download()
    print(f"LODES 8 WAC, Florida, {YEAR}   {len(blob)/1e6:.1f} MB")

    text = gzip.decompress(blob).decode("utf8")
    reader = csv.DictReader(io.StringIO(text))

    bg = defaultdict(lambda: defaultdict(int))
    blocks_read = blocks_kept = 0
    jobs_state = jobs_kept = 0

    for row in reader:
        blocks_read += 1
        geo = row["w_geocode"]
        # 15-digit block: state(2) county(3) tract(6) block(4).
        # Block group is the first 12 digits - the block's leading digit IS the
        # block group number, so this is a prefix, not an arbitrary truncation.
        jobs_state += int(row["C000"])
        if geo[:5] not in KEEP:
            continue
        blocks_kept += 1
        jobs_kept += int(row["C000"])
        key = geo[:12]
        for act, cols in ACTIVITY.items():
            bg[key][act] += sum(int(row[c]) for c in cols)

    print(f"{blocks_read:,} Florida blocks -> {blocks_kept:,} in the five counties")
    print(f"{jobs_state:,} Florida jobs   -> {jobs_kept:,} here "
          f"({jobs_kept/jobs_state:.1%} of the state)")
    print(f"{len(bg):,} block groups with at least one job\n")

    print(f"  {'activity':<26}{'opportunities':>15}{'share of jobs':>15}")
    tot = {a: sum(v[a] for v in bg.values()) for a in ACTIVITY}
    for act in ACTIVITY:
        print(f"  {act:<26}{tot[act]:>15,}{tot[act]/tot['work']:>14.1%}")

    # The five non-work categories are subsets of C000 and must not exceed it.
    non_work = sum(tot[a] for a in ACTIVITY if a != "work")
    if non_work > tot["work"]:
        sys.exit(f"FAIL: non-work activities ({non_work:,}) exceed all jobs "
                 f"({tot['work']:,}). The NAICS mapping double counts.")
    print(f"\n  the five named activities are {non_work/tot['work']:.1%} of all jobs;")
    print(f"  the rest is manufacturing, logistics, construction, offices -")
    print(f"  workplaces that are not destinations for anybody else.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["GEOID20"] + list(ACTIVITY))
        for key in sorted(bg):
            w.writerow([key] + [bg[key][a] for a in ACTIVITY])
    print(f"\nwrote {OUT}  ({len(bg):,} rows)")


if __name__ == "__main__":
    main()
