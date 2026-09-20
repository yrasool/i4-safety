"""Step 47 - the five bike networks, one table, computed not remembered.

WHY THIS EXISTS. The project quotes a bracket around its headline - strictly
low-stress at one end, bikes-anywhere at the other - and until now those
numbers came from runs done by hand with MEP_BIKE_NETWORK set in a shell. A
figure no script produces cannot go stale when the model changes, because
nothing recomputes it; it just stops being true. That is exactly how the
version B headline survived the move from 16.2% to 13.4% unchanged. This runs
all five and writes them, so 28_check_report.py can guard every one.

THE FIVE, and what separates them:

  any               bikes on any road but a motorway - standard MEP
  lts               strictly low-stress, no crossing allowed at all
  lts_connect       low-stress plus a 250 m crossing, measured per FRAGMENT
                    (the retired bug: half its miles were pieces of long
                    arterials)
  lts_connect_byway low-stress plus a 250 m crossing, measured per OSM WAY
                    - SHIPPED
  lts_connect_halfmile  the same at 0.5 mile. Tested because a 2026
                    micromobility note argued for a half-mile PROTECTED
                    cycleway across a barrier. A protected facility
                    changes a road's LTS class rather than buying a
                    crossing of an unprotected one, so the two are not
                    the same quantity - but the difference is worth 1.8
                    points and belongs in the bracket rather than in an
                    argument.
  lts_nrel          NREL's own method: nothing deleted, every edge slowed by
                    LTS band (Sharda et al. 2024)

READ THE DIRECTION BEFORE QUOTING. The strictest network gives the SMALLEST
loss, and NREL's most permissive one gives a larger loss than ours. That is not
a contradiction: MEP prices crash harm per passenger-mile, so a network that
reaches less carries fewer miles and less harm. It means this safety term can
be reduced by shrinking the network, which is a property of the method and
worth stating before a reviewer finds it.

Reads:  data/interim/ (via step 26's own loaders), one tt matrix per network
Writes: data/final/bike_network_bracket.csv
"""
import csv
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
OUT = FINAL / "bike_network_bracket.csv"

NETWORKS = [
    ("any", "bikes on any road but a motorway"),
    ("lts", "strictly low-stress, no crossings"),
    ("lts_connect", "250 m crossing, per fragment  [retired bug]"),
    ("lts_connect_byway", "250 m crossing, per OSM way  [SHIPPED]"),
    ("lts_connect_halfmile", "0.5 mile crossing, per OSM way"),
    ("lts_fdot", "OSM tags matched to FDOT inventory  [scenario]"),
    ("lts_nrel", "NREL: nothing deleted, slowed by band"),
]


def load_step26():
    """Reuse step 26's build/mep/wmean. One implementation of MEP, not two."""
    spec = importlib.util.spec_from_file_location("v26", SRC / "26_validate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["v26"] = m
    spec.loader.exec_module(m)
    return m


def main():
    v = load_step26()
    shipped = os.environ.get("MEP_BIKE_NETWORK", "")

    r_drive, r_transit, R_WALK, R_BIKE = v.read_rates()
    rows = []

    print("=" * 76)
    print("BIKE NETWORK BRACKET - same model, same rates, five networks")
    print("=" * 76)
    print(f"  {'network':<20}{'published':>11}{'with harm':>11}"
          f"{'drop':>8}{'40-min weighted':>16}")

    for tag, note in NETWORKS:
        os.environ["MEP_BIKE_NETWORK"] = tag
        try:
            geoid, county, o, n = v.build()
        except FileNotFoundError:
            print(f"  {tag:<20}  MISSING - run 42_bike_lts.py first")
            continue
        with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
            popmap = {r["GEOID20"]: float(r["pop"])
                      for r in csv.DictReader(fh)}
        pop = np.array([popmap.get(g, 0.0) for g in geoid])

        # Route-assigned drive risk, exactly as steps 23 and 26 build it, so
        # only the BIKE network differs between these five rows.
        with (FINAL / "route_risk_by_origin.csv").open(encoding="utf8") as fh:
            rb = {r["GEOID20"]: r for r in csv.DictReader(fh)}
        bands = np.zeros((len(v.BANDS), n))
        for bi, b in enumerate(v.BANDS):
            for k, g in enumerate(geoid):
                s = rb.get(g, {}).get(f"r_band{b}", "")
                bands[bi, k] = float(s) if s else r_drive
        v.ROUTE_BANDS = bands

        base = v.wmean(v.mep(o, n, {}), pop)
        harm = v.wmean(v.mep(o, n, {"drive": "route", "transit": r_transit,
                                    "walk": R_WALK[0], "bike": R_BIKE[0]}), pop)
        drop = harm / base - 1.0
        # NOT a destination count - this is the weighted opportunity total
        # the 40-minute band reaches, which is what MEP actually sums. Naming
        # it "reach" would invite it being quoted as destinations.
        opp40 = float(np.median(o["bike"][-1]))
        print(f"  {tag:<20}{base:>11,.1f}{harm:>11,.1f}{drop:>8.1%}"
              f"{opp40:>16,.0f}")
        rows.append([tag, note, f"{base:.4f}", f"{harm:.4f}", f"{drop:.6f}",
                     f"{opp40:.1f}"])

    if shipped:
        os.environ["MEP_BIKE_NETWORK"] = shipped
    else:
        os.environ.pop("MEP_BIKE_NETWORK", None)

    drops = {r[0]: float(r[4]) for r in rows}
    if "lts" in drops and "lts_connect_byway" in drops and "lts_nrel" in drops:
        ok = abs(drops["lts"]) < abs(drops["lts_connect_byway"]) < abs(drops["lts_nrel"])
        print(f"\n  strict < shipped < NREL holds: {ok}")
        if not ok:
            sys.exit("FAIL: the bracket is out of order. Either a network was "
                     "rebuilt with different inputs or one tt matrix is stale.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["network", "description", "published_score",
                    "score_with_harm", "drop", "median_40min_weighted_opps"])
        w.writerows(rows)
    print(f"\nwrote {OUT}")
    print("  The strictest network gives the SMALLEST loss. MEP prices harm")
    print("  per passenger-mile, so a network that reaches less carries fewer")
    print("  miles and less harm. Say that before someone asks.")


if __name__ == "__main__":
    main()
