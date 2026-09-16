"""
Does the fatality count in the cleaned Excel match the fatality count in the
figures? The statistics notebook recodes Non-Traffic Fatality to Fatality, but
the Excel file it reads from is never updated, so the two can disagree.
"""

import pandas as pd

df = pd.read_excel(
    r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx",
    engine="openpyxl",
)

print("Severity as stored in the Excel file:")
print(df["Severity"].value_counts().to_string())

print("\nSeverity_Detail values containing 'Fatal':")
mask = df["Severity_Detail"].astype(str).str.contains("Fatal", case=False, na=False)
print(df.loc[mask, "Severity_Detail"].value_counts().to_string())

nt = df["Severity_Detail"].astype(str).eq("Non-Traffic Fatality")
print(f"\nNon-Traffic Fatality rows: {nt.sum()}")

if nt.sum():
    print("\nHow the notebook stores them vs how the figures show them:")
    print(df.loc[nt, ["REPORT_NUMBER", "Year", "Severity",
                      "Severity_Detail", "Location", "Direction"]]
          .to_string(index=False))
    print(f"\n  Excel file says fatalities  = {(df['Severity'] == 'Fatality').sum()}")
    print(f"  Figures say fatalities      = "
          f"{(df['Severity'] == 'Fatality').sum() + nt.sum()}")
