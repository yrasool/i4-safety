"""
Step 32 - walking and cycling crash risk BY PLACE.

WHY THIS IS THE MOST IMPORTANT REMAINING STEP. Step 30 made DRIVING risk vary by
place. Driving is 15% of the loss. Cycling and walking are 84%, and until now
both carried one regional number, so the part of the answer that matters most
was flat across 2,170 block groups.

Two inputs make this possible, and neither was being used:

  NUMERATOR   The crash file carries LATITUDE and LONGITUDE. Every pedestrian
              and cyclist casualty can be placed directly, with no road-segment
              intermediary. Step 09 only ever matched crashes to FDOT segments,
              which covers state highways and drops 27% of crashes; coordinates
              drop none.

  DENOMINATOR ACS table B08301, means of transportation to work, IS PUBLISHED
              AT BLOCK GROUP LEVEL - all 2,170 of ours. Columns E019 (walked)
              and E018 (bicycle) give a per-neighbourhood propensity to walk and
              cycle, which is the spatial allocator the regional NHTS exposure
              was missing.

METHOD. Regional walk and bike person-miles from step 17 are allocated across
block groups in proportion to population times commute-mode share, then each
block group's own casualties are divided by its own exposure.

    w_i        = pop_i * (walkers_i / workers_i)
    PMT_i      = regional_PMT * w_i / SUM w
    r_i        = (K_i*VSL + A_i*A_val) / YEARS / PMT_i

TWO HONEST LIMITS, both stated in the report:

  1. COMMUTE SHARE IS NOT ALL WALKING. B08301 counts journey-to-work only, and
     most walking is not commuting. It is used as a PROPENSITY INDEX, not as a
     trip count - the regional total still comes from NHTS. The assumption is
     that a neighbourhood where twice as many people walk to work also walks
     about twice as much overall, which is the same assumption FHWA's scalable
     risk method makes.

  2. NEAREST-CENTROID ASSIGNMENT. Crashes are assigned to the closest block
     group centroid, not by point-in-polygon, because TIGER polygons are not on
     disk. The distance distribution is printed so the error is visible rather
     than assumed away.

EMPIRICAL BAYES, again, and for the same reason as step 29. Most block groups
have zero or one pedestrian casualty. Dividing a 1 by a small exposure produces
a spectacular rate that is pure noise. The counts are shrunk toward what a
neighbourhood with that much walking exposure normally sees.

=====================================================================
THE RESULT OF THIS STEP IS A NEGATIVE ONE, AND IT IS THE POINT.
=====================================================================

Six candidate allocators were fitted against pedestrian KSI on a common sample
of 1,913 block groups. The elasticity `b` says how strongly casualties scale
with the thing you are dividing by. A working safety performance function has
b in the 0.7 to 0.9 range - step 29 gets 0.7892 on road segments.

    population                 b = -0.0994     -2logL 5838.7
    road density D3A           b = -0.0095     -2logL 5833.9
    nearby road VMT 800 m      b = +0.0123     -2logL 5804.7
    nearby road VMT 1.5 km     b = +0.2149     -2logL 5784.2   best
    nearby road VMT 3 km       b = +0.2459     -2logL 5804.6
    population x nearby VMT    b = +0.1700     -2logL 5801.1

And with both covariates together, on the 530 block groups where each is
non-zero:

    walk exposure only         b = 0.1561                  AIC 1752.5
    nearby VMT only            b = 0.2772                  AIC 1732.1
    both                       b1 = 0.1287, b2 = 0.2679    AIC 1729.9

NEARBY TRAFFIC VOLUME IS ABOUT TWICE AS PREDICTIVE AS RESIDENT WALKING, and
neither is strong. Read that as the finding: people walk where they LIVE and are
struck where they CROSS ARTERIALS, and no areal measure available here separates
the two well.

WHY THIS STEP DOES NOT FEED THE HEADLINE. With b that weak, Empirical Bayes
correctly shrinks nearly every block group toward a near-constant expectation.
The surviving variation in r_i is then dominated by 1/exposure - which is
arithmetic, not risk. Publishing it as a pedestrian risk map would repeat the
identity mistake in a new costume.

So the rates are written out, labelled exploratory, and NOT substituted into
step 23. What this step establishes is that the data cannot yet support a
spatial non-motorist risk surface, and exactly which measurement would change
that: counted pedestrian and cyclist exposure at sub-regional geography, from
StreetLight, Replica, or FHWA's scalable risk assessment method.

Writes: data/final/nonmotor_risk_by_place.csv   (EXPLORATORY - see above)
"""

import csv
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from scipy.special import gammaln

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (CRASH_CSV, COUNTIES, STATE_FP, USER_AGENT,  # noqa: E402
                       COST_PER_PERSON, YEARS)

ROOT = Path(__file__).resolve().parents[1]
RAW, INTERIM, FINAL = (ROOT / "data" / "raw", ROOT / "data" / "interim",
                       ROOT / "data" / "final")

YEAR = 2023
ACS = ("https://www2.census.gov/programs-surveys/acs/summary_file/"
       f"{YEAR}/table-based-SF/data/5YRData/acsdt5y{YEAR}-b08301.dat")
BG_LEVEL = "1500000US"
KEEP = tuple(BG_LEVEL + STATE_FP + c for c in COUNTIES)

# B08301 columns. E001 total workers, E018 bicycle, E019 walked.
COL = {"workers": "B08301_E001", "bike": "B08301_E018", "walk": "B08301_E019"}

MAX_SNAP_M = 4000        # beyond this the nearest centroid is not a real match


def denul(fh):
    for line in fh:
        yield line.replace("\x00", "")


def num(row, col):
    v = row.get(col)
    if not v:
        return 0
    try:
        return int(float(v))
    except ValueError:
        return 0


def fetch_acs():
    path = RAW / f"acs{YEAR}_b08301.dat"
    if not path.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(ACS, headers=USER_AGENT)
        with urllib.request.urlopen(req, timeout=900) as r:
            path.write_bytes(r.read())
    lines = path.read_text(encoding="utf8", errors="replace").splitlines()
    head = lines[0].split("|")
    out = {}
    for ln in lines[1:]:
        if not ln.startswith(KEEP):
            continue
        f = dict(zip(head, ln.split("|")))
        gid = f["GEO_ID"].split("US")[1]
        def g(k):
            try:
                return max(0.0, float(f.get(COL[k], 0) or 0))
            except ValueError:
                return 0.0
        out[gid] = {"workers": g("workers"), "walk": g("walk"),
                    "bike": g("bike")}
    return out


# An elasticity below this means the allocator does not predict the outcome,
# so any rate built on it is exposure arithmetic rather than measured risk.
# Step 29's road-segment SPF reaches 0.7892 for comparison.
MIN_DEFENSIBLE_B = 0.45


def nb_fit(y, exposure, traffic=None):
    """
    Negative binomial SPF, one or two covariates.

    Two, when nearby road VMT is supplied:  mu = exp(a) * E^b1 * V^b2

    The second covariate exists because the one-covariate fit on walk exposure
    alone returns b = 0.02, i.e. casualties do not scale with resident walking
    at all. Nearby traffic volume roughly doubles the elasticity and wins on
    AIC, which is the evidence for the "struck where they cross" reading.
    """
    # FIT ONLY WHERE EVERY COVARIATE IS POSITIVE.
    # Substituting 1e-9 for a zero and raising it to a power produces values
    # around 1e-9^b that dominate the likelihood and drag the elasticity to
    # zero. Fitted on the full array with 250 zero-traffic block groups, the
    # two-covariate model returned b1 = b2 = 0.019; fitted on positive rows it
    # returns 0.129 and 0.268. The zeros were the whole difference.
    e_all = np.maximum(exposure, 0.0)
    two = traffic is not None
    v_all = np.maximum(traffic, 0.0) if two else None
    fit_on = e_all > 0
    if two:
        fit_on &= v_all > 0
    if fit_on.sum() < 50:
        return (None,) * 5 + (False,)
    y_f = y[fit_on]
    e = e_all[fit_on]
    v = v_all[fit_on] if two else None

    def nll(p):
        if two:
            a, b1, b2, logk = p
            mu = np.exp(a) * np.power(e, b1) * np.power(v, b2)
        else:
            a, b1, logk = p
            mu = np.exp(a) * np.power(e, b1)
        mu = np.clip(mu, 1e-9, None)
        r = 1.0 / np.exp(logk)
        ll = (gammaln(y_f + r) - gammaln(r) - gammaln(y_f + 1)
              + r * np.log(r / (r + mu)) + y_f * np.log(mu / (r + mu)))
        return -ll.sum()

    x0 = [-10.0, 0.3, 0.3, 0.0] if two else [-10.0, 0.7, 0.0]
    res = minimize(nll, x0, method="Nelder-Mead",
                   options={"maxiter": 60000, "xatol": 1e-9, "fatol": 1e-9})
    # Predict for EVERY row, flooring the covariates so a zero-traffic block
    # group gets the model's smallest sensible expectation rather than an
    # infinity or a zero.
    fl_e = np.maximum(e_all, np.percentile(e[e > 0], 1))
    if two:
        a, b1, b2, logk = res.x
        fl_v = np.maximum(v_all, np.percentile(v[v > 0], 1))
        mu = np.exp(a) * np.power(fl_e, b1) * np.power(fl_v, b2)
        return a, b1, b2, np.exp(logk), mu, res.success
    a, b1, logk = res.x
    mu = np.exp(a) * np.power(fl_e, b1)
    return a, b1, None, np.exp(logk), mu, res.success


def nearby_road_vmt(clat, clon, radius_m=1500.0):
    """
    Period VMT on FDOT segments whose midpoint is within `radius_m`.

    1.5 km was chosen by fitting 800 m, 1.5 km and 3 km and taking the lowest
    -2logL on a common sample. It is a fitted choice, not a round number.
    """
    geom = json.loads((RAW / "fdot_segment_geometry.json").read_text())
    with (FINAL / "segment_eb.csv").open(encoding="utf8") as fh:
        segs = list(csv.DictReader(fh))
    sl, so, sv = [], [], []
    for x in segs:
        g = geom.get(f"{x['roadway']}|{float(x['begin_post'])}"
                     f"|{float(x['end_post'])}")
        if g:
            sl.append(g[0]); so.append(g[1]); sv.append(float(x["vmt_period"]))
    if not sl:
        return None
    sl, so, sv = np.array(sl), np.array(so), np.array(sv)
    lat0 = np.radians(clat.mean())
    f = lambda la, lo: np.column_stack(
        [np.radians(lo) * 6_371_000 * np.cos(lat0),
         np.radians(la) * 6_371_000])
    tree = cKDTree(f(sl, so))
    return np.array([sv[tree.query_ball_point(pt, radius_m)].sum()
                     for pt in f(clat, clon)])


def main():
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    geoid = [r["GEOID20"] for r in cent]
    n = len(cent)
    pos = {g: i for i, g in enumerate(geoid)}
    clat = np.array([float(r["lat"]) for r in cent])
    clon = np.array([float(r["lon"]) for r in cent])

    lat0 = np.radians(clat.mean())
    to_m = lambda la, lo: np.column_stack(
        [np.radians(lo) * 6_371_000 * np.cos(lat0),
         np.radians(la) * 6_371_000])
    tree = cKDTree(to_m(clat, clon))

    # --- numerator: place every ped and cyclist casualty by coordinate -------
    print("assigning pedestrian and cyclist casualties by coordinate")
    pK = np.zeros(n); pA = np.zeros(n)
    bK = np.zeros(n); bA = np.zeros(n)
    pts, load = [], []
    seen = nogeo = 0
    with open(CRASH_CSV, encoding="utf8", errors="replace") as fh:
        for row in csv.DictReader(denul(fh)):
            seen += 1
            k = (num(row, "S4_PEDESTRIAN_FATALITY_COUNT"),
                 num(row, "S4_PEDESTRIAN_INCAPACITATING_INJURY_COUNT"),
                 num(row, "S4_BICYCLIST_FATALITY_COUNT"),
                 num(row, "S4_BICYCLIST_INCAPACITATING_INJURY_COUNT"))
            if not any(k):
                continue
            try:
                la = float(row.get("LATITUDE") or "nan")
                lo = float(row.get("LONGITUDE") or "nan")
            except ValueError:
                nogeo += 1
                continue
            if not (27.0 < la < 29.5 and -83.5 < lo < -82.0):
                nogeo += 1
                continue
            pts.append((la, lo))
            load.append(k)

    pts = np.asarray(pts)
    dist, idx = tree.query(to_m(pts[:, 0], pts[:, 1]), k=1)
    for j, (a, b, c, d) in enumerate(load):
        i = idx[j]
        pK[i] += a; pA[i] += b; bK[i] += c; bA[i] += d

    print(f"  {seen:,} crashes read, {len(pts):,} carried a walk or bike "
          f"casualty and a usable coordinate")
    print(f"  {nogeo:,} dropped for missing or out-of-area coordinates "
          f"({nogeo / max(len(pts) + nogeo, 1):.1%})")
    print(f"  snap distance to nearest block group centroid: "
          f"median {np.median(dist):,.0f} m, p90 {np.percentile(dist, 90):,.0f} m,"
          f" max {dist.max():,.0f} m")
    far = int((dist > MAX_SNAP_M).sum())
    print(f"  {far} beyond {MAX_SNAP_M:,} m ({far / len(pts):.2%})")
    print(f"  totals placed: walk {pK.sum():,.0f} K / {pA.sum():,.0f} A"
          f"   bike {bK.sum():,.0f} K / {bA.sum():,.0f} A")

    # Reconcile against the regional counts step 02 produced from the same file.
    with (INTERIM / "casualties_by_mode.csv").open(encoding="utf8") as fh:
        cas = {r["mode"]: r for r in csv.DictReader(fh)}
    for label, got, want in (("walk K", pK.sum(), int(cas["walk"]["K"])),
                             ("walk A", pA.sum(), int(cas["walk"]["A"])),
                             ("bike K", bK.sum(), int(cas["bike"]["K"])),
                             ("bike A", bA.sum(), int(cas["bike"]["A"]))):
        pct = got / want - 1 if want else 0.0
        print(f"    {label}: placed {got:,.0f} of {want:,} ({pct:+.1%})")
        if abs(pct) > 0.15:
            sys.exit(f"FAIL: {label} placed by coordinate differs from step 02 "
                     f"by more than 15%. Coordinates are dropping casualties "
                     f"non-randomly; do not build a rate on this.")

    # --- denominator: allocate NHTS exposure by commute-mode propensity ------
    print("\nallocating exposure by ACS B08301 commute mode share")
    acs = fetch_acs()
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        pop = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
    with (INTERIM / "nonmotorised_exposure.csv").open(encoding="utf8") as fh:
        nm = {(r["geography"], r["mode"]): float(r["miles_per_person_yr"])
              for r in csv.DictReader(fh)}

    P = np.array([pop.get(g, 0.0) for g in geoid])
    workers = np.array([acs.get(g, {}).get("workers", 0.0) for g in geoid])
    matched = sum(1 for g in geoid if g in acs)
    print(f"  B08301 matched {matched:,} of {n:,} block groups")

    print("  computing nearby road VMT within 1.5 km of each block group")
    nv = nearby_road_vmt(clat, clon)
    if nv is None:
        sys.exit("FAIL: no FDOT segment geometry. Run step 30 first.")
    print(f"    median {np.median(nv)/1e6:,.0f} M vehicle-miles, "
          f"{(nv == 0).sum():,} block groups with none")

    out_rows = []
    result = {}
    exploratory = []
    for mode, K, A in (("walk", pK, pA), ("bike", bK, bA)):
        cnt = np.array([acs.get(g, {}).get(mode, 0.0) for g in geoid])
        share = np.divide(cnt, workers, out=np.zeros(n), where=workers > 0)
        w = P * share
        if w.sum() <= 0:
            sys.exit(f"FAIL: no {mode} commute share anywhere. B08301 columns "
                     f"are wrong.")
        regional_pmt = nm[("South Atlantic 2022", mode)] * P.sum()
        pmt = regional_pmt * w / w.sum()

        y = K + A
        a, b1, b2, kk, mu, ok = nb_fit(y, np.maximum(pmt, 1.0), traffic=nv)
        if not ok:
            sys.exit(f"FAIL: {mode} exposure model did not converge.")
        b = b1
        wgt = 1.0 / (1.0 + kk * mu)
        eb = wgt * mu + (1.0 - wgt) * y

        # Split EB casualties back into K and A, shrunk like step 29.
        reg_k = K.sum() / max(y.sum(), 1.0)
        k_share = (K + 10.0 * reg_k) / (y + 10.0)
        cost = (eb * k_share * COST_PER_PERSON["K"]
                + eb * (1 - k_share) * COST_PER_PERSON["A"]) / YEARS
        r = np.divide(cost, pmt, out=np.zeros(n), where=pmt > 0)
        result[mode] = (r, pmt, y, eb, share)

        live = pmt > 0
        print(f"\n  {mode.upper()}")
        print(f"    commute share: median {np.median(share[live]):.2%}  "
              f"p90 {np.percentile(share[live], 90):.2%}  "
              f"max {share.max():.1%}")
        print(f"    SPF  b_exposure={b1:.4f}"
              + (f"  b_nearby_traffic={b2:.4f}" if b2 is not None else "")
              + f"  k={kk:.4f}")
        print(f"    {(y == 0).sum():,} block groups with zero casualties")
        print(f"    EB total {eb.sum():,.0f} against observed {y.sum():,.0f} "
              f"({eb.sum() / max(y.sum(), 1) - 1:+.1%})")
        print(f"    r per passenger-mile: p10 ${np.percentile(r[live], 10):.2f}"
              f"   median ${np.median(r[live]):.2f}"
              f"   p90 ${np.percentile(r[live], 90):.2f}")
        agg = cost.sum() / pmt.sum()
        print(f"    exposure-weighted mean ${agg:.2f}")

        # RECONCILE against step 04's regional rate. Same casualties, same
        # exposure total, just distributed. If these disagree the allocation
        # has changed the level, which it must not.
        with (FINAL / "injury_cost_by_mode.csv").open(encoding="utf8") as f2:
            reg = {r["mode"]: r for r in csv.DictReader(f2)}
        lo = float(reg[mode]["cost_per_pmt_lo"])
        hi = float(reg[mode]["cost_per_pmt_hi"])
        print(f"    step 04 regional range ${lo:.2f} to ${hi:.2f}   "
              f"ratio {agg / ((lo + hi) / 2):.2f}x")

        # THE ELASTICITY IS THE DIAGNOSTIC THAT MATTERS.
        # b is how strongly casualties scale with exposure. If it is near zero
        # the allocator does NOT predict where people get hurt, and every rate
        # below is exposure noise rather than risk.
        strongest = max(abs(b1), abs(b2 or 0.0))
        if strongest < MIN_DEFENSIBLE_B:
            print(f"    *** EXPLORATORY ONLY. Strongest elasticity {strongest:.4f}"
                  f" < {MIN_DEFENSIBLE_B}.")
            print(f"        Step 29's road SPF reaches 0.79 for comparison.")
            print(f"        Nearby traffic ({b2:.3f}) predicts {mode} casualties"
                  f" about {abs((b2 or 0)/max(abs(b1),1e-9)):.0f}x better than")
            print(f"        resident {mode} exposure ({b1:.3f}) - people travel")
            print(f"        where they live and are struck where they cross.")
            print(f"        With b this weak, EB shrinks to a near-constant mu,")
            print(f"        so r_i varies as 1/exposure. That is arithmetic, not")
            print(f"        risk. NOT substituted into step 23.")
            exploratory.append(mode)
        spread = (np.percentile(r[live], 90)
                  / max(np.percentile(r[live], 10), 1e-9))
        print(f"    spread p90/p10 = {spread:.1f}x   "
              f"CV {r[live].std() / r[live].mean():.3f}")

    with (FINAL / "nonmotor_risk_by_place.csv").open("w", newline="",
                                                     encoding="utf8") as fh:
        wtr = csv.writer(fh)
        wtr.writerow(["GEOID20", "county", "pop",
                      "walk_commute_share", "walk_pmt", "walk_ksi_obs",
                      "walk_ksi_eb", "r_walk",
                      "bike_commute_share", "bike_pmt", "bike_ksi_obs",
                      "bike_ksi_eb", "r_bike"])
        rw, pw, yw, ew, sw = result["walk"]
        rb, pb, yb, eb2, sb = result["bike"]
        for i, g in enumerate(geoid):
            wtr.writerow([g, cent[i]["county"], f"{P[i]:.0f}",
                          f"{sw[i]:.6f}", f"{pw[i]:.0f}", f"{yw[i]:.0f}",
                          f"{ew[i]:.4f}", f"{rw[i]:.4f}",
                          f"{sb[i]:.6f}", f"{pb[i]:.0f}", f"{yb[i]:.0f}",
                          f"{eb2[i]:.4f}", f"{rb[i]:.4f}"])
    print(f"\nwrote {FINAL / 'nonmotor_risk_by_place.csv'}")


if __name__ == "__main__":
    main()
