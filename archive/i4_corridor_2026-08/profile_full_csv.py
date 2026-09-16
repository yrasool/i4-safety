"""
What is actually in the 527 MB crash extract?

The corridor study uses 648 of its 602,110 rows. Before proposing anything built
on the rest, establish what the rest covers: which districts, counties, years and
road types, and how many records carry usable geometry.

Read-only. Loads a narrow column subset so it is quick.
"""

import os

import pandas as pd

RAW = r"D:\Yusra\I4 Safety Ana;ysis\crash_roadway_vehicle_driver.csv"

COLS = [
    "REPORT_NUMBER", "CRASH_YEAR", "MANAGING_DOT_DISTRICT", "COUNTY",
    "LRS_ROADWAY", "LRS_MILEPOINT", "LATITUDE", "LONGITUDE",
    "S4_CRASH_SEVERITY", "FUNC_CLASS", "ON_STREET_ROAD_HIGHWAY",
    "S4_IS_CMV_INVOLVED", "RURAL_OR_URBAN",
]


def main():
    print("Loading (narrow columns) ...")
    avail = pd.read_csv(RAW, nrows=1).columns.tolist()
    use = [c for c in COLS if c in avail]
    missing = [c for c in COLS if c not in avail]
    if missing:
        print(f"  not present: {missing}")

    df = pd.read_csv(RAW, usecols=use, low_memory=False)
    print(f"  {len(df):,} rows x {len(avail)} columns in file\n")

    print("=" * 66)
    print("SCOPE")
    print("=" * 66)

    print(f"\nYears: {int(df['CRASH_YEAR'].min())} - {int(df['CRASH_YEAR'].max())}")
    print(df["CRASH_YEAR"].value_counts().sort_index().to_string())

    print("\nFDOT districts:")
    print(df["MANAGING_DOT_DISTRICT"].value_counts(dropna=False).sort_index().to_string())

    if "COUNTY" in df.columns:
        print(f"\nCounties: {df['COUNTY'].nunique()}")
        print(df["COUNTY"].value_counts().head(12).to_string())

    print(f"\nDistinct LRS routes: {df['LRS_ROADWAY'].astype(str).nunique():,}")
    print("Top 12 routes by crash count:")
    print(df["LRS_ROADWAY"].astype(str).value_counts().head(12).to_string())

    print("\n" + "=" * 66)
    print("GEOMETRY USABILITY")
    print("=" * 66)
    has_xy = df[["LATITUDE", "LONGITUDE"]].notna().all(axis=1)
    print(f"  With coordinates:      {int(has_xy.sum()):,} "
          f"({has_xy.mean() * 100:.1f}%)")

    has_mp = df["LRS_MILEPOINT"].notna() & (df["LRS_MILEPOINT"] > 0)
    print(f"  With usable milepoint: {int(has_mp.sum()):,} "
          f"({has_mp.mean() * 100:.1f}%)")

    # The headline number for a data-quality study: how much of the state's
    # crash geometry is a shared point rather than a measured position?
    geo = df[has_xy].copy()
    key = (geo["LATITUDE"].round(6).astype(str) + "," +
           geo["LONGITUDE"].round(6).astype(str))
    counts = key.value_counts()
    geo["stack"] = key.map(counts)

    print(f"\n  Distinct coordinates:  {len(counts):,}")
    print(f"  Crashes per coordinate (mean): {len(geo) / len(counts):.2f}")
    for thresh in (2, 5, 10, 25, 50):
        n = int((geo["stack"] >= thresh).sum())
        print(f"  On a point shared by {thresh:>2}+ crashes: {n:>7,} "
              f"({n / len(geo) * 100:5.1f}%)")

    print("\n  Ten most-reused coordinates statewide:")
    top = counts.head(10)
    for coord, n in top.items():
        sample = geo[key == coord]
        road = sample["ON_STREET_ROAD_HIGHWAY"].astype(str).mode()
        road = road.iloc[0][:40] if len(road) else "?"
        lrs = sample["LRS_ROADWAY"].astype(str).mode()
        lrs = lrs.iloc[0] if len(lrs) else "?"
        yrs = f"{int(sample['CRASH_YEAR'].min())}-{int(sample['CRASH_YEAR'].max())}"
        print(f"    {coord:>26}  {n:>5} crashes  LRS {lrs:<10} {yrs}  {road}")

    print("\n" + "=" * 66)
    print("SEVERITY")
    print("=" * 66)
    print(df["S4_CRASH_SEVERITY"].value_counts(dropna=False).to_string())

    if "S4_IS_CMV_INVOLVED" in df.columns:
        cmv = df["S4_IS_CMV_INVOLVED"].astype(str).str.upper().eq("Y")
        print(f"\nCommercial vehicle involved: {int(cmv.sum()):,} "
              f"({cmv.mean() * 100:.1f}%)")


if __name__ == "__main__":
    main()
