"""
Step 01 - pull the accessibility surface.

EPA's Smart Location Database already publishes what a routing engine would have
had to compute: jobs reachable within 45 minutes by car (D5AR) and by transit
(D5BR), per block group. Using their number instead of a home-rolled one means
nobody has to ask how the travel times were validated.

Also pulls the built-environment "D variables", which step 07 uses, and the
vehicle-ownership counts, which are the equity split.

Writes: data/interim/sld.parquet   (2,098 rows)
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE = ("https://geodata.epa.gov/arcgis/rest/services/OA/"
        "SmartLocationDatabase/MapServer/1")
UA = {"User-Agent": "tampa-mep/1.0 (research)"}

# FDOT District 7. Hillsborough, Pinellas, Pasco, Hernando, Citrus.
COUNTIES = {"057": "Hillsborough", "103": "Pinellas", "101": "Pasco",
            "053": "Hernando", "017": "Citrus"}
WHERE = ("STATEFP='12' AND COUNTYFP IN ("
         + ",".join(f"'{c}'" for c in COUNTIES) + ")")

# Field names are CASE-SENSITIVE. TOTPOP returns null; TotPop returns the value.
FIELDS = [
    "GEOID20", "COUNTYFP",
    "TotPop", "TotEmp", "HH", "Workers",
    "D5AR", "D5BR",            # jobs in 45 min: auto, transit
    "D5AE", "D5BE",            # working-age pop equivalents
    "D1B",                     # gross population density
    "D2A_JPHH",                # jobs per household
    "D3A", "D3B",              # road density, street intersection density
    "D4A", "D4C", "D4D",       # transit proximity, frequency, per capita
    "AutoOwn0", "AutoOwn1", "AutoOwn2p",
]

# EPA's no-data sentinel. NOT a value. Converted to NA on read so it can never
# be averaged in by accident - see the note in step 04.
NODATA = -99999

OUT = Path(__file__).resolve().parents[1] / "data" / "interim" / "sld.parquet"


def fetch(params, tries=3):
    url = f"{BASE}/query?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)
        except Exception as exc:
            if attempt == tries - 1:
                raise
            print(f"    retry {attempt + 1}: {str(exc)[:60]}")
            time.sleep(2 ** attempt)


def fetch_live():
    """Page the live EPA service. Called only when no raw cache exists."""
    expected = fetch({"where": WHERE, "returnCountOnly": "true",
                      "f": "json"})["count"]
    print(f"block groups in study area: {expected}")

    # The service caps at 1000 records per response, so page through.
    rows, offset = [], 0
    while True:
        page = fetch({
            "where": WHERE,
            "outFields": ",".join(FIELDS),
            "returnGeometry": "false",
            "resultOffset": offset,
            "resultRecordCount": 1000,
            "orderByFields": "GEOID20",
            "f": "json"})
        feats = page.get("features", [])
        if not feats:
            break
        rows.extend(f["attributes"] for f in feats)
        offset += len(feats)
        print(f"  fetched {offset}")
        if not page.get("exceededTransferLimit"):
            break
    return expected, rows


# CACHED, BECAUSE THE SOURCE IS LIVE.
#
# This step used to query EPA's ArcGIS service on every run and keep nothing.
# That is the exact arrangement that made FDOT's live segment layer return
# 2,429 segments one day and 2,427 the next, which moved the headline and was
# caught only by run_all.py's before/after diff.
#
# It also sat OUTSIDE run_all.py, while steps 03, 04 and 26 all read its
# output. Step 26's two external-validation figures - Spearman 0.8985 against
# D5AR, 0.6161 against D5BR - are gated in the report, and they rested on a
# file no pipeline step produced. Third instance of that bug in this project,
# after steps 05 and 33.
#
# So the raw response is now kept in data/raw/, beside the other downloads,
# and re-fetched only if deleted. The row count the service reported at fetch
# time is stored with it, so the completeness check below still means
# something on a cached run rather than comparing the cache to itself.
RAW_CACHE = OUT.parents[1] / "raw" / "sld_epa_rows.json"


def main():
    if RAW_CACHE.exists():
        cached = json.loads(RAW_CACHE.read_text(encoding="utf8"))
        expected, rows = cached["expected"], cached["rows"]
        print(f"read {len(rows)} rows from {RAW_CACHE.name} "
              f"(service reported {expected} at fetch time; delete the file "
              f"to re-fetch)")
    else:
        expected, rows = fetch_live()
        RAW_CACHE.parent.mkdir(parents=True, exist_ok=True)
        RAW_CACHE.write_text(json.dumps({"expected": expected, "rows": rows}),
                             encoding="utf8")
        print(f"cached raw response to {RAW_CACHE}")

    df = pd.DataFrame(rows)

    # Fail loudly rather than quietly analysing a partial region.
    if len(df) != expected:
        sys.exit(f"FAIL: got {len(df)} rows, service reports {expected}")
    if df["GEOID20"].duplicated().any():
        sys.exit("FAIL: duplicate GEOID20 - paging returned overlapping rows")

    df["county"] = df["COUNTYFP"].map(COUNTIES)
    if df["county"].isna().any():
        sys.exit("FAIL: unexpected COUNTYFP outside the five study counties")

    # Sentinel -> NA, before anything can average it.
    sentinel_cols = ["D5AR", "D5BR", "D5AE", "D5BE"]
    counts = {c: int((df[c] == NODATA).sum()) for c in sentinel_cols}
    for c in sentinel_cols:
        df[c] = df[c].replace(NODATA, pd.NA)

    print("\nno-data (-99999 -> NA)")
    for c, n in counts.items():
        print(f"  {c:<6}{n:>5} of {len(df)}  ({n / len(df):5.1%})")

    print("\nno transit-reachable jobs, by county")
    for fips, name in sorted(COUNTIES.items(),
                             key=lambda kv: -len(df[df.COUNTYFP == kv[0]])):
        sub = df[df.COUNTYFP == fips]
        nd = int(sub["D5BR"].isna().sum())
        print(f"  {name:<14}{nd:>4} of {len(sub):>4}  ({nd / len(sub):5.1%})")

    # D5AR should never be missing. Every other invariant here exits; this one
    # used to only warn, and step 06 would then have turned the NA into ZERO
    # car-accessible jobs - a number that reads as "nowhere to drive to from
    # here", which is essentially never true and would corrupt the whole loss
    # and equity comparison. Fail closed like the rest.
    if counts["D5AR"]:
        sys.exit(f"FAIL: D5AR has {counts['D5AR']} missing values and had none "
                 f"before. The SLD release changed; do not trust the auto "
                 f"surface until this is understood.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"\nwrote {OUT}  ({len(df)} rows, {len(df.columns)} cols)")


if __name__ == "__main__":
    main()
