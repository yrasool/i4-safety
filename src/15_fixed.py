"""FIXED: Florida crash share, motorbikes added, ride-hail 1.7x, ranges not points."""
VSL, A_VAL, YRS, POP = 13_700_000, 1_302_300, 6.9, 3_468_871
VMT, OCC = 37_269_685_355, 1.5
K = {"drive":1582, "walk":915, "bike":277, "motorbike":697}
A = {"drive":14774, "walk":1612, "bike":1263, "motorbike":2656}
ATF = 356_500_000
cost = {m:(K[m]*VSL + A[m]*A_VAL)/YRS for m in K}

print("1  THE BILL  - now including motorbikes, which were missing\n")
print(f"  {'mode':<12}{'deaths':>8}{'serious':>9}{'$ per year':>14}")
for m in K: print(f"  {m:<12}{K[m]:>8,}{A[m]:>9,}{cost[m]/1e9:>13.2f}B")
tot = sum(cost.values())
print(f"  {'TOTAL':<12}{sum(K.values()):>8,}{sum(A.values()):>9,}{tot/1e9:>13.2f}B")
print(f"\n  ${tot/POP:,.0f} per resident. Previously quoted $2,548 - that left")
print(f"  motorbikes out. The real figure is {tot/1e9:.1f}B, not 8.8B.")

print(f"\n{'='*70}\n2  COST PER MILE  - ranges where the distance is not measured\n{'='*70}")
d = cost["drive"]/(VMT*OCC)
MOTO_VMT = VMT*0.006*1.1                       # ~0.6% of miles, ~1.1 riders
print(f"  {'mode':<12}{'$ per mile':>22}{'vs driving':>14}   basis")
print(f"  {'drive':<12}{d:>22.4f}{'1x':>14}   FDOT counts, solid")
for lbl, m, lo_pm, hi_pm in (
        ("walk","walk", ATF*0.90*1.5, ATF*0.80*0.5),
        ("bike","bike", ATF*0.20*4.0, ATF*0.10*1.5)):
    lo, hi = cost[m]/lo_pm, cost[m]/hi_pm
    print(f"  {lbl:<12}{f'{lo:.2f} to {hi:.2f}':>22}{f'{lo/d:.0f}x to {hi/d:.0f}x':>14}   distance estimated")
mo = cost["motorbike"]/MOTO_VMT
print(f"  {'motorbike':<12}{mo:>22.2f}{f'{mo/d:.0f}x':>14}   miles estimated")
print(f"  {'ride-hail':<12}{d*1.7:>22.4f}{'1.7x':>14}   1.7x driving (deadhead 40-45%)")

print(f"\n{'='*70}\n3  DELAY  - Florida's own figure, not the US average\n{'='*70}")
TTI = 112_436_000
pm_f, pm_a = VMT*0.230*OCC, VMT*0.404*OCC
for lbl, s in (("Florida motorway (TTI)",0.05),("Florida main road (TTI)",0.125),
               ("US average (FHWA)",0.25)):
    h = TTI*s
    mins = 15*(0.40*h*0.60/pm_f*60 + 0.60*h*0.40/pm_a*60)
    print(f"  {lbl:<26}{s:>6.1%}  ->  {mins:.2f} min on a 30-min drive")
print(f"\n  Most Tampa Bay driving is on main roads, so 12.5% is the right one.")

from math import exp
W_E,W_T,W_M = -0.5,-0.08,-0.5
h = TTI*0.125
dmin = 15*(0.40*h*0.60/pm_f*60 + 0.60*h*0.40/pm_a*60)
print(f"\n{'='*70}\n4  INTO MEP  (Florida crash share)\n{'='*70}")
print(f"  {'mode':<12}{'MEP now':>10}{'with harm':>12}{'change':>9}")
for m,(e,c,r) in {"drive":(0.90,0.48,d),"ride-hail":(1.80,1.54,d*1.7),
                  "walk":(0,0,cost['walk']/(ATF*0.85*0.7)),
                  "bike":(0,0,cost['bike']/(ATF*0.15*2.0))}.items():
    dl = dmin if m in ("drive","ride-hail") else 0
    now = exp(W_E*e + W_T*30 + W_M*c)
    new = exp(W_E*e + W_T*(30+dl) + W_M*(c+r))
    print(f"  {m:<12}{now:>10.5f}{new:>12.5f}{new/now-1:>+9.1%}")
