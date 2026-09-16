"""
Does EPA's Smart Location Database actually serve D5AR / D5BR for Florida?

The whole rescope rests on this: if EPA already publishes jobs-reachable-in-45-
minutes by auto and by transit at block-group level, the routing engine is
unnecessary and the project's contribution narrows to the injury term.

Checks the layer exists, carries the fields, and returns real values for the five
study counties.
"""

import json
import urllib.parse
import urllib.request

BASE = ("https://geodata.epa.gov/arcgis/rest/services/OA/"
        "SmartLocationDatabase/MapServer")
UA = {"User-Agent": "tampa-mep/1.0 (research)"}
# FIPS: Hillsborough 057, Pinellas 103, Pasco 101, Hernando 053, Citrus 017
COUNTIES = ["057", "103", "101", "053", "017"]


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


print("SERVICE")
try:
    svc = fetch(f"{BASE}?f=json")
    print(f"  {svc.get('serviceDescription','')[:70]}")
    print(f"  {len(svc.get('layers', []))} layers")
except Exception as exc:
    raise SystemExit(f"  service unreachable: {exc}")

# Find a layer that carries the accessibility fields.
target = None
for lyr in svc.get("layers", []):
    lid = lyr["id"]
    try:
        meta = fetch(f"{BASE}/{lid}?f=json")
    except Exception:
        continue
    names = {f["name"].upper() for f in meta.get("fields", [])}
    if {"D5AR", "D5BR"} <= names:
        target = (lid, lyr["name"], meta)
        break

if not target:
    print("\n  D5AR/D5BR not found on any layer — check field naming")
    for lyr in svc.get("layers", [])[:20]:
        print(f"    {lyr['id']:>3}  {lyr['name'][:66]}")
    raise SystemExit

lid, lname, meta = target
print(f"\nLAYER {lid}: {lname}")
wanted = ["GEOID10", "GEOID20", "STATEFP", "COUNTYFP", "TOTPOP", "TOTEMP",
          "D5AR", "D5AE", "D5BR", "D5BE", "D1A", "D1B", "D2A_JPHH",
          "D3A", "D3B", "D4A", "D4C", "D4D", "AC_TOT", "AUTOOWN0", "AUTOOWN1"]
have = {f["name"].upper(): f["type"] for f in meta.get("fields", [])}
print(f"  {len(have)} fields total")
for w in wanted:
    print(f"    {'+' if w in have else '-'} {w}")

print(f"\nSAMPLE — the five study counties")
where = ("STATEFP='12' AND COUNTYFP IN ("
         + ",".join(f"'{c}'" for c in COUNTIES) + ")")
q = (f"{BASE}/{lid}/query?" + urllib.parse.urlencode({
    "where": where,
    "outFields": "COUNTYFP,TOTPOP,TOTEMP,D5AR,D5BR,D1B,D3B,D4C,AUTOOWN0",
    "returnGeometry": "false",
    "resultRecordCount": "5",
    "f": "json"}))
try:
    rows = fetch(q).get("features", [])
    for r in rows:
        a = r["attributes"]
        print(f"  county {a.get('COUNTYFP')}  pop {a.get('TOTPOP')}"
              f"  jobs45_auto {a.get('D5AR')}  jobs45_transit {a.get('D5BR')}")
except Exception as exc:
    print(f"  query failed: {exc}")

cnt = (f"{BASE}/{lid}/query?" + urllib.parse.urlencode({
    "where": where, "returnCountOnly": "true", "f": "json"}))
try:
    print(f"\n  block groups in study area: {fetch(cnt).get('count')}")
except Exception as exc:
    print(f"  count failed: {exc}")
