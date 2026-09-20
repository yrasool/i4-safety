"""Step 46 - the version B headline, which nothing else computes.

THE GAP THIS FILLS. Step 35 computes the version B RATE - what driving costs
once the harm it does to people outside the car is charged to it - but never
runs MEP on it, so the project has quoted a version B headline that no script
produces. It sat on a slide as "8.2%" beside a 16.2% version A, and survived
the move to 13.4% unchanged because nothing recomputed it.

THE TWO CONVENTIONS.
  A  the harm lands on whoever is hurt        - what ships
  B  the harm is charged to whoever caused it - this file

99.02% of people killed walking here were struck by a car, and 98.56% of people
killed cycling. Under B those shares move to driving, so walking and cycling
keep only the fraction NOT involving a car, and driving's rate rises from
$0.1059 to $0.1573 per passenger-mile - both figures read from step 35's own
output, neither declared here.

THE ONE JUDGEMENT, STATED. Driving's version A risk varies by route, band by
band; version B is a single regional rate. Replacing the routed surface with a
scalar would change TWO things at once - the convention and the spatial
resolution - and the comparison would no longer isolate the convention. So the
routed bands are scaled by the ratio version B / version A, which keeps each
origin's relative danger and changes only the level. State it when quoting: B
is version A's geography at version B's price.

Reads:  data/final/externality.csv, injury_cost_by_mode.csv,
        injury_rate_by_mode.csv, route_risk_by_origin.csv,
        data/interim/ (via step 26's own loaders)
Writes: data/final/version_b_headline.csv
"""
import csv
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
FINAL = ROOT / "data" / "final"
INTERIM = ROOT / "data" / "interim"
OUT = FINAL / "version_b_headline.csv"


def load_step26():
    """Reuse step 26's build/mep/wmean rather than restating the model.

    A second implementation of MEP in a second file is how two numbers that
    should be identical drift apart - which is the exact failure this step
    exists to repair.
    """
    spec = importlib.util.spec_from_file_location("v26", SRC / "26_validate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["v26"] = m
    spec.loader.exec_module(m)
    return m


def read_csv(p):
    with p.open(encoding="utf8") as fh:
        return list(csv.DictReader(fh))


def main():
    v = load_step26()

    ext = {(r["metric"], r["mode"]): float(r["value"])
           for r in read_csv(FINAL / "externality.csv")}
    car_walk = ext[("car_involved_share_K", "walk")]
    car_bike = ext[("car_involved_share_K", "bike")]
    r_drive_a = ext[("r_drive_version_a", "drive")]
    r_drive_b = ext[("r_drive_version_b", "drive")]
    scale = r_drive_b / r_drive_a

    geoid, county, o, n = v.build()
    with (INTERIM / "acs_blockgroups.csv").open(encoding="utf8") as fh:
        popmap = {r["GEOID20"]: float(r["pop"]) for r in csv.DictReader(fh)}
    pop = np.array([popmap.get(g, 0.0) for g in geoid])

    _, r_transit, R_WALK, R_BIKE = v.read_rates()

    # routed drive risk, band by band, exactly as step 23 builds it
    rb = {r["GEOID20"]: r for r in read_csv(FINAL / "route_risk_by_origin.csv")}
    bands_a = np.zeros((len(v.BANDS), n))
    for bi, b in enumerate(v.BANDS):
        for k, g in enumerate(geoid):
            s = rb.get(g, {}).get(f"r_band{b}", "")
            bands_a[bi, k] = float(s) if s else r_drive_a

    base = v.mep(o, n, {})
    base_w = v.wmean(base, pop)

    def run(bands, rw, rbk, label):
        v.ROUTE_BANDS = bands
        m = v.mep(o, n, {"drive": "route", "transit": r_transit,
                         "walk": rw, "bike": rbk})
        w = v.wmean(m, pop)
        drop = w / base_w - 1.0
        print(f"  {label:<44}{w:>10,.1f}{drop:>10.1%}")
        return w, drop

    print("=" * 72)
    print("WHO CARRIES THE CRASH COST - A vs B, SAME MODEL, SAME NETWORK")
    print("=" * 72)
    print(f"  car-involved share of deaths   walk {car_walk:.2%}   "
          f"bike {car_bike:.2%}")
    print(f"  driving  ${r_drive_a:.4f}/PMT  ->  ${r_drive_b:.4f}/PMT "
          f"(x{scale:.3f}, applied to every routed band)")
    print(f"  walking  ${R_WALK[0]:.2f}  ->  ${R_WALK[0]*(1-car_walk):.4f}"
          f"     cycling  ${R_BIKE[0]:.2f}  ->  ${R_BIKE[0]*(1-car_bike):.4f}")
    print(f"\n  {'':<44}{'score':>10}{'change':>10}")
    print(f"  {'published, no crash term':<44}{base_w:>10,.1f}{'':>10}")
    a_w, a_d = run(bands_a, R_WALK[0], R_BIKE[0],
                   "A  charged to the person hurt  (ships)")
    b_w, b_d = run(bands_a * scale, R_WALK[0] * (1 - car_walk),
                   R_BIKE[0] * (1 - car_bike),
                   "B  charged to the driver")

    print(f"\n  Under B the loss is {abs(b_d) / abs(a_d):.2f}x version A's.")
    print("  Same model, same network, same data. Only the convention moves.")
    print("  Quote it as version A's geography at version B's price.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["metric", "value"])
        w.writerow(["base_population_weighted", f"{base_w:.4f}"])
        w.writerow(["version_a_score", f"{a_w:.4f}"])
        w.writerow(["version_a_drop", f"{a_d:.6f}"])
        w.writerow(["version_b_score", f"{b_w:.4f}"])
        w.writerow(["version_b_drop", f"{b_d:.6f}"])
        w.writerow(["b_over_a", f"{abs(b_d) / abs(a_d):.4f}"])
        w.writerow(["drive_rate_scale", f"{scale:.6f}"])
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
