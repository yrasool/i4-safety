"""
Step 06 - the results that survive review.

REPLACES `06_apply_to_sld.py`, which produced a block-group "price of safety"
map. That map was an exact arithmetic identity and has been deleted.

WHY, because this must not be rebuilt by someone who thinks it was a bug:

    loss_pct = (1 - f_d) + s*(f_d - f_t)      f_k = exp(DELTA*r_k)
                                              s   = weighted transit share

Verified to 3.5e-16 across all 2,098 block groups. The rows enter ONLY through
`s`, which is itself a monotone function of D5BR/D5AR. The map was therefore a
recolouring of the transit share, and it was RANK-INVARIANT under every injury
rate tested - (0.0953,0.0115), (0.30,0.02), (0.012,0.0001) all produce the
identical ordering. The injury data contributed exactly two scalars to a
2,098-row surface.

This is a THEOREM given a regional per-mode `r_k`, not an implementation fault.
Mode-constant rates make loss a function of modal composition alone, always. A
real spatial injury surface needs place-varying `r_k`, which needs route-based
or home-based attribution - and the home-address field is verified absent from
this extract.

The absolute opportunity columns are gone too. They were 36.6x off MEP's scale
AND unrescalable: three independent unknown scalars (the omitted exp(BETA*t),
which must not be applied because SLD is already time-decayed and t=45 is a
CUTOFF not a duration; the omitted Eq.1 normalisation; and the mismatch between
SLD's decayed sums and MEP's raw isochrone counts). Percentages are exactly
correct under all three and are all that may be reported.

What remains is true, and is the project:
  1. a mode-level result, which needs no geography
  2. a transit-availability surface, labelled as exactly that
  3. the equity result (step 07), which never routed through the injury term

Writes: data/final/mode_results.csv, data/final/transit_access.csv
"""

import sys
from math import exp
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (ALPHA, GAMMA, MEP_DEFAULTS as MEP,  # noqa: E402
                       SCENARIOS, COUNTIES)

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"


def main():
    rates = pd.read_csv(FINAL / "injury_rate_by_mode.csv").set_index("mode")
    r = {"drive": float(rates.loc["drive", "r"]),
         "transit": float(rates.loc["transit", "r"])}
    ci_lo = float(rates.loc["transit", "ci_lo"])
    ci_hi = float(rates.loc["transit", "ci_hi"])

    # --- 1. THE RESULT ------------------------------------------------------
    print("=" * 68)
    print("1. THE MISSING TERM, BY MODE   (no geography - none is possible)")
    print("=" * 68)
    print(f"  {'mode':<9}{'r ($/PMT)':>12}{'sigma*c':>10}{'delta*r':>11}"
          f"{'% of cost':>11}{'weight x':>10}")

    rows = []
    for name, delta in SCENARIOS.items():
        for mode in ("drive", "transit"):
            gc = GAMMA * MEP[mode]["c"]
            dr = delta * r[mode]
            rows.append({"scenario": name, "mode": mode, "r": r[mode],
                         "sigma_c": gc, "delta_r": dr,
                         "pct_of_cost_term": abs(dr / gc),
                         "weight_multiplier": exp(dr)})
        if name == "base":
            for row in rows[-2:]:
                print(f"  {row['mode']:<9}{row['r']:>12.6f}"
                      f"{row['sigma_c']:>10.4f}{row['delta_r']:>11.5f}"
                      f"{row['pct_of_cost_term']:>10.1%}"
                      f"{row['weight_multiplier']:>10.4f}")

    base = {x["mode"]: x for x in rows if x["scenario"] == "base"}
    asym = base["drive"]["pct_of_cost_term"] / base["transit"]["pct_of_cost_term"]
    ratio = r["drive"] / r["transit"]

    print(f"\n  Driving carries {ratio:.0f}x the traffic-collision fatality cost")
    print(f"  per passenger-mile of a fixed-route bus.")
    print(f"  Poisson range on 12 bus deaths: "
          f"{r['drive'] / ci_hi:.0f}x to {r['drive'] / ci_lo:.0f}x")
    print(f"\n  MEP's omission is asymmetric by {asym:.0f}x - the term it leaves")
    print(f"  out is {base['drive']['pct_of_cost_term']:.1%} of what it already charges driving and")
    print(f"  {base['transit']['pct_of_cost_term']:.2%} of transit's. Omitting it flatters the car.")

    print(f"""
  NAMING. This is TRAFFIC-COLLISION fatality cost, not "safety" and not
  "injury risk". Onboard crime is excluded from both modes because a crash
  database cannot see car-occupant assault. Nationally that removes 52 of 71
  bus rider deaths; in Tampa Bay it removes none - HART and PSTA recorded
  ZERO rider fatalities across 753 events and 1.17 billion passenger-miles
  over ten years, including 18 security events. State the exclusion, its
  national size and its local size, or the 52 homicides become a gotcha.
""")

    # --- 2. TRANSIT AVAILABILITY, honestly labelled -------------------------
    print("=" * 68)
    print("2. TRANSIT AVAILABILITY   (this is what the old map actually showed)")
    print("=" * 68)
    sld = pd.read_parquet(INTERIM / "sld.parquet")
    t = sld[["GEOID20", "county", "TotPop", "AutoOwn0", "D5AR", "D5BR"]].copy()
    t["A_drive"] = pd.to_numeric(t["D5AR"], errors="coerce")
    assert t["A_drive"].notna().all(), "D5AR missing - step 01 should have caught it"
    t["no_transit"] = t["D5BR"].isna()
    t["A_transit"] = pd.to_numeric(t["D5BR"], errors="coerce").fillna(0.0)
    # The quantity the deleted surface was a monotone recolouring of.
    t["transit_share"] = t["A_transit"] / (t["A_drive"] + t["A_transit"])

    print(f"  {len(t):,} block groups   "
          f"{t.no_transit.sum():,} with no transit-reachable jobs "
          f"({t.no_transit.mean():.1%})")
    print(f"\n  {'county':<14}{'BGs':>6}{'no transit':>12}{'median share':>14}")
    by = (t.groupby("county")
            .agg(bg=("GEOID20", "size"), nt=("no_transit", "mean"),
                 share=("transit_share", "median"))
            .sort_values("nt", ascending=False))
    for c, row in by.iterrows():
        print(f"  {c:<14}{row.bg:>6.0f}{row.nt:>11.1%}{row.share:>14.3f}")

    print(f"""
  ⚠ D5BR is min(transit, walk <=15 min), so an unknown share of it is WALK
    access priced here at transit's rate - the safest in the model - while
    walking is the most dangerous mode per mile. Bias is toward understating
    the gap. And D5BR is max(forward, reverse) while D5AR is single-directed,
    which is why transit exceeds driving in 345 block groups.
""")

    FINAL.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(FINAL / "mode_results.csv", index=False)
    t.drop(columns=["D5AR", "D5BR"]).to_csv(FINAL / "transit_access.csv",
                                            index=False)
    for stale in ("blockgroup_surface.csv", "mep_weights.csv"):
        p = FINAL / stale
        if p.exists():
            p.unlink()
            print(f"  deleted stale {stale} (contained the identity surface)")
    print(f"\nwrote {FINAL / 'mode_results.csv'}")
    print(f"wrote {FINAL / 'transit_access.csv'}")


if __name__ == "__main__":
    main()
