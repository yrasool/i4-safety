"""
Step 23 - MEP itself.  All three equations, on data this project computed.

    Eq 1   o_ikt = SUM_j  o_ijkt * (N*/N_j) * (f_j / SUM f_j)
    Eq 2   M_ikt = alpha*e_k + beta*t + sigma*c_k        [+ the new terms]
    Eq 3   MEP_i = SUM_k SUM_t (o_ikt - o_ik,t-10) * exp(M_ikt)

EQUATION 1, why the normalisation is there. Tampa Bay has 1,570,813 jobs and
30,150 arts-and-recreation destinations. Summed raw, work would be 98% of every
score and the other five activities would be rounding error. N*/N_j puts each
activity on a common scale first; f_j/SUM f_j then weights them by how often
people actually make that trip, from NHTS 2022. N* is a constant across j, so
it sets the absolute scale and cancels out of every ratio and every ranking.

EQUATION 3 IS A BAND DIFFERENCE, NOT A CUMULATIVE SUM. `o_ikt - o_ik,t-10` is
the opportunities reached BETWEEN two isochrones, priced at the outer band's
weight. Summing cumulative counts instead would count the same nearby
destination four times, once in each band, and inflate dense places most.

WHAT THIS PROJECT ADDS, and nothing else:

    c_k  ->  c_k + r_k     crash cost, dollars per passenger-mile, the same
                           unit MEP's cost term already carries

ONE input changes. Nothing else. Precedent: Garikapati et al. added ride-
hailing to MEP by changing three input values, not by changing the maths.

A SECOND term, crash-caused delay added to t, was built and then DELETED. It
was worth 2.4 points of a 25-point result, so nothing rested on it, and it was
the only input in the project that no script derived - a typed literal in two
files at once. Deleting it also retires the argument it needed (that step 20's
free-flow speeds contain no congestion, so incident delay cannot double count).
The headline is now smaller and every number behind it is reproducible.
See DELAY_MINUTES in constants.py.

Writes: data/final/mep_by_blockgroup.csv, data/final/mep_summary.csv
"""

import csv
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (ALPHA, BETA, GAMMA, MEP_DEFAULTS,  # noqa: E402
                       DELAY_MINUTES)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"

BANDS = (10, 20, 30, 40)
MODES = ("drive", "transit", "walk", "bike")

# Energy (kWh/PMT) and cost ($/PMT) come from constants.py, which sources them
# from FDOT BDV29-977-66 Table 7 - the MEP tool's own default table. NOT
# redeclared here: an earlier version of this file hardcoded transit cost as
# 0.86 while the reference says 0.85, and nothing would have caught it.
# Walk and bike are zero for BOTH energy and cost in the published defaults,
# which is precisely why omitting crash cost makes them unbeatable in a region
# that kills pedestrians.
E_C = {m: (MEP_DEFAULTS[m]["e"], MEP_DEFAULTS[m]["c"]) for m in MODES}

# Crash cost per passenger-mile.
#
# r_drive is READ from step 04's output, not retyped here. It depends on
# occupancy, which changed from a wrong 1.67 to a measured 1.502, and a
# hardcoded copy would have silently kept the old value. Everything the
# pipeline computes gets read; only inputs it cannot compute are declared.
#
# Walk and bike are RANGES because their exposure is estimated, not measured:
# a national mean trip length applied to a regional trip count. They are the
# weakest inputs in the project and are never given as point values.
def read_rates():
    """
    Every r_k, READ. None of them declared.

    All four used to be literals here. r_walk and r_bike traced to a scratch
    script whose walk and bike mode shares summed to 110% at one end of its
    "range" and 90% at the other, and they carried 79% of the headline.
    r_transit was 0.0010 against step 05's computed 0.0010477.

    A DELIBERATE ASYMMETRY REMAINS AND IS NOT A BUG. r_drive, r_walk and r_bike
    are KSI (deaths plus serious injuries). r_transit is FATALITY-ONLY, because
    NTD records zero serious injuries for bus in every year: serious injury is
    a rail-only concept there, inherited from the State Safety Oversight regime
    under 49 CFR Part 674. There is no alternative field and no defensible
    imputation.

    That means transit's rate is NOT comparable to the road modes' without
    saying so. Inside MEP it is fine - each mode's cost term stands alone and
    nothing divides one by another. It is NOT fine in a sentence of the form
    "the crash term is X% of driving's cost and Y% of transit's", which compares
    them directly. Step 04 emits a fatality-only drive rate for exactly that
    comparison, and the report uses it there.
    """
    p = FINAL / "injury_cost_by_mode.csv"
    if not p.exists():
        sys.exit("FAIL: injury_cost_by_mode.csv missing. Run step 04 first.")
    rows = {}
    with p.open(encoding="utf8") as fh:
        for row in csv.DictReader(fh):
            rows[row["mode"]] = row

    def need(mode, field):
        v = rows.get(mode, {}).get(field)
        if not v:
            sys.exit(f"FAIL: {field} for {mode} is empty in step 04's output. "
                     f"Run steps 17 and 04, in that order.")
        return float(v)

    r_drive = need("vehicle_occupant", "cost_per_pmt")
    walk = (need("walk", "cost_per_pmt_lo"), need("walk", "cost_per_pmt_hi"))
    bike = (need("bike", "cost_per_pmt_lo"), need("bike", "cost_per_pmt_hi"))

    q = FINAL / "injury_rate_by_mode.csv"
    if not q.exists():
        sys.exit("FAIL: injury_rate_by_mode.csv missing. Run step 05 first.")
    with q.open(encoding="utf8") as fh:
        transit = next(float(r["r"]) for r in csv.DictReader(fh)
                       if r["mode"] == "transit")
    return r_drive, transit, walk, bike


# Crash-caused delay, READ from constants.py and currently ZERO.
#
# It was a literal here and a second literal in 26_validate.py, in neither case
# derived by any script. See the DELAY_MINUTES block in constants.py for why it
# is disabled rather than repaired. Dropping it costs 2.4 points of a 25-point
# result and removes the need to defend the free-flow-speeds argument at all.
D_DRIVE = DELAY_MINUTES


def load_matrix(mode):
    p = INTERIM / f"tt_{mode}.npy"
    if not p.exists():
        sys.exit(f"FAIL: {p.name} missing. Run steps 21 and 22 first.")
    return np.load(p)


def main():
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    geoid = [r["GEOID20"] for r in cent]
    county = [r["county"] for r in cent]
    n = len(cent)
    pos = {g: i for i, g in enumerate(geoid)}

    # --- opportunities, aligned to the centroid order ---------------------
    with (INTERIM / "opportunities.csv").open(encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    acts = [c for c in rows[0] if c != "GEOID20"]
    O = np.zeros((n, len(acts)))
    hit = 0
    for r in rows:
        i = pos.get(r["GEOID20"])
        if i is None:
            continue
        hit += 1
        for j, a in enumerate(acts):
            O[i, j] = float(r[a])
    print(f"opportunities matched to {hit:,} of {len(rows):,} job-carrying "
          f"block groups")

    # --- f_j, activity frequencies ----------------------------------------
    with (INTERIM / "activity_freq.csv").open(encoding="utf8") as fh:
        freq = [r for r in csv.DictReader(fh)
                if r["geography"] == "South Atlantic 2022"]
    f = np.array([float(next(x["f_share"] for x in freq
                             if x["activity"] == a)) for a in acts])
    f = f / f.sum()

    # --- OPTIONAL sensitivity override, e.g. MEP_WORK_SHARE=0.272 ------------
    # BTS passenger origin-destination data (phone traces, 2022) puts WORK at
    # 27.2% of trips INSIDE the Tampa metro, against the 20.3% this pipeline
    # takes from NHTS 2022 South Atlantic. The FDOT South Florida study used
    # 30%. The gap is worth quantifying rather than arguing about, so this
    # pins work at a chosen share and rescales the other five activities
    # PROPORTIONALLY, which is the only defensible way to absorb the residual
    # when the outside source is binary (work / non-work) and cannot say how
    # the non-work half divides.
    #
    # A run with the override set REFUSES TO WRITE. A sensitivity scenario
    # must never be able to leave its numbers sitting in data/final/ where the
    # report generator and the number checker will read them as the real
    # result. This project has already shipped one figure that came from a
    # retired script's leftover output.
    # MEP_FREQ_JSON replaces the WHOLE vector, e.g. from the 2018-19 Tampa Bay
    # Regional Travel Survey, which is local but does not separate medical from
    # shopping/errands/appointments. Shares are renormalised, so they need not
    # sum to 1.
    override = os.environ.get("MEP_FREQ_JSON")
    if override:
        import json
        given = json.loads(override)
        if set(given) != set(acts):
            sys.exit(f"FAIL: MEP_FREQ_JSON has {sorted(given)}, "
                     f"need {sorted(acts)}")
        f = np.array([given[a] for a in acts], dtype=float)
        f = f / f.sum()
        print("\n  *** SENSITIVITY RUN: frequency vector replaced. "
              "NOTHING WILL BE WRITTEN. ***")

    override = override or os.environ.get("MEP_WORK_SHARE")
    if os.environ.get("MEP_WORK_SHARE") and not os.environ.get("MEP_FREQ_JSON"):
        wj = acts.index("work")
        target = float(override)
        rest = 1.0 - target
        others = f.sum() - f[wj]
        f = f * (rest / others)
        f[wj] = target
        print(f"\n  *** SENSITIVITY RUN: work share pinned to {target:.1%} "
              f"(pipeline value {float(next(x['f_share'] for x in freq if x['activity'] == 'work')):.1%}). "
              f"NOTHING WILL BE WRITTEN. ***")

    # --- Equation 1 spatial equivalency, A*/A_k ---------------------------
    # NATIONAL, from step 25. NOT the local maximum. The reference defines A_k
    # as "total opportunities of activity k among multiple cities in the U.S."
    # and says the factor "should remain constant for a given city" - which is
    # only possible if its basis sits outside that city. A locally-derived
    # factor inflates whatever the study region happens to lack, and makes two
    # cities' MEP scores incomparable, which is the property it exists to give.
    se_path = INTERIM / "spatial_equivalency.csv"
    if not se_path.exists():
        sys.exit("FAIL: spatial_equivalency.csv missing. Run step 25 first. Do "
                 "NOT fall back to a local maximum - that is the bug this file "
                 "was changed to remove.")
    with se_path.open(encoding="utf8") as fh:
        se = {r["activity"]: float(r["spatial_equivalency"])
              for r in csv.DictReader(fh)}
    if set(se) != set(acts):
        sys.exit(f"FAIL: spatial equivalency covers {sorted(se)} but the "
                 f"opportunity table has {sorted(acts)}. The NAICS mapping in "
                 f"steps 16 and 25 has diverged, so the ratio is meaningless.")
    A = np.array([se[a] for a in acts])
    N = O.sum(axis=0)
    w = A * f                              # per-activity weight
    print(f"\n  {'activity':<12}{'local total':>13}{'f_k':>9}{'A*/A_k':>10}"
          f"{'weight':>10}")
    for j, a in enumerate(acts):
        print(f"  {a:<12}{N[j]:>13,.0f}{f[j]:>9.1%}{A[j]:>10.2f}"
              f"{w[j]:>10.3f}")

    # --- Equations 1 and 3 -------------------------------------------------
    tt = {m: load_matrix(m) for m in MODES}
    # LOW-STRESS BIKE NETWORK, opt-in: MEP_BIKE_NETWORK=lts (step 42). Bike
    # reach is rebuilt on roads an "interested but concerned" adult will ride,
    # so the crash term prices cycling access that plausibly exists rather
    # than access along six-lane arterials. No-write until compared.
    if os.environ.get("MEP_BIKE_NETWORK") in ("lts", "lts_connect"):
        p_lts = INTERIM / f"tt_bike_{os.environ['MEP_BIKE_NETWORK']}.npy"
        if not p_lts.exists():
            sys.exit("FAIL: MEP_BIKE_NETWORK=lts but tt_bike_lts.npy is "
                     "missing. Run step 42 first.")
        tt["bike"] = np.load(p_lts)
        override = override or "bike_lts"
        print("\n  *** SENSITIVITY RUN: bike reach on the LOW-STRESS network "
              "(step 42). NOTHING WILL BE WRITTEN. ***")
    if os.environ.get("MEP_WALK_NETWORK") == "lts":
        p_wl = INTERIM / "tt_walk_lts.npy"
        if not p_wl.exists():
            sys.exit("FAIL: MEP_WALK_NETWORK=lts but tt_walk_lts.npy is "
                     "missing. Run step 42 first.")
        tt["walk"] = np.load(p_wl)
        override = override or "walk_lts"
        print("\n  *** SENSITIVITY RUN: walk reach on the LOW-STRESS network "
              "(step 42). NOTHING WILL BE WRITTEN. ***")
    # o[mode][band] = weighted opportunities reached from each origin
    o = {m: np.zeros((len(BANDS), n)) for m in MODES}
    for m in MODES:
        T = tt[m]
        for bi, b in enumerate(BANDS):
            reach = (T <= b)               # n x n boolean
            o[m][bi] = reach @ (O @ w)     # Eq 1, weighted and summed
        print(f"\n  {m:<9}median opportunities reached: " + "  ".join(
            f"{b}min {np.median(o[m][bi]):,.0f}" for bi, b in enumerate(BANDS)))

    r_drive, R_TRANSIT, R_WALK, R_BIKE = read_rates()

    # PLACE-VARYING DRIVE RISK, if step 30 has produced it. Every other rate is
    # a scalar; this one is a vector of length n, one value per origin, built
    # from Empirical-Bayes segment rates weighted by MEP's own time decay.
    #
    # This is the only input in the project that varies by place, and it exists
    # because step 26 proves the surface is otherwise an identity in mode mix.
    # Whether it is ENOUGH is decided by Test 1, not asserted here.
    local = FINAL / "origin_risk.csv"
    r_drive_i = None
    if local.exists():
        with local.open(encoding="utf8") as fh:
            byid = {r["GEOID20"]: r["r_drive_local"]
                    for r in csv.DictReader(fh)}
        vals = [byid.get(g, "") for g in geoid]
        if sum(1 for v in vals if v) >= 0.95 * n:
            # Origins with no reachable rated segment fall back to the regional
            # figure rather than to zero, which would read as "perfectly safe".
            r_drive_i = np.array([float(v) if v else r_drive for v in vals])
            print(f"\n  PLACE-VARYING r_drive from step 30: "
                  f"{sum(1 for v in vals if v):,} origins")
            print(f"    p10 ${np.percentile(r_drive_i, 10):.4f}   "
                  f"median ${np.median(r_drive_i):.4f}   "
                  f"p90 ${np.percentile(r_drive_i, 90):.4f}")
        else:
            print(f"\n  origin_risk.csv covers only "
                  f"{sum(1 for v in vals if v):,} of {n:,} origins - "
                  f"too few, using the regional scalar")
    # ROUTE-ASSIGNED DRIVE RISK, opt-in: MEP_DRIVE_RISK=route.
    # Step 40 sums segment risk along the shortest route to every destination
    # and averages it over the opportunities in EACH 10-minute band. That lets
    # the drive cost differ by band: a 10-minute trip on local streets and a
    # 40-minute trip down a deadly arterial are no longer charged one number.
    # It replaces step 30's proximity estimate for drive only. Opt-in and
    # no-write until it has been compared, because it changes the one input
    # in the model that varies by place.
    route_bands = None
    if os.environ.get("MEP_DRIVE_RISK") == "scalar":
        # the one-regional-number version, kept as the reference that step
        # 26 proves is an identity in mode mix
        r_drive_i = None
        override = override or "scalar"
        print("\n  *** SENSITIVITY RUN: ONE regional drive rate. NOTHING WILL "
              "BE WRITTEN. ***")
    # SHIPPED DEFAULT since 2026-09-16: route-assigned risk whenever step 40
    # has run. MEP_DRIVE_RISK=proximity reproduces the step 30 surface and
    # MEP_DRIVE_RISK=scalar the one-number surface, both as no-write scenarios.
    mode_env = os.environ.get("MEP_DRIVE_RISK", "")
    if mode_env == "proximity":
        override = override or "proximity"
        print("\n  *** SENSITIVITY RUN: step 30 PROXIMITY drive risk. NOTHING "
              "WILL BE WRITTEN. ***")
    rpath = FINAL / "route_risk_by_origin.csv"
    if mode_env == "route" and not rpath.exists():
        sys.exit("FAIL: MEP_DRIVE_RISK=route but route_risk_by_origin.csv "
                 "is missing. Run step 40 first.")
    if mode_env not in ("proximity", "scalar") and rpath.exists():
        with rpath.open(encoding="utf8") as fh:
            rb = {r["GEOID20"]: r for r in csv.DictReader(fh)}
        fallback = r_drive_i if r_drive_i is not None else np.full(n, r_drive)
        route_bands = np.zeros((len(BANDS), n))
        empty = 0
        for bi, b in enumerate(BANDS):
            for k, g in enumerate(geoid):
                v = rb.get(g, {}).get(f"r_band{b}", "")
                if v:
                    route_bands[bi, k] = float(v)
                else:
                    # no destination in this band: the band carries no
                    # opportunities, so the value is never weighted; use the
                    # origin's own estimate rather than an arbitrary zero
                    route_bands[bi, k] = fallback[k]
                    empty += 1
        print(f"\n  ROUTE-ASSIGNED drive risk by band (step 40), shipped. "
              f"{empty:,} of {len(BANDS) * n:,} origin-bands had no destination "
              f"and use the origin estimate.")
        for bi, b in enumerate(BANDS):
            print(f"    {b:>2}-min band   median ${np.median(route_bands[bi]):.4f}"
                  f"   p10 ${np.percentile(route_bands[bi], 10):.4f}"
                  f"   p90 ${np.percentile(route_bands[bi], 90):.4f}")

    print(f"\n  CRASH COST PER PASSENGER-MILE, all read, none declared")
    print(f"    drive    ${r_drive:>7.4f}    KSI, step 04")
    print(f"    transit  ${R_TRANSIT:>7.4f}    FATALITY-ONLY, step 05 "
          f"(NTD records no bus serious injuries)")
    print(f"    walk     ${R_WALK[0]:>7.2f} to ${R_WALK[1]:.2f}    KSI, "
          f"NHTS 2022 exposure")
    print(f"    bike     ${R_BIKE[0]:>7.2f} to ${R_BIKE[1]:.2f}    KSI, "
          f"NHTS 2022 exposure")

    def mep(inject_crash, r_walk=None, r_bike=None, d_drive=0.0):
        total = np.zeros(n)
        for m in MODES:
            e, c = E_C[m]
            r = 0.0
            if inject_crash:
                # `r` is a scalar for every mode except drive, where it may be
                # a length-n vector. numpy broadcasts either against `band`, so
                # nothing below needs to know which it got.
                r = {"drive": r_drive if r_drive_i is None else r_drive_i,
                     "transit": R_TRANSIT,
                     "walk": r_walk, "bike": r_bike}[m]
            for bi, b in enumerate(BANDS):
                prev = o[m][bi - 1] if bi else 0.0
                band = o[m][bi] - prev              # Eq 3 band DIFFERENCE
                t = b + (d_drive if m in ("drive", "transit") else 0.0)
                rb_ = (route_bands[bi] if (inject_crash and m == "drive"
                                           and route_bands is not None) else r)
                M = ALPHA * e + BETA * t + GAMMA * (c + rb_)
                total += band * np.exp(M)
        return total

    base = mep(False)
    lo = mep(True, R_WALK[0], R_BIKE[0], D_DRIVE[0])
    hi = mep(True, R_WALK[1], R_BIKE[1], D_DRIVE[1])

    # --- aggregation, MEP's own rule -----------------------------------------
    # Hou et al. (2019), p.9: "The overall MEP for a city can be calculated by
    # taking the POPULATION PROPORTION WEIGHTED SUMMATION of MEP across tracts
    # or block groups". Columbus's published 162 is computed that way.
    #
    # This report previously led with the UNWEIGHTED mean, which is a different
    # statistic and the largest of the three available. All three are printed
    # here so the reader can see which is which, and the MEP-conformant one is
    # named as the headline.
    pop = None
    acs = INTERIM / "acs_blockgroups.csv"
    if acs.exists():
        with acs.open(encoding="utf8") as fh:
            byid = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
        pop = np.array([byid.get(g, 0.0) for g in geoid])
        if pop.sum() <= 0:
            pop = None

    print(f"\n{'='*70}\nMEP BEFORE AND AFTER PRICING CRASH HARM\n{'='*70}")
    if pop is not None:
        wpub = np.average(base, weights=pop)
        wlo = np.average(lo, weights=pop)
        whi = np.average(hi, weights=pop)
        print(f"  POPULATION-WEIGHTED  <- MEP's own aggregation rule, "
              f"Hou et al. p.9")
        print(f"  {'':<14}{'published':>14}{'with harm (lo)':>17}"
              f"{'with harm (hi)':>17}")
        print(f"  {'city score':<14}{wpub:>14,.1f}{wlo:>17,.1f}{whi:>17,.1f}")
        print(f"  {'change':<14}{'':>14}{wlo/wpub-1:>+17.1%}"
              f"{whi/wpub-1:>+17.1%}")
        print(f"\n  unweighted, for comparison only (NOT the headline):")
    print(f"  {'':<14}{'published':>14}{'with harm (lo)':>17}"
          f"{'with harm (hi)':>17}")
    print(f"  {'median':<14}{np.median(base):>14,.1f}{np.median(lo):>17,.1f}"
          f"{np.median(hi):>17,.1f}")
    print(f"  {'mean':<14}{base.mean():>14,.1f}{lo.mean():>17,.1f}"
          f"{hi.mean():>17,.1f}")
    print(f"  {'change':<14}{'':>14}{lo.mean()/base.mean()-1:>+17.1%}"
          f"{hi.mean()/base.mean()-1:>+17.1%}")

    # --- does the ranking move? -------------------------------------------
    def rank(x):
        return np.argsort(np.argsort(-x))
    rb, rl = rank(base), rank(lo)
    moved = (rb != rl)
    top100_b = set(np.argsort(-base)[:100])
    top100_l = set(np.argsort(-lo)[:100])
    from scipy.stats import spearmanr
    rho = spearmanr(base, lo).statistic
    print(f"\n  block groups changing rank      {moved.mean():>8.1%}")
    print(f"  median rank move                {np.median(np.abs(rb-rl)):>8,.0f}"
          f" of {n:,}")
    print(f"  top-100 churn                   "
          f"{len(top100_b - top100_l):>8} places")
    print(f"  Spearman rank correlation       {rho:>8.5f}")

    print(f"\n  {'county':<15}{'MEP now':>11}{'with harm':>12}{'change':>9}")
    for c in sorted(set(county)):
        m = np.array([x == c for x in county])
        print(f"  {c:<15}{base[m].mean():>11,.1f}{lo[m].mean():>12,.1f}"
              f"{lo[m].mean()/base[m].mean()-1:>+9.1%}")

    dump = os.environ.get("MEP_DUMP")
    if dump:
        # per-origin arrays for comparing scenarios, written ONLY to the path
        # given - never into data/, so the report cannot read them. Allowed on
        # the shipped run too, so a comparison can include the baseline.
        np.savez(dump, base=base, lo=lo, geoid=np.array(geoid),
                 county=np.array(county),
                 pop=pop if pop is not None else np.zeros(n))
        print(f"\n  scenario arrays dumped to {dump}")
    if override:
        print("\nSENSITIVITY RUN - mep_by_blockgroup.csv NOT written, so the "
              "real result in data/final/ is untouched.")
        return

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "mep_by_blockgroup.csv").open("w", newline="",
                                                encoding="utf8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["GEOID20", "county", "mep_published", "mep_harm_lo",
                      "mep_harm_hi", "rank_published", "rank_harm"])
        for i in range(n):
            wtr.writerow([geoid[i], county[i], f"{base[i]:.4f}",
                          f"{lo[i]:.4f}", f"{hi[i]:.4f}",
                          int(rb[i]) + 1, int(rl[i]) + 1])
    print(f"\nwrote {FINAL / 'mep_by_blockgroup.csv'}")


if __name__ == "__main__":
    main()
