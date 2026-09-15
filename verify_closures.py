"""
Verify the three closure inputs are reachable before writing them into METHOD.md.

  NTD monthly ridership   closes "ridership, usage" in responsibility 5, and
                          supplies the transit occupancy the energy term needs -
                          bus energy per PASSENGER-mile is meaningless without it
  FL EV registrations     closes "emerging transportation technologies" in
                          responsibility 1
  Fuel economy / energy   the per-mode energy factors the dollar conversion uses
"""

import io
import json
import urllib.parse
import urllib.request

UA = {"User-Agent": "tampa-mep/1.0 (research)"}


def probe(url, label, want=None):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=90) as r:
            head = r.read(6000)
        txt = head.decode("utf-8", "replace")
        hit = "" if want is None else ("  contains " + want
                                       if want.lower() in txt.lower()
                                       else "  (marker not in first 6 KB)")
        print(f"  OK    {label:<44}{hit}")
        return txt
    except Exception as exc:
        print(f"  FAIL  {label:<44}{str(exc)[:46]}")
        return None


print("NTD RIDERSHIP  (data.transportation.gov, Socrata)")
# Annual service by agency - carries unlinked passenger trips and revenue miles,
# which together give the occupancy figure the energy term needs.
SVC = ("https://data.transportation.gov/resource/6y83-7vuw.json"
       "?$limit=5&$where=" + urllib.parse.quote("state='FL'"))
txt = probe(SVC, "annual service by agency, FL")
if txt:
    try:
        rows = json.loads(txt)
        if rows:
            print(f"        sample keys: {sorted(rows[0].keys())[:12]}")
    except Exception:
        pass

# Which Tampa Bay agencies actually report?
for agency in ("Hillsborough", "Pinellas"):
    q = ("https://data.transportation.gov/resource/6y83-7vuw.json?$limit=3"
         "&$where=" + urllib.parse.quote(f"agency like '%{agency}%'"))
    t = probe(q, f"agency search: {agency}", agency)
    if t:
        try:
            rows = json.loads(t)
            for r in rows[:2]:
                name = r.get("agency", "?")
                upt = r.get("unlinked_passenger_trips") or r.get("upt") or "?"
                vrm = r.get("vehicle_revenue_miles") or "?"
                print(f"        {name[:44]:<46}UPT {upt}  VRM {vrm}")
        except Exception:
            pass

print("\nEV REGISTRATIONS  (for the electrification scenario)")
probe("https://afdc.energy.gov/vehicle-registration?year=2024",
      "AFDC state EV registration counts")
probe("https://www.fdot.gov/agencyresources/webapps/", "FDOT web apps index")

print("\nENERGY FACTORS")
probe("https://www.eia.gov/totalenergy/data/monthly/", "EIA monthly energy review")
probe("https://afdc.energy.gov/data/10310", "AFDC average fuel economy by mode")
