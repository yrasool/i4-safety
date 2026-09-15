"""
THE PROJECT. Cars, walking, cycling and ride-hail in Tampa Bay.
Bus dropped: barely used here, and its data blocked injury counting.
"""
from math import exp

# ---- fixed values ------------------------------------------------------
VSL, A_VAL   = 13_700_000, 1_302_300      # USDOT: a death, a serious injury
YEARS, POP   = 6.9, 3_468_871
VMT          = 37_269_685_355             # FDOT, 5 counties, all public roads
OCC          = 1.5                        # MEP's own: 33.7/25/1.5 = 0.90
W_E, W_T, W_M = -0.5, -0.08, -0.5         # MEP weights

# ---- counted from 602,110 police reports -------------------------------
K = {"drive": 1582, "walk": 915, "bike": 277}
A = {"drive": 14774, "walk": 1612, "bike": 1263}
CRASHES_ALL = 602_110                     # incl. 431,829 with no injury

# ---- exposure ----------------------------------------------------------
ATF = 356_500_000                         # FHWA: walk + bike + ferry trips/yr
BIKE_SHARE, WALK_MI, BIKE_MI = 0.15, 0.7, 2.0
PM = {"drive": VMT*OCC,
      "walk":  ATF*(1-BIKE_SHARE)*WALK_MI,
      "bike":  ATF*BIKE_SHARE*BIKE_MI}

# ---- delay -------------------------------------------------------------
TTI_HOURS = 112_436_000                   # TTI 2025, Tampa-St Pete, 2024
SHARES = {"FL freeway": 0.05, "FL arterial": 0.125, "FHWA national": 0.25}
FWY_S, ART_S, FWY_D = 0.230, 0.404, 0.60

# ---- MEP published defaults --------------------------------------------
MEP = {"drive": (0.90, 0.48), "walk": (0.0, 0.0), "bike": (0.0, 0.0),
       "ride-hail": (1.80, 1.54)}         # TNC: deadheading doubles both
L = lambda t: print(f"\n{'='*72}\n{t}\n{'='*72}")

L("1  WHAT HARM COSTS PER MILE")
rate = {m: (K[m]*VSL + A[m]*A_VAL)/YEARS/PM[m] for m in K}
rate["ride-hail"] = rate["drive"]*2.0     # ~2x miles per paying passenger
print(f"  {'mode':<11}{'deaths':>8}{'serious':>9}{'person-mi/yr':>16}{'$/mile':>10}")
for m in K:
    print(f"  {m:<11}{K[m]:>8,}{A[m]:>9,}{PM[m]:>16,.0f}{rate[m]:>10.4f}")
print(f"  {'ride-hail':<11}{'same cars':>8}{'':>9}{'~half the miles paid':>16}{rate['ride-hail']:>10.4f}")
print(f"\n  walking is {rate['walk']/rate['drive']:.0f}x driving per mile, cycling {rate['bike']/rate['drive']:.0f}x")
print(f"  deaths are {sum(K[m]*VSL for m in K)/sum(K[m]*VSL+A[m]*A_VAL for m in K):.0%} of the cost, injuries the rest")

L("2  TIME LOST BEHIND CRASHES")
pm_f, pm_a = VMT*FWY_S*OCC, VMT*ART_S*OCC
def dly(s, speed, fwy, art, mins=30):
    h = TTI_HOURS*s
    return (speed*mins/60)*(fwy*h*FWY_D/pm_f*60 + art*h*(1-FWY_D)/pm_a*60)
print(f"  All {CRASHES_ALL:,} crashes block roads, not just the {sum(K.values()):,} fatal ones.")
print(f"  TTI measured {TTI_HOURS/1e6:.1f}M hours lost to congestion in 2024.\n")
for lbl, s in SHARES.items():
    print(f"    {lbl:<16}{s:>6.1%} of it from crashes  ->  "
          f"{dly(s,30,.40,.60):.2f} extra min on a 30-min drive")

L("3  INTO MEP     score = e^(fuel x-0.5 + minutes x-0.08 + dollars x-0.5)")
SPEED = {"drive": (30,.40,.60), "ride-hail": (28,.40,.60),
         "walk": (3,0,0), "bike": (10,0,0)}
print(f"  {'mode':<11}{'MEP now':>10}{'+harm':>10}{'+delay':>10}{'+both':>10}{'change':>9}")
res = {}
for m,(e,c) in MEP.items():
    sp,f,a = SPEED[m]
    d = dly(SHARES["FHWA national"], sp, f, a)
    now  = exp(W_E*e + W_T*30 + W_M*c)
    harm = exp(W_E*e + W_T*30 + W_M*(c+rate[m]))
    dl   = exp(W_E*e + W_T*(30+d) + W_M*c)
    both = exp(W_E*e + W_T*(30+d) + W_M*(c+rate[m]))
    res[m] = (now, both)
    print(f"  {m:<11}{now:>10.5f}{harm:>10.5f}{dl:>10.5f}{both:>10.5f}{both/now-1:>+9.1%}")

L("4  RESULT")
order_before = sorted(res, key=lambda m: -res[m][0])
order_after  = sorted(res, key=lambda m: -res[m][1])
print(f"  MEP ranks them now :  {'  >  '.join(order_before)}")
print(f"  With harm priced   :  {'  >  '.join(order_after)}")
print(f"\n  Walking and cycling score highest in MEP today. They are the two")
print(f"  modes that get people killed here. Pricing that inverts the ranking.")
print(f"\n  Driving loses {1-res['drive'][1]/res['drive'][0]:.1%}. Ride-hail loses {1-res['ride-hail'][1]/res['ride-hail'][0]:.1%}.")
tot = sum(K[m]*VSL + A[m]*A_VAL for m in K)/YEARS
print(f"\n  Regional bill ${tot/1e9:.1f} B a year, ${tot/POP:,.0f} per resident.")
