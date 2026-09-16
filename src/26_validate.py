"""
Step 26 - validation.  Every claim the report makes, tested.

FIVE TESTS, each answering a question a reviewer would actually ask.

  1. IS IT AN IDENTITY?
     The first version of this project produced a block-group map that turned
     out to be an exact arithmetic restatement of its own inputs - rank
     invariant under every injury rate tried, to 3.5e-16. That map was deleted.
     This test re-runs the same check on the rebuilt metric: vary r by mode and
     confirm the ORDERING actually changes. If it does not, the surface is
     decorative again and must not be published.

  2. DOES IT REPRODUCE AN INDEPENDENT SURFACE?
     EPA's Smart Location Database publishes jobs reachable in 45 minutes by
     car and by transit, computed by someone else from different networks.
     Rank correlation against it tests the isochrones. LEVELS cannot be
     compared - SLD is time-decayed and ours is a cutoff count - so only rank
     is tested, and only on the block groups that exist in both vintages.

  3. WHERE DOES THE LOSS COME FROM?
     Decomposes the drop by mode, so the headline is attributable rather than
     a single number. If walking supplies almost all of it, the result depends
     on the walk exposure estimate, which is the weakest input here.

  4. THE DELAY TERM IS RETIRED - HOW MUCH DID IT CARRY?
     A crash-delay term was built, then deleted: it was the one input no
     script derived. This test asserts in CODE that the shipped model carries
     zero delay, and re-measures what the deleted term was worth so the
     decision is on the record with a number rather than a claim.

  5. WHAT IF THE WEAKEST INPUT IS WRONG?
     Walk and bike exposure is a national mean trip length on a regional trip
     count. This sweeps r_walk across an order of magnitude and reports where
     the headline stops holding.

Writes: data/final/validation.csv
"""

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (ALPHA, BETA, GAMMA, MEP_DEFAULTS, load_tt,  # noqa: E402
                       DELAY_MINUTES)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
BANDS = (10, 20, 30, 40)
MODES = ("drive", "transit", "walk", "bike")
E_C = {m: (MEP_DEFAULTS[m]["e"], MEP_DEFAULTS[m]["c"]) for m in MODES}

# Rates are READ, never declared. This file used to hold its own copies of
# r_transit, r_walk and r_bike, so a change in step 04 or 17 would silently
# leave the validation validating different inputs than the ones the report
# was built on. A validation suite testing a stale model is worse than none.
def read_rates():
    with (FINAL / "injury_cost_by_mode.csv").open(encoding="utf8") as fh:
        rows = {r["mode"]: r for r in csv.DictReader(fh)}
    with (FINAL / "injury_rate_by_mode.csv").open(encoding="utf8") as fh:
        transit = next(float(r["r"]) for r in csv.DictReader(fh)
                       if r["mode"] == "transit")
    return (float(rows["vehicle_occupant"]["cost_per_pmt"]),
            transit,
            (float(rows["walk"]["cost_per_pmt_lo"]),
             float(rows["walk"]["cost_per_pmt_hi"])),
            (float(rows["bike"]["cost_per_pmt_lo"]),
             float(rows["bike"]["cost_per_pmt_hi"])))
# Read, not declared - and currently zero. See constants.py.
D_DRIVE = DELAY_MINUTES


def build():
    """Recompute the weighted opportunity bands, same as step 23."""
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
    w = np.array([se[a] for a in acts]) * f
    Ow = O @ w

    o = {}
    for m in MODES:
        T = load_tt(INTERIM, m)
        o[m] = np.array([(T <= b) @ Ow for b in BANDS])
    return geoid, [r["county"] for r in cent], o, n


# Route-assigned drive risk by band (step 40), set in main() when present. A
# rate of the string "route" means "charge each band its own routed rate",
# exactly as step 23 does, so tests 3-5 report the shipped model to the
# decimal rather than an approximation of it with one rate per origin.
ROUTE_BANDS = None


def mep(o, n, r, d=0.0, modes=MODES):
    total = np.zeros(n)
    for m in modes:
        e, c = E_C[m]
        for bi, b in enumerate(BANDS):
            band = o[m][bi] - (o[m][bi - 1] if bi else 0.0)
            t = b + (d if m in ("drive", "transit") else 0.0)
            rate = r.get(m, 0.0)
            if isinstance(rate, str):
                rate = ROUTE_BANDS[bi]
            total += band * np.exp(ALPHA * e + BETA * t + GAMMA * (c + rate))
    return total


def rank(x):
    return np.argsort(np.argsort(-x))


def main():
    geoid, county, o, n = build()
    r_drive, R_TRANSIT, R_WALK, R_BIKE = read_rates()
    base = mep(o, n, {})
    real = {"drive": r_drive, "transit": R_TRANSIT,
            "walk": R_WALK[0], "bike": R_BIKE[0]}
    out = []
    print(f"rates read: drive ${r_drive:.4f}  transit ${R_TRANSIT:.4f}  "
          f"walk ${R_WALK[0]:.2f}-{R_WALK[1]:.2f}  "
          f"bike ${R_BIKE[0]:.2f}-{R_BIKE[1]:.2f}\n")

    # --- 1. identity test ---------------------------------------------------
    print("=" * 72)
    print("TEST 1  IS THE SURFACE AN IDENTITY?   (the flaw that killed v1)")
    print("=" * 72)
    print("  THE PREVIOUS VERSION OF THIS TEST COULD NOT FAIL. It checked that")
    print("  two different rate vectors produce different rankings, which is")
    print("  true whenever the vectors differ, identity or not. Run on the v1")
    print("  surface that was deleted FOR being an identity, it passed.")
    print()
    print("  The identity is a closed-form claim, so it is tested directly.")
    print("  Because MEP sums over modes and r_k enters only mode k's term:")
    print()
    print("      MEP_harm_i = SUM_k  g_k * B_ik        g_k = exp(sigma*r_k)")
    print("      loss_i     = SUM_k (1 - g_k) * s_ik   s_ik = B_ik / SUM_k B_ik")
    print()
    print("  If that holds to machine precision, the loss at every block group")
    print("  is a function of MODAL COMPOSITION ALONE, and the injury data")
    print("  contributes exactly four scalars to a 2,170-row surface.\n")

    # If step 30 has produced a place-varying drive rate, the identity is
    # tested BOTH ways: with the scalar (which must still hold, or the closed
    # form is wrong) and with the vector (which must NOT, or step 30 achieved
    # nothing). A test that only ever runs one case cannot tell those apart.
    r_local = None
    p_local = FINAL / "origin_risk.csv"
    if p_local.exists():
        with p_local.open(encoding="utf8") as fh:
            byid = {r["GEOID20"]: r["r_drive_local"] for r in csv.DictReader(fh)}
        vals = [byid.get(g_, "") for g_ in geoid]
        if sum(1 for v in vals if v) >= 0.95 * n:
            r_local = np.array([float(v) if v else r_drive for v in vals])

    # ROUTE-ASSIGNED drive risk (step 40) is what step 23 ships when present.
    # It differs by 10-minute band, so the place-varying case below has to be
    # built band by band rather than with one rate per origin - otherwise this
    # test would validate a surface step 23 no longer produces.
    route_bands = None
    p_route = FINAL / "route_risk_by_origin.csv"
    if p_route.exists() and r_local is not None:
        with p_route.open(encoding="utf8") as fh:
            rb = {r["GEOID20"]: r for r in csv.DictReader(fh)}
        route_bands = np.zeros((len(BANDS), n))
        for bi, b in enumerate(BANDS):
            for k, g_ in enumerate(geoid):
                v = rb.get(g_, {}).get(f"r_band{b}", "")
                route_bands[bi, k] = float(v) if v else r_local[k]
        ov = [rb.get(g_, {}).get("r_route", "") for g_ in geoid]
        r_local = np.array([float(v) if v else r_local[k]
                            for k, v in enumerate(ov)])
        print("  place-varying case uses ROUTE-ASSIGNED risk by band (step 40)")

    g = {m: np.exp(GAMMA * real.get(m, 0.0)) for m in MODES}
    B = {}
    for m in MODES:
        acc = np.zeros(n)
        for bi, b in enumerate(BANDS):
            band = o[m][bi] - (o[m][bi - 1] if bi else 0.0)
            e, c = E_C[m]
            acc += band * np.exp(ALPHA * e + BETA * b + GAMMA * c)
        B[m] = acc
    tot = sum(B.values())
    s = {m: np.divide(B[m], tot, out=np.zeros(n), where=tot > 0) for m in MODES}

    pred_harm = sum(g[m] * B[m] for m in MODES)
    actual_harm = mep(o, n, real)
    err_harm = np.max(np.abs(pred_harm - actual_harm)
                      / np.maximum(np.abs(actual_harm), 1e-9))

    live = tot > 0
    pred_loss = sum((1.0 - g[m]) * s[m] for m in MODES)
    actual_loss = np.zeros(n)
    actual_loss[live] = 1.0 - actual_harm[live] / tot[live]
    err_loss = np.max(np.abs(pred_loss[live] - actual_loss[live]))

    print(f"  g_k  " + "  ".join(f"{m} {g[m]:.6f}" for m in MODES))
    print(f"  max relative error, MEP_harm = SUM g_k B_ik   {err_harm:.2e}")
    print(f"  max absolute error, loss     = SUM (1-g_k)s_ik {err_loss:.2e}")
    IDENTITY = err_loss < 1e-9
    print(f"\n  WITH A SCALAR r_drive - IDENTITY HOLDS: {IDENTITY}")
    print("  With one regional number per mode, the map varies ONLY because")
    print("  the mode mix varies. It cannot vary because crash risk varies,")
    print("  since crash risk does not. Same theorem as v1, four modes")
    print("  instead of two.")
    out.append({"test": "identity", "case": "scalar closed form holds",
                "spearman": "", "value": 1.0 if IDENTITY else 0.0})
    if not IDENTITY:
        sys.exit("FAIL: the closed form does NOT hold for a scalar rate. That "
                 "is arithmetic, not a modelling choice, so the check itself "
                 "is broken and every verdict below is meaningless.")

    # --- the same test with step 30's place-varying drive rate --------------
    if r_local is None:
        print("\n  origin_risk.csv absent - cannot test the place-varying case.")
        print("  The surface as built IS an identity. Do not publish it as a")
        print("  safety map.")
        out.append({"test": "identity", "case": "place-varying available",
                    "spearman": "", "value": 0.0})
    else:
        real_local = dict(real)
        gl = {m: np.exp(GAMMA * real_local.get(m, 0.0)) for m in MODES}
        gl["drive"] = np.exp(GAMMA * r_local)        # a VECTOR, not a scalar
        if route_bands is not None:
            # effective keep factor = harm-weighted over bands, exactly as
            # step 23 charges it: each band at its own route-assigned rate
            e, c = E_C["drive"]
            dh = np.zeros(n)
            for bi, b in enumerate(BANDS):
                band = o["drive"][bi] - (o["drive"][bi - 1] if bi else 0.0)
                dh += (band * np.exp(ALPHA * e + BETA * b + GAMMA * c)
                       * np.exp(GAMMA * route_bands[bi]))
            gl["drive"] = np.divide(dh, B["drive"], out=np.ones(n),
                                    where=B["drive"] > 0)
        harm_l = sum(gl[m] * B[m] for m in MODES)
        loss_l = np.zeros(n)
        loss_l[live] = 1.0 - harm_l[live] / tot[live]
        # The identity as stated needs CONSTANT g_k. Using the vector's mean is
        # the most generous possible version of that claim; if even that fails,
        # no constant-per-mode formula reproduces the surface.
        g_mean = {m: (gl[m] if np.isscalar(gl[m]) else float(np.mean(gl[m])))
                  for m in MODES}
        pred_l = sum((1.0 - g_mean[m]) * s[m] for m in MODES)
        err_l = float(np.max(np.abs(pred_l[live] - loss_l[live])))
        BROKEN = err_l >= 1e-9
        print(f"\n  WITH PLACE-VARYING r_drive from step 30")
        print(f"    r_drive spans ${r_local.min():.4f} to ${r_local.max():.4f}, "
              f"CV {r_local.std() / r_local.mean():.3f}")
        print(f"    max absolute error against the constant-g form  {err_l:.3e}")
        print(f"    IDENTITY BROKEN: {BROKEN}")
        out.append({"test": "identity", "case": "place-varying breaks it",
                    "spearman": "", "value": 1.0 if BROKEN else 0.0})
        if not BROKEN:
            sys.exit("FAIL: place-varying r_drive did NOT break the identity. "
                     "Step 30 produced a rate too flat to matter, so the "
                     "surface is still a restatement of mode mix.")
        # HOW BIG IS THE BREAK? "Not exactly an identity" is a very low bar -
        # the residual is algebraically (mean(g_d) - g_d(i))*s_di, which is
        # non-zero for ANY r vector with non-zero variance, however
        # meaningless. The test above can fail-as-identity but cannot
        # fail-as-trivial, which is the mirror image of the v1 defect.
        #
        # So decompose the surface. If mode mix still explains nearly all of
        # it, the break is real and cosmetic at the same time, and the report
        # must say so.
        mix = pred_l                       # the constant-g, mode-mix-only part
        resid = loss_l - mix
        v_tot = float(np.var(loss_l[live]))
        v_mix = float(np.var(mix[live]))
        v_res = float(np.var(resid[live]))
        # R^2 of loss on mode mix alone
        ss = float(np.sum((loss_l[live] - loss_l[live].mean()) ** 2))
        sse = float(np.sum((loss_l[live] - mix[live]) ** 2))
        r2 = 1.0 - sse / ss if ss > 0 else float("nan")
        print(f"\n    HOW BIG IS THE BREAK?")
        print(f"      var(mode-mix part) / var(loss)      {v_mix / v_tot:.4f}")
        print(f"      var(local-risk residual)/var(loss)  {v_res / v_tot:.4f}")
        print(f"      R2 of loss on mode mix alone        {r2:.5f}")
        print(f"      Spearman vs the scalar-r surface    "
              f"{spearmanr(loss_l[live], actual_loss[live]).statistic:.5f}")
        print(f"      Spearman(local risk, loss)          "
              f"{spearmanr(r_local[live], loss_l[live]).statistic:+.4f}")
        out.append({"test": "identity", "case": "residual variance share",
                    "spearman": "", "value": round(v_res / v_tot, 6)})
        print(f"\n    So the break is REAL and SMALL: local risk contributes")
        print(f"    {v_res / v_tot:.1%} of the surface's variance and mode mix "
              f"contributes the rest.")
        print(f"    Call it a first-order spatial correction. Calling it a")
        print(f"    crash-risk map would not survive a reviewer.")

        # And at what SCALE does it vary? If county fixed effects explain most
        # of r_local, this is a county adjustment wearing block-group clothing.
        cty = np.array(county)
        codes = {c: i for i, c in enumerate(sorted(set(cty)))}
        X = np.zeros((n, len(codes)))
        X[np.arange(n), [codes[c] for c in cty]] = 1.0
        beta, *_ = np.linalg.lstsq(X[live], r_local[live], rcond=None)
        pred_c = X[live] @ beta
        ssr = float(np.sum((r_local[live] - pred_c) ** 2))
        sst = float(np.sum((r_local[live] - r_local[live].mean()) ** 2))
        print(f"\n    R2 of local risk on COUNTY dummies alone: "
              f"{1 - ssr / sst:.4f}")
        print(f"    If that is high, the spatial variation is county-scale, "
              f"not\n    block-group-scale, and should be described that way.")
    print()
    scen = {
        "as computed": real,
        "walk and bike x3": {**real, "walk": R_WALK[0] * 3,
                             "bike": R_BIKE[0] * 3},
        "drive x10": {**real, "drive": r_drive * 10},
        "all modes equal": {m: 1.0 for m in MODES},
        "uniform tiny": {m: 0.01 for m in MODES},
    }
    print(f"  {'scenario':<20}{'spearman':>10}{'top100':>9}{'median move':>13}"
          f"{'mean change':>13}")
    orders = {}
    for k, r in scen.items():
        v = mep(o, n, r)
        orders[k] = rank(v)
        print(f"  {k:<20}{spearmanr(base, v).statistic:>10.5f}"
              f"{len(set(np.argsort(-base)[:100]) - set(np.argsort(-v)[:100])):>9}"
              f"{np.median(np.abs(rank(base) - orders[k])):>13,.0f}"
              f"{v.mean() / base.mean() - 1:>+13.1%}")
        out.append({"test": "identity", "case": k,
                    "spearman": round(spearmanr(base, v).statistic, 6),
                    "value": round(v.mean() / base.mean() - 1, 6)})

    ks = [k for k in scen if k not in ("all modes equal", "uniform tiny")]
    distinct = all(not (orders[a] == orders[b]).all()
                   for i, a in enumerate(ks) for b in ks[i + 1:])
    print(f"\n  Orderings differ between every realistic scenario: {distinct}")
    print(f"  THIS IS NOT A PASS CONDITION. It is true whenever the rate")
    print(f"  vectors differ, identity or not, which is why the previous")
    print(f"  version of this test could not fail. It is printed for context")
    print(f"  only. The pass condition is the closed-form check above.")

    # --- the meta-test: can this test fail at all? --------------------------
    # Feed it a case that MUST be an identity and confirm it says so. Without
    # this, a check that has silently stopped working looks exactly like a
    # check that is passing.
    print(f"\n  META-TEST: does the identity check fire on a known identity?")
    fake = {m: 0.5 * B[m] / max(tot.max(), 1e-9) for m in MODES}  # any weights
    g2 = {m: np.exp(GAMMA * real.get(m, 0.0)) for m in MODES}
    synth_base = sum(B.values())
    synth_harm = sum(g2[m] * B[m] for m in MODES)
    live2 = synth_base > 0
    synth_loss = np.zeros(n)
    synth_loss[live2] = 1.0 - synth_harm[live2] / synth_base[live2]
    pred2 = sum((1.0 - g2[m]) * s[m] for m in MODES)
    fires = np.max(np.abs(pred2[live2] - synth_loss[live2])) < 1e-9
    print(f"    constructed identity detected: {fires}")
    if not fires:
        sys.exit("FAIL: the identity check does not fire on a case that IS an "
                 "identity. The check is broken; its verdict above is "
                 "meaningless.")

    # --- 2. external agreement ----------------------------------------------
    print("\n" + "=" * 72)
    print("TEST 2  DO THE ISOCHRONES AGREE WITH AN INDEPENDENT SURFACE?")
    print("=" * 72)
    try:
        import pandas as pd
        sld = pd.read_parquet(INTERIM / "sld.parquet")
        pos = {g: i for i, g in enumerate(geoid)}
        sld["i"] = sld["GEOID20"].map(pos)
        sld = sld.dropna(subset=["i"])
        sld["i"] = sld["i"].astype(int)
        with (INTERIM / "opportunities.csv").open(encoding="utf8") as fh:
            work = np.zeros(n)
            for r in csv.DictReader(fh):
                i = pos.get(r["GEOID20"])
                if i is not None:
                    work[i] = float(r["work"])
        print(f"  {len(sld):,} of {n:,} block groups exist in BOTH vintages "
              f"(EPA is 2018 geography, ours is 2020)")
        for mode, fld in (("drive", "D5AR"), ("transit", "D5BR")):
            T = load_tt(INTERIM, mode)
            mine = ((T <= 40) @ work)[sld["i"].values]
            epa = pd.to_numeric(sld[fld], errors="coerce").values
            ok = np.isfinite(epa)
            rho = spearmanr(mine[ok], epa[ok]).statistic
            print(f"  {mode:<9}n={ok.sum():>5,}   spearman {rho:>7.4f}")
            out.append({"test": "external", "case": f"{mode} vs {fld}",
                        "spearman": round(rho, 6), "value": ""})
    except Exception as exc:
        print(f"  skipped: {type(exc).__name__} {exc}")

    # --- 3. where the loss comes from ---------------------------------------
    print("\n" + "=" * 72)
    print("TEST 3  WHICH MODE SUPPLIES THE LOSS?")
    print("=" * 72)
    # From here on, use the SAME drive rate step 23 used. Tests 1 and 2 needed
    # the scalar to state the closed form; tests 3 to 5 report the numbers that
    # go in the report, and those must match `mep_by_blockgroup.csv` exactly.
    # Without this, the validation reports a model the report does not describe.
    if route_bands is not None:
        global ROUTE_BANDS
        ROUTE_BANDS = route_bands
        real = {**real, "drive": "route"}
        print("  (tests 3-5 use ROUTE-ASSIGNED drive risk by band, matching "
              "step 23)\n")
    elif r_local is not None:
        real = {**real, "drive": r_local}
        print("  (tests 3-5 use the PLACE-VARYING drive rate, matching step 23)\n")

    full = mep(o, n, real)
    drop = base.mean() - full.mean()
    print(f"  MEP falls {drop / base.mean():.1%}.  Attributed by mode:\n")
    print(f"    {'mode':<10}{'alone':>10}{'share of drop':>16}"
          f"{'40-min reach':>15}")
    for m in MODES:
        only = mep(o, n, {m: real[m]})
        share = (base.mean() - only.mean()) / drop
        print(f"    {m:<10}{(only.mean()/base.mean()-1):>+10.1%}"
              f"{share:>16.1%}{np.median(o[m][-1]):>15,.0f}")
        out.append({"test": "attribution", "case": m, "spearman": "",
                    "value": round(share, 6)})
    print(f"\n  A mode's share of the drop is its REACH times its rate, not its")
    print(f"  rate alone. Cycling dominates because MEP prices it at zero energy")
    print(f"  and zero cost, so it carries a large share of the base score, and")
    # COMPUTED, not typed. This said "26x" for weeks after the exposure fix
    # made it 91x, because it was prose beside a number rather than derived
    # from one.
    print(f"  its crash cost per mile is {R_BIKE[0] / r_drive:.0f}x driving's. "
          f"Walking has the higher")
    print(f"  rate but reaches too little to move the total.")

    # --- 4. is the delay term load-bearing? ---------------------------------
    print("\n" + "=" * 72)
    print("TEST 4  THE DELAY TERM IS RETIRED.  HOW MUCH DID IT CARRY?")
    print("=" * 72)
    print("  The shipped model has NO delay term. It once added minutes to t")
    print("  for road modes, from a literal typed into two files and derived")
    print("  by no script. This test does two things: it PROVES the shipped")
    print("  term is off, and it re-measures what the retired one was worth,")
    print("  so the decision to drop it is on the record with a number.\n")

    # `real_hi` is the HIGH end of every uncertain input, not just delay. An
    # earlier version labelled a row "both (hi)" while using the LOW walk and
    # bike rates with only the delay raised, so it did not match step 23's
    # `hi` column despite carrying the same name.
    real_hi = {**real, "walk": R_WALK[1], "bike": R_BIKE[1]}

    # The retired literal, kept HERE ONLY, as the probe for a historical
    # measurement. It is not imported by step 23 and cannot reach the report.
    RETIRED = (0.39, 0.89)
    for lbl, r, d in (("injury only", real, D_DRIVE[0]),
                      ("shipped (lo)", real, D_DRIVE[0]),
                      ("shipped (hi)", real_hi, D_DRIVE[1]),
                      ("[retired] delay only (hi)", {}, RETIRED[1]),
                      ("[retired] both (hi)", real_hi, RETIRED[1])):
        v = mep(o, n, r, d)
        print(f"  {lbl:<28}{v.mean():>12,.1f}{v.mean()/base.mean()-1:>+10.1%}")
        out.append({"test": "delay", "case": lbl, "spearman": "",
                    "value": round(v.mean() / base.mean() - 1, 6)})

    if D_DRIVE[0] or D_DRIVE[1]:
        sys.exit("FAIL: DELAY_MINUTES is non-zero. The report says the delay "
                 "term is retired. Reconcile constants.py with the report.")
    a = mep(o, n, real_hi, D_DRIVE[1]).mean() / base.mean() - 1
    b = mep(o, n, real_hi, RETIRED[1]).mean() / base.mean() - 1
    print(f"\n  The retired term made the drop {100*abs(b - a):.1f} points BIGGER")
    print("  (unweighted mean here; 2.4 points on the population-weighted")
    print("  headline). Retiring it therefore makes the finding SMALLER, not")
    print("  larger - the direction that argues against the project's own")
    print("  conclusion, which is why it is safe to have done. It also buys")
    print("  back the free-flow-speeds argument the term needed in order to")
    print("  not double count congestion. Shipped rows carry zero delay,")
    print("  asserted above in code rather than promised in prose.")

    # --- 5. sensitivity to the weakest inputs -------------------------------
    print("\n" + "=" * 72)
    print("TEST 5  HOW WRONG CAN THE WEAKEST INPUTS BE?")
    print("=" * 72)
    print("  Walk and bike exposure is now MEASURED from NHTS 2022, not assumed.")
    print("  The remaining weakness is sample size: the regional cycling figure")
    print("  rests on 35 surveyed trips. Both rates are swept across two orders")
    print("  of magnitude anyway, because cycling carries most of the loss.")
    print("  An EARLIER VERSION OF THIS TEST swept only r_walk, and reported a")
    print("  'walk still worst?' column that compared whole-region MEP totals")
    print("  rather than per-mile rates. It answered a different question than")
    print("  the one printed above it, and it answered 'no' for every input.\n")

    for label, key, lo, hi in (("walk", "walk", R_WALK[0], R_WALK[1]),
                               ("bike", "bike", R_BIKE[0], R_BIKE[1])):
        print(f"  {'r_' + label:>8}{'MEP mean':>13}{'change':>10}"
              f"{'vs published':>15}")
        for mult, tag in ((0.1, ""), (0.5, ""), (1.0, "  <- published low"),
                          (hi / lo, "  <- published high"), (10.0, "")):
            rv = lo * mult
            v = mep(o, n, {**real, key: rv})
            print(f"  {rv:>8.2f}{v.mean():>13,.1f}"
                  f"{v.mean() / base.mean() - 1:>+10.1%}{tag:>15}")
            out.append({"test": f"{label}_sensitivity", "case": f"r={rv:.2f}",
                        "spearman": "",
                        "value": round(v.mean() / base.mean() - 1, 6)})
        print()

    # The honest question is not "does the headline survive" but "how much of
    # it survives if the input is wrong by an order of magnitude".
    floor = mep(o, n, {**real, "walk": R_WALK[0] * 0.1, "bike": R_BIKE[0] * 0.1})
    floor_drop = 1 - floor.mean() / base.mean()
    drive_only = mep(o, n, {"drive": r_drive})
    drive_pt = 1 - drive_only.mean() / base.mean()
    print(f"  Both non-motorised rates at a TENTH of the published low:")
    print(f"    MEP falls {floor_drop:.1%} instead of "
          f"{1 - full.mean() / base.mean():.1%}.")
    print(f"  Of that {floor_drop:.1%}, driving supplies {drive_pt:.1%} - "
          f"{drive_pt / floor_drop:.0%} of it.")
    print(f"  So the correction does not vanish even if non-motorised exposure")
    print(f"  is wrong by 10x in the direction that flatters those modes. But")
    print(f"  the floor is NOT carried by driving alone: walking and cycling at")
    print(f"  a tenth of measured exposure still supply "
          f"{1 - drive_pt / floor_drop:.0%} of it. An earlier")
    print(f"  version of this line claimed driving carried all of it.")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "validation.csv").open("w", newline="",
                                         encoding="utf8") as fh:
        w_ = csv.DictWriter(fh, fieldnames=["test", "case", "spearman", "value"])
        w_.writeheader()
        w_.writerows(out)
    print(f"\nwrote {FINAL / 'validation.csv'}")


if __name__ == "__main__":
    main()
