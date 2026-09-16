"""
Did stacked points cause ramp crashes to be missed during manual tagging?

The test: crashes sharing an identical coordinate are, by definition, at the same
place. They must therefore carry the same zone. Any coordinate holding both a
"Ramp" and a "Mainline" tag is an inconsistency - and the most likely cause is
that only the top dot was visible on the map the tagging was done from.

Read-only on the source. Writes results here.
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"
OUT = os.path.join(HERE, "I4_TaggingConflicts.xlsx")


def main():
    df = pd.read_excel(SRC, engine="openpyxl").dropna(subset=["LATITUDE", "LONGITUDE"])

    df["coord_key"] = (df["LATITUDE"].round(6).astype(str) + "," +
                       df["LONGITUDE"].round(6).astype(str))
    df["is_ramp"] = df["Location"].astype(str).str.startswith("Ramp")

    print("=" * 68)
    print("TEST: do crashes at the SAME coordinate carry the SAME zone?")
    print("=" * 68)

    g = df.groupby("coord_key").agg(
        n=("REPORT_NUMBER", "size"),
        n_ramp=("is_ramp", "sum"),
        zones=("Location", lambda s: sorted(set(s))),
    )
    g["n_main"] = g["n"] - g["n_ramp"]

    shared = g[g["n"] > 1]
    mixed = g[(g["n_ramp"] > 0) & (g["n_main"] > 0)]

    print(f"\n  Locations holding more than one crash: {len(shared)}")
    print(f"  Locations holding BOTH ramp and mainline tags: {len(mixed)}")

    if len(mixed) == 0:
        print("\n  No contradictions. Tagging is internally consistent.")
    else:
        print(f"\n  {int(mixed['n_main'].sum())} crashes are tagged Mainline while "
              f"sitting on the exact\n  coordinate of a crash tagged Ramp.")
        print("\n  Conflicting locations:")
        for k, r in mixed.iterrows():
            print(f"    {k}   {int(r['n'])} crashes "
                  f"({int(r['n_ramp'])} ramp / {int(r['n_main'])} mainline)")
            print(f"       zones present: {r['zones']}")

    # How exposed was each tagged ramp crash - was it alone, or in a pile?
    print("\n" + "=" * 68)
    print("VISIBILITY OF THE 39 MANUALLY TAGGED RAMP CRASHES")
    print("=" * 68)
    ramps = df[df["is_ramp"]].copy()
    ramps["stack"] = ramps["coord_key"].map(df["coord_key"].value_counts())
    print(f"\n  Tagged ramp crashes: {len(ramps)}")
    print(f"  Sitting alone on their coordinate: "
          f"{int((ramps['stack'] == 1).sum())}")
    print(f"  Sharing with other crashes:        "
          f"{int((ramps['stack'] > 1).sum())}")

    print("\n  By interchange:")
    for zone, grp in ramps.groupby("Location"):
        print(f"    {zone:26s} {len(grp):3d} tagged, "
              f"{int((grp['stack'] > 1).sum()):3d} of them on a shared point")

    # The reverse exposure: untagged crashes hiding beneath tagged ramp dots.
    ramp_coords = set(ramps["coord_key"])
    buried = df[df["coord_key"].isin(ramp_coords) & ~df["is_ramp"]]
    print(f"\n  Untagged crashes sharing a coordinate with a tagged ramp: "
          f"{len(buried)}")

    if len(buried):
        cols = ["REPORT_NUMBER", "Year", "Location", "Direction", "Severity",
                "On_Street", "Milepost", "coord_key"]
        print("\n" + buried[cols].to_string(index=False))
        buried.to_excel(OUT, index=False, engine="openpyxl")
        print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
