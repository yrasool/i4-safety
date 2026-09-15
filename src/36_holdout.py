"""
Step 36 - does the safety model PREDICT, or only describe?

WHY THIS STEP EXISTS. Everything else in this project checks CONSISTENCY: the
report matches the CSVs, the pipeline reproduces itself, NREL's scenarios move
the score the right way. None of that tests whether the road-safety model is
any good at the one thing it is for - saying which roads WILL be dangerous.

A model fitted to seven years and evaluated on the same seven years can only
ever look good. So this step does what the road-safety literature does to
validate Empirical Bayes: split time, fit on the past, score on the future.

    fit      2019 - 2022    4.0 years   (includes the 2020 anomaly - see step 34)
    score    2023 - 2025    2.9 years   (2025 runs to November)

THREE PREDICTORS COMPETE for the future count on each of 2,848 segments:

    naive    the segment's own past count, scaled to the future window.
             What a spreadsheet ranking of "worst roads" does.
    SPF      the safety performance function alone - traffic and length,
             ignoring the segment's history entirely.
    EB       the Empirical Bayes blend the pipeline actually uses:
             w*SPF + (1-w)*history, w = 1/(1 + k*mu)   (HSM Part C, A.2.4)

THE TESTS, and they are the published ones, not invented here.

  1. Per-segment error. Mean absolute error and RMSE against the observed
     future count. Reported twice: raw, and after rescaling every predictor to
     the observed future total - because 2023-25 may simply be a safer period
     than 2019-22, and that shifts all three predictors equally without saying
     anything about which one ranks roads correctly.

  2. Hotspot identification, Cheng & Washington (2005, 2008):
     - Site consistency: flag the top 5% / 10% of segments using PAST data,
       then add up their FUTURE casualties. A method that flags genuinely
       dangerous roads keeps finding casualties there. A method that flags
       bad luck watches its hotspots regress to the mean.
     - Method consistency: apply the method to each period separately and
       count how many flagged segments appear in both. Stable = trustworthy.

  3. Spearman rank correlation between prediction and future count.

THE PREDICTION, STATED BEFORE THE RESULT. Theory says EB should beat naive on
every test (it removes regression to the mean) and beat SPF on site
consistency (it uses the segment's own record). If it does not, that is the
finding and the report says so. Nothing in this step exits on a bad RESULT -
only on a data-integrity failure - because an evaluation that can only pass is
the same defect as the identity test this project already had to rewrite.

INTEGRITY CHECK. Crashes are re-matched to segments here, by year, using step
09's exact method. The two periods must sum, segment by segment, to step 09's
totals. If they do not, the re-matching has drifted from the pipeline and every
number below would be about a different dataset.

Reads:  data/raw/fdot_rci_segments.json, the Signal Four crash export,
        data/final/segment_rates.csv, data/final/segment_facility.csv
Writes: data/final/holdout_eval.csv
"""

import csv
import json
import sys
from bisect import bisect_right
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import CRASH_CSV, YEARS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW, FINAL = ROOT / "data" / "raw", ROOT / "data" / "final"

FIT_YEARS = ("2019", "2020", "2021", "2022")
T_FIT = 4.0
T_TEST = round(YEARS - T_FIT, 3)          # 2.9: 2023, 2024, Jan-Nov 2025
SCALE = T_TEST / T_FIT
TOP_SHARES = (0.05, 0.10)


def denul(fh):
    for line in fh:
        yield line.replace("\x00", "")


def num(row, col):
    try:
        return int(float(row.get(col) or 0))
    except ValueError:
        return 0


def load_segments():
    """Step 09's segment index, built identically, from the same cache."""
    segs = json.loads((RAW / "fdot_rci_segments.json").read_text())
    by_road = defaultdict(list)
    for s in segs:
        b, e = s.get("BEGIN_POST"), s.get("END_POST")
        if b is None or e is None or e <= b:
            continue
        by_road[str(s["ROADWAY"]).strip()].append(
            (float(b), float(e), float(s.get("AADT") or 0)))
    for r in by_road:
        by_road[r].sort()
    starts = {r: [x[0] for x in v] for r, v in by_road.items()}
    return by_road, starts


def tally_by_period(by_road, starts):
    """Occupant KSI per segment, split into fit and test periods."""
    fit = defaultdict(int)
    test = defaultdict(int)
    with open(CRASH_CSV, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(denul(fh)):
            rw = (row.get("LRS_ROADWAY") or "").strip()
            mp_raw = (row.get("LRS_MILEPOINT") or "").strip()
            if not rw or not mp_raw or rw not in by_road:
                continue
            try:
                mp = float(mp_raw)
            except ValueError:
                continue
            i = bisect_right(starts[rw], mp) - 1
            if i < 0 or mp > by_road[rw][i][1]:
                continue
            b, e, aadt = by_road[rw][i]

            # Occupants are the residual, exactly as in steps 02 and 09.
            k = num(row, "S4_FATALITY_COUNT")
            a = num(row, "S4_INCAPACITATING_INJURY_COUNT")
            res_k = k - sum(num(row, f"S4_{m}_FATALITY_COUNT")
                            for m in ("PEDESTRIAN", "BICYCLIST", "MOTORCYCLIST"))
            res_a = a - sum(num(row, f"S4_{m}_INCAPACITATING_INJURY_COUNT")
                            for m in ("PEDESTRIAN", "BICYCLIST", "MOTORCYCLIST"))
            ksi = max(0, res_k) + max(0, res_a)
            if not ksi:
                continue
            key = (rw, round(b, 3), round(e, 3), int(aadt))
            yr = (row.get("CRASH_YEAR") or "").strip()
            (fit if yr in FIT_YEARS else test)[key] += ksi
    return fit, test


def nb_nll(params, y, aadt, length, T):
    """Step 29's likelihood, with the exposure period as an argument."""
    a, b, log_k = params
    k = np.exp(log_k)
    mu = np.clip(np.exp(a) * np.power(aadt, b) * length * T, 1e-9, None)
    r = 1.0 / k
    ll = (gammaln(y + r) - gammaln(r) - gammaln(y + 1)
          + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu)))
    return -ll.sum()


def fit_spf(y, aadt, length, T, facility):
    """Stratified exactly as step 29: per facility, pooled if too thin."""
    def one(mask):
        r = minimize(nb_nll, x0=[-6.0, 0.8, 0.0],
                     args=(y[mask], aadt[mask], length[mask], T),
                     method="Nelder-Mead",
                     options={"maxiter": 40000, "xatol": 1e-9, "fatol": 1e-9})
        if not r.success:
            sys.exit(f"FAIL: SPF did not converge: {r.message}")
        return r.x

    a, b, lk = one(np.ones(len(y), bool))
    mu = np.zeros(len(y))
    kk = np.zeros(len(y))
    for f in sorted(set(facility)):
        m = facility == f
        af, bf, lkf = ((a, b, lk) if m.sum() < 60 or y[m].sum() < 40
                       else one(m))
        mu[m] = np.exp(af) * np.power(aadt[m], bf) * length[m] * T
        kk[m] = np.exp(lkf)
    return mu, kk


def eb(y, mu, k):
    w = 1.0 / (1.0 + k * mu)
    return w * mu + (1.0 - w) * y


def top(x, share):
    n = int(round(share * len(x)))
    return set(np.argsort(-x, kind="stable")[:n])


def main():
    by_road, starts = load_segments()

    with (FINAL / "segment_rates.csv").open(encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    # KEYED ON AADT TOO, exactly as step 09 keys its tally. FDOT's file holds
    # one pair of records covering the same extent - roadway 14121000, posts
    # 0.0 to 4.36 in Pasco - with different AADT (18,400 and 35,000). Step 09
    # treats them as two segments; a (roadway, begin, end) key would silently
    # merge them. Found by the uniqueness check below on its first run. Both
    # carry zero occupant KSI, so the effect is nil, but the join must match.
    keys = [(r["roadway"], float(r["begin_post"]), float(r["end_post"]),
             int(r["aadt"])) for r in rows]
    if len(set(keys)) != len(keys):
        sys.exit("FAIL: segment keys are not unique; the join below would "
                 "silently merge segments.")
    with (FINAL / "segment_facility.csv").open(encoding="utf8") as fh:
        fmap = {(r["roadway"], float(r["begin_post"]), float(r["end_post"])):
                r["facility"] for r in csv.DictReader(fh)}
    facility = np.array([fmap.get(k_[:3], "") for k_ in keys])
    if (facility == "").mean() > 0.05:
        sys.exit("FAIL: facility missing for >5% of segments. Run step 33.")

    aadt = np.array([float(r["aadt"]) for r in rows])
    length = np.array([float(r["length_mi"]) for r in rows])
    total = np.array([float(r["occ_deaths"]) + float(r["occ_serious"])
                      for r in rows])

    print("re-matching 602,110 crashes to segments, by year ...")
    fit_c, test_c = tally_by_period(by_road, starts)
    y1 = np.array([fit_c.get(k_, 0) for k_ in keys], float)
    y2 = np.array([test_c.get(k_, 0) for k_ in keys], float)

    # --- INTEGRITY: the split must reassemble step 09 exactly --------------
    bad = int((np.abs(y1 + y2 - total) > 0.5).sum())
    print(f"\n  fit {y1.sum():,.0f} + test {y2.sum():,.0f} = "
          f"{y1.sum() + y2.sum():,.0f} occupant KSI   (step 09: "
          f"{total.sum():,.0f})")
    if bad:
        sys.exit(f"FAIL: {bad} segments do not reassemble to step 09's totals. "
                 f"The re-matching has drifted from the pipeline; every result "
                 f"below would describe a different dataset.")
    print(f"  all {len(keys):,} segments reassemble to step 09 exactly")

    # --- fit on the past, predict the future --------------------------------
    mu1, k1 = fit_spf(y1, aadt, length, T_FIT, facility)
    preds = {
        "naive": y1 * SCALE,
        "SPF": mu1 * SCALE,
        "EB": eb(y1, mu1, k1) * SCALE,
    }
    out = []

    print("\n" + "=" * 72)
    print(f"1  PER-SEGMENT ERROR   (fit 2019-22, predict 2023-25, "
          f"{len(keys):,} segments)")
    print("=" * 72)
    print(f"  observed future total   {y2.sum():>8,.0f} occupant KSI")
    print(f"  {'':<8}{'predicted':>11}{'MAE':>9}{'RMSE':>9}"
          f"{'MAE*':>9}{'RMSE*':>9}{'Spearman':>10}")
    for name, p in preds.items():
        cal = p * (y2.sum() / p.sum())       # level removed, shape kept
        mae, rmse = np.abs(p - y2).mean(), np.sqrt(((p - y2) ** 2).mean())
        mae_c = np.abs(cal - y2).mean()
        rmse_c = np.sqrt(((cal - y2) ** 2).mean())
        rho = spearmanr(p, y2).statistic
        print(f"  {name:<8}{p.sum():>11,.0f}{mae:>9.3f}{rmse:>9.3f}"
              f"{mae_c:>9.3f}{rmse_c:>9.3f}{rho:>10.4f}")
        for m, v in (("predicted_total", p.sum()), ("mae", mae),
                     ("rmse", rmse), ("mae_calibrated", mae_c),
                     ("rmse_calibrated", rmse_c), ("spearman", rho)):
            out.append({"test": "error", "method": name, "metric": m,
                        "value": round(float(v), 6)})
    print("  * = every predictor rescaled to the observed future total, so a")
    print("      safer or more dangerous test period cannot favour any method.")
    level = preds["EB"].sum() / y2.sum() - 1
    print(f"\n  All three share the same level error ({level:+.1%} for EB): the")
    print("  future period is not the past period at a different time. That is")
    print("  step 34's severity break showing up, and it is why the starred")
    print("  columns are the fair comparison between methods.")

    # --- hotspot identification ---------------------------------------------
    print("\n" + "=" * 72)
    print("2  HOTSPOT IDENTIFICATION   (Cheng & Washington 2005, 2008)")
    print("=" * 72)
    mu2, k2 = fit_spf(y2, aadt, length, T_TEST, facility)
    rank_past = {"naive": y1, "SPF": mu1, "EB": eb(y1, mu1, k1)}
    rank_future = {"naive": y2, "SPF": mu2, "EB": eb(y2, mu2, k2)}

    for share in TOP_SHARES:
        n = int(round(share * len(keys)))
        print(f"\n  top {share:.0%} of segments = {n} flagged, using PAST data")
        print(f"  {'':<8}{'future KSI on flagged':>24}{'kept in both periods':>23}")
        best_future = np.sort(y2)[::-1][:n].sum()
        for name in preds:
            flagged = top(rank_past[name], share)
            sct = y2[list(flagged)].sum()
            mct = len(flagged & top(rank_future[name], share))
            print(f"  {name:<8}{sct:>16,.0f} ({sct / best_future:>5.1%})"
                  f"{mct:>15} of {n}")
            out += [{"test": f"hotspot_top{int(share * 100)}", "method": name,
                     "metric": "site_consistency", "value": float(sct)},
                    {"test": f"hotspot_top{int(share * 100)}", "method": name,
                     "metric": "method_consistency", "value": float(mct)}]
        print(f"  {'oracle':<8}{best_future:>16,.0f} (100.0%)   <- the best "
              f"any method could do, knowing the future")

    print("\n  READ THE SECOND COLUMN WITH CARE. SPF's stability is not earned")
    print("  here: it ranks on AADT and length alone, and this project has ONE")
    print("  AADT vintage, so its inputs are identical in both periods and it")
    print("  cannot help but flag the same roads. Method consistency is only a")
    print("  fair test between naive and EB, which both see different data in")
    print("  each period.")

    # --- is the margin real, or noise? --------------------------------------
    # EB's lead over naive is small - under 2% on error, about 1% on site
    # consistency. "Held" on a point estimate alone would overstate it. A
    # PAIRED bootstrap resamples segments with replacement and recomputes the
    # DIFFERENCE between methods on the same draw each time, so segment-to-
    # segment variation that hits both methods equally cancels out. A 95%
    # interval that excludes zero means the lead survives; one that straddles
    # zero means "held" was luck, and must be reported as such.
    print("\n" + "=" * 72)
    print("2b IS THE MARGIN REAL?   paired bootstrap, 2,000 resamples of segments")
    print("=" * 72)
    rng = np.random.default_rng(20260911)
    B = 2000
    n_seg = len(keys)
    cal = {m: p * (y2.sum() / p.sum()) for m, p in preds.items()}
    flag = {(m, s): np.zeros(n_seg, bool) for m in preds for s in TOP_SHARES}
    for m in preds:
        for s in TOP_SHARES:
            flag[(m, s)][list(top(rank_past[m], s))] = True
    boot = defaultdict(list)
    for _ in range(B):
        ix = rng.integers(0, n_seg, n_seg)
        yb = y2[ix]
        for rival in ("naive", "SPF"):
            # Positive = EB better. MAE: rival minus EB. Site consistency:
            # EB minus rival, as a share of the resampled future total.
            boot[("mae", rival)].append(
                np.abs(cal[rival][ix] - yb).mean()
                - np.abs(cal["EB"][ix] - yb).mean())
            for s in TOP_SHARES:
                boot[(f"sct{int(s * 100)}", rival)].append(
                    (yb[flag[("EB", s)][ix]].sum()
                     - yb[flag[(rival, s)][ix]].sum()) / yb.sum())
    sig = {}
    print(f"  {'EB advantage over':<34}{'point':>9}{'95% interval':>22}  verdict")
    for (metric, rival), vals in sorted(boot.items()):
        v = np.array(vals)
        lo, hi = np.percentile(v, [2.5, 97.5])
        pt = float(np.median(v))
        real = lo > 0
        sig[(metric, rival)] = real
        label = {"mae": "calibrated MAE", "sct5": "site consistency top 5%",
                 "sct10": "site consistency top 10%"}[metric]
        fmt = (lambda x: f"{x:+.4f}") if metric == "mae" else \
              (lambda x: f"{x:+.2%}")
        print(f"  {rival + ', ' + label:<34}{fmt(pt):>9}"
              f"   [{fmt(lo)}, {fmt(hi)}]  "
              f"{'REAL' if real else 'within noise'}")
        out.append({"test": "bootstrap", "method": f"EB_vs_{rival}",
                    "metric": f"{metric}_ci_lo", "value": round(float(lo), 6)})
        out.append({"test": "bootstrap", "method": f"EB_vs_{rival}",
                    "metric": f"{metric}_ci_hi", "value": round(float(hi), 6)})

    # --- verdict, computed rather than written ------------------------------
    print("\n" + "=" * 72)
    print("3  VERDICT AGAINST THE PREDICTION MADE BEFORE RUNNING")
    print("=" * 72)
    get = {(r["test"], r["method"], r["metric"]): r["value"] for r in out}
    claims = [
        ("EB beats naive on calibrated MAE",
         get[("error", "EB", "mae_calibrated")]
         < get[("error", "naive", "mae_calibrated")]),
        ("EB beats SPF on calibrated MAE",
         get[("error", "EB", "mae_calibrated")]
         < get[("error", "SPF", "mae_calibrated")]),
    ]
    for share in TOP_SHARES:
        t = f"hotspot_top{int(share * 100)}"
        claims += [
            (f"EB beats naive on site consistency, top {share:.0%}",
             get[(t, "EB", "site_consistency")]
             > get[(t, "naive", "site_consistency")]),
            (f"EB beats SPF on site consistency, top {share:.0%}",
             get[(t, "EB", "site_consistency")]
             > get[(t, "SPF", "site_consistency")]),
        ]
    held = sum(ok for _, ok in claims)
    for text, ok in claims:
        print(f"  {'HELD  ' if ok else 'FAILED'}  {text}")
        out.append({"test": "verdict", "method": "EB", "metric": text,
                    "value": 1.0 if ok else 0.0})
    print(f"\n  {held} of {len(claims)} predictions held. "
          + ("The blending method earns its place in the pipeline."
             if held == len(claims) else
             "Where a prediction failed, the report must say so - this step "
             "does not exit on a bad result, by design."))

    FINAL.mkdir(parents=True, exist_ok=True)
    path = FINAL / "holdout_eval.csv"
    with path.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["test", "method", "metric", "value"])
        w.writeheader()
        w.writerows(out)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
