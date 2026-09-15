"""
Are the free MEP inputs actually reachable and usable?

Nothing gets committed to until every input is confirmed downloadable, sized, and
licensed for use. Checks, without downloading the bulk:

    HART GTFS       Hillsborough transit, via Mobility Database
    PSTA GTFS       Pinellas transit
    LEHD LODES      workplace jobs by census block, for the accessibility target
    Census PUMS     the seed for a synthetic population
    TIGER blocks    geography to hang jobs on

HEAD requests where possible so this is cheap to re-run.
"""

import gzip
import io
import re
import urllib.request

UA = {"User-Agent": "tampa-mep/1.0 (research)"}


def head(url, label, note=""):
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=60) as r:
            size = r.headers.get("Content-Length")
            mb = f"{int(size)/1e6:.1f} MB" if size else "size unknown"
            print(f"  OK    {label:<34}{mb}   {note}")
            return True
    except Exception as exc:
        print(f"  FAIL  {label:<34}{str(exc)[:52]}")
        return False


def get(url, label, nbytes=None):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read(nbytes) if nbytes else r.read()
        print(f"  OK    {label:<34}{len(data)/1e3:.0f} KB read")
        return data
    except Exception as exc:
        print(f"  FAIL  {label:<34}{str(exc)[:52]}")
        return None


print("TRANSIT")
HART = ("https://files.mobilitydatabase.org/mdb-325/"
        "mdb-325-202608130142/mdb-325-202608130142.zip")
head(HART, "HART GTFS (Hillsborough)", "32 routes, 2026-08-13")
# The obvious google_transit.zip path 404s. Transitland's registry gives the
# real fetch URL PSTA publishes, and the bus feed sits beside the ferry one.
for path in ("latest/google_bus.zip", "latest/google_transit.zip",
             "latest/google_ferry.zip"):
    head(f"https://psta.net/{path}", f"PSTA GTFS ({path.split('/')[-1]})")

print("\nJOBS — LEHD LODES8, Florida")
page = get("https://lehd.ces.census.gov/data/lodes/LODES8/fl/wac/",
           "WAC directory listing")
if page:
    names = sorted(set(re.findall(rb"fl_wac_S000_JT00_\d{4}\.csv\.gz", page)))
    if names:
        yrs = [int(n.decode()[-11:-7]) for n in names]
        print(f"        all-jobs files: {len(names)}   years {min(yrs)}-{max(yrs)}")
        latest = names[-1].decode()
        head(f"https://lehd.ces.census.gov/data/lodes/LODES8/fl/wac/{latest}",
             f"  latest: {latest}")

head("https://lehd.ces.census.gov/data/lodes/LODES8/fl/fl_xwalk.csv.gz",
     "block->county crosswalk")

print("\nSYNTHETIC POPULATION SEED — Census PUMS 2019-2023 ACS 5yr, FL")
head("https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year/"
     "csv_pfl.zip", "PUMS person records, FL")
head("https://www2.census.gov/programs-surveys/acs/data/pums/2023/5-Year/"
     "csv_hfl.zip", "PUMS household records, FL")

print("\nGEOGRAPHY — TIGER 2023 blocks, the five study counties")
FIPS = {"057": "Hillsborough", "103": "Pinellas", "101": "Pasco",
        "053": "Hernando", "017": "Citrus"}
ok = 0
for code, name in FIPS.items():
    if head(f"https://www2.census.gov/geo/tiger/TIGER2023/TABBLOCK20/"
            f"tl_2023_12_tabblock20.zip", f"FL blocks (covers {name})"):
        ok += 1
        break     # one statewide file covers all five
print(f"\n  statewide block file covers all five counties: {'yes' if ok else 'unverified'}")
