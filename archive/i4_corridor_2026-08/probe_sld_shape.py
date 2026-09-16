"""
Shape of the SLD extract before it becomes the project's spine.

Two things matter and neither is cosmetic:

  -99999 is EPA's no-data sentinel, not a value. Averaging it in would drag
  every transit figure to nonsense. It also carries real meaning here - a block
  group with no transit-reachable jobs is the "the bus doesn't reach one at all"
  case, which is a finding, not a gap to fill.

  Field naming shifts between SLD releases (GEOID10 vs GEOID20, TOTPOP vs
  variants), so confirm what actually holds population before relying on it.
"""

import json
import urllib.parse
import urllib.request

BASE = ("https://geodata.epa.gov/arcgis/rest/services/OA/"
        "SmartLocationDatabase/MapServer/1")
UA = {"User-Agent": "tampa-mep/1.0 (research)"}
COUNTIES = ["057", "103", "101", "053", "017"]
NAMES = {"057": "Hillsborough", "103": "Pinellas", "101": "Pasco",
         "053": "Hernando", "017": "Citrus"}
STUDY = ("STATEFP='12' AND COUNTYFP IN ("
         + ",".join(f"'{c}'" for c in COUNTIES) + ")")


def fetch(params):
    url = f"{BASE}/query?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def count(where):
    return fetch({"where": where, "returnCountOnly": "true", "f": "json"})["count"]


print("NO-DATA SENTINEL  (-99999)")
total = count(STUDY)
for fld in ("D5AR", "D5BR", "D5AE", "D5BE"):
    n = count(f"{STUDY} AND {fld} = -99999")
    print(f"  {fld:<6}{n:>6} of {total}  ({n / total:5.1%})")

print("\n  by county, D5BR (transit)")
for c in COUNTIES:
    w = f"STATEFP='12' AND COUNTYFP='{c}'"
    tot, nd = count(w), count(f"{w} AND D5BR = -99999")
    print(f"    {NAMES[c]:<14}{nd:>5} of {tot:>4} no transit  ({nd / tot:5.1%})")

# Which field actually holds population? Grab one row whole and look.
print("\nPOPULATION / EXPOSURE FIELDS")
row = fetch({"where": f"{STUDY} AND COUNTYFP='057'", "outFields": "*",
             "returnGeometry": "false", "resultRecordCount": "1",
             "f": "json"})["features"][0]["attributes"]
for k in sorted(row):
    if any(t in k.upper() for t in ("POP", "EMP", "HH", "GEOID", "AREA",
                                    "AUTOOWN", "WORKERS")):
        print(f"  {k:<18}{row[k]}")

print("\nDISTRIBUTION  (valid rows only)")
for fld in ("D5AR", "D5BR"):
    stats = fetch({
        "where": f"{STUDY} AND {fld} <> -99999",
        "outStatistics": json.dumps([
            {"statisticType": t, "onStatisticField": fld,
             "outStatisticFieldName": t} for t in ("min", "max", "avg")]),
        "f": "json"})["features"][0]["attributes"]
    print(f"  {fld:<6}min {stats['min']:>10,.0f}   "
          f"avg {stats['avg']:>10,.0f}   max {stats['max']:>10,.0f}")
