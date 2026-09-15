"""
How much real spatial resolution does the crash file have?

648 rows is not 648 locations. Many coordinates are milepost lookups rather than
measured positions, so several crashes land on one point. This measures the true
resolution and shows what the data looks like when it is analysed at the scale it
actually has - by milepost segment rather than by point.

Reads source read-only. Writes results here.
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"
OUT = os.path.join(HERE, "I4_StackedPoints.xlsx")

# Milepost bin width, in miles. 0.1 mi = 528 ft, a common safety-study segment.
BIN_MI = 0.1


def main():
    df = pd.read_excel(SRC, engine="openpyxl").dropna(subset=["LATITUDE", "LONGITUDE"])

    key = (df["LATITUDE"].round(6).astype(str) + "," +
           df["LONGITUDE"].round(6).astype(str))
    df["coord_key"] = key
    df["stack"] = key.map(key.value_counts())

    n_rows = len(df)
    n_unique = df["coord_key"].nunique()

    print("=" * 66)
    print("TRUE SPATIAL RESOLUTION")
    print("=" * 66)
    print(f"  Crash records:      {n_rows}")
    print(f"  Distinct locations: {n_unique}")
    print(f"  Crashes per location (average): {n_rows / n_unique:.2f}")
    print(f"  Records sharing a coordinate:   "
          f"{int((df['stack'] > 1).sum())} ({(df['stack'] > 1).mean() * 100:.1f}%)")

    print("\nHow deep do the stacks go?")
    # One row per distinct location, then count how many locations hold N crashes.
    per_location = df.groupby("coord_key").size()
    for size, count in per_location.value_counts().sort_index().items():
        print(f"  {int(size):2d} crash(es) on one point : {int(count):4d} location(s)"
              f"   = {int(size) * int(count):4d} records")

    print("\nThe ten heaviest stacks:")
    top = (df.groupby("coord_key")
             .agg(crashes=("REPORT_NUMBER", "size"),
                  lat=("LATITUDE", "first"), lon=("LONGITUDE", "first"),
                  milepost=("Milepost", "first"), zone=("Location", "first"))
             .sort_values("crashes", ascending=False).head(10))
    print(top.to_string(float_format=lambda v: f"{v:.6f}"))

    # Are the stack points sitting on round mileposts? That would confirm they
    # are lookups against milepost markers rather than measured positions.
    print("\nMileposts of the heaviest stacks (looking for round numbers):")
    for mp in top["milepost"].tolist():
        frac = round(mp % 1, 3)
        note = "  <- lands on a tenth" if abs(frac * 10 - round(frac * 10)) < 1e-6 else ""
        print(f"  {mp:8.3f}{note}")

    # The honest unit of analysis: segments, not points.
    print("\n" + "=" * 66)
    print(f"CRASHES PER {BIN_MI} MILE SEGMENT (the resolution the data has)")
    print("=" * 66)
    df["seg"] = (df["Milepost"] / BIN_MI).round() * BIN_MI
    seg = (df.groupby("seg")
             .agg(crashes=("REPORT_NUMBER", "size"),
                  injuries=("Total_Injuries", "sum"),
                  fatal=("Fatalities", "sum"))
             .sort_index())
    for s, r in seg.iterrows():
        bar = "#" * min(int(r["crashes"]), 55)
        print(f"  MP {s:6.1f}  {int(r['crashes']):3d}  {bar}")

    print(f"\n  Segments with crashes: {len(seg)}")
    print(f"  Busiest segment: MP {seg['crashes'].idxmax():.1f} "
          f"with {int(seg['crashes'].max())} crashes")

    df.sort_values(["stack", "coord_key"], ascending=[False, True]).to_excel(
        OUT, index=False, engine="openpyxl")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
