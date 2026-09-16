"""
What happened to the west (McIntosh) end of the corridor?

Rebuilds Steps 3 and 4 from the raw statewide CSV, then compares that set against
the 648 rows that survived into the cleaned Excel file, so we can say exactly how
many crashes were dropped and where along the corridor they sat.

Reads the source data read-only. Writes results here.
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = r"D:\Yusra\I4 Safety Ana;ysis"
RAW = os.path.join(FOLDER, "crash_roadway_vehicle_driver.csv")
CLEAN = os.path.join(FOLDER, "I4_BranchForbes_Crashes_Clean.xlsx")
OUT = os.path.join(HERE, "I4_DroppedCrashes.xlsx")

# Step 2 constants, copied from the notebook.
I4_LRS_ID = "10190000"
YEARS = [2021, 2022, 2023, 2024, 2025]
MAINLINE_LON_WEST = -82.2446584799336
MAINLINE_LON_EAST = -82.18669748126841
MAINLINE_LAT_MIN = 28.0225
MAINLINE_LAT_MAX = 28.0295
GORE_WEST = -82.23912020511585
GORE_EAST = -82.19359219348705

USECOLS = [
    "REPORT_NUMBER", "CRASH_YEAR", "MANAGING_DOT_DISTRICT", "LRS_ROADWAY",
    "LATITUDE", "LONGITUDE", "ON_STREET_ROAD_HIGHWAY", "S4_CRASH_SEVERITY",
    "JUNCTION_FLAG",
]


def main():
    print("Loading raw CSV (527 MB, only the columns needed) ...")
    df = pd.read_csv(RAW, usecols=USECOLS, low_memory=False)
    print(f"  {len(df):,} rows")

    # Step 3
    df["LRS_ROADWAY"] = df["LRS_ROADWAY"].astype(str)
    f = df[
        df["MANAGING_DOT_DISTRICT"].isin([7, 5]) & df["CRASH_YEAR"].isin(YEARS)
    ].copy()
    print(f"Step 3 (Districts 7+5, {min(YEARS)}-{max(YEARS)}): {len(f):,}")

    # Step 4
    box = f[
        (f["LRS_ROADWAY"] == I4_LRS_ID)
        & (f["LONGITUDE"] >= MAINLINE_LON_WEST)
        & (f["LONGITUDE"] <= MAINLINE_LON_EAST)
        & (f["LATITUDE"] >= MAINLINE_LAT_MIN)
        & (f["LATITUDE"] <= MAINLINE_LAT_MAX)
    ].copy()
    print(f"Step 4 (LRS + bounding box):                {len(box):,}")

    kept = pd.read_excel(CLEAN, engine="openpyxl")
    kept_ids = set(kept["REPORT_NUMBER"].astype(str).str.strip())
    print(f"Survived into the cleaned file:             {len(kept):,}")

    box["rid"] = box["REPORT_NUMBER"].astype(str).str.strip()
    box["kept"] = box["rid"].isin(kept_ids)
    dropped = box[~box["kept"]].copy()
    print(f"\nDropped between Step 4 and the final file:  {len(dropped):,}")

    # Where along the corridor did the drops happen?
    def zone(lon):
        if lon < GORE_WEST:
            return "1. West of west gore (McIntosh interchange)"
        if lon > GORE_EAST:
            return "3. East of east gore (Branch Forbes interchange)"
        return "2. Between the gores (kept mainline)"

    box["segment"] = box["LONGITUDE"].apply(zone)
    dropped["segment"] = dropped["LONGITUDE"].apply(zone)

    print("\n" + "=" * 70)
    print("BY CORRIDOR SEGMENT")
    print("=" * 70)
    tab = pd.crosstab(box["segment"], box["kept"], margins=True)
    tab.columns = [str(c) for c in tab.columns]
    print(tab.to_string())

    print("\nShare dropped, by segment:")
    for seg, grp in box.groupby("segment"):
        d = int((~grp["kept"]).sum())
        print(f"  {seg:48s} {d:4d} / {len(grp):4d}  ({d / len(grp) * 100:5.1f}%)")

    west = dropped[dropped["segment"].str.startswith("1.")]
    print(f"\nMcIntosh-end drops: {len(west)}")
    if len(west):
        print("\n  Severity of the dropped west-end crashes:")
        print(west["S4_CRASH_SEVERITY"].value_counts().to_string())
        print("\n  Their street names (top 12):")
        print(west["ON_STREET_ROAD_HIGHWAY"].astype(str).str[:46]
              .value_counts().head(12).to_string())
        print("\n  Junction coding:")
        print(west["JUNCTION_FLAG"].value_counts(dropna=False).to_string())

    dropped.to_excel(OUT, index=False, engine="openpyxl")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
