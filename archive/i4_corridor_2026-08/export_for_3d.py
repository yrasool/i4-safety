"""
Export the I-4 crashes for the 3D scene.

The whole reason for going 3D: 350 of 648 crashes share a coordinate with another
crash, and one point holds 41. On a flat map those are one dot and 40 invisible
records. Given a vertical axis, a shared coordinate becomes a visible column and
every crash gets its own body in space - the defect turns into the subject.

So each crash carries a stack index (its floor in the column) alongside its
position, and the classification the scene colours by.
"""

import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "I4_StackedPoints.xlsx")
OUT = os.path.join(HERE, "i4_crashes_3d.json")


def classify(row):
    """Three families, which is what she asked to separate.

    Ramp crashes are the ones tagged to an interchange. Intersection crashes are
    mainline records whose junction coding says they happened at or because of a
    junction. Everything else is open mainline.
    """
    loc = str(row.get("Location") or "")
    if loc.startswith("Ramp"):
        return "ramp_bf" if "Branch" in loc else "ramp_mc"
    junc = str(row.get("Junction") or "").strip().lower()
    rel = str(row.get("Intersection_Related") or "").strip().upper()
    if rel == "Y" or "intersection" in junc or "ramp" in junc:
        return "intersection"
    return "mainline"


def main():
    df = pd.read_excel(SRC, engine="openpyxl")
    df = df.dropna(subset=["LATITUDE", "LONGITUDE"])

    # The stats notebook recodes this; carry it so the fatality count matches
    # the published figures (5, not the 4 stored in the spreadsheet).
    if "Severity_Detail" in df.columns:
        nt = df["Severity_Detail"].astype(str).eq("Non-Traffic Fatality")
        df.loc[nt, "Severity"] = "Fatality"

    df["klass"] = df.apply(classify, axis=1)

    key = (df["LATITUDE"].round(6).astype(str) + "," +
           df["LONGITUDE"].round(6).astype(str))
    df["coord_key"] = key
    df["stack_n"] = key.map(key.value_counts())
    # Floor number within its column, oldest first so the order is meaningful.
    sort_cols = [c for c in ["coord_key", "Year", "Date_Time"] if c in df.columns]
    df = df.sort_values(sort_cols)
    df["floor"] = df.groupby("coord_key").cumcount()

    def s(v):
        if pd.isna(v):
            return None
        return str(v)

    out = []
    for _, r in df.iterrows():
        out.append({
            "id": s(r.get("REPORT_NUMBER")),
            "lat": float(r["LATITUDE"]),
            "lon": float(r["LONGITUDE"]),
            "k": r["klass"],
            "f": int(r["floor"]),
            "n": int(r["stack_n"]),
            "sev": s(r.get("Severity")) or "No Injury",
            "dir": s(r.get("Direction")) or "",
            "yr": s(r.get("Year")) or "",
            "dt": s(r.get("Date_Time")) or "",
            "dow": s(r.get("Day_of_Week")) or "",
            "typ": s(r.get("Crash_Type")) or "",
            "hrm": s(r.get("First_Harmful_Event")) or "",
            "lgt": s(r.get("Light_Condition")) or "",
            "wea": s(r.get("Weather")) or "",
            "surf": s(r.get("Road_Surface")) or "",
            "mp": float(r["Milepost"]) if pd.notna(r.get("Milepost")) else None,
            "st": s(r.get("On_Street")) or "",
            "veh": int(r["Num_Vehicles"]) if pd.notna(r.get("Num_Vehicles")) else 0,
            "inj": int(r["Total_Injuries"]) if pd.notna(r.get("Total_Injuries")) else 0,
            "fat": int(r["Fatalities"]) if pd.notna(r.get("Fatalities")) else 0,
            "cmv": str(r.get("CMV_Involved") or "").upper().startswith("Y"),
            "spd": str(r.get("Speeding") or "").upper().startswith("Y"),
            "ldp": str(r.get("Lane_Departure") or "").upper().startswith("Y"),
        })

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))

    print(f"{len(out)} crashes")
    print(f"  distinct coordinates : {df['coord_key'].nunique()}")
    print(f"  tallest column       : {int(df['stack_n'].max())} crashes")
    print(f"  on a shared point    : {int((df['stack_n'] > 1).sum())}")
    print()
    for k, n in df["klass"].value_counts().items():
        print(f"  {k:<14}{n:>4}")
    print()
    for k, n in df["Severity"].value_counts().items():
        print(f"  {k:<16}{n:>4}")
    print(f"\nWrote {OUT}  ({os.path.getsize(OUT) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
