"""Step 50 - what a safety programme buys, in accessibility.

THE QUESTION. Every figure in this project so far describes a problem. This one
describes a remedy: if the worst road segments were made as safe as a typical
one, how much of the lost accessibility comes back?

It is the shape of question NREL answered for Delaware and for Miami's bike
corridors - measure an intervention's effect on MEP - but on the lever a state
DOT actually holds. FDOT does not choose how far people ride. It chooses which
roads to rebuild.

WHY THIS IS WORTH RUNNING. Harm on the state system is extremely concentrated:
half the expected KSI sits on about 200 of 2,848 segments, roughly a fifth of
the mileage. A remedy aimed at those is a small programme, and the question is
whether a small programme moves a regional metric at all.

WHAT THE SCENARIO DOES, precisely. Segments are ranked by EXPECTED KSI, not by
rate - a lethal road nobody drives is not where a DOT spends. The worst N have
their $/passenger-mile capped at the regional median segment rate. Nothing else
changes: same network, same speeds, same opportunities, same travel times. Then
step 40 is rerun on the capped rates and MEP is recomputed.

WHAT IT IS NOT. Not a cost-benefit study - there is no construction cost here,
so "per segment fixed" is a unit of effort, not of money. Not a prediction that
any particular treatment achieves the median rate; the median is a target, and
which treatment reaches it is an engineering question this model cannot answer.
Read it as: this is the accessibility on the table, if the safety can be had.

Reads:  data/final/segment_eb.csv, route_risk_by_origin*.csv, plus step 26's
        own loaders for the MEP inputs
Writes: data/final/segment_fix_scenario.csv
        data/final/segment_eb_capped_*.csv   (the scenario's input, kept so the
                                              run can be reproduced exactly)
"""
import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
OUT = FINAL / "segment_fix_scenario.csv"

# How many of the worst segments the programme treats. 200 because that is
# roughly where half the expected KSI has accumulated; 50 and 500 bracket it.
FIX_COUNTS = (50, 200, 500)


def load_step26():
    """One implementation of MEP, imported - never restated."""
    spec = importlib.util.spec_from_file_location("v26", SRC / "26_validate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["v26"] = m
    spec.loader.exec_module(m)
    return m


def read_csv(p):
    with p.open(encoding="utf8") as fh:
        return list(csv.DictReader(fh))


def write_capped(segs, n_fix, target, tag):
    """Cap the worst n_fix segments' rate at `target` and write the file."""
    ksi = np.array([float(s["ksi_eb"] or 0) for s in segs])
    worst = set(np.argsort(-ksi)[:n_fix].tolist())
    out, treated_mi, ksi_removed = [], 0.0, 0.0
    for i, s in enumerate(segs):
        row = dict(s)
        if i in worst and float(s["r_per_pmt"] or 0) > target:
            treated_mi += float(s["length_mi"] or 0)
            old = float(s["r_per_pmt"])
            ksi_removed += float(s["ksi_eb"] or 0) * (1 - target / old)
            row["r_per_pmt"] = f"{target:.6f}"
        out.append(row)
    p = FINAL / f"segment_eb_capped_{tag}.csv"
    with p.open("w", encoding="utf8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(segs[0]))
        w.writeheader()
        w.writerows(out)
    return p, treated_mi, ksi_removed


def run_step40(seg_name, tag):
    """Rerun route assignment on the capped rates. ~17 minutes."""
    import os
    env = dict(os.environ, MEP_SEGMENT_FILE=seg_name, MEP_ROUTE_TAG=f"_{tag}")
    r = subprocess.run([sys.executable, str(SRC / "40_route_assignment.py")],
                       env=env, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"FAIL: step 40 failed for {tag}\n{r.stdout[-2000:]}\n"
                 f"{r.stderr[-2000:]}")
    return FINAL / f"route_risk_by_origin_{tag}.csv"


def bands_from(path, geoid, n, bands, fallback):
    rb = {r["GEOID20"]: r for r in read_csv(path)}
    out = np.zeros((len(bands), n))
    for bi, b in enumerate(bands):
        for k, g in enumerate(geoid):
            v = rb.get(g, {}).get(f"r_band{b}", "")
            out[bi, k] = float(v) if v else fallback
    return out


def main():
    v = load_step26()
    segs = read_csv(FINAL / "segment_eb.csv")
    rates = np.array([float(s["r_per_pmt"] or 0) for s in segs])
    ksi = np.array([float(s["ksi_eb"] or 0) for s in segs])
    target = float(np.median(rates))

    geoid, county, o, n = v.build()
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        popmap = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
    pop = np.array([popmap.get(g, 0.0) for g in geoid])
    r_drive, r_transit, R_WALK, R_BIKE = v.read_rates()
    real = {"drive": "route", "transit": r_transit,
            "walk": R_WALK[0], "bike": R_BIKE[0]}

    print("=" * 74)
    print("SEGMENT SAFETY PROGRAMME - what the accessibility is worth")
    print("=" * 74)
    print(f"  2,848 segments, {ksi.sum():,.0f} expected KSI over the period")
    print(f"  median segment rate, the cap target: ${target:.4f}/PMT\n")

    base_w = v.wmean(v.mep(o, n, {}), pop)
    v.ROUTE_BANDS = bands_from(FINAL / "route_risk_by_origin.csv",
                               geoid, n, v.BANDS, r_drive)
    now_w = v.wmean(v.mep(o, n, real), pop)
    now_drop = now_w / base_w - 1

    print(f"  {'scenario':<22}{'MEP':>10}{'loss':>8}{'recovered':>11}"
          f"{'mi treated':>12}{'KSI/yr saved':>14}")
    print(f"  {'today':<22}{now_w:>10,.1f}{now_drop:>8.1%}{'':>11}")

    rows = [["scenario", "segments_fixed", "mep", "loss", "points_recovered",
             "miles_treated", "ksi_per_year_avoided"]]
    rows.append(["today", 0, f"{now_w:.4f}", f"{now_drop:.6f}", "0", "0", "0"])

    YEARS = 83 / 12
    for n_fix in FIX_COUNTS:
        tag = f"fix{n_fix}"
        p, mi, ksi_rm = write_capped(segs, n_fix, target, tag)
        rr = run_step40(p.name, tag)
        v.ROUTE_BANDS = bands_from(rr, geoid, n, v.BANDS, r_drive)
        w = v.wmean(v.mep(o, n, real), pop)
        drop = w / base_w - 1
        pts = (drop - now_drop) * 100
        print(f"  {'fix worst ' + str(n_fix):<22}{w:>10,.1f}{drop:>8.1%}"
              f"{pts:>+10.2f}p{mi:>12,.0f}{ksi_rm / YEARS:>14,.0f}")
        rows.append([f"fix_worst_{n_fix}", n_fix, f"{w:.4f}", f"{drop:.6f}",
                     f"{pts:.4f}", f"{mi:.1f}", f"{ksi_rm / YEARS:.1f}"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    print(f"\nwrote {OUT}")
    print("  'points recovered' is percentage POINTS of the headline, not a")
    print("  percentage of it. No construction cost is modelled, so read this")
    print("  as the accessibility on the table if the safety can be had.")


if __name__ == "__main__":
    main()
