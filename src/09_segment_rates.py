"""
Step 09 - crash rates road by road, on the state highway system.

The project's regional rate cannot vary by place (step 06 proves why). This
step builds the spatial version where the data actually supports it.

  numerator    Signal Four crashes carrying LRS_ROADWAY + LRS_MILEPOINT
               547,205 of 602,110 (90.9%), covering 95.7% of deaths
  denominator  FDOT RCI segment AADT x segment length x 365
               2,850 segments, 1,854 roadways, 30.46 B VMT = 82% of all-roads

WHAT THIS CAN AND CANNOT SAY. A rate needs both halves. Local and county roads
carry 57% of crashes but FDOT publishes no counts for them, so those crashes
can be COUNTED on a road and never RATED. Counting without a denominator is
how you end up ranking busy roads instead of dangerous ones - the exact error
the Allegheny screening found, where ranking by count and by rate produced
top-25 lists sharing one road.

ASSUMPTION, stated because it is load-bearing: AADT is 2025 only, applied
across a 2019-2025 crash period. Traffic changed over those years, most
sharply in 2020. Segments whose volume moved a lot will have a biased rate.

Writes: data/final/segment_rates.csv
"""

import csv
import json
import sys
import urllib.parse
import urllib.request
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import CRASH_CSV, USER_AGENT, YEARS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"
RCI = "https://gis.fdot.gov/arcgis/rest/services/RCI_Layers/FeatureServer/0"
# FDOT county codes: Hillsborough 10, Pinellas 15, Pasco 14, Hernando 08, Citrus 02
COUNTY_DOT = {"10": "Hillsborough", "15": "Pinellas", "14": "Pasco",
              "08": "Hernando", "02": "Citrus"}


def denul(fh):
    for line in fh:
        yield line.replace("\x00", "")


SEG_CACHE = ROOT / "data" / "raw" / "fdot_rci_segments.json"


def fetch_segments():
    """
    FDOT's RCI layer, CACHED ON FIRST FETCH.

    WHY THE CACHE EXISTS. This is a LIVE ArcGIS service and its contents change.
    Two runs of this pipeline a few hours apart returned 2,429 and then 2,427
    segments, which moved the SPF fit (b from 0.7056 to 0.7300) and with it
    every origin's local crash rate and the region's MEP-with-harm mean. The
    reproducibility check in `run_all.py` caught it: `mep_published` was
    identical to the last decimal while `mep_harm_lo` had moved.

    Every other external input here is already pinned to a downloaded file -
    OSM tiles, GTFS zips, LODES, NHTS, ACS. This one was queried fresh each
    run, so the pipeline could not reproduce itself. A result that changes
    between runs on the same inputs cannot be defended, however small the
    change.

    Delete the cache file to deliberately refresh against current FDOT data.
    """
    if SEG_CACHE.exists():
        rows = json.loads(SEG_CACHE.read_text())
        print(f"  using cached FDOT segments ({len(rows):,}) from "
              f"{SEG_CACHE.name}; delete it to re-fetch")
        return rows

    where = "COUNTYDOT IN (" + ",".join(f"'{c}'" for c in COUNTY_DOT) + ")"
    rows, off = [], 0
    while True:
        url = (f"{RCI}/query?where={urllib.parse.quote(where)}"
               f"&outFields=ROADWAY,COUNTYDOT,BEGIN_POST,END_POST,AADT,YEAR_,DESC_FRM"
               f"&returnGeometry=false&resultOffset={off}&resultRecordCount=2000&f=json")
        req = urllib.request.Request(url, headers=USER_AGENT)
        with urllib.request.urlopen(req, timeout=180) as r:
            d = json.load(r)
        feats = d.get("features", [])
        if not feats:
            break
        rows += [f["attributes"] for f in feats]
        off += len(feats)
        if not d.get("exceededTransferLimit"):
            break
    # Written only after the whole fetch completed, so an interrupted download
    # cannot be mistaken for a complete snapshot on the next run.
    SEG_CACHE.parent.mkdir(parents=True, exist_ok=True)
    SEG_CACHE.write_text(json.dumps(rows))
    print(f"  cached {len(rows):,} FDOT segments to {SEG_CACHE.name}")
    return rows


def main():
    segs = fetch_segments()
    print(f"{len(segs):,} FDOT segments")

    # Index by roadway, sorted on BEGIN_POST so a milepost can be located by
    # binary search rather than scanning every segment for every crash.
    by_road = defaultdict(list)
    for s in segs:
        b, e = s.get("BEGIN_POST"), s.get("END_POST")
        if b is None or e is None or e <= b:
            continue
        by_road[str(s["ROADWAY"]).strip()].append(
            (float(b), float(e), float(s.get("AADT") or 0),
             str(s.get("COUNTYDOT")).zfill(2), s.get("DESC_FRM") or ""))
    for r in by_road:
        by_road[r].sort()
    starts = {r: [x[0] for x in v] for r, v in by_road.items()}
    print(f"{len(by_road):,} roadways indexed")

    # The full segment list, so zero-crash segments can be emitted too. Keys
    # are built identically to the tally keys, or the join below silently
    # misses and every segment looks like a zero-crash one.
    seg_keys = [(rw, b, e, aadt, cty, desc)
                for rw, v in by_road.items()
                for (b, e, aadt, cty, desc) in v]
    print(f"{len(seg_keys):,} segments to report on, crashes or not")

    # A (serious injury) is tallied alongside K because r_drive is KSI, and a
    # segment-level rate built on deaths alone could not be substituted into it
    # without changing the severity basis - the exact mistake that produced a
    # "188 to 1" asymmetry from a 95 to 1 reality elsewhere in this project.
    # OCCUPANT casualties are tallied separately from total, and the difference
    # is not cosmetic. A segment rate is only substitutable into `r_drive` if it
    # counts the same people. `r_drive` is what vehicle OCCUPANTS suffer
    # (specification A). The raw S4 total counts pedestrians, cyclists and
    # motorcyclists too, which is what driving CAUSES (specification B).
    # Region-wide those differ by 23,776 against 16,356 KSI, so swapping one for
    # the other inside MEP's drive cost term would silently change which
    # question the metric is answering.
    #
    # Occupants are the residual, exactly as in step 02, and the clamp is
    # counted for the same reason: it can only ever UNDERCOUNT occupants, so a
    # high hit rate would bias the segment rate low without raising.
    tally = defaultdict(lambda: {"crashes": 0, "K": 0, "A": 0, "pedK": 0,
                                 "occK": 0, "occA": 0})
    clamped = 0
    seen = matched = no_road = outside = 0
    deaths_all = deaths_matched = 0

    with open(CRASH_CSV, "r", encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(denul(fh)):
            seen += 1
            try:
                k = int(float(row.get("S4_FATALITY_COUNT") or 0))
            except ValueError:
                k = 0
            deaths_all += k

            rw = (row.get("LRS_ROADWAY") or "").strip()
            mp_raw = (row.get("LRS_MILEPOINT") or "").strip()
            if not rw or not mp_raw or rw not in by_road:
                no_road += 1
                continue
            try:
                mp = float(mp_raw)
            except ValueError:
                no_road += 1
                continue

            # Rightmost segment whose BEGIN_POST <= milepost, then check END_POST.
            i = bisect_right(starts[rw], mp) - 1
            if i < 0 or mp > by_road[rw][i][1]:
                outside += 1
                continue

            b, e, aadt, cty, desc = by_road[rw][i]
            t = tally[(rw, b, e, aadt, cty, desc)]
            def num(col):
                try:
                    return int(float(row.get(col) or 0))
                except ValueError:
                    return 0

            tot_a = num("S4_INCAPACITATING_INJURY_COUNT")
            ped_k = num("S4_PEDESTRIAN_FATALITY_COUNT")
            ped_a = num("S4_PEDESTRIAN_INCAPACITATING_INJURY_COUNT")
            bik_k = num("S4_BICYCLIST_FATALITY_COUNT")
            bik_a = num("S4_BICYCLIST_INCAPACITATING_INJURY_COUNT")
            mot_k = num("S4_MOTORCYCLIST_FATALITY_COUNT")
            mot_a = num("S4_MOTORCYCLIST_INCAPACITATING_INJURY_COUNT")

            t["crashes"] += 1
            t["K"] += k
            t["A"] += tot_a
            t["pedK"] += ped_k
            res_k = k - ped_k - bik_k - mot_k
            res_a = tot_a - ped_a - bik_a - mot_a
            if res_k < 0 or res_a < 0:
                clamped += 1
            t["occK"] += max(0, res_k)
            t["occA"] += max(0, res_a)
            matched += 1
            deaths_matched += k
            if seen % 100_000 == 0:
                print(f"  {seen:,}")

    print(f"\nMATCH RESULT  ({seen:,} crashes)")
    print(f"  matched to a segment    {matched:>9,}  {matched/seen:>6.1%}")
    print(f"  no roadway/milepost     {no_road:>9,}  {no_road/seen:>6.1%}")
    print(f"  milepost outside segs   {outside:>9,}  {outside/seen:>6.1%}")
    print(f"  deaths on matched       {deaths_matched:>9,} of {deaths_all:,}"
          f"  ({deaths_matched/deaths_all:.1%})")

    # EVERY SEGMENT IS EMITTED, INCLUDING THOSE WITH ZERO CRASHES.
    #
    # This loop used to iterate `tally`, which only contains segments a crash
    # matched to. That silently dropped 421 of 2,848 segments - the ones with
    # no crashes at all - and those are systematically the short, quiet ones.
    #
    # For the segment RATES it made little difference: a zero-crash segment has
    # a rate of zero and adds nothing to a ranking. For the SAFETY PERFORMANCE
    # FUNCTION in step 29 it is fatal. Fitting `crashes ~ AADT^b * L` on a
    # sample SELECTED ON HAVING CRASHES is selection on the outcome variable.
    # It biases exp(a) upward and b downward, so the model over-predicts for
    # quiet roads - and Empirical Bayes then shrinks those roads TOWARD an
    # inflated expectation, which is the exact opposite of what EB is for.
    #
    # A zero-crash segment is data. It says: this much exposure produced no
    # casualties.
    out = []
    zero_crash = 0
    for key in seg_keys:
        rw, b, e, aadt, cty, desc = key
        t = tally.get(key) or {"crashes": 0, "K": 0, "A": 0, "pedK": 0,
                               "occK": 0, "occA": 0}
        if t["crashes"] == 0:
            zero_crash += 1
        length = e - b
        vmt = aadt * length * 365 * YEARS
        if vmt <= 0:
            continue
        out.append({
            "roadway": rw, "county": COUNTY_DOT.get(cty, cty),
            "begin_post": round(b, 3), "end_post": round(e, 3),
            "length_mi": round(length, 3), "aadt": int(aadt),
            "description": desc[:60],
            "crashes": t["crashes"], "deaths": t["K"],
            "serious": t["A"], "ped_deaths": t["pedK"],
            "occ_deaths": t["occK"], "occ_serious": t["occA"],
            "vmt_period": round(vmt),
            "deaths_per_100M_vmt": round(t["K"] / (vmt / 1e8), 3),
            "crashes_per_100M_vmt": round(t["crashes"] / (vmt / 1e8), 1),
        })

    occ_k = sum(r["occ_deaths"] for r in out)
    occ_a = sum(r["occ_serious"] for r in out)
    all_k = sum(r["deaths"] for r in out)
    all_a = sum(r["serious"] for r in out)
    print("\n  CASUALTIES ON MATCHED SEGMENTS")
    print(f"    all modes        {all_k:>7,} K   {all_a:>7,} A   "
          f"{all_k + all_a:>7,} KSI   <- what driving CAUSES")
    print(f"    occupants only   {occ_k:>7,} K   {occ_a:>7,} A   "
          f"{occ_k + occ_a:>7,} KSI   <- what drivers SUFFER")
    print(f"    residual clamp fired on {clamped:,} crashes "
          f"({clamped / max(matched, 1):.2%} of matched)")
    print(f"    Only the occupant columns are substitutable into r_drive.")

    tot_vmt = sum(r["vmt_period"] for r in out)
    tot_k = sum(r["deaths"] for r in out)
    print(f"\n  {len(out):,} segments with volume, of which {zero_crash:,} had "
          f"ZERO crashes")
    print(f"    Zero-crash segments are KEPT. Dropping them, as an earlier")
    print(f"    version did, made the step 29 SPF a sample selected on the")
    print(f"    outcome variable: biased exp(a) up and b down, so Empirical")
    print(f"    Bayes then shrank quiet roads toward an inflated expectation.")
    print(f"  period VMT on them      {tot_vmt/1e9:>9.1f} B")
    print(f"  regional fatality rate  {tot_k/(tot_vmt/1e8):>9.2f} per 100M VMT"
          f"   (Florida statewide ~1.54)")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "segment_rates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out[0].keys())
        w.writeheader()
        w.writerows(sorted(out, key=lambda r: -r["deaths_per_100M_vmt"]))
    print(f"\nwrote {FINAL / 'segment_rates.csv'}")


if __name__ == "__main__":
    main()
