"""
Step 25 - the spatial equivalency factor A*/A_k in MEP Equation 1.

    O_nmt = SUM_k  O_nmtk * (A*/A_k) * (f_k / SUM f_k)

READ THE DEFINITION CAREFULLY, BECAUSE GETTING IT WRONG IS SILENT:

    A*   total benchmark opportunities AMONG MULTIPLE CITIES IN THE U.S.
    A_k  total opportunities of activity k AMONG MULTIPLE CITIES IN THE U.S.
    "This factor should remain constant for a given city."
                            - FDOT BDV29-977-66, section 2.1, after Hou et al.

The denominator is NATIONAL. It is not the study region's own totals.

An earlier version of this pipeline used the local maximum, N*/N_j computed
from Tampa Bay alone. That produced a weight of 52 on arts-and-recreation, not
because arts destinations matter more, but because this region happens to have
few of them. Every scarce local activity got inflated, and the effect was
strongest exactly where the local count was least reliable.

It also breaks the property the factor exists to provide. MEP is meant to be
"comparable across locations"; a factor derived from local totals makes every
city's weights different, so no two MEP scores can be compared. The report says
the factor should remain constant for a given city, which is only possible if
its basis is external to that city.

This step computes it from LODES 8 for the whole United States, on exactly the
NAICS-to-activity mapping used for Tampa Bay, so numerator and denominator are
defined identically.

Writes: data/interim/spatial_equivalency.csv
"""

import csv
import gzip
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import USER_AGENT  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "lodes_national"
OUT = ROOT / "data" / "interim" / "spatial_equivalency.csv"

YEAR = 2023
URL = ("https://lehd.ces.census.gov/data/lodes/LODES8/{s}/wac/"
       "{s}_wac_S000_JT00_{y}.csv.gz")

STATES = ["al", "ak", "az", "ar", "ca", "co", "ct", "de", "dc", "fl", "ga",
          "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma",
          "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny",
          "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx",
          "ut", "vt", "va", "wa", "wv", "wi", "wy"]

# IDENTICAL to step 16. If these two ever diverge, the ratio is meaningless.
ACTIVITY = {"work": ["C000"], "meals": ["CNS18"], "social": ["CNS17"],
            "shopping": ["CNS07"], "medical": ["CNS16"],
            "school": ["CNS15", "CNS19"]}
# A* is the benchmark activity's national total.
#
# MEALS, because that is what the MEP tool itself uses. From the tool's own
# configuration documentation, quoted in FDOT BDV29-977-66:
#
#     "N_star: the baseline total opportunities for reference category
#      (meals by default)"
#
# and Hou et al. (2019) use the same reference: "taking meal as the reference
# category... the factor for shopping would be 0.17".
#
# THIS WAS "work" AND THAT WAS AN 11.05x ERROR ON EVERY SCORE. A* is constant
# across activities, so the benchmark choice is a single multiplicative scalar:
# A*_work / A*_meals = 150,944,613 / 13,655,757 = 11.0536. Every ranking, every
# percentage and every conclusion is invariant to it - which is exactly why it
# survived so long - but the ABSOLUTE level is not, and the absolute level is
# the first thing a reviewer compares against their own published scores.
#
# It also falsified a claim this project was making: that its scale gap against
# the published 122.35 and 11,983 was "unrescalable through three independent
# unknown scalars". One of those scalars was known exactly and was ours.
BENCHMARK = "meals"


def latest_year(state):
    """
    The newest JT00 release a state actually has.

    LODES is published per state and states fall behind independently. At the
    time of writing Florida has 2023, Michigan stops at 2021 and Alaska at
    2016. There is NO year for which all 51 files exist, so a benchmark that
    insists on one year is a benchmark missing two states.
    """
    idx = urllib.request.Request(
        f"https://lehd.ces.census.gov/data/lodes/LODES8/{state}/wac/",
        headers=USER_AGENT)
    with urllib.request.urlopen(idx, timeout=180) as r:
        html = r.read().decode("utf8", "replace")
    yrs = re.findall(rf"{state}_wac_S000_JT00_(\d{{4}})\.csv\.gz", html)
    if not yrs:
        raise SystemExit(f"FAIL: no JT00 releases listed for {state}")
    return max(yrs)


def get(state):
    """Returns (bytes, year_used). Falls back to the state's newest release."""
    for y in (str(YEAR), None):
        if y is None:
            y = latest_year(state)
            if y == str(YEAR):
                raise SystemExit(f"FAIL: {state} {YEAR} is listed but would "
                                 f"not download. Do not silently skip it.")
        p = RAW / f"{state}_wac_{y}.csv.gz"
        if p.exists():
            return p.read_bytes(), y
        RAW.mkdir(parents=True, exist_ok=True)
        try:
            req = urllib.request.Request(URL.format(s=state, y=y),
                                         headers=USER_AGENT)
            with urllib.request.urlopen(req, timeout=600) as r:
                blob = r.read()
        except urllib.error.HTTPError:
            continue
        p.write_bytes(blob)
        return blob, y
    raise SystemExit(f"FAIL: no usable LODES release for {state}")


def main():
    print(f"LODES 8 WAC {YEAR}, all states - national activity totals")
    tot = defaultdict(int)
    stale = []
    jobs_by_state = {}
    for i, st in enumerate(STATES, 1):
        blob, used = get(st)
        if used != str(YEAR):
            stale.append((st, used))
        head = None
        n = before = 0
        before = tot["work"]
        for line in gzip.decompress(blob).decode("utf8").splitlines():
            f = line.split(",")
            if head is None:
                head = {c: j for j, c in enumerate(f)}
                continue
            n += 1
            for act, cols in ACTIVITY.items():
                tot[act] += sum(int(f[head[c]]) for c in cols)
        jobs_by_state[st] = tot["work"] - before
        flag = "" if used == str(YEAR) else f"  <- {used}"
        print(f"  [{i:>2}/{len(STATES)}] {st}  {n:>8,} blocks  "
              f"running total {tot['work']:>12,} jobs{flag}", flush=True)

    if stale:
        share = sum(jobs_by_state[s] for s, _ in stale) / tot["work"]
        print(f"\n  {len(stale)} states are not on {YEAR}: "
              + ", ".join(f"{s} ({y})" for s, y in stale))
        print(f"  they contribute {share:.2%} of the national job total.")
        print(f"  A*/A_k is a RATIO of sector shares, and sector shares move "
              f"slowly,\n  so a stale minority year shifts it far less than "
              f"dropping the states would.")
        if share > 0.10:
            sys.exit(f"FAIL: {share:.1%} of the benchmark comes from stale "
                     f"years. That is too much to call this a {YEAR} "
                     f"benchmark.")

    a_star = tot[BENCHMARK]
    print(f"\n{'activity':<12}{'US total':>14}{'A*/A_k':>10}   basis")
    rows = []
    for act in ACTIVITY:
        factor = a_star / tot[act]
        rows.append({"activity": act, "us_total": tot[act],
                     "spatial_equivalency": round(factor, 6)})
        print(f"{act:<12}{tot[act]:>14,}{factor:>10.3f}   "
              f"{'benchmark' if act == BENCHMARK else '+'.join(ACTIVITY[act])}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
