"""
Step 31 - NREL's own validation scenarios, run against this implementation.

Hou et al. (2019) do not just publish MEP; they publish the checks they used to
convince themselves the formulation behaves. Section "SCENARIO ANALYSES":

    "Scenario analysis exercises were carried out to ensure that the MEP
     responds as anticipated to varying inputs."

    Scenario 1 - fuel economy tripled, 25 MPG to 75 MPG, Columbus.
    "These results verify one of the required properties of the MEP - with
     everything else remaining the same, if the energy efficiency of a mode
     increases, the overall MEP should increase accordingly."

    Scenario 2 - travel time deterrence of car reduced, so a 10-minute
    distance becomes a 3-minute distance.
    "improving the travel efficiency of a mode improves the MEP scores"

If this implementation is a correct MEP, it must reproduce those behaviours. If
it does not, the equations are wired wrongly and no result from it means
anything - which is a far more fundamental failure than any input being soft.

These are DIRECTIONAL tests. NREL's own words: "first-order analyses". The
magnitudes will not match Columbus and are not expected to; the SIGNS must.

A THIRD CHECK IS ADDED HERE, because a metric that only ever goes up when
inputs improve is not obviously working - it might be monotone in everything.
Raising a mode's COST must LOWER the score. A formulation that rises on both
would be broken in a way neither published scenario would catch.

Writes: data/final/nrel_scenarios.csv
"""

import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import ALPHA, BETA, GAMMA, MEP_DEFAULTS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
BANDS = (10, 20, 30, 40)
MODES = ("drive", "transit", "walk", "bike")


def load():
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    geoid = [r["GEOID20"] for r in cent]
    n = len(cent)
    pos = {g: i for i, g in enumerate(geoid)}

    with (INTERIM / "opportunities.csv").open(encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    acts = [c for c in rows[0] if c != "GEOID20"]
    O = np.zeros((n, len(acts)))
    for r in rows:
        i = pos.get(r["GEOID20"])
        if i is not None:
            for j, a in enumerate(acts):
                O[i, j] = float(r[a])

    with (INTERIM / "activity_freq.csv").open(encoding="utf8") as fh:
        fr = [r for r in csv.DictReader(fh)
              if r["geography"] == "South Atlantic 2022"]
    f = np.array([float(next(x["f_share"] for x in fr if x["activity"] == a))
                  for a in acts])
    f /= f.sum()
    with (INTERIM / "spatial_equivalency.csv").open(encoding="utf8") as fh:
        se = {r["activity"]: float(r["spatial_equivalency"])
              for r in csv.DictReader(fh)}
    Ow = O @ (np.array([se[a] for a in acts]) * f)

    tt = {m: np.load(INTERIM / f"tt_{m}.npy") for m in MODES}
    return n, Ow, tt


def mep(n, Ow, tt, energy, cost, time_scale=None):
    """
    MEP with per-mode energy, cost and an optional per-mode time multiplier.

    `time_scale` implements NREL's scenario 2: shrinking travel time means a
    given destination now falls inside a SHORTER band, so the isochrone
    thresholds move, not the band labels. Scaling the matrix and re-cutting is
    the same operation and keeps Eq 3 untouched.
    """
    total = np.zeros(n)
    for m in MODES:
        T = tt[m] if not time_scale else tt[m] * time_scale.get(m, 1.0)
        prev = 0.0
        for b in BANDS:
            reach = (T <= b) @ Ow
            band = reach - prev
            prev = reach
            total += band * np.exp(ALPHA * energy[m] + BETA * b
                                   + GAMMA * cost[m])
    return total


def main():
    n, Ow, tt = load()
    E = {m: MEP_DEFAULTS[m]["e"] for m in MODES}
    C = {m: MEP_DEFAULTS[m]["c"] for m in MODES}

    base = mep(n, Ow, tt, E, C)
    print(f"baseline MEP mean {base.mean():,.1f}\n")
    print(f"{'=' * 72}")
    print("NREL'S PUBLISHED VALIDATION SCENARIOS  (Hou et al. 2019)")
    print(f"{'=' * 72}")

    out, failures = [], []

    # --- Scenario 1: fuel economy 25 -> 75 MPG ------------------------------
    # Energy intensity is per passenger-mile, so tripling MPG divides it by 3.
    E1 = dict(E); E1["drive"] = E["drive"] / 3.0
    s1 = mep(n, Ow, tt, E1, C)
    chg1 = s1.mean() / base.mean() - 1
    ok1 = chg1 > 0
    print(f"\n1. FUEL ECONOMY TRIPLED  (25 -> 75 MPG, drive energy "
          f"{E['drive']:.2f} -> {E1['drive']:.2f} kWh/PMT)")
    print(f"   NREL: \"if the energy efficiency of a mode increases, the "
          f"overall MEP\n   should increase accordingly\"")
    print(f"   this build: {chg1:+.1%}   {'PASS' if ok1 else 'FAIL'}")
    out.append(("fuel economy tripled", chg1, ok1))
    if not ok1:
        failures.append("MEP did not rise when driving got more efficient")

    # --- Scenario 2: travel time deterrence reduced -------------------------
    # NREL: a 10-minute distance becomes a 3-minute distance, so times x 0.3.
    #
    # THIS TEST IS TRUNCATED AND THE MAGNITUDE MUST NOT BE QUOTED.
    # tt_*.npy is computed with a 40-minute Dijkstra cutoff, so everything
    # beyond 40 minutes is `inf`, not a number. Scaling by 0.3 should pull
    # destinations 40 to 133 minutes away INSIDE the widest band - and those
    # destinations do not exist in the matrix. `(T*0.3 <= 40)` is therefore
    # the identical boolean array to `(T <= 40)`, verified below.
    #
    # What the test still does: re-bin already-reachable destinations into
    # shorter bands, which raises the score through exp(BETA*t). That is a
    # genuine directional check and a LOWER BOUND of unknown tightness. It is
    # not the magnitude NREL's scenario would produce.
    T = tt["drive"]
    same_set = np.array_equal(np.isfinite(T) & (T <= max(BANDS)),
                              np.isfinite(T) & (T * 0.3 <= max(BANDS)))
    s2 = mep(n, Ow, tt, E, C, time_scale={"drive": 0.3})
    chg2 = s2.mean() / base.mean() - 1
    ok2 = chg2 > 0
    print(f"\n2. DRIVE TRAVEL TIME REDUCED  (10-minute distance now takes 3)")
    print(f"   NREL: \"improving the travel efficiency of a mode improves the "
          f"MEP scores\"")
    print(f"   this build: {chg2:+.1%}   {'PASS' if ok2 else 'FAIL'}  "
          f"(DIRECTION ONLY)")
    if same_set:
        print(f"   TRUNCATED: the {max(BANDS)}-minute Dijkstra cutoff means "
              f"scaling times by 0.3")
        print(f"   brings in ZERO new destinations - the reachable set is "
              f"identical. This")
        print(f"   change is pure re-binning of already-reachable "
              f"destinations, so it is a")
        print(f"   LOWER BOUND. Quoting {chg2:+.1%} as NREL's scenario result "
              f"would be wrong.")
        print(f"   To run it properly, recompute tt_drive to a "
              f"{max(BANDS) / 0.3:.0f}-minute horizon.")
    out.append(("drive travel time x0.3 (truncated, direction only)",
                chg2, ok2))
    if not ok2:
        failures.append("MEP did not rise when driving got faster")

    # --- Added check: cost must push the OTHER way --------------------------
    C3 = dict(C); C3["drive"] = C["drive"] * 3.0
    s3 = mep(n, Ow, tt, E, C3)
    chg3 = s3.mean() / base.mean() - 1
    ok3 = chg3 < 0
    print(f"\n3. DRIVE COST TRIPLED  (${C['drive']:.2f} -> ${C3['drive']:.2f} "
          f"per passenger-mile)   [added here, not in NREL's paper]")
    print(f"   A metric that rises on every input change is not responding, "
          f"it is\n   monotone. Cost must move the score DOWN.")
    print(f"   this build: {chg3:+.1%}   {'PASS' if ok3 else 'FAIL'}")
    out.append(("drive cost tripled", chg3, ok3))
    if not ok3:
        failures.append("MEP did not fall when driving got more expensive")

    # --- Added check: the null ----------------------------------------------
    s4 = mep(n, Ow, tt, E, C)
    same = np.allclose(s4, base)
    print(f"\n4. NULL SCENARIO  (nothing changed)   [added here]")
    print(f"   Re-running with identical inputs must return identical scores, "
          f"or the\n   three results above are noise.")
    print(f"   identical: {same}   {'PASS' if same else 'FAIL'}")
    out.append(("null scenario", 0.0, same))
    if not same:
        failures.append("identical inputs produced different scores")

    print(f"\n{'=' * 72}")
    if failures:
        print("FAILED. This implementation does not behave like MEP:")
        for f in failures:
            print(f"  - {f}")
        print("\nNo result from this pipeline is meaningful until that is "
              "fixed.")
    else:
        print("ALL PASS ON DIRECTION - this implementation reproduces the")
        print("directional behaviour NREL published as MEP's required")
        print("properties, plus two checks they did not publish.")
        print("")
        print("MAGNITUDES ARE NOT COMPARABLE AND ARE NOT CLAIMED. Hou et al.")
        print("publish no numeric scenario results at all - Figures 5 and 6 are")
        print("colour maps. Only the SIGNS are testable against the paper, and")
        print("scenario 2 is additionally truncated (see above).")
    print(f"{'=' * 72}")

    # --- scale, against the reference's own published scores -----------------
    print(f"\nON ABSOLUTE SCALE, WHICH IS NOT A DEFECT AND IS DOCUMENTED")
    print(f"  this build, mean over 2,170 block groups   {base.mean():>10,.0f}")
    print(f"  Columbus, Hou et al. 2019                  {162:>10,}")
    print(f"  South Florida, TomTom + CoStar             {122.35:>10,.2f}")
    print(f"  South Florida, SERPM network + MAZ         {11983:>10,}")
    print(f"""
  The reference implementation produced BOTH 122.35 and 11,983 for the same
  region, and says why: "the MAZ data represent number of employment by
  category while the CoStar data represent number of destinations". An office
  block with 500 jobs is one destination and five hundred jobs.

  This build uses LODES employment counts, so it sits on the employment scale,
  as the reference's own SERPM run did. The reference's conclusion on that
  comparison is the relevant precedent: "although the absolute scores come in
  different magnitudes, the patterns align reasonably well."

  Hence percentages and rankings only. No absolute MEP score is quoted from
  this work, and none should be.""")

    with (FINAL / "nrel_scenarios.csv").open("w", newline="",
                                             encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["scenario", "mean_change", "passed"])
        for name, chg, ok in out:
            w.writerow([name, f"{chg:.6f}", ok])
    print(f"\nwrote {FINAL / 'nrel_scenarios.csv'}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
