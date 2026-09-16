"""
FINAL. Every audit finding applied.

FIXED SINCE THE LAST VERSION
  delay divided PERSON-hours by VEHICLE-miles -> 1.67x too large. Now
    person-miles on both sides.
  "55% crash share" was TTI's whole non-recurring pie (incidents + work
    zones + weather + special events). Deleted. Florida-specific shares added.
  walk denominator was FHWA "ATF" = walk + bike + ferry, not walk. Bikes
    removed at the project's own 15%.
  occupancy 1.67 was fitted to an AAA figure that does not exist in AAA 2019.
    Now 1.5, which is what MEP's OWN energy default back-solves to:
    33.7 kWh/gal / 25 mpg / 1.5 = 0.90 = MEP's published value.
  transit operating cost is ambiguous (0.85 tool / 1.05 paper). Both run.
"""
from math import exp

VSL, YEARS, POP = 13_700_000, 6.9, 3_468_871
VMT, OCC = 37.269685355e9, 1.5
DEATHS = {"car": 1582, "walk": 915, "bike": 277, "moto": 697}
PED_BY_CAR, BIKE_BY_CAR = 0.927, 0.920

ATF_TRIPS, BIKE_SHARE, WALK_MI = 356_500_000, 0.15, 0.7
BUS_K, BUS_MI = 12/10, 156_919_941_747/10

W_E, W_T, W_M = -0.5, -0.08, -0.5
DRIVE_E, DRIVE_C, TRANSIT_E = 0.90, 0.48, 0.65
TRANSIT_C = {"tool Table 10": 0.85, "2019 paper": 1.05}

TTI_HOURS = 112_436_000                      # TTI UMR 2025, Tampa-St Pete 2024
INCIDENT = {"FL urban freeway (TTI)": 0.05,
            "FL arterial (TTI)": 0.125,
            "FHWA national": 0.25}
FWY_S, ART_S, FWY_DELAY = 0.230, 0.404, 0.60

pm_drive = VMT * OCC
pm_walk  = ATF_TRIPS * (1 - BIKE_SHARE) * WALK_MI
L = lambda t: print(f"\n{'='*72}\n{t}\n{'='*72}")

L("1  EXPOSURE AND RATES")
r_drive = DEATHS["car"]/YEARS*VSL/pm_drive
r_walk  = DEATHS["walk"]/YEARS*VSL/pm_walk
r_bus   = BUS_K*VSL/BUS_MI
caused  = DEATHS["car"] + DEATHS["walk"]*PED_BY_CAR + DEATHS["bike"]*BIKE_BY_CAR
r_ext   = caused/YEARS*VSL/pm_drive
print(f"  {'mode':<9}{'deaths/yr':>11}{'person-mi/yr':>17}{'$/mile':>10}")
print(f"  {'drive':<9}{DEATHS['car']/YEARS:>11.0f}{pm_drive:>17,.0f}{r_drive:>10.4f}")
print(f"  {'walk':<9}{DEATHS['walk']/YEARS:>11.0f}{pm_walk:>17,.0f}{r_walk:>10.4f}")
print(f"  {'bus':<9}{BUS_K:>11.1f}{BUS_MI:>17,.0f}{r_bus:>10.4f}   national")
print(f"\n  walk/drive {r_walk/r_drive:>5.0f}x     drive/bus {r_drive/r_bus:>5.0f}x")
print(f"  externality: charging drive for the people it kills -> ${r_ext:.4f} "
      f"(+{r_ext/r_drive-1:.0%})")

L("2  CRASH DELAY  (person-hours / person-miles, units now match)")
pm_fwy, pm_art = VMT*FWY_S*OCC, VMT*ART_S*OCC
def dly(share, speed, fwy, art, mins=30):
    h = TTI_HOURS*share
    return (speed*mins/60)*(fwy*h*FWY_DELAY/pm_fwy*60 + art*h*(1-FWY_DELAY)/pm_art*60)
for lbl, s in INCIDENT.items():
    print(f"  {lbl:<26}{s:>6.1%}  ->  {dly(s,30,0.40,0.60):>5.2f} extra min on a 30-min drive")

L("3  MEP  -  score = e^(energy x-0.5 + minutes x-0.08 + dollars x-0.5)")
walk_base = exp(W_T*30)
walk_new  = exp(W_T*30 + W_M*r_walk)
print(f"  WALKING   {walk_base:.5f} -> {walk_new:.5f}   {walk_new/walk_base-1:+.1%}"
      f"   (no delay term: pedestrians do not queue)")
print(f"\n  {'transit cost':<16}{'crash share':<26}{'drive':>9}{'bus':>9}   leader")
out=[]
for tlbl, tc in TRANSIT_C.items():
    b_dr = exp(W_E*DRIVE_E + W_T*30 + W_M*DRIVE_C)
    b_bs = exp(W_E*TRANSIT_E + W_T*30 + W_M*tc)
    for ilbl, s in INCIDENT.items():
        dr = exp(W_E*DRIVE_E + W_T*(30+dly(s,30,.40,.60)) + W_M*(DRIVE_C+r_drive))
        bs = exp(W_E*TRANSIT_E + W_T*(30+dly(s,12,.05,.95)) + W_M*(tc+r_bus))
        lead = dr/bs-1
        out.append((tlbl,ilbl,dr/b_dr-1,bs/b_bs-1,lead,b_dr/b_bs-1))
        print(f"  {tlbl:<16}{ilbl:<26}{dr/b_dr-1:>+9.1%}{bs/b_bs-1:>+9.1%}   "
              f"{'driving' if lead>0 else 'the BUS'} by {abs(lead):.1%}")

L("4  WHAT HOLDS")
print(f"  ROBUST   Walking loses {1-walk_new/walk_base:.0%} of its score in every scenario.")
print(f"           MEP rates walking BEST here; {DEATHS['walk']} people died walking.")
print(f"           Independent of delay, transit cost, and occupancy.")
drv_wins = sum(1 for o in out if o[4] > 0)
print(f"\n  FRAGILE  Drive vs bus flips: driving leads in {drv_wins} of {len(out)} scenarios.")
print(f"           Do not quote a drive-vs-bus margin. Quote the range.")
print(f"\n  Driving loses {abs(sum(o[2] for o in out)/len(out)):.0%} on average, the bus {abs(sum(o[3] for o in out)/len(out)):.0%}. "
      f"The omission is not neutral.")
tot = sum(DEATHS.values())
print(f"\n  Regional bill ${tot/YEARS*VSL/1e9:.1f} B/yr, ${tot/YEARS*VSL/POP:,.0f} per resident.")
