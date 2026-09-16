"""Field names in the NTD annual service dataset, for the transit occupancy term."""

import json
import urllib.parse
import urllib.request

BASE = "https://data.transportation.gov/resource/6y83-7vuw.json"
UA = {"User-Agent": "tampa-mep/1.0 (research)"}

where = urllib.parse.quote("agency like '%Hillsborough Area%'")
url = f"{BASE}?$limit=3&$where={where}"

req = urllib.request.Request(url, headers=UA)
rows = json.load(urllib.request.urlopen(req, timeout=90))

print(f"{len(rows)} rows\n\nFIELDS")
for k in sorted(rows[0]):
    print(f"  {k:<44}{str(rows[0][k])[:40]}")

# The two numbers the energy term needs: passenger trips and revenue miles.
print("\nOCCUPANCY-RELEVANT")
for k in sorted(rows[0]):
    kl = k.lower()
    if any(t in kl for t in ("passenger", "upt", "revenue", "mile", "hour",
                             "capacity", "year", "mode")):
        for r in rows:
            print(f"  {k:<44}{r.get(k)}")
        break
print()
for r in rows:
    print("  ", {k: v for k, v in r.items()
                 if k.lower() in ("year", "mode", "unlinked_passenger_trips",
                                  "vehicle_revenue_miles", "upt", "vrm",
                                  "passenger_miles_traveled", "pmt")})
