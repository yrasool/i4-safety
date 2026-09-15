"""
Step 10 - which segments are actually dangerous?

Step 09 gives a fatality rate for 2,429 segments. Ranking on that raw rate is
a trap. A 0.1-mile segment carrying 2,000 vehicles a day accumulates about
0.5 million vehicle-miles over the period, so a SINGLE death there prints a
rate near 200 per 100M VMT - roughly 130x the regional average - on evidence
of one event.

The Allegheny screening found the consequence directly: ranking by crash count
and ranking by crash rate produced top-25 lists that shared one road. Neither
list was wrong. They were answering different questions, and only one of them
was about danger.

This step loads the segments and prints the diagnostics that show the problem,
then applies whatever screening rule is defined below.

Writes: data/final/screened_segments.csv
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"

# Florida statewide, FDOT 2055 FTP Performance Report, PM1 2023.
STATEWIDE_RATE = 1.54     # deaths per 100M VMT


def load():
    with (FINAL / "segment_rates.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("length_mi", "deaths_per_100M_vmt", "crashes_per_100M_vmt"):
            r[k] = float(r[k])
        for k in ("aadt", "crashes", "deaths", "ped_deaths", "vmt_period"):
            r[k] = int(float(r[k]))
    return rows


def diagnostics(rows):
    with_k = [r for r in rows if r["deaths"] > 0]
    print(f"{len(rows):,} segments   {len(with_k):,} with at least one death\n")

    print("  WHY THE RAW RATE MISLEADS")
    top = sorted(rows, key=lambda r: -r["deaths_per_100M_vmt"])[:5]
    print(f"    {'rate':>8}{'deaths':>8}{'VMT (M)':>10}{'len mi':>8}  road")
    for r in top:
        print(f"    {r['deaths_per_100M_vmt']:>8.1f}{r['deaths']:>8}"
              f"{r['vmt_period']/1e6:>10.1f}{r['length_mi']:>8.2f}  "
              f"{r['county']} {r['description'][:34]}")

    print("\n  RANKING BY COUNT VS BY RATE - how much do they agree?")
    by_rate = [r["roadway"] + str(r["begin_post"])
               for r in sorted(rows, key=lambda r: -r["deaths_per_100M_vmt"])[:25]]
    by_count = [r["roadway"] + str(r["begin_post"])
                for r in sorted(rows, key=lambda r: -r["deaths"])[:25]]
    print(f"    segments in both top-25 lists: {len(set(by_rate) & set(by_count))} of 25")


def screen(rows):
    """
    TODO(human): decide which segments count as high-risk, and return them.

    Return a list of the rows that should be flagged, most serious first.
    Each row is a dict with: deaths, crashes, ped_deaths, vmt_period,
    length_mi, aadt, deaths_per_100M_vmt, crashes_per_100M_vmt, county,
    roadway, begin_post, end_post, description.

    STATEWIDE_RATE (1.54 deaths per 100M VMT) is available as a comparator.
    """
    return []


def main():
    rows = load()
    diagnostics(rows)

    flagged = screen(rows)
    if not flagged:
        print("\n  screen() returned nothing yet - see TODO(human) in this file")
        return

    print(f"\n  FLAGGED {len(flagged):,} segments "
          f"({len(flagged)/len(rows):.1%} of the network)")
    tot_k = sum(r["deaths"] for r in rows)
    fl_k = sum(r["deaths"] for r in flagged)
    fl_mi = sum(r["length_mi"] for r in flagged)
    all_mi = sum(r["length_mi"] for r in rows)
    print(f"    they carry {fl_k:,} of {tot_k:,} deaths ({fl_k/tot_k:.1%})")
    print(f"    on {fl_mi:,.0f} of {all_mi:,.0f} miles ({fl_mi/all_mi:.1%})")

    with (FINAL / "screened_segments.csv").open("w", newline="",
                                                encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=flagged[0].keys())
        w.writeheader()
        w.writerows(flagged)
    print(f"\nwrote {FINAL / 'screened_segments.csv'}")


if __name__ == "__main__":
    main()
