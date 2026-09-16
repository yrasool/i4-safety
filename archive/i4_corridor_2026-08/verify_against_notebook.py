"""
Does the inspector map reproduce the notebook's own numbers?

The map is only trustworthy if it agrees with the pipeline it was built from, so
every figure the notebooks and Word reports publish is asserted here against the
data the map actually renders. Any disagreement is a bug in the map, not a
finding about the data.

Decision on record: follow the notebook, not the methodology PDF. That means the
McIntosh-to-Branch-Forbes box, 2021-2025, the gore trim, and the stats notebook's
Non-Traffic-Fatality recode.

Read-only on the source. Prints a pass/fail table.
"""

import json
import os
import re

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"
MAP = os.path.join(HERE, "I4_Crash_Inspector_v2.html")

results = []


def check(label, actual, expected, note=""):
    ok = actual == expected
    results.append((ok, label, actual, expected, note))
    return ok


def main():
    df = pd.read_excel(SRC, engine="openpyxl")

    # ---- what the notebook pipeline produced -------------------------------
    check("Total crashes", len(df), 648)
    check("Mainline", int((df["Location"] == "Mainline").sum()), 609)
    check("Ramp - Branch Forbes Rd",
          int((df["Location"] == "Ramp - Branch Forbes Rd").sum()), 34)
    check("Ramp - McIntosh Rd",
          int((df["Location"] == "Ramp - McIntosh Rd").sum()), 5)

    check("Westbound (all)", int((df["Direction"] == "Westbound").sum()), 348)
    check("Eastbound (all)", int((df["Direction"] == "Eastbound").sum()), 300)

    main_df = df[df["Location"] == "Mainline"]
    check("Westbound (mainline)",
          int((main_df["Direction"] == "Westbound").sum()), 336,
          "docs say 336")
    check("Eastbound (mainline)",
          int((main_df["Direction"] == "Eastbound").sum()), 273,
          "docs say 273")

    check("Serious Injury", int((df["Severity"] == "Serious Injury").sum()), 17)
    check("Fatality (Excel, before recode)",
          int((df["Severity"] == "Fatality").sum()), 4,
          "docs text says 4")

    # The stats notebook's recode - this is what the published figures show.
    nt = df["Severity_Detail"].astype(str).eq("Non-Traffic Fatality")
    check("Fatality (after notebook recode)",
          int((df["Severity"] == "Fatality").sum() + nt.sum()), 5,
          "figures show 5; map uses this")

    by_year = df.groupby("Year").size().to_dict()
    for yr, exp in [(2021, 140), (2022, 115), (2023, 127), (2024, 134), (2025, 132)]:
        check(f"Year {yr}", int(by_year.get(yr, 0)), exp)

    check("Year range low", int(df["Year"].min()), 2021)
    check("Year range high", int(df["Year"].max()), 2025)

    # ---- what the map actually holds --------------------------------------
    if os.path.exists(MAP):
        with open(MAP, encoding="utf-8") as fh:
            html = fh.read()
        m = re.search(r"const DATA\s*=\s*(\[.*?\]);\s*\nconst DROPPED", html, re.S)
        if m:
            data = json.loads(m.group(1))
            check("Map: records rendered", len(data), 648)
            check("Map: fatalities rendered",
                  sum(1 for d in data if d["sev"] == "Fatality"), 5,
                  "recode applied")
            check("Map: mainline rendered",
                  sum(1 for d in data if d["zone"] == "Mainline"), 609)
            check("Map: westbound rendered",
                  sum(1 for d in data if d["dir"] == "Westbound"), 348)
            years = sorted({d["year"] for d in data if d["year"]})
            check("Map: years rendered", years,
                  ["2021", "2022", "2023", "2024", "2025"])
        else:
            results.append((False, "Map: could not parse embedded data", "-", "-", ""))
    else:
        results.append((False, "Map: file not found", "-", "-", ""))

    # ---- report ------------------------------------------------------------
    width = max(len(r[1]) for r in results) + 2
    print("=" * (width + 34))
    print("MAP vs NOTEBOOK".ljust(width) + "actual    expected  ")
    print("=" * (width + 34))
    for ok, label, actual, expected, note in results:
        mark = "PASS" if ok else "FAIL"
        print(f"  {mark}  {label:<{width}} {str(actual):>8}  {str(expected):>8}"
              + (f"   {note}" if note else ""))

    n_fail = sum(1 for r in results if not r[0])
    print("=" * (width + 34))
    print(f"  {len(results) - n_fail} passed, {n_fail} failed")
    if n_fail == 0:
        print("\n  The map reproduces the notebook exactly.")


if __name__ == "__main__":
    main()
