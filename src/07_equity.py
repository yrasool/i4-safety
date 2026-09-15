"""
Step 07 - who has neither option.

This is the one spatial result in the project, and it survives review for a
specific reason: IT NEVER ROUTED THROUGH THE INJURY TERM. It is a statement
about mode availability, made from EPA accessibility data and Census vehicle
ownership. Nothing here is a recolouring of an injury constant.

Everything that did route through the injury term has been removed. The
previous version reported loss-of-access quintiles and a population-weighted
loss; step 06's docstring explains why those were an arithmetic identity.

The argument the numbers support:

  driving carries 48x the traffic-collision fatality cost per passenger-mile
  of a bus, so shifting a trip from car to bus is a large safety gain

  but 39.9% of block groups have no transit-reachable jobs at all

  and a household with no car in one of those places cannot make that shift.
  It walks - and walking is the most dangerous mode per mile in the region.

So the burden falls where the ALTERNATIVES are missing, not where the crashes
happen. That is what makes it survive the attribution problem: it is a claim
about what modes exist in a place, not about which roads are dangerous.

Writes: data/final/equity.csv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import MIDPERIOD_POP  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"


def main():
    df = pd.read_csv(FINAL / "transit_access.csv")
    sld = pd.read_parquet(INTERIM / "sld.parquet")

    df["GEOID20"] = df["GEOID20"].astype(str)
    own = sld[["GEOID20", "AutoOwn0", "AutoOwn1", "AutoOwn2p", "HH"]].copy()
    own["GEOID20"] = own["GEOID20"].astype(str)
    df = df.drop(columns=["AutoOwn0"]).merge(own, on="GEOID20", how="left")

    # Assert rather than default. An earlier version read these with
    # .get(default=0), which made the denominator AutoOwn0 itself and reported
    # a zero-car share of 100% in three of five quintiles - a table that still
    # looked monotonic and readable.
    for c in ("AutoOwn0", "AutoOwn1", "AutoOwn2p"):
        assert df[c].notna().all(), f"{c} has NA after join"
    assert df["AutoOwn1"].sum() > 0, "ownership bands empty - SLD changed"

    df["HH_est"] = df["AutoOwn0"] + df["AutoOwn1"] + df["AutoOwn2p"]

    # 0/0 in block groups with no households - industrial land, parks, water.
    # Filling 0 would file them as car-owning neighbourhoods and let them pull
    # the medians in a distributional claim.
    empty = df["HH_est"] == 0
    if empty.any():
        print(f"  excluding {empty.sum()} block groups with no households")
        df = df[~empty].copy()
    df["zero_car_share"] = df["AutoOwn0"] / df["HH_est"]

    share = df["AutoOwn0"].sum() / df["HH_est"].sum()
    assert 0.01 < share < 0.25, f"zero-car share {share:.1%} implausible"
    print(f"  region-wide zero-vehicle share {share:.1%}   "
          f"population {MIDPERIOD_POP:,} (Census PEP mid-period)")

    stranded = df[df["no_transit"]]
    n_str = stranded["AutoOwn0"].sum()
    tot0 = df["AutoOwn0"].sum()

    print(f"\n{'=' * 64}\nHOUSEHOLDS WITH NEITHER A CAR NOR A BUS\n{'=' * 64}")
    print(f"  {n_str:,.0f} of {tot0:,.0f} zero-vehicle households  "
          f"({n_str / tot0:.1%})")
    print(f"  across {len(stranded):,} block groups\n")

    by = pd.DataFrame({
        "zero_car_hh": df.groupby("county")["AutoOwn0"].sum(),
        "stranded": stranded.groupby("county")["AutoOwn0"].sum(),
        "no_transit_bg": df.groupby("county")["no_transit"].mean(),
    })
    by["stranded_share"] = by["stranded"] / by["zero_car_hh"]
    by = by.sort_values("stranded_share", ascending=False)
    print(f"  {'county':<14}{'0-car HH':>10}{'stranded':>10}"
          f"{'share':>8}{'BGs no transit':>16}")
    for c, row in by.iterrows():
        print(f"  {c:<14}{row.zero_car_hh:>10,.0f}{row.stranded:>10,.0f}"
              f"{row.stranded_share:>8.1%}{row.no_transit_bg:>15.1%}")

    print(f"""
  These households cannot take the safer mode, because taking it requires a
  bus that reaches a job. Their remaining option is walking. The project
  cannot price walking per mile - Tampa Bay publishes no walk exposure - but
  the break-even test puts it far above driving, and driving is already 48x
  the bus.

  This is the project's one spatial claim, and it is about which modes exist
  in a place. It makes no statement about which roads are dangerous, which is
  why it survives the attribution problem that removed the block-group map.
""")

    keep = ["GEOID20", "county", "TotPop", "AutoOwn0", "HH_est",
            "zero_car_share", "no_transit", "transit_share", "A_drive",
            "A_transit"]
    df[keep].to_csv(FINAL / "equity.csv", index=False)
    print(f"wrote {FINAL / 'equity.csv'}")


if __name__ == "__main__":
    main()
