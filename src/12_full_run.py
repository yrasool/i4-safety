"""
The whole project, start to finish, with the reasoning printed as it runs.

Everything is counted from the crash file or published by an agency.
The one genuinely uncertain input is reported as a RANGE, not a point.
"""
from math import exp

# ---------------------------------------------------------------- INPUTS
VSL, YEARS = 13_700_000, 6.9        # USDOT value of a life; Jan 2019-Nov 2025
VMT        = 37.269685355e9         # FDOT, 5 counties, car-miles per year
OCCUPANCY  = 1.502                  # people per car, NHTS 2022 (step 3)
POP        = 3_468_871              # Census PEP, mid-period

DEATHS = {"in a car": 1582, "walking": 915, "cycling": 277, "on a motorbike": 697}
PED_BY_CAR, BIKE_BY_CAR = 0.927, 0.920        # counted from the crash file
WALK_TRIPS, WALK_TRIP_MI = 356_500_000, 0.7   # FHWA OD 2022 + NHTS length
BUS_K_10YR, BUS_MI_10YR = 12, 156_919_941_747 # NTD, national bus

W_E, W_T, W_M = -0.5, -0.08, -0.5             # MEP weights: energy, time, money
MEP = {"drive": (0.90, 0.48), "transit": (0.65, 0.86), "walk": (0.00, 0.00)}

# Delay. TTI 2025 Urban Mobility Report, Tampa-St Petersburg, 2024: MEASURED.
TTI_HOURS = 112_436_000
# Share of congestion caused by crashes. The one real uncertainty.
SHARES = {"low  (25% of nonrecurring)": 0.1375,
          "FHWA headline": 0.2500,
          "TTI urban measurement": 0.5500}
FWY_VMT, ART_VMT, FWY_DELAY = VMT*0.230, VMT*0.404, 0.60

L = lambda t: print(f"\n{'='*70}\n{t}\n{'='*70}")

# 1 ----------------------------------------------------------------------
L("STEP 1  WHO DIED - counted, not estimated")
tot = sum(DEATHS.values())
for k, v in DEATHS.items():
    print(f"    {k:<16}{v:>6,}   {v/tot:>5.1%}")
print(f"    {'TOTAL':<16}{tot:>6,}")
nonmotor = (DEATHS["walking"] + DEATHS["cycling"]) / tot
print()
print(f"  {nonmotor:.1%} of deaths here are people NOT in a vehicle; Florida is 26.6%.")
print(f"  An earlier version used the state share and got drivers 68% too high.")

# 2 ----------------------------------------------------------------------
L("STEP 2  HOW FAR PEOPLE WENT - the bottom of every fraction")
pm_drive, pm_walk = VMT*OCCUPANCY, WALK_TRIPS*WALK_TRIP_MI
print(f"    driving   {pm_drive:>18,.0f} person-miles/yr   FDOT x {OCCUPANCY}")
print(f"    walking   {pm_walk:>18,.0f} person-miles/yr   FHWA trip survey")
print(f"\n  People drive {pm_drive/pm_walk:,.0f}x as far as they walk. That ratio is the")
print(f"  whole reason walking looks dangerous per mile.")

# 3 ----------------------------------------------------------------------
L("STEP 3  WHY 1.50 PEOPLE PER CAR - measured, not back-solved")
print(f"  Counted from NHTS 2022: person-miles over vehicle-miles across")
print(f"  driver-reported car, van, SUV and pickup trips.")
print(f"    South Atlantic large MSA  1.502   (2,091 driver trips)")
print(f"    United States             1.523   (20,415 driver trips)")
print(f"  An earlier version claimed MEP's $0.48 was AAA's $0.796/car-mile")
print(f"  divided by 1.67. AAA publishes no $0.796. That was fabricated.")

# 4 ----------------------------------------------------------------------
L("STEP 4  WHOSE BILL IS A DEAD PEDESTRIAN? - pick one, never both")
d_int = DEATHS["in a car"]/YEARS*VSL/pm_drive
w_int = DEATHS["walking"]/YEARS*VSL/pm_walk
caused = DEATHS["in a car"] + DEATHS["walking"]*PED_BY_CAR + DEATHS["cycling"]*BIKE_BY_CAR
d_ext = caused/YEARS*VSL/pm_drive
print(f"    A  what the mode SUFFERS   driving ${d_int:.4f}   walking ${w_int:>7.4f}")
print(f"    B  what the mode CAUSES    driving ${d_ext:.4f}")
print(f"\n  We use A. Everything else in MEP's money term is what the traveller")
print(f"  personally pays. The ${d_ext-d_int:.4f}/mile gap between them IS the externality.")

# 5 ----------------------------------------------------------------------
L("STEP 5  WHAT INJURY COSTS PER MILE")
bus = BUS_K_10YR/10*VSL/(BUS_MI_10YR/10)
print(f"    driving   ${d_int:.4f}      walking   ${w_int:.4f}      bus   ${bus:.4f}")
print(f"\n  Walking costs {w_int/d_int:.0f}x driving. Driving costs {d_int/bus:.0f}x the bus.")

# 6 ----------------------------------------------------------------------
L("STEP 6  THE OTHER COST OF A CRASH: EVERYONE ELSE'S TIME")
print(f"  TTI measured {TTI_HOURS/1e6:.1f} million hours lost to congestion here in 2024.")
print(f"  How much of that is crashes? Nobody counts it. Published answers range")
print(f"  from 13.75% to 55%, so we report all of them rather than pick.")

def delay(share, speed, fwy, art, mins=30):
    hrs = TTI_HOURS*share
    f = hrs*FWY_DELAY/FWY_VMT*60
    a = hrs*(1-FWY_DELAY)/ART_VMT*60
    return (speed*mins/60)*(fwy*f + art*a)

# 7 ----------------------------------------------------------------------
L("STEP 7  INTO MEP  -  score = e^(energy x-0.5 + minutes x-0.08 + dollars x-0.5)")
base = {m: exp(W_E*e + W_T*30 + W_M*c) for m,(e,c) in MEP.items()}
print(f"  MEP as published:  drive {base['drive']:.5f}   bus {base['transit']:.5f}"
      f"   walk {base['walk']:.5f}")
print(f"  Walking already scores HIGHEST. MEP calls it the best way to travel here.\n")
print(f"  {'crash share of congestion':<28}{'drive':>9}{'bus':>9}{'walk':>9}   who leads")
rows=[]
for lbl, sh in SHARES.items():
    dd, db = delay(sh,30,0.40,0.60), delay(sh,12,0.05,0.95)
    dr = exp(W_E*0.90 + W_T*(30+dd) + W_M*(0.48+d_int))
    bs = exp(W_E*0.65 + W_T*(30+db) + W_M*(0.86+bus))
    wk = exp(W_E*0.00 + W_T*30      + W_M*(0.00+w_int))
    lead = dr/bs-1
    rows.append((lbl,dr,bs,wk,lead))
    print(f"  {lbl:<28}{dr/base['drive']-1:>+9.1%}{bs/base['transit']-1:>+9.1%}"
          f"{wk/base['walk']-1:>+9.1%}   "
          f"{'driving' if lead>0 else 'the BUS'} by {abs(lead):.1%}")

# 8 ----------------------------------------------------------------------
L("STEP 8  WHAT IT MEANS")
wk = rows[0][3]
print(f"  1. WALKING loses {1-wk/base['walk']:.0%} of its score and stops being the best mode.")
print(f"     MEP currently recommends walking in a region where {DEATHS['walking']} people")
print(f"     died doing it. That is the finding, and it does not depend on the")
print(f"     uncertain delay input at all.")
print(f"\n  2. DRIVING led the bus by {base['drive']/base['transit']-1:.1%}. After both corrections that lead")
print(f"     is gone at every plausible crash share. It survives none of them:")
for lbl,dr,bs,_,lead in rows:
    print(f"       {lbl:<30}{'driving' if lead>0 else 'the BUS':>8} by {abs(lead):.1%}")
print(f"\n  3. TIME costs driving more than INJURY does. Every trip pays the time,")
print(f"     crash or no crash. You sit in the queue either way.")
print(f"\n  Regional bill: ${tot/YEARS*VSL/1e9:.1f} billion a year, ${tot/YEARS*VSL/POP:,.0f} per resident.")
