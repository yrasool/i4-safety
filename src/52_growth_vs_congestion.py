"""Step 52 - does growth outrun congestion, or the other way round?

THE DELAWARE FINDING, PUT AS A QUESTION. NREL's 2030 scenario for DelDOT lost
3.28% of statewide MEP, and their own reading was that congestion "outweighed
the projected growth in land use opportunities and jobs". Two forces pulling
opposite ways, and the slower network won.

Tampa Bay is one of the fastest-growing metros in the country, so the same two
forces are larger here and the question is sharper: HOW MUCH growth would it
take to stand still?

WHY THIS IS NOT A FORECAST. This project has no population or employment
projection - no BEBR county series, no travel demand model, no 2050 land use.
Inventing one would be the exact failure the rest of the pipeline exists to
avoid. So this does not predict a year. It prints the TRADE-OFF SURFACE: MEP
for every combination of opportunity growth and congestion, and the break-even
growth that exactly offsets each congestion level.

A planner brings their own projection to this table and reads off the answer.
That is more useful than a number with someone else's forecast buried in it.

WHAT GROWTH MEANS HERE. Opportunities are scaled uniformly - every block group
gains the same proportion. Real growth is not uniform: Tampa Bay's is
concentrated in Pasco and east Hillsborough, on the edges, where accessibility
is already lowest. Uniform growth therefore FLATTERS the result, because it
adds opportunities where people can already reach them. Read the break-even
growth as an optimistic floor.

THE ONE PIECE OF ARITHMETIC WORTH KNOWING. MEP sums opportunities times a
decay, so scaling every opportunity by (1+g) scales the whole score by (1+g)
exactly - growth is linear. Congestion is not: it moves destinations across
time bands, and the exponential decay does the rest. That asymmetry is the
whole finding, and it is why break-even growth rises faster than TTI does.

Reads:  data/interim/tt_drive_tti*.npy (step 51), and step 26's own loaders
Writes: data/final/growth_vs_congestion.csv
"""
import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
INTERIM = ROOT / "data" / "interim"
FINAL = ROOT / "data" / "final"
OUT = FINAL / "growth_vs_congestion.csv"

TTIS = (1.00, 1.15, 1.30, 1.50)
GROWTH = (0.00, 0.10, 0.20, 0.30, 0.50)


def load_step26():
    spec = importlib.util.spec_from_file_location("v26", SRC / "26_validate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["v26"] = m
    spec.loader.exec_module(m)
    return m


def rows_of(p):
    with p.open(encoding="utf8") as fh:
        return list(csv.DictReader(fh))


def main():
    v = load_step26()
    geoid, county, o, n = v.build()
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        popmap = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
    pop = np.array([popmap.get(g, 0.0) for g in geoid])
    r_drive, r_transit, R_WALK, R_BIKE = v.read_rates()

    rb = {r["GEOID20"]: r for r in rows_of(FINAL / "route_risk_by_origin.csv")}
    bands = np.zeros((len(v.BANDS), n))
    for bi, b in enumerate(v.BANDS):
        for k, g in enumerate(geoid):
            s = rb.get(g, {}).get(f"r_band{b}", "")
            bands[bi, k] = float(s) if s else r_drive
    v.ROUTE_BANDS = bands
    real = {"drive": "route", "transit": r_transit,
            "walk": R_WALK[0], "bike": R_BIKE[0]}

    # The drive band under each congestion level. Built by step 51 and saved,
    # so this step costs seconds rather than another four Dijkstra passes.
    o_by_tti = {1.00: o}
    for tti in TTIS:
        if tti == 1.00:
            continue
        tag = str(tti).replace(".", "")
        p = INTERIM / f"tt_drive_tti{tag}.npy"
        if not p.exists():
            sys.exit(f"FAIL: {p.name} missing. Run 51_congestion_scenario.py "
                     "first - it writes the congested travel-time matrices.")
        tt = np.load(p)
        # Opportunity weights, same construction step 26 uses.
        rws = rows_of(INTERIM / "opportunities.csv")
        acts = [c for c in rws[0] if c != "GEOID20"]
        pos = {g: i for i, g in enumerate(geoid)}
        O = np.zeros((n, len(acts)))
        for r in rws:
            i = pos.get(r["GEOID20"])
            if i is not None:
                for j, a in enumerate(acts):
                    O[i, j] = float(r[a])
        fr = [r for r in rows_of(INTERIM / "activity_freq.csv")
              if r["geography"] == "South Atlantic 2022"]
        f = np.array([float(next(x["f_share"] for x in fr
                                 if x["activity"] == a)) for a in acts])
        f /= f.sum()
        se = {r["activity"]: float(r["spatial_equivalency"])
              for r in rows_of(INTERIM / "spatial_equivalency.csv")}
        Ow = O @ (np.array([se[a] for a in acts]) * f)
        o2 = dict(o)
        o2["drive"] = np.array([(tt <= b) @ Ow for b in v.BANDS])
        o_by_tti[tti] = o2

    base = v.wmean(v.mep(o, n, {}), pop)

    print("=" * 78)
    print("GROWTH AGAINST CONGESTION - published MEP, population-weighted")
    print("=" * 78)
    print("  MEP scales EXACTLY with uniform opportunity growth, so each row")
    print("  is its TTI=1.00 value times (1+g). The interesting number is the")
    print("  last column: the growth that exactly cancels that congestion.\n")
    print(f"  {'congestion':<14}" + "".join(f"{f'+{int(g*100)}%':>11}"
                                            for g in GROWTH)
          + f"{'break-even':>13}")

    out = [["tti", "growth", "published_mep", "vs_today"]]
    be_rows = []
    for tti in TTIS:
        oo = o_by_tti[tti]
        at0 = v.wmean(v.mep(oo, n, {}), pop)
        cells = []
        for g in GROWTH:
            val = at0 * (1 + g)
            cells.append(val)
            out.append([f"{tti}", f"{g}", f"{val:.4f}",
                        f"{val / base - 1:.6f}"])
        be = base / at0 - 1.0
        be_rows.append([f"{tti}", "break_even_growth", "", f"{be:.6f}"])
        print(f"  {'TTI ' + f'{tti:.2f}':<14}"
              + "".join(f"{c:>11,.0f}" for c in cells)
              + (f"{be:>12.1%}" if be > 0 else f"{'-':>12}"))

    out += be_rows

    print("\n  WHAT THE LAST COLUMN SAYS")
    for tti in TTIS[1:]:
        at0 = v.wmean(v.mep(o_by_tti[tti], n, {}), pop)
        be = base / at0 - 1.0
        print(f"    at TTI {tti:.2f}, the region needs {be:.0%} more "
              f"opportunities everywhere just to hold today's access")

    print("\n  Growth is linear in MEP; congestion is not, because it moves")
    print("  destinations across time bands and the decay is exponential.")
    print("  Uniform growth FLATTERS this - Tampa Bay grows on its edges,")
    print("  where accessibility is already lowest - so read break-even as an")
    print("  optimistic floor.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        csv.writer(fh).writerows(out)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
