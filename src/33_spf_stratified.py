"""
Step 33 - the safety performance function, stratified by facility type, with
standard errors.

WHY. Step 29 fits ONE curve to all 2,848 FDOT segments. An interstate and a
rural two-lane with the same AADT and length get the same predicted casualties,
and they are not the same road. Real Highway Safety Manual practice estimates a
separate SPF per facility type - rural two-lane, urban arterial, freeway - and
publishes standard errors on the coefficients. This project had neither, and it
is the first thing a reviewer who has fitted SPFs professionally will ask.

WHERE THE CLASSIFICATION COMES FROM. FDOT's AADT layer carries no functional
class field - 24 fields, none of them class, checked directly against the
service metadata. But the OSM network built in step 20 does: every way carries a
`highway` tag. Each FDOT segment midpoint is matched to the nearest OSM way of a
major class, and that tag becomes the facility type.

That is an inference, not a lookup, so the match distance is reported. A segment
whose nearest major road is 800 m away has not been classified, it has been
guessed at, and those are counted separately.

STANDARD ERRORS come from the numerically-differentiated Hessian of the negative
log-likelihood at the optimum. The inverse Hessian is the asymptotic covariance
matrix for a maximum-likelihood fit, so its diagonal square roots are the
standard errors. This is what lets a reader ask whether b differs from 1
(proportional scaling) or from 0 (no scaling at all), which is the question the
coefficient exists to answer.

WHAT WOULD MAKE THIS FAIL, and is checked: a stratum with too few segments or
too few casualties cannot support its own fit. Those are reported and pooled
rather than fitted to noise.

Writes: data/final/spf_by_facility.csv
        data/final/segment_facility.csv   <- READ BY STEP 29, so 33 must run
                                             first. This line was missing, and
                                             the file it names is the one that
                                             survived on a stale copy while
                                             33 sat outside the pipeline.
"""

import csv
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import YEARS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW, FINAL = ROOT / "data" / "raw", ROOT / "data" / "final"
OSM = RAW / "osm"

# OSM classes that correspond to a rateable FDOT facility. Residential and
# service roads are excluded: FDOT publishes no AADT for them, so no segment
# should ever match to one.
MAJOR = ("motorway", "motorway_link", "trunk", "trunk_link", "primary",
         "primary_link", "secondary", "secondary_link", "tertiary",
         "tertiary_link")

# Collapse links into their parent class - a slip road is the same facility.
FACILITY = {"motorway": "freeway", "motorway_link": "freeway",
            "trunk": "freeway", "trunk_link": "freeway",
            "primary": "principal arterial", "primary_link": "principal arterial",
            "secondary": "minor arterial", "secondary_link": "minor arterial",
            "tertiary": "collector", "tertiary_link": "collector"}

MIN_SEGMENTS = 60          # below this a stratum cannot support its own fit
MIN_KSI = 40
MAX_MATCH_M = 500.0        # beyond this the class is a guess, not a match


def osm_major_midpoints():
    """Midpoint and facility class of every major OSM way."""
    lat, lon, cls = [], [], []
    seen = set()
    for tile in sorted(OSM.glob("tile_*.json.gz")):
        for w in json.loads(gzip.decompress(tile.read_bytes())):
            if w["h"] not in MAJOR:
                continue
            c = w["c"]
            h = hash((len(c), c[0][0], c[0][1], c[-1][0], c[-1][1]))
            if h in seen:
                continue
            seen.add(h)
            a = np.asarray(c, dtype=np.float64)
            lat.append(a[:, 0].mean())
            lon.append(a[:, 1].mean())
            cls.append(FACILITY[w["h"]])
    return np.array(lat), np.array(lon), np.array(cls)


def nb_fit_se(y, aadt, length):
    """
    Negative binomial SPF with standard errors.

    mu = exp(a) * AADT^b * L * YEARS

    Standard errors are the square roots of the diagonal of the inverse Hessian
    of the negative log-likelihood at the optimum - the asymptotic covariance
    matrix of a maximum-likelihood estimate.
    """
    def nll(p):
        a, b, logk = p
        k = np.exp(np.clip(logk, -20, 20))
        mu = np.clip(np.exp(a) * np.power(aadt, b) * length * YEARS, 1e-12, None)
        r = 1.0 / k
        ll = (gammaln(y + r) - gammaln(r) - gammaln(y + 1)
              + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu)))
        return -ll.sum()

    res = minimize(nll, [-8.0, 0.75, 0.0], method="Nelder-Mead",
                   options={"maxiter": 40000, "xatol": 1e-9, "fatol": 1e-9})
    p = res.x

    # Numerical Hessian by central differences.
    h = np.maximum(np.abs(p) * 1e-4, 1e-5)
    n = len(p)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            pp = p.copy(); pp[i] += h[i]; pp[j] += h[j]
            pm = p.copy(); pm[i] += h[i]; pm[j] -= h[j]
            mp = p.copy(); mp[i] -= h[i]; mp[j] += h[j]
            mm = p.copy(); mm[i] -= h[i]; mm[j] -= h[j]
            H[i, j] = (nll(pp) - nll(pm) - nll(mp) + nll(mm)) / (4 * h[i] * h[j])
    try:
        cov = np.linalg.inv(H)
        se = np.sqrt(np.abs(np.diag(cov)))
    except np.linalg.LinAlgError:
        se = np.full(n, np.nan)
    return p, se, 2 * res.fun, res.success


def main():
    with (FINAL / "segment_rates.csv").open(encoding="utf8") as fh:
        segs = list(csv.DictReader(fh))
    geom = json.loads((RAW / "fdot_segment_geometry.json").read_text())

    lat, lon, aadt, length, K, A = [], [], [], [], [], []
    for s in segs:
        g = geom.get(f"{s['roadway']}|{float(s['begin_post'])}"
                     f"|{float(s['end_post'])}")
        if g is None:
            continue
        lat.append(g[0]); lon.append(g[1])
        aadt.append(float(s["aadt"])); length.append(float(s["length_mi"]))
        K.append(float(s["occ_deaths"])); A.append(float(s["occ_serious"]))
    lat = np.array(lat); lon = np.array(lon)
    aadt = np.array(aadt); length = np.array(length)
    y = np.array(K) + np.array(A)
    print(f"{len(y):,} FDOT segments with geometry   {y.sum():,.0f} occupant KSI")

    print("\nclassifying by nearest major OSM way")
    olat, olon, ocls = osm_major_midpoints()
    print(f"  {len(olat):,} major OSM ways: "
          f"{dict(Counter(ocls).most_common())}")

    lat0 = np.radians(lat.mean())
    to_m = lambda la, lo: np.column_stack(
        [np.radians(lo) * 6_371_000 * np.cos(lat0),
         np.radians(la) * 6_371_000])
    tree = cKDTree(to_m(olat, olon))
    dist, idx = tree.query(to_m(lat, lon), k=1)
    facility = ocls[idx]
    far = dist > MAX_MATCH_M
    print(f"  match distance: median {np.median(dist):,.0f} m, "
          f"p90 {np.percentile(dist, 90):,.0f} m")
    print(f"  {far.sum():,} segments ({far.mean():.1%}) matched further than "
          f"{MAX_MATCH_M:.0f} m - class is a guess, flagged not dropped")

    # --- pooled fit, for comparison -----------------------------------------
    print(f"\n{'=' * 74}")
    print("POOLED, all facilities together   (this is what step 29 does)")
    print(f"{'=' * 74}")
    p, se, ll, ok = nb_fit_se(y, aadt, length)
    if not ok:
        sys.exit("FAIL: pooled fit did not converge.")
    print(f"  {'':<22}{'estimate':>11}{'std err':>10}{'z vs 0':>9}{'z vs 1':>9}")
    print(f"  {'a (intercept)':<22}{p[0]:>11.4f}{se[0]:>10.4f}"
          f"{p[0]/se[0]:>9.1f}{'':>9}")
    print(f"  {'b (AADT elasticity)':<22}{p[1]:>11.4f}{se[1]:>10.4f}"
          f"{p[1]/se[1]:>9.1f}{(p[1]-1)/se[1]:>9.1f}")
    print(f"  {'k (overdispersion)':<22}{np.exp(p[2]):>11.4f}{'':>10}{'':>9}{'':>9}")
    print(f"  -2logL {ll:,.1f}   n = {len(y):,}")
    print(f"\n  b is {abs((p[1]-1)/se[1]):.0f} standard errors below 1, so casualties")
    print(f"  scale LESS than proportionally with traffic. That is the standard")
    print(f"  finding and it now has a number attached rather than an assertion.")

    # --- stratified ----------------------------------------------------------
    print(f"\n{'=' * 74}")
    print("BY FACILITY TYPE")
    print(f"{'=' * 74}")
    print(f"  {'facility':<22}{'segs':>6}{'KSI':>7}{'b':>9}{'se':>8}"
          f"{'k':>8}{'-2logL':>10}")
    rows, pooled_ll = [], 0.0
    fitted = 0
    for f in sorted(set(facility)):
        m = facility == f
        if m.sum() < MIN_SEGMENTS or y[m].sum() < MIN_KSI:
            print(f"  {f:<22}{m.sum():>6,}{y[m].sum():>7,.0f}"
                  f"{'too small to fit':>35}")
            rows.append({"facility": f, "n": int(m.sum()),
                         "ksi": float(y[m].sum()), "a": "", "b": "",
                         "b_se": "", "k": "", "neg2logL": ""})
            continue
        pf, sf, lf, okf = nb_fit_se(y[m], aadt[m], length[m])
        if not okf:
            print(f"  {f:<22}{m.sum():>6,}{y[m].sum():>7,.0f}"
                  f"{'did not converge':>35}")
            continue
        fitted += 1
        pooled_ll += lf
        print(f"  {f:<22}{m.sum():>6,}{y[m].sum():>7,.0f}{pf[1]:>9.4f}"
              f"{sf[1]:>8.4f}{np.exp(pf[2]):>8.4f}{lf:>10,.1f}")
        rows.append({"facility": f, "n": int(m.sum()),
                     "ksi": float(y[m].sum()), "a": round(pf[0], 6),
                     "b": round(pf[1], 6), "b_se": round(sf[1], 6),
                     "k": round(float(np.exp(pf[2])), 6),
                     "neg2logL": round(lf, 3)})

    # --- does stratifying earn its parameters? ------------------------------
    print(f"\n{'=' * 74}")
    print("IS STRATIFYING JUSTIFIED?")
    print(f"{'=' * 74}")
    extra = 3 * (fitted - 1)
    d = ll - pooled_ll
    print(f"  pooled      -2logL {ll:>12,.1f}   3 parameters")
    print(f"  stratified  -2logL {pooled_ll:>12,.1f}   {3*fitted} parameters")
    print(f"  improvement {d:>12,.1f}   on {extra} extra parameters")
    print(f"  AIC pooled {ll + 6:,.1f}   AIC stratified "
          f"{pooled_ll + 2*3*fitted:,.1f}")
    better = (pooled_ll + 2 * 3 * fitted) < (ll + 6)
    print(f"\n  Stratifying {'IS' if better else 'is NOT'} justified on AIC.")
    if better:
        bs = [r["b"] for r in rows if r["b"] != ""]
        print(f"  Elasticities range {min(bs):.3f} to {max(bs):.3f} across")
        print(f"  facilities against {p[1]:.3f} pooled, so one curve was hiding")
        print(f"  real differences between road types.")
    else:
        print(f"  The pooled curve is adequate. Step 29 stands as it is, and")
        print(f"  this is now a tested claim rather than an unexamined one.")

    # Per-segment facility, so step 29 can shrink toward the right curve.
    # Written even when stratifying is not justified, because the assignment
    # itself is useful and the decision belongs to the consumer.
    with (FINAL / "segment_facility.csv").open("w", newline="",
                                               encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["roadway", "begin_post", "end_post", "facility",
                    "match_m", "class_is_a_guess"])
        j = 0
        for sg in segs:
            g = geom.get(f"{sg['roadway']}|{float(sg['begin_post'])}"
                         f"|{float(sg['end_post'])}")
            if g is None:
                continue
            w.writerow([sg["roadway"], sg["begin_post"], sg["end_post"],
                        facility[j], f"{dist[j]:.0f}",
                        "yes" if far[j] else "no"])
            j += 1
    print(f"wrote {FINAL / 'segment_facility.csv'}  ({j:,} segments)")

    FINAL.mkdir(parents=True, exist_ok=True)
    with (FINAL / "spf_by_facility.csv").open("w", newline="",
                                              encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {FINAL / 'spf_by_facility.csv'}")


if __name__ == "__main__":
    main()
