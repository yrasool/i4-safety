"""
Step 29 - Safety Performance Function and Empirical Bayes, road by road.

WHY THIS EXISTS. Step 26 proves the block-group surface is an identity: the loss
at every origin reduces to a function of its mode mix, because `r_k` is one
regional number per mode. Four scalars cannot make a map. Place-varying risk
can, and this is the first half of building it.

THE PROBLEM WITH RAW SEGMENT RATES. `segment_rates.csv` already divides each
segment's casualties by its own VMT. On a short, quiet road that rate is mostly
noise: the top of the list is led by a segment with AADT 350 and another
described as "DEAD END". Median deaths per segment is 0 and the mean is 1.2, so
most of the distribution is a coin-flip away from doubling.

THE STANDARD ANSWER, from the Highway Safety Manual, is two steps.

  1. A SAFETY PERFORMANCE FUNCTION predicts what a road LIKE THIS normally sees,
     from traffic volume and length:

         mu_i = exp(a) * AADT_i^b * L_i * YEARS

     fitted by negative binomial regression, because crash counts are
     overdispersed - their variance exceeds their mean, so Poisson would report
     far more significance than the data supports.

  2. EMPIRICAL BAYES blends that prediction with what the segment actually saw:

         w_i    = 1 / (1 + k * mu_i)
         N_eb_i = w_i * mu_i + (1 - w_i) * y_i

     `k` is the overdispersion parameter from the fit. A busy segment with a lot
     of exposure has small w and is trusted on its own record; a short quiet one
     has w near 1 and is pulled back toward what its class normally does. That
     is the regression-to-the-mean correction, and it is exactly what stops a
     dead-end street with two deaths from topping a ranking.

KSI, NOT DEATHS. Fitted on deaths plus serious injuries, because `r_drive` is
KSI and a segment rate on a different severity basis could not be substituted
into it. Deaths alone would also be too sparse to fit: median 0 per segment.

Writes: data/final/segment_eb.csv
"""

import csv
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import COST_PER_PERSON, YEARS, OCCUPANCY  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "data" / "final"


def nb_negloglik(params, y, aadt, length):
    """
    Negative binomial log-likelihood for mu = exp(a) * AADT^b * L * YEARS.

    Parameterised by log k so the optimiser cannot wander to k <= 0, which
    would make the variance term negative and the likelihood undefined.
    """
    a, b, log_k = params
    k = np.exp(log_k)
    mu = np.exp(a) * np.power(aadt, b) * length * YEARS
    mu = np.clip(mu, 1e-9, None)
    r = 1.0 / k                      # NB "size"; Var = mu + k*mu^2
    ll = (gammaln(y + r) - gammaln(r) - gammaln(y + 1)
          + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu)))
    return -ll.sum()


def main():
    path = FINAL / "segment_rates.csv"
    with path.open(encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))
    for col in ("occ_deaths", "occ_serious"):
        if col not in rows[0]:
            sys.exit(f"FAIL: segment_rates.csv has no `{col}`. Rerun step 09.")

    aadt = np.array([float(r["aadt"]) for r in rows])
    length = np.array([float(r["length_mi"]) for r in rows])

    # OCCUPANT casualties, not all-mode. The all-mode columns are also present
    # and were used first, which made the exposure-weighted mean segment rate
    # $0.2084 against r_drive's $0.1059 - roughly double, because all-mode KSI
    # on these roads is 19,999 against 16,356 occupant KSI region-wide, and the
    # two answer different questions. All-mode is what driving CAUSES;
    # r_drive is what drivers SUFFER. Substituting the first into MEP's drive
    # cost term would switch specifications without saying so.
    K = np.array([float(r["occ_deaths"]) for r in rows])
    A = np.array([float(r["occ_serious"]) for r in rows])
    y = K + A                                    # occupant KSI count
    vmt = np.array([float(r["vmt_period"]) for r in rows])

    print(f"{len(rows):,} segments")
    print(f"  KSI per segment: median {np.median(y):.0f}  mean {y.mean():.2f}  "
          f"max {y.max():.0f}  zero on {(y == 0).mean():.1%}")
    print(f"  variance {y.var():,.1f} against mean {y.mean():.2f} - "
          f"ratio {y.var() / y.mean():.1f}")
    print(f"  A Poisson model assumes that ratio is 1. It is not, which is why")
    print(f"  the fit below is negative binomial and why EB is needed at all.\n")

    # --- fit -----------------------------------------------------------------
    # STRATIFIED BY FACILITY TYPE where step 33 has classified the segments.
    # A pooled curve gives an interstate and a collector the same expectation at
    # the same AADT, and they are not the same road. Step 33 shows the
    # elasticity runs 0.628 on collectors to 0.828 on freeways, and that
    # stratifying wins on AIC (10,693.6 against 10,765.4), so the strata are
    # earned rather than assumed. EB then shrinks each segment toward the curve
    # for ITS OWN road type.
    fac_path = FINAL / "segment_facility.csv"
    facility = None
    if fac_path.exists():
        with fac_path.open(encoding="utf8") as fh:
            fmap = {(r["roadway"], float(r["begin_post"]),
                     float(r["end_post"])): r["facility"]
                    for r in csv.DictReader(fh)}
        facility = np.array([fmap.get((r["roadway"], float(r["begin_post"]),
                                       float(r["end_post"])), "")
                             for r in rows])
        if (facility == "").mean() > 0.05:
            print(f"  facility class missing for "
                  f"{(facility == '').mean():.1%} of segments - pooling instead")
            facility = None

    def fit(mask):
        r = minimize(nb_negloglik, x0=[-6.0, 0.8, 0.0],
                     args=(y[mask], aadt[mask], length[mask]),
                     method="Nelder-Mead",
                     options={"maxiter": 40000, "xatol": 1e-9, "fatol": 1e-9})
        if not r.success:
            sys.exit(f"FAIL: SPF did not converge: {r.message}")
        return r.x

    a, b, log_k = fit(np.ones(len(y), bool))
    k = np.exp(log_k)
    mu = np.exp(a) * np.power(aadt, b) * length * YEARS

    if facility is not None:
        mu = np.zeros(len(y))
        kk = np.zeros(len(y))
        print("\n  STRATIFIED SPF, one curve per facility type")
        print(f"  {'facility':<22}{'segs':>7}{'b':>9}{'k':>9}")
        for f in sorted(set(facility)):
            m = facility == f
            # A stratum too thin to fit keeps the pooled curve rather than
            # being fitted to noise.
            if m.sum() < 60 or y[m].sum() < 40:
                af, bf, lkf = a, b, log_k
                note = "  (pooled - too thin)"
            else:
                af, bf, lkf = fit(m)
                note = ""
            mu[m] = np.exp(af) * np.power(aadt[m], bf) * length[m] * YEARS
            kk[m] = np.exp(lkf)
            print(f"  {f:<22}{m.sum():>7,}{bf:>9.4f}{np.exp(lkf):>9.4f}{note}")
        k = kk

    print("\nSAFETY PERFORMANCE FUNCTION  mu = exp(a) * AADT^b * L * years")
    print(f"  pooled a     {a:>10.4f}")
    print(f"  pooled b     {b:>10.4f}   elasticity of KSI to traffic volume")
    print(f"  pooled k     {np.exp(log_k):>10.4f}   overdispersion")
    if facility is not None:
        print(f"  (the pooled row is shown for comparison; EB below uses the")
        print(f"   per-facility curves above. Standard errors are in step 33.)")
    print(f"\n  b = {b:.2f} means KSI rises {'less' if b < 1 else 'more'} than "
          f"proportionally with volume,")
    print(f"  so a road with twice the traffic has {2 ** b:.2f}x the KSI, not "
          f"2x. That is the")
    print(f"  standard finding and it is why a RATE per VMT falls as volume "
          f"rises.")

    # --- Empirical Bayes -----------------------------------------------------
    # k is now per-segment when stratified, scalar when pooled. numpy handles
    # both without the formula changing.
    w = 1.0 / (1.0 + k * mu)
    n_eb = w * mu + (1.0 - w) * y

    print(f"\nEMPIRICAL BAYES")
    print(f"  weight on the model, w = 1/(1 + k*mu):")
    print(f"    median {np.median(w):.3f}   p10 {np.percentile(w, 10):.3f}   "
          f"p90 {np.percentile(w, 90):.3f}")
    print(f"  {(w > 0.9).sum():,} segments are >90% model - too little exposure")
    print(f"  {(w < 0.5).sum():,} segments are majority their own record")

    # Total KSI must be roughly preserved; EB redistributes, it does not invent.
    print(f"\n  observed KSI total {y.sum():,.0f}   EB total {n_eb.sum():,.0f}"
          f"   ({n_eb.sum() / y.sum() - 1:+.1%})")
    if abs(n_eb.sum() / y.sum() - 1) > 0.10:
        sys.exit("FAIL: EB moved the regional KSI total by more than 10%. It "
                 "is meant to redistribute risk between segments, not change "
                 "how much there is. Check the SPF fit.")

    # --- what it does to the ranking ----------------------------------------
    raw_rate = np.divide(y, vmt / 1e8, out=np.zeros_like(y), where=vmt > 0)
    eb_rate = np.divide(n_eb, vmt / 1e8, out=np.zeros_like(n_eb), where=vmt > 0)
    top_raw = set(np.argsort(-raw_rate)[:25])
    top_eb = set(np.argsort(-eb_rate)[:25])
    print(f"\n  TOP 25 BY RATE: {len(top_raw - top_eb)} of 25 drop out when EB "
          f"is applied")
    print(f"\n  {'':<3}{'road':<34}{'AADT':>8}{'KSI':>5}{'raw rate':>10}"
          f"{'EB rate':>9}")
    print("  before EB:")
    for i in list(np.argsort(-raw_rate)[:5]):
        print(f"     {rows[i]['description'][:32]:<34}{aadt[i]:>8,.0f}"
              f"{y[i]:>5.0f}{raw_rate[i]:>10.1f}{eb_rate[i]:>9.1f}")
    print("  after EB:")
    for i in list(np.argsort(-eb_rate)[:5]):
        print(f"     {rows[i]['description'][:32]:<34}{aadt[i]:>8,.0f}"
              f"{y[i]:>5.0f}{raw_rate[i]:>10.1f}{eb_rate[i]:>9.1f}")

    # --- crash cost per passenger-mile, per segment -------------------------
    # Same construction as r_drive, on the same USDOT per-person values, so a
    # segment rate is substitutable into MEP's cost term. KSI is split back into
    # K and A by each segment's own observed mix, falling back to the regional
    # mix where a segment has no casualties at all to split.
    # THE SEVERITY SPLIT IS SHRUNK TOO, OR EB IS UNDONE.
    #
    # This used each segment's RAW observed K/KSI ratio. A death costs 10.5x a
    # serious injury, so a segment with K=1, A=0 got `k_share = 1.0` and 10.5x
    # the per-casualty cost of a neighbouring K=0, A=1 segment - on a sample of
    # one casualty each. Empirical Bayes smoothed the COUNT and then the split
    # multiplied it by an unsmoothed, extremely noisy ratio, putting the
    # variance straight back and putting it back correlated with the same
    # noise.
    #
    # Beta-binomial shrinkage on the same logic as the count: blend the
    # segment's own ratio toward the regional one, with weight set by how many
    # casualties the segment actually has. `m` is the prior strength in
    # casualty-equivalents; at m = 10 a segment needs about ten casualties
    # before its own severity mix outweighs the region's.
    SEVERITY_PRIOR = 10.0
    reg_k_share = K.sum() / max(y.sum(), 1.0)
    k_share = (K + SEVERITY_PRIOR * reg_k_share) / (y + SEVERITY_PRIOR)
    raw_share = np.divide(K, y, out=np.full_like(K, reg_k_share), where=y > 0)
    eb_K = n_eb * k_share
    eb_A = n_eb * (1.0 - k_share)
    print(f"\nSEVERITY SPLIT, SHRUNK  (regional K share {reg_k_share:.4f})")
    print(f"  raw   K share: p10 {np.percentile(raw_share, 10):.3f}  "
          f"median {np.median(raw_share):.3f}  "
          f"p90 {np.percentile(raw_share, 90):.3f}  "
          f"sd {raw_share.std():.3f}")
    print(f"  shrunk K share: p10 {np.percentile(k_share, 10):.3f}  "
          f"median {np.median(k_share):.3f}  "
          f"p90 {np.percentile(k_share, 90):.3f}  "
          f"sd {k_share.std():.3f}")
    print(f"  {(raw_share == 1.0).sum():,} segments had a RAW K share of "
          f"exactly 1.0 (all casualties fatal)")
    print(f"  {(k_share > 0.9).sum():,} still exceed 0.9 after shrinkage - "
          f"those have the evidence for it")
    cost = (eb_K * COST_PER_PERSON["K"] + eb_A * COST_PER_PERSON["A"]) / YEARS
    pmt = vmt / YEARS * OCCUPANCY
    r_seg = np.divide(cost, pmt, out=np.zeros_like(cost), where=pmt > 0)

    print(f"\nCRASH COST PER PASSENGER-MILE, BY SEGMENT")
    print(f"  median ${np.median(r_seg):.4f}   p10 ${np.percentile(r_seg, 10):.4f}"
          f"   p90 ${np.percentile(r_seg, 90):.4f}   max ${r_seg.max():.3f}")
    total_r = cost.sum() / pmt.sum()
    print(f"  exposure-weighted mean ${total_r:.4f}")

    # Reconcile against the regional figure rather than asserting a direction.
    # An earlier version of this line claimed the segment rate should be LOWER
    # than r_drive "because volumes are higher here", while printing a number
    # that was twice as high. The sentence was written before the number and
    # never re-read against it.
    with (FINAL / "injury_cost_by_mode.csv").open(encoding="utf8") as fh:
        r_drive = float(next(x["cost_per_pmt"] for x in csv.DictReader(fh)
                             if x["mode"] == "vehicle_occupant"))
    ratio = total_r / r_drive
    direction = "above" if ratio > 1 else "below"
    print(f"  regional r_drive (step 04, all roads)  ${r_drive:.4f}")
    print(f"  ratio  {ratio:.2f}x  - the segment mean is {direction} it")
    print(f"\n  These are the same severity basis and the same people now")
    print(f"  (occupants, KSI), so the gap is exposure coverage: these segments")
    print(f"  carry {pmt.sum() * YEARS / 1e9:.0f} B passenger-miles of the "
          f"region's driving, and the")
    print(f"  local and county roads that carry the rest are not rateable at "
          f"all,\n  because FDOT publishes no volumes for them.")
    if not 0.5 < ratio < 2.0:
        print(f"\n  WARNING: {ratio:.2f}x is outside the range a coverage "
              f"difference alone\n  should explain. Check the occupant residual "
              f"and the VMT denominators\n  before using these rates.")
    print(f"\n  Spread: p90 is {np.percentile(r_seg, 90) / max(np.percentile(r_seg, 10), 1e-9):.0f}x p10. "
          f"THAT SPREAD IS THE POINT - it is the\n  place-to-place variation a "
          f"single regional number cannot carry.")

    with (FINAL / "segment_eb.csv").open("w", newline="", encoding="utf8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["roadway", "county", "begin_post", "end_post",
                      "length_mi", "aadt", "description", "ksi_observed",
                      "ksi_spf", "eb_weight", "ksi_eb", "vmt_period",
                      "r_per_pmt"])
        for i, rw in enumerate(rows):
            wtr.writerow([rw["roadway"], rw["county"], rw["begin_post"],
                          rw["end_post"], rw["length_mi"], rw["aadt"],
                          rw["description"], f"{y[i]:.0f}", f"{mu[i]:.3f}",
                          f"{w[i]:.4f}", f"{n_eb[i]:.3f}",
                          rw["vmt_period"], f"{r_seg[i]:.6f}"])
    print(f"\nwrote {FINAL / 'segment_eb.csv'}")


if __name__ == "__main__":
    main()
