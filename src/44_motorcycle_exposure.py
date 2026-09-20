"""Motorcycle exposure for District 7, from FDOT's own classification counts.

The gap this closes: motorbikes killed 697 people in these five counties and had
no per-mile rate, because no agency appeared to publish how far motorcycles are
ridden. FLHSMV publishes registrations and endorsements - how many bikes exist,
not how far they go - which is the wrong denominator and would have understated
the rate several-fold.

FDOT does count them. In the federal 13-class scheme Class 1 is motorcycles, and
FDOT's Traffic Characteristics Inventory holds an annual class distribution for
every classification site. So:

    Class 1 share of traffic  x  vehicle-miles travelled  =  motorcycle miles

The share is weighted by each site's AADT, so a site on a busy road counts for
more than one on a quiet road - an unweighted mean of site percentages would let
a single rural counter move the county.

KNOWN BIAS, AND ITS DIRECTION: loop and axle classifiers are documented to miss
single-track vehicles, so Class 1 is an undercount. Undercounted miles means the
dollars-per-mile rate computed here is too HIGH, not too low. Treated as an
upper bound, never as a measurement.
"""
from pathlib import Path
import os
import sys

import pandas as pd
import pyodbc

ROOT = Path(__file__).resolve().parents[1]
MDB = ROOT / "data" / "raw" / "fdot_fti" / "fti_2025.mdb"
OUT = ROOT / "data" / "processed" / "motorcycle_exposure.csv"

# District 7 - the five counties of this study, by FDOT county code
D7 = {"02": "Citrus", "08": "Hernando", "10": "Hillsborough",
      "14": "Pasco", "15": "Pinellas"}

# Daily vehicle-miles travelled, thousands, from FDOT's 2025 NHS report
# (State Highway System roads on the National Highway System).
DVMT_THOUSANDS = {"Citrus": 1773.684712, "Hernando": 2784.619814,
                  "Hillsborough": 24238.454419, "Pasco": 7424.65573,
                  "Pinellas": 9295.444771}


def connect(path):
    if not path.exists():
        sys.exit(f"missing {path} - download fti_2025.zip from FDOT first")
    return pyodbc.connect(
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ="
        + str(path.resolve()) + ";", autocommit=True)


def main():
    cn = connect(MDB)

    cls = pd.read_sql("SELECT YEAR, COUNTY, SITE, CLASS, DESCRIPTION, "
                      "PERCENTAGE FROM [ANNUAL_VEHICLE_CLASSIFICATION]", cn)
    aadt = pd.read_sql("SELECT COUNTY, SITE, YEAR, ASCAADT, DSCAADT "
                       "FROM [ALL_SITES_AADT]", cn)

    for df in (cls, aadt):
        df["COUNTY"] = df["COUNTY"].astype(str).str.strip().str.zfill(2)
        df["SITE"] = df["SITE"].astype(str).str.strip()
        df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")

    cls["CLASS"] = pd.to_numeric(cls["CLASS"], errors="coerce")
    cls["PERCENTAGE"] = pd.to_numeric(cls["PERCENTAGE"], errors="coerce")

    year = int(cls["YEAR"].max())
    print(f"classification year: {year}")

    moto = cls[(cls.CLASS == 1) & (cls.YEAR == year) & cls.COUNTY.isin(D7)]
    print(f"Class 1 rows in District 7: {len(moto)}  "
          f"(description: {moto.DESCRIPTION.dropna().unique()[:1]})")

    # a site's own traffic, both directions, so the share is weighted by
    # how much traffic that counter actually sees
    aadt["site_aadt"] = (pd.to_numeric(aadt.ASCAADT, errors="coerce").fillna(0)
                         + pd.to_numeric(aadt.DSCAADT, errors="coerce").fillna(0))
    a = aadt[aadt.YEAR == year].groupby(["COUNTY", "SITE"], as_index=False)["site_aadt"].max()

    m = moto.merge(a, on=["COUNTY", "SITE"], how="left")
    unmatched = m.site_aadt.isna().sum()
    m = m.dropna(subset=["site_aadt", "PERCENTAGE"])
    m = m[m.site_aadt > 0]

    rows = []
    for code, name in sorted(D7.items(), key=lambda kv: kv[1]):
        g = m[m.COUNTY == code]
        if g.empty:
            rows.append({"county": name, "sites": 0})
            continue
        share = (g.PERCENTAGE * g.site_aadt).sum() / g.site_aadt.sum()
        dvmt = DVMT_THOUSANDS[name] * 1_000          # vehicle-miles a day
        rows.append({"county": name, "sites": len(g),
                     "moto_pct_aadt_weighted": round(share, 4),
                     "moto_pct_unweighted": round(g.PERCENTAGE.mean(), 4),
                     "dvmt_all_vehicles": round(dvmt),
                     "moto_vmt_per_day": round(dvmt * share / 100),
                     "moto_vmt_per_year": round(dvmt * share / 100 * 365)})

    out = pd.DataFrame(rows)
    tot_dvmt = out.dvmt_all_vehicles.sum()
    tot_moto = out.moto_vmt_per_year.sum()
    region_share = out.moto_vmt_per_day.sum() / tot_dvmt * 100

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"\nsites unmatched to an AADT record: {unmatched}")
    print(out.to_string(index=False))
    print(f"\nDistrict 7 motorcycle share of traffic : {region_share:.3f}%")
    print(f"District 7 motorcycle vehicle-miles/yr : {tot_moto/1e6:,.1f} million")
    print(f"District 7 all-vehicle miles/yr        : {tot_dvmt*365/1e9:,.2f} billion")


if __name__ == "__main__":
    main()


# ── the rate this exposure makes possible ─────────────────────────────────
#
# One caution decides whether this number means anything: the DVMT above is
# State Highway System roads on the National Highway System - a SUBSET of the
# roads people ride on. The study's own exposure for all modes is 56bn
# passenger-miles across ALL roads, so the SHS-NHS subset covers only part of
# travel. Dividing casualties from every road by miles from some roads would
# overstate the rate. Both bounds are printed rather than one false point.

KILLED, SERIOUS = 697, 2656          # District 7 motorbike casualties
YEARS = 83 / 12                      # Jan 2019 - Nov 2025
VSL, VSI = 13.7e6, 1.30e6            # USDOT values, as used everywhere else
OCC_MOTO = 1.05                      # 95% of FL rider deaths are the driver
ALL_MODE_PMT = 56e9                  # the study's own all-roads exposure


def rate(moto_vmt_year, dvmt_all_year):
    cost = (KILLED / YEARS * VSL + SERIOUS / YEARS * VSI)
    pmt_shs = moto_vmt_year * OCC_MOTO
    # what share of all travel the SHS-NHS subset represents, in the study's
    # own units, so the two denominators are comparable
    shs_pmt = dvmt_all_year * 1.502
    coverage = shs_pmt / ALL_MODE_PMT
    print(f"\nmotorbike harm            : ${cost/1e9:,.2f}bn a year")
    print(f"SHS-NHS share of all travel: {coverage*100:.1f}%")
    print(f"upper bound (SHS miles only): ${cost/pmt_shs:,.2f} per passenger-mile")
    print(f"scaled to all roads         : ${cost/(pmt_shs/coverage):,.2f} per passenger-mile")
    print("classifiers undercount single-track vehicles, so both are high.")


if __name__ == "__main__":
    import pandas as _pd
    _d = _pd.read_csv(OUT)
    rate(_d.moto_vmt_per_year.sum(), _d.dvmt_all_vehicles.sum() * 365)
