"""
Step 27 - who bears the correction.

The regional headline is one number. It hides the thing that matters: the loss
is not spread evenly, and the modes it falls on hardest are the ones people
without a car have no alternative to.

REPLACES step 07, which ran on EPA's 2018 block groups and on vehicle-ownership
counts from ACS 2014-2018. This one runs on the same 2020 geography as the rest
of the rebuilt pipeline, with ACS 2023 five-year estimates from step 24.

THREE THINGS ARE TESTED:

  1. Is the loss correlated with zero-car share? If the households with no car
     lose most, the metric was overstating the accessibility of exactly the
     people with the fewest options.
  2. How much does it change when weighted by POPULATION rather than by block
     group? A block group is not a person. Rural Citrus block groups are large
     and empty; Pinellas ones are small and full.
  3. Does the ranking of the WORST-OFF places change? A metric used to target
     investment is only useful if the bottom of its distribution is stable.

CORRELATION IS NOT ATTRIBUTION. A block group where many households have no car
is also dense, walkable and near transit, and density drives both the zero-car
share and the mode mix. This step reports the association and does not claim
the causal direction.

Writes: data/final/equity_2020.csv
"""

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"


def main():
    with (FINAL / "mep_by_blockgroup.csv").open(encoding="utf8") as fh:
        mep = {r["GEOID20"]: r for r in csv.DictReader(fh)}
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        acs = {r["GEOID20"]: r for r in csv.DictReader(fh)}

    both = sorted(set(mep) & set(acs))
    if len(both) != len(mep):
        print(f"  NOTE: {len(mep) - len(both)} block groups have MEP but no ACS")
    print(f"{len(both):,} block groups with both MEP and ACS")

    geo = np.array(both)
    county = np.array([mep[g]["county"] for g in both])
    base = np.array([float(mep[g]["mep_published"]) for g in both])
    harm = np.array([float(mep[g]["mep_harm_lo"]) for g in both])
    pop = np.array([float(acs[g]["pop"]) for g in both])
    hh = np.array([float(acs[g]["households"]) for g in both])
    zero = np.array([float(acs[g]["zero_vehicle_hh"]) for g in both])

    # Loss as a fraction. Guard the divide: a block group with no reachable
    # opportunity at all has base 0, and 0/0 would silently become nan and then
    # drop out of every mean below without appearing anywhere as missing.
    live = base > 0
    loss = np.full(len(both), np.nan)
    loss[live] = 1.0 - harm[live] / base[live]
    print(f"  {(~live).sum()} block groups reach nothing at all and are "
          f"excluded from the loss statistics")

    zc = np.divide(zero, hh, out=np.zeros_like(zero), where=hh > 0)

    # --- 1. does the loss track zero-car share? ---------------------------
    print(f"\n{'=' * 70}\n1  DOES THE LOSS FALL ON HOUSEHOLDS WITHOUT A CAR?"
          f"\n{'=' * 70}")
    ok = live & np.isfinite(zc)
    rho = spearmanr(zc[ok], loss[ok]).statistic
    print(f"  Spearman, zero-car share against MEP loss:  {rho:+.4f}")

    # Quintiles by RANK, not by value. Value-based cut points collapse here:
    # so many block groups have a zero-car share of exactly 0.0% that the 0th
    # and 20th percentiles are the same number, and the first bin comes out
    # empty while its rows silently pile into the second.
    idx = np.flatnonzero(ok)
    idx = idx[np.argsort(zc[idx], kind="stable")]
    groups = np.array_split(idx, 5)
    print(f"\n  {'zero-car quintile':<22}{'BGs':>6}{'population':>12}"
          f"{'zero-car':>10}{'MEP loss':>10}")
    for i, g in enumerate(groups):
        label = f"{zc[g].min():.1%} to {zc[g].max():.1%}"
        print(f"  {label:<22}{len(g):>6,}{pop[g].sum():>12,.0f}"
              f"{zc[g].mean():>10.1%}{loss[g].mean():>10.1%}")
    lo_q, hi_q = groups[0], groups[-1]
    gap = (loss[hi_q].mean() - loss[lo_q].mean()) * 100
    # MONOTONICITY IS TESTED, NOT ASSERTED. An earlier version of this line
    # claimed "monotonic across all five" while the printed table showed the
    # first two quintiles out of order. The claim was written once and never
    # re-derived after the inputs changed.
    means = [loss[g].mean() for g in groups]
    mono = all(means[i] <= means[i + 1] for i in range(len(means) - 1))
    print(f"\n  Top quintile loses {gap:+.1f} PERCENTAGE POINTS more than the "
          f"bottom ({loss[hi_q].mean():.1%} against {loss[lo_q].mean():.1%}).")
    if mono:
        print(f"  The progression is monotonic across all five quintiles.")
    else:
        breaks = [i + 1 for i in range(len(means) - 1)
                  if means[i] > means[i + 1]]
        print(f"  It is NOT monotonic: quintile(s) {breaks} sit above the one "
              f"above them.")
        print(f"  The trend is real but the bottom two quintiles are "
              f"effectively tied\n  ({means[0]:.1%} and {means[1]:.1%}), so "
              f"report the gradient, not a clean ladder.")

    # --- 2. block groups against people -----------------------------------
    print(f"\n{'=' * 70}\n2  BLOCK GROUPS ARE NOT PEOPLE\n{'=' * 70}")
    unweighted = loss[live].mean()
    weighted = np.average(loss[live], weights=pop[live])
    print(f"  mean loss per block group           {unweighted:>8.1%}")
    print(f"  mean loss per RESIDENT              {weighted:>8.1%}")
    print(f"  difference                          {weighted - unweighted:>+8.1%}")
    print(f"\n  Weighting by population {'raises' if weighted > unweighted else 'lowers'} "
          f"the loss, which means the correction")
    print(f"  falls {'harder' if weighted > unweighted else 'lighter'} on where "
          f"people actually live than a block-group average shows.")

    # --- 3. is the bottom of the distribution stable? ---------------------
    print(f"\n{'=' * 70}\n3  DOES THE WORST-OFF SET CHANGE?\n{'=' * 70}")
    for k in (50, 100, 200):
        worst_b = set(np.argsort(base)[:k])
        worst_h = set(np.argsort(harm)[:k])
        churn = len(worst_b - worst_h)
        print(f"  worst {k:>3} places   {churn:>3} change "
              f"({churn / k:.0%})   {pop[list(worst_b)].sum():>9,.0f} residents")

    # --- county table ------------------------------------------------------
    print(f"\n{'=' * 70}\n4  BY COUNTY\n{'=' * 70}")
    print(f"  {'county':<15}{'population':>12}{'zero-car hh':>13}"
          f"{'MEP loss':>10}{'per resident':>14}")
    for c in sorted(set(county)):
        m = live & (county == c)
        print(f"  {c:<15}{pop[m].sum():>12,.0f}{zc[m].mean():>13.1%}"
              f"{loss[m].mean():>10.1%}"
              f"{np.average(loss[m], weights=pop[m]):>14.1%}")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "equity_2020.csv").open("w", newline="",
                                          encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["GEOID20", "county", "population", "households",
                    "zero_vehicle_hh", "zero_car_share",
                    "mep_published", "mep_harm", "loss_fraction"])
        for i, g in enumerate(both):
            w.writerow([g, county[i], f"{pop[i]:.0f}", f"{hh[i]:.0f}",
                        f"{zero[i]:.0f}", f"{zc[i]:.6f}",
                        f"{base[i]:.4f}", f"{harm[i]:.4f}",
                        "" if not live[i] else f"{loss[i]:.6f}"])
    print(f"\nwrote {FINAL / 'equity_2020.csv'}")


if __name__ == "__main__":
    main()
