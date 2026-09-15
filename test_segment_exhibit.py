"""
Is a milepost concentration figure publishable, or would it publish an artifact?

The report's crash-rate table treats the mainline as two segments, 3.04 mi
eastbound and 3.08 mi westbound. A milepost figure would add what that table
cannot show: where inside those three miles the crashes actually sit.

The risk is that Milepost is snapped the same way the coordinates are. If a
concentration is really one milepost marker collecting records, publishing it as
a hotspot would be wrong. This measures how much of each peak is contributed by
shared coordinates.

Read-only on the source.
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"
OUT = os.path.join(HERE, "I4_SegmentAudit.xlsx")

BIN = 0.1
STACK_WARN = 10


def main():
    df = pd.read_excel(SRC, engine="openpyxl").dropna(subset=["LATITUDE", "LONGITUDE"])

    key = (df["LATITUDE"].round(6).astype(str) + "," +
           df["LONGITUDE"].round(6).astype(str))
    df["stack"] = key.map(key.value_counts())
    df["suspect"] = df["stack"] >= STACK_WARN

    valid = df[df["Milepost"].notna() & (df["Milepost"] > 1)].copy()
    print(f"Records with a usable Milepost: {len(valid)} of {len(df)}")

    valid["seg"] = (valid["Milepost"] / BIN).round() * BIN

    seg = valid.groupby("seg").agg(
        crashes=("REPORT_NUMBER", "size"),
        suspect=("suspect", "sum"),
        distinct_coords=("stack", lambda s: len(s)),
    )
    seg["clean"] = seg["crashes"] - seg["suspect"]
    seg["pct_suspect"] = (seg["suspect"] / seg["crashes"] * 100).round(1)

    # How many genuinely distinct locations sit behind each segment's count?
    nunique = valid.groupby("seg").apply(
        lambda g: (g["LATITUDE"].round(6).astype(str) + "," +
                   g["LONGITUDE"].round(6).astype(str)).nunique())
    seg["locations"] = nunique

    print("\n" + "=" * 74)
    print("EVERY SEGMENT: total, how much is from suspect coordinates, and")
    print("how many distinct locations actually underlie the count")
    print("=" * 74)
    print(f"  {'MP':>6}  {'total':>5}  {'clean':>5}  {'suspect':>7}  "
          f"{'%susp':>6}  {'locs':>4}")
    for s, r in seg.sort_index().iterrows():
        flag = "  <-- mostly one point" if r["pct_suspect"] >= 50 else ""
        print(f"  {s:6.1f}  {int(r['crashes']):5d}  {int(r['clean']):5d}  "
              f"{int(r['suspect']):7d}  {r['pct_suspect']:6.1f}  "
              f"{int(r['locations']):4d}{flag}")

    print("\n" + "=" * 74)
    print("TOP 5 BY RAW COUNT vs TOP 5 AFTER REMOVING SUSPECT COORDINATES")
    print("=" * 74)
    raw = seg.sort_values("crashes", ascending=False).head(5)
    cln = seg.sort_values("clean", ascending=False).head(5)
    print(f"  {'raw':<22}{'clean':<22}")
    for (a, ra), (b, rb) in zip(raw.iterrows(), cln.iterrows()):
        print(f"  MP {a:5.1f}  {int(ra['crashes']):3d}        "
              f"MP {b:5.1f}  {int(rb['clean']):3d}")

    # Does the ranking survive? That is the publishability test.
    same = list(raw.index[:3]) == list(cln.index[:3])
    print(f"\n  Top 3 unchanged after cleaning: {same}")

    total_susp = int(seg["suspect"].sum())
    print(f"  Crashes on suspect coordinates: {total_susp} "
          f"({total_susp / len(valid) * 100:.1f}%)")

    seg.to_excel(OUT, engine="openpyxl")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
