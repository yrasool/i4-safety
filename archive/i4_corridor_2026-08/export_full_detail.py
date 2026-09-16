"""
Export every usable field for the analyst map.

The 502 MB source is unreachable again, so this works from the preserved corridor
extract: 648 crashes, 62 fields. That is thin on rows but rich on columns - time,
light, weather, surface, crash type, first harmful event, contributing factors,
vehicle types, occupant detail - which is what an analyst actually filters on.

Everything that can be filtered gets exported. The map is only as interrogable as
this file.
"""

import json
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "I4_StackedPoints.xlsx")
OUT = os.path.join(HERE, "i4_full_detail.json")

FLAGS = [
    ("Speeding", "speeding"), ("Alcohol_Related", "alcohol"),
    ("Drug_Related", "drugs"), ("Distracted", "distracted"),
    ("Aggressive_Driving", "aggressive"), ("Lane_Departure", "lane departure"),
    ("Hit_and_Run", "hit and run"), ("CMV_Involved", "commercial vehicle"),
    ("Work_Zone", "work zone"), ("Intersection_Related", "intersection related"),
    ("Aging_Driver", "driver 65+"), ("Teen_Driver", "teen driver"),
    ("Unrestrained", "unrestrained"),
]


def yes(v):
    return str(v).strip().upper().startswith("Y") or str(v).strip() == "1"


def parse_hour(s):
    """Date_Time reads like '15-JAN-2021 12:55 AM'."""
    m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)", str(s), re.I)
    if not m:
        return None
    h = int(m.group(1)) % 12
    if m.group(3).upper() == "PM":
        h += 12
    return h


def parse_month(s):
    m = re.search(r"-([A-Z]{3})-", str(s).upper())
    if not m:
        return None
    months = ["JAN","FEB","MAR","APR","MAY","JUN",
              "JUL","AUG","SEP","OCT","NOV","DEC"]
    return months.index(m.group(1)) + 1 if m.group(1) in months else None


def clean(v):
    if pd.isna(v):
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def main():
    df = pd.read_excel(SRC, engine="openpyxl").dropna(subset=["LATITUDE", "LONGITUDE"])

    # The statistics notebook recodes this and the spreadsheet never learns.
    nt = df["Severity_Detail"].astype(str).eq("Non-Traffic Fatality")
    df.loc[nt, "Severity"] = "Fatality"

    key = (df["LATITUDE"].round(6).astype(str) + "," +
           df["LONGITUDE"].round(6).astype(str))
    df["stack_n"] = key.map(key.value_counts())
    df["coord_key"] = key
    df = df.sort_values(["coord_key", "Year"])
    df["floor"] = df.groupby("coord_key").cumcount()

    def zone(r):
        loc = str(r.get("Location") or "")
        if loc.startswith("Ramp"):
            return "ramp_bf" if "Branch" in loc else "ramp_mc"
        j = str(r.get("Junction") or "").lower()
        if yes(r.get("Intersection_Related")) or "intersection" in j:
            return "intersection"
        return "mainline"

    out = []
    for _, r in df.iterrows():
        rec = {
            "id": clean(r.get("REPORT_NUMBER")),
            "lat": float(r["LATITUDE"]), "lon": float(r["LONGITUDE"]),
            "k": zone(r), "f": int(r["floor"]), "n": int(r["stack_n"]),
            "sev": clean(r.get("Severity")) or "No Injury",
            "dir": clean(r.get("Direction")) or "Unknown",
            "yr": int(r["Year"]) if pd.notna(r.get("Year")) else None,
            "hr": parse_hour(r.get("Date_Time")),
            "mo": parse_month(r.get("Date_Time")),
            "dow": clean(r.get("Day_of_Week")),
            "dt": clean(r.get("Date_Time")),
            "typ": clean(r.get("Crash_Type")),
            "typs": clean(r.get("Crash_Type_Simple")),
            "hrm": clean(r.get("First_Harmful_Event")),
            "imp": clean(r.get("Impact_Type")),
            "lgt": clean(r.get("Light_Condition")),
            "dn": clean(r.get("Day_Night")),
            "wea": clean(r.get("Weather")),
            "surf": clean(r.get("Road_Surface")),
            "junc": clean(r.get("Junction")),
            "mp": float(r["Milepost"]) if pd.notna(r.get("Milepost")) else None,
            "spd": float(r["Posted_Speed"]) if pd.notna(r.get("Posted_Speed")) else None,
            "lanes": float(r["Num_Lanes"]) if pd.notna(r.get("Num_Lanes")) else None,
            "veh": int(r["Num_Vehicles"]) if pd.notna(r.get("Num_Vehicles")) else 0,
            "ppl": int(r["Num_Persons"]) if pd.notna(r.get("Num_Persons")) else 0,
            "inj": int(r["Total_Injuries"]) if pd.notna(r.get("Total_Injuries")) else 0,
            "fat": int(r["Fatalities"]) if pd.notna(r.get("Fatalities")) else 0,
            "v1": clean(r.get("V1_Body_Type")), "v2": clean(r.get("V2_Body_Type")),
            "st": clean(r.get("On_Street")),
            "fl": [lab for col, lab in FLAGS if yes(r.get(col))],
        }
        out.append(rec)

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))

    def spread(field):
        c = {}
        for r in out:
            v = r.get(field)
            if v is not None:
                c[v] = c.get(v, 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1])[:8])

    print(f"{len(out)} crashes -> {OUT} ({os.path.getsize(OUT)/1024:.0f} KB)")
    print(f"\nhour parsed:   {sum(1 for r in out if r['hr'] is not None)}")
    print(f"month parsed:  {sum(1 for r in out if r['mo'] is not None)}")
    for f in ["typs", "lgt", "wea", "surf", "dow", "v1"]:
        print(f"\n{f}: {spread(f)}")
    fl = {}
    for r in out:
        for x in r["fl"]:
            fl[x] = fl.get(x, 0) + 1
    print(f"\nflags: {dict(sorted(fl.items(), key=lambda kv: -kv[1]))}")


if __name__ == "__main__":
    main()
