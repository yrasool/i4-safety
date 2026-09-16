# The maths — every calculation, explained from zero

This file explains **every calculation** in the project, one at a time, as if you have
never seen any of it. Each one has: **what it's for**, **the formula**, **what each part
means**, **a worked example with numbers you can check by hand**, and **why it's done
this way**.

Other files: `DATA.md` (where the numbers come from), `ASSUMPTIONS_AND_CHOICES.md` (why
each choice was made), `HOW_IT_RUNS_VS_STANDARD_MEP.md` (how it runs, and how it
compares with NREL's MEP).

| # | calculation |
|---|---|
| 0 | how to read the symbols |
| 1 | turning crashes into dollars per year |
| 2 | how much travel happens |
| 3 | crash cost per mile |
| 4 | the bus crash rate, and how sure we are |
| 5 | the Minnesota check |
| 6 | MEP Equation 1 — what you can reach |
| 7 | travel times |
| 8 | MEP Equation 2 — the penalty |
| 9 | MEP Equation 3 — the score |
| 10 | combining neighbourhoods into one region |
| 11 | how much of the drop each mode causes |
| 12 | why the first map was fake |
| 13 | the road-danger model |
| 14 | each neighbourhood's driving danger |
| 15 | the walking and biking attempt |
| 16 | the traffic-by-year check |
| 17 | who pays when a car hits someone |
| 18 | the prediction test |
| 19 | who is hit hardest |
| 20 | how much the ranking changes |
| 21 | what if the walking and biking numbers are wrong? |

---

## 0. How to read the symbols

| symbol | means | example |
|---|---|---|
| × | multiply | 3 × 4 = 12 |
| ÷ | divide | 12 ÷ 4 = 3 |
| x² or x^2 | x multiplied by itself | 3² = 9 |
| x^b | x "to the power b" | 2^0.8 ≈ 1.74 |
| √ | square root — the number that multiplied by itself gives this | √9 = 3 |
| π | pi, about 3.14 | |
| Σ | "add up all of these" | Σ of 2, 3, 5 = 10 |
| e | a fixed number, about 2.718 | |
| e^x | e to the power x | e^0 = 1, e^−1 ≈ 0.37 |

**Why e^x shows up:** it's a smooth way to turn "a penalty" into "a share you keep". If the
penalty is 0, e^0 = 1, so you keep **100%**. The bigger the penalty, the closer to 0 — but
it never goes below 0. You never need to work it out by hand; a calculator or computer
does.

**Average vs weighted average:**
- **Average** of 10 and 20 = (10 + 20) ÷ 2 = **15**. Both count equally.
- **Weighted average**, where 10 counts 3 times as much as 20:
  (3 × 10 + 1 × 20) ÷ (3 + 1) = 50 ÷ 4 = **12.5**. It leans toward the one that counts more.

Weighted averages appear many times below.

---

## 1. Turning crashes into dollars per year

**What it's for:** MEP measures cost in dollars, so crash harm has to be in dollars too.

**Formula:**
> **crash cost per year = (people killed × $13,700,000 + people seriously injured × $1,302,300) ÷ 6.9 years**

**Each part:**
- **$13,700,000** and **$1,302,300** — the US Department of Transportation's official values
  for a death and a serious injury (2024 dollars).
- **6.9 years** — the crash records run January 2019 to November 2025. Dividing turns a
  total into "per year".

**Worked example — people in cars:**
- 1,582 killed × $13,700,000 = **$21.67 billion**
- 14,774 seriously injured × $1,302,300 = **$19.24 billion**
- total = **$40.91 billion** over 6.9 years
- ÷ 6.9 = **$5.93 billion a year**

**All modes:**

| who was hurt | killed | seriously injured | cost per year |
|---|---:|---:|---:|
| in vehicles | 1,582 | 14,774 | $5.93B |
| walking | 915 | 1,612 | $2.12B |
| motorbikes | 697 | 2,656 | $1.89B |
| cycling | 277 | 1,263 | $0.79B |
| **total** | **3,471** | **20,305** | **$10.72B** |

**Cost per person living here:** $10.72 billion ÷ 3,468,871 people = **$3,092 a year**.

**Why this way:** the values are **per person**, and we count **people**. (An early version
used the government's **per crash** values on counts of people — that was one reason it
came out 8 times too high.)

---

## 2. How much travel happens

### Cars

**Formula:**
> **car passenger-miles per year = vehicle-miles per day × 365 × people per car**

- **102,108,727** vehicle-miles a day (Florida DOT, all roads in the five counties)
- × 365 = **37.27 billion** vehicle-miles a year
- × **1.502** people per car = **55.98 billion passenger-miles a year**

**How "people per car" is measured (from the travel survey):**
> **people per car = total passenger-miles ÷ total vehicle-miles**, on drivers' trips only

*Example:* a driver takes a 10-mile trip with one passenger. That's 10 vehicle-miles and
20 passenger-miles → 20 ÷ 10 = 2 people. Averaged over thousands of trips → **1.502**.

**Why drivers' trips only:** in the survey, the driver **and** the passenger each report the
same trip. Counting both would count one car trip twice.

### Walking and biking

**Formula:**
> **passenger-miles per year = miles one person travels a year × population**

- Biking: **23.7** miles a year × 3,468,871 people = **82.2 million passenger-miles**
- Walking: **49.0** miles a year × 3,468,871 = **169.8 million passenger-miles**

**How "miles one person travels a year" is measured:** add up the survey's bike (or walk)
trip lengths, each multiplied by the survey's **weight** (how many real trips each surveyed
trip stands for), then divide by the number of people.

*Why weights?* A survey can't ask everyone. One surveyed trip might stand for thousands of
real trips. The weight says how many.

### Bus

Bus passenger-miles come straight from the National Transit Database (see part 4).

---

## 3. Crash cost per mile

**What it's for:** the single most important number. It lets us compare modes fairly and
plug crash cost into MEP.

**Formula:**
> **crash cost per mile = crash cost per year ÷ passenger-miles per year**

**Worked out:**

| mode | cost per year | ÷ passenger-miles per year | = crash cost per mile |
|---|---:|---:|---:|
| car | $5.93 billion | 55.98 billion | **$0.1059** |
| bike (regional survey) | $0.79 billion | 82.2 million | **$9.59** |
| bike (national survey) | $0.79 billion | 66.8 million | $11.79 |
| walk (national survey) | $2.12 billion | 183.4 million | $11.57 |
| walk (regional survey) | $2.12 billion | 169.8 million | $12.49 |

**Why bikes are so high — the restaurant-bill example:**
- **Table A** (cars): a $100 bill shared by 50 people = **$2 each**.
- **Table B** (bikes): a $50 bill shared by 2 people = **$25 each**.

The bike bill is smaller, but shared by far fewer. Bikes have much less harm in total, but
it's spread over **680 times fewer miles** than cars.

**Why ranges for walking and biking:** the national and regional surveys give different
miles per person, and neither is clearly better (the regional biking figure rests on only
35 trips), so we report both.

**A deaths-only car rate** (for comparing with buses, which record no serious injuries):
1,582 × $13,700,000 ÷ 6.9 ÷ 55.98 billion = **$0.0561 a mile**.

---

## 4. The bus crash rate, and how sure we are

**Formula:**
> **bus crash cost per mile = (bus riders killed per year × $13,700,000) ÷ bus passenger-miles per year**

- **12** bus riders killed in traffic crashes, whole US, over **10 years** (2015–2024)
- per year: 12 ÷ 10 = **1.2**
- × $13,700,000 = **$16.4 million a year**
- ÷ **15.69 billion** bus passenger-miles a year = **$0.00105 a mile**

**How sure are we?** With only **12** events, chance matters a lot. Counts of rare events
follow a pattern called **Poisson**, and from it we can work out a range where the true rate
very likely sits (95% confident):

| | crash cost per mile |
|---|---:|
| low end | $0.00054 |
| **our number** | **$0.00105** |
| high end | $0.00183 |

**What that says:** the true bus rate could easily be about **half** to **1.7 times** our number.
That sounds like a lot — but bus crash cost is so small that it barely affects the score either
way.

---

## 5. The Minnesota check

**What it's for:** proving our car crash cost isn't crazy, by comparing with a published study
(Cui & Levinson, Minneapolis area).

**Problem:** their number isn't in the same units, and uses older dollars. Three conversions
make it comparable.

### Conversion 1 — person-miles to car-miles
Theirs is per **car**-mile; ours is per **person**-mile.
> **ours per car-mile = $0.1059 × 1.502 people per car = $0.1591**

### Conversion 2 — kilometres to miles
Theirs is **$0.040 per car-kilometre**. One mile = 1.609344 km.
> **$0.040 × 1.609344 = $0.0644 per car-mile** (in 2010 dollars)

### Conversion 3 — 2010 dollars to 2024 dollars
Their study valued a death at **$9,134,786** (2010 dollars). Ours uses **$13,700,000** (2024).
> **dollar adjustment = $13,700,000 ÷ $9,134,786 = 1.50**
> **$0.0644 × 1.50 = $0.0966 per car-mile** (2024 dollars)

### The comparison
> **ratio = ours ÷ theirs = $0.1591 ÷ $0.0966 = 1.65**

**Pass rule:** the step **refuses to finish** unless the ratio is between **1.2 and 3.0**.
- **Why above 1.2:** Florida's roads are about twice as deadly per mile as Minnesota's, so ours
  should be clearly higher.
- **Why below 3.0:** they count **all** injury levels and we count only deaths and serious
  injuries, which makes ours *lower* than a full match — so a ratio far above 2 would mean
  something is counted twice.

**Harm to everyone** (step 35) gets its own check against their "full" number ($0.023 more per
km for harm to people outside the car): **1.55**. Also passes.

---

## 6. MEP Equation 1 — what you can reach

**What it's for:** counting the useful places each neighbourhood can reach, by each mode, in each
time band (10, 20, 30, 40 minutes).

**Formula:**
> **reach = Σ over the six kinds of place: (jobs of that kind reachable) × (scaling number) × (trip share)**

### Part A — the scaling number

**Problem:** there are 1.57 million jobs in total but only about 30,000 arts jobs. Added up
raw, work would be 98% of every score.

> **scaling number = US restaurant jobs ÷ US jobs of that kind**

| kind of place | US jobs | scaling number |
|---|---:|---:|
| restaurants | 13,655,757 | 13,655,757 ÷ 13,655,757 = **1** |
| fun / arts | 2,720,476 | 13,655,757 ÷ 2,720,476 = **5.02** |
| shopping | 15,437,805 | **0.885** |
| school | 18,030,644 | **0.757** |
| doctor | 23,202,931 | **0.589** |
| work (all jobs) | 150,944,613 | **0.090** |

**What it does:** puts every kind of place on the same footing — as if each were measured in
"restaurant-equivalents".

**Why national numbers:** so every city is scaled the same way.

### Part B — the trip share
How often people go to each kind of place, from the survey: shopping **28.1%**, work **20.3%**,
fun **19.5%**, restaurants **15.2%**, school **13.8%**, doctor **3.2%**.

**How it's measured:** each surveyed trip's weight, added up by purpose, divided by the total.

### Part C — the weight
> **weight = scaling number × trip share**

| kind of place | scaling | × trip share | = weight |
|---|---:|---:|---:|
| fun / arts | 5.02 | 0.195 | **0.977** |
| shopping | 0.885 | 0.281 | **0.249** |
| restaurants | 1 | 0.152 | **0.152** |
| school | 0.757 | 0.138 | **0.104** |
| doctor | 0.589 | 0.032 | **0.019** |
| work | 0.090 | 0.203 | **0.018** |

### Worked example
Within 10 minutes by car, a neighbourhood reaches **300 shop jobs** and **100 restaurant jobs**
(ignoring the other kinds to keep it simple):
> **reach = 300 × 0.249 + 100 × 0.152 = 74.7 + 15.2 = 89.9**

---

## 7. Travel times

### Shortest route (Dijkstra's method) — cars, walking, bikes
**The idea, like a GPS:**
1. Start at your point. Its time is 0.
2. Look at every road leaving it; note how long each takes (length ÷ speed).
3. Always extend from the **quickest place found so far**.
4. Repeat until every reachable place has its quickest time.

**It stops at 40 minutes**, because MEP never uses longer trips — which saves a lot of computing.

**Time along a road link:**
> **minutes = length in miles ÷ speed in mph × 60**

*Example:* 1 mile at 30 mph = 1 ÷ 30 × 60 = **2 minutes**. On a bike at 12 mph = **5 minutes**.

### Time to reach places inside your own neighbourhood
**Problem:** a neighbourhood is an area. Places inside it aren't "0 minutes" away.

**Formula:**
> **minutes = (2/3) × √(area ÷ π) ÷ speed**

**Each part:**
1. **√(area ÷ π)** — pretend the neighbourhood is a circle. This is its **radius** (centre to
   edge). (Because a circle's area = π × radius².)
2. **× 2/3** — in a circle, the **average** distance from the centre to a random point is about
   two-thirds of the radius.
3. **÷ speed** — turns distance into time.

**Worked example (walking):**
- area = 3.14 km² → radius = √(3.14 ÷ 3.14) = √1 = **1 km**
- × 2/3 = **0.67 km**
- walking speed 3 mph = 4.83 km/h → 0.67 ÷ 4.83 = 0.138 hours = **8.3 minutes**

### Bus travel times (RAPTOR)
**Problem:** buses only run at certain times, so "quickest route" depends on **when** you arrive
at a stop.

**The idea — rounds:**
- **Round 1:** from every stop you can walk to, take **one bus**. Record the earliest arrival at
  every stop it passes.
- **Round 2:** from every stop reached, walk to a nearby stop (up to 300 m, × 1.4 for street
  detours) and take **a second bus**. Record any **earlier** arrivals.
- **Round 3:** once more — **a third bus** (two changes).

Then walk from each stop to the destination (up to 10 minutes). A destination counts as bus-reachable
only if you **actually rode a bus**.

**Three departure times** (7:45, 8:00, 8:15) are run, and the travel times averaged.

---

## 8. MEP Equation 2 — the penalty

**What it's for:** turning energy, time and money into one number that says how much a trip "costs"
overall.

**Formula:**
> **M = −0.5 × energy − 0.08 × minutes − 0.5 × (money + crash cost)**
> **keep = e^M**

**Each part:**

| part | unit | weight | meaning |
|---|---|---:|---|
| energy | kWh per passenger-mile | −0.5 | each 1 kWh per mile lowers M by 0.5 |
| minutes | the time band (10, 20, 30, 40) | −0.08 | each extra minute lowers M by 0.08 |
| money + crash cost | dollars per passenger-mile | −0.5 | each extra $1 per mile lowers M by 0.5 |

The weights (−0.5, −0.08, −0.5) are MEP's own. **Crash cost is added to money** — the only change to
MEP's formula.

**Mode settings (MEP's defaults):**

| mode | energy | money |
|---|---:|---:|
| car | 0.90 | $0.48 |
| bus | 0.65 | $0.85 |
| walk | 0 | $0 |
| bike | 0 | $0 |

### What "keep = e^M" does
| M | keep |
|---:|---:|
| 0 | 100% |
| −0.5 | 61% |
| −1 | 37% |
| −2 | 14% |
| −5 | 0.7% |

**The "60% per dollar" rule:** adding $1 per mile lowers M by 0.5, and e^−0.5 = **0.61**. So **each
extra dollar keeps 61% of what was left.** $2 → 37%, $5 → 8%, $10 → under 1%.

### Worked examples (10-minute band)

**Car, no crash cost:**
M = −0.5 × 0.90 − 0.08 × 10 − 0.5 × 0.48 = −0.45 − 0.80 − 0.24 = **−1.49** → keep **22.5%**

**Car, with crash cost $0.1059:**
M = −0.45 − 0.80 − 0.5 × (0.48 + 0.1059) = −0.45 − 0.80 − 0.293 = **−1.543** → keep **21.4%**
→ that's 21.4 ÷ 22.5 = **95%** of what it was.

**Bike, no crash cost:**
M = 0 − 0.80 − 0 = **−0.80** → keep **44.9%**

**Bike, with crash cost $9.59:**
M = −0.80 − 0.5 × 9.59 = −0.80 − 4.795 = **−5.60** → keep **0.37%**
→ that's 0.37 ÷ 44.9 = **0.8%** of what it was.

**A useful shortcut:** because M is a sum, adding crash cost multiplies keep by **e^(−0.5 × crash
cost)** — the same for every time band. Car: e^(−0.5 × 0.1059) = **0.948**. Bike: e^(−0.5 × 9.59) =
**0.0083**.

---

## 9. MEP Equation 3 — the score

**Formula:**
> **score = Σ over modes and time bands: (places newly reached in that band) × keep**

### "Newly reached"
Travel times give **cumulative** counts — everything reachable **within** each time:

| within | reach (cumulative) | newly reached in this band |
|---|---:|---:|
| 10 min | 100 | 100 |
| 20 min | 250 | 250 − 100 = **150** |
| 30 min | 400 | 400 − 250 = **150** |
| 40 min | 500 | 500 − 400 = **100** |

**Why:** a place 5 minutes away is inside all four circles. Counting the cumulative numbers would
count it **four times**. Taking the differences counts every place **once**, in the band where it's
first reached.

### Worked example (one mode, car, no crash cost)
Keep for the car in each band (M gets 0.8 more negative each 10 minutes):

| band | M | keep | newly reached | points |
|---|---:|---:|---:|---:|
| 10 | −1.49 | 0.225 | 100 | 22.5 |
| 20 | −2.29 | 0.101 | 150 | 15.2 |
| 30 | −3.09 | 0.046 | 150 | 6.8 |
| 40 | −3.89 | 0.020 | 100 | 2.0 |
| **total** | | | | **46.5** |

**What it shows:** nearby places count a lot more than far ones — the first 100 places give almost
half the points.

The same is done for bus, walk and bike, and all four are added up.

---

## 10. Combining neighbourhoods into one region

**Formula:**
> **region score = Σ (neighbourhood score × people living there) ÷ total people**

**Worked example:**

| | people | score |
|---|---:|---:|
| Maple | 2,000 | 28.35 |
| Oak | 500 | 10.00 |

(2,000 × 28.35 + 500 × 10) ÷ 2,500 = (56,700 + 5,000) ÷ 2,500 = **24.7**

**Why weighted by people:** a score is about people's access. A neighbourhood where 2,000 people live
should count 4 times as much as one with 500. This is MEP's own rule.

**The drop:**
> **drop = 1 − (score with crash cost ÷ normal score)**

Real region: 1 − (5,796 ÷ 7,567) = 1 − 0.766 = **23.4%**

---

## 11. How much of the drop each mode causes

**Formula:**
> **mode's share of the drop = (that mode's points lost) ÷ (all points lost)**

**Worked example (the 100-point neighbourhood):**

| mode | points before | × keep | points after | points lost |
|---|---:|---:|---:|---:|
| car | 80 | 0.948 | 75.9 | 4.1 |
| bike | 18 | 0.0083 | 0.15 | 17.85 |
| walk | 1 | 0.003 | 0.00 | 1.0 |
| bus | 1 | 0.9995 | 1.0 | 0.0 |
| **total** | **100** | | **77.0** | **23.0** |

Bike's share = 17.85 ÷ 23.0 = **78%**. (Real region: **76.8%**.)

**Why the shares add up to exactly 100%:** each mode's crash cost only changes **that mode's** points.
So the total loss is just the four losses added together, with nothing left over.

---

## 12. Why the first map was fake

**The problem:** when every neighbourhood gets the **same** crash cost per mode, each neighbourhood's
drop can be written as:

> **drop = Σ over modes: (1 − keep for that mode) × (that mode's share of the neighbourhood's score)**

**Each part:**
- **(1 − keep)** — how much a mode loses. **The same for every neighbourhood**: car 0.052, bike 0.992,
  and so on.
- **share of the score** — how much the neighbourhood relies on that mode. **This is the only part that
  differs between neighbourhoods.**

**Worked example:**

| | car share | bike share | drop |
|---|---:|---:|---:|
| A | 90% | 10% | 0.90 × 0.052 + 0.10 × 0.992 = **14.6%** |
| B | 70% | 30% | 0.70 × 0.052 + 0.30 × 0.992 = **33.4%** |

B drops more **only** because it relies more on biking — not because it's more dangerous. So the map
only shows **how people travel**, not where it's dangerous.

**How we proved it:** this formula matched every real neighbourhood's drop to **16 decimal places** —
exactly.

**How it was (partly) broken:** giving each neighbourhood its **own** car crash cost (part 14). Then
"1 − keep" for the car differs by place. Measured afterwards, local danger explains **7.0%** of the
differences between neighbourhoods; mode mix explains **98.7%**.

---

## 13. The road-danger model

### Step 1 — the raw rate for each road
> **vehicle-miles on a road over the study = vehicles per day × length in miles × 365 × 6.9**
> **raw rate = casualties ÷ vehicle-miles**

*Example:* 20,000 vehicles a day × 1 mile × 365 × 6.9 = **50.4 million vehicle-miles**. With 5
casualties → about **1 casualty per 10 million vehicle-miles**.

**Why raw rates mislead:** a very quiet road with **one** unlucky death gets a huge rate from a single
event.

### Step 2 — are crash counts "extra uneven"?
A simple counting model (**Poisson**) assumes the **spread** of counts (the **variance**) is about the
same as their **average**.

> **variance** = the average of (each count − the average count)²

Our roads: average **4.98** casualties, variance **114.7** → **23 times** more spread than Poisson
expects.

**So we use a "negative binomial" model**, which allows extra spread:
> **variance = average + k × average²**

where **k** measures the extra unevenness.

### Step 3 — the safety curve
> **expected casualties = e^a × (traffic)^b × length × 6.9**

**Each part:**
- **e^a** — a base level (fitted from the data)
- **traffic^b** — how casualties grow with traffic
- **length × 6.9** — longer roads over more years have more casualties

**What b means:**
> **double the traffic → casualties × 2^b**

| b | double the traffic gives |
|---:|---:|
| 1.0 | 2× casualties |
| 0.8 | 2^0.8 = **1.74×** |
| 0.63 | 2^0.63 = **1.55×** |

**How a and b are found ("fitting"):** the computer tries different values of a, b and k, and keeps the
ones that make the real crash counts **most likely** to happen. This is called **maximum likelihood**.

**Results, one curve per road type:**

| road type | roads | b | k |
|---|---:|---:|---:|
| collector | 943 | 0.628 | 1.213 |
| minor arterial | 445 | 0.740 | 0.687 |
| principal arterial | 673 | 0.809 | 0.689 |
| freeway | 787 | 0.828 | 1.004 |
| all together | 2,848 | 0.789 | 0.928 |

**Standard error** — how sure we are about a number. All roads together: b = 0.789, standard error
0.022. Roughly, the true b is very likely within **0.789 ± 2 × 0.022 = 0.75 to 0.83**.

**AIC** — a score for "how well a model fits, minus a penalty for extra complexity". **Lower is better.**
One curve: **10,765**. Four curves: **10,694**. The four-curve version wins even after its penalty.

### Step 4 — the blend (Empirical Bayes)
> **w = 1 ÷ (1 + k × expected)**
> **blended = w × expected + (1 − w) × actual**

**Each part:**
- **w** — how much to trust the curve (between 0 and 1)
- a road with **small expected** casualties → w near 1 → trust the curve
- a road with **large expected** casualties → w near 0 → trust its own count

**Worked examples** (k = 1):

| road | expected | actual | w | blended |
|---|---:|---:|---:|---:|
| quiet | 1 | 3 | 1 ÷ (1 + 1) = **0.50** | 0.5 × 1 + 0.5 × 3 = **2.0** |
| busy | 50 | 60 | 1 ÷ (1 + 50) = **0.02** | 0.02 × 50 + 0.98 × 60 = **59.8** |

**Why:** small numbers are mostly luck; large numbers are mostly real.

### Step 5 — the share of deaths on each road
**Problem:** a death costs about **10 times** a serious injury. A road with 1 casualty who died shows
"100% deaths" — almost certainly luck.

> **shared-out death share = (deaths + 10 × 0.095) ÷ (casualties + 10)**

**Each part:** pretend every road also had **10 casualties at the regional average** (9.5% deaths).

**Worked examples:**

| road | deaths | casualties | raw share | shared-out share |
|---|---:|---:|---:|---:|
| tiny | 1 | 1 | 100% | (1 + 0.95) ÷ 11 = **17.7%** |
| big | 20 | 200 | 10% | (20 + 0.95) ÷ 210 = **10.0%** |

### Step 6 — each road's crash cost per mile
> **road cost per year = (blended deaths × $13.7M + blended serious injuries × $1.3M) ÷ 6.9**
> **road crash cost per mile = road cost per year ÷ (vehicle-miles per year × 1.502)**

---

## 14. Each neighbourhood's driving danger

**Formula:**
> **neighbourhood rate = Σ roads (traffic × e^(−0.08 × minutes to road) × road rate) ÷ Σ roads (traffic × e^(−0.08 × minutes to road))**

It's a **weighted average** of road rates. Each road's weight = its **traffic** × **e^(−0.08 ×
minutes)**:

| minutes away | e^(−0.08 × minutes) |
|---:|---:|
| 0 | 1.00 |
| 10 | 0.45 |
| 20 | 0.20 |
| 40 | 0.04 |

(−0.08 per minute is MEP's own time weight.)

**Worked example** (both roads same traffic):

| road | minutes | weight | rate |
|---|---:|---:|---:|
| A | 5 | e^−0.4 = 0.67 | $0.20 |
| B | 20 | 0.20 | $0.05 |

(0.67 × 0.20 + 0.20 × 0.05) ÷ (0.67 + 0.20) = (0.134 + 0.010) ÷ 0.87 = **$0.166**

**Results:** safest neighbourhood **$0.08**, typical **$0.10**, most dangerous **$0.40** a mile.

---

## 15. The walking and biking attempt (step 32)

**Idea:** make walking danger vary by neighbourhood, the same way.

> **walking miles in a neighbourhood = regional walking miles × (its people × its share who walk to work) ÷ Σ of that over all neighbourhoods**

Then fit a curve like part 13:
> **expected walking casualties = e^a × (something)^b**

and try six "somethings" to see which predicts walking casualties best.

**Result:** the best was **car traffic within 1.5 km**, with **b = 0.21**. Double the nearby traffic →
2^0.21 = **1.16×** walking casualties. Weak. The number of people walking predicted almost nothing.

**Why it wasn't used:** with signals this weak, the blend (part 13) pulls almost every neighbourhood back
to the average, and the leftover differences would mostly be noise.

---

## 16. The traffic-by-year check (step 34)

**Problem:** we divide 7 years of crashes by **2025's** traffic, repeated 6.9 times. But traffic was
lower in earlier years.

**Formula:**
> **true rate ÷ our rate = (2025 traffic × 6.9) ÷ Σ (each year's actual traffic)**

**Why it's so simple:** both rates have the **same top number** (the crashes), so it cancels out. Only the
bottom numbers matter.

**Worked example (made-up, simple):**
- we use: 100 × 3 years = **300**
- real traffic: 90 + 95 + 100 = **285**
- true rate ÷ our rate = 300 ÷ 285 = **1.05** → ours is **5% too low**

**Real result:** our rates are **8.1% to 12.0% too low**. (Two versions, because 2025's statewide traffic
figure isn't published yet — one keeps it at 2024's level, one grows it at the recent rate.)

---

## 17. Who pays when a car hits someone (step 35)

**Two ways of counting driving's crash cost:**

> **what people in the car suffer = car occupants' crash cost ÷ car passenger-miles**
> **what driving causes = (car occupants' cost + cost of people walking and cycling hit by cars) ÷ car passenger-miles**

**Worked out:**
- in the car: $5.93 billion ÷ 55.98 billion = **$0.1059**
- harm to walkers and cyclists hit by cars (only crashes involving a car, not a motorbike): **$2.88
  billion a year**
- everyone: ($5.93B + $2.88B) ÷ 55.98B = **$0.1573**
- difference: $0.1573 − $0.1059 = **$0.0514 a mile**

**Measured along the way:** 99.0% of people killed walking, and 98.6% killed cycling, were in a crash
involving a car.

---

## 18. The prediction test (step 36)

**What it's for:** checking whether the road-danger model actually **predicts** the future.

**How:** fit on **2019–2022** (4 years) only, predict **2023–2025** (2.9 years), compare.

**Check the split is honest:** 9,567 casualties in the first period + 4,612 in the second = **14,179**,
the same total as the full model.

### Three competing predictors
> **past count:** future guess = past casualties × (2.9 ÷ 4)
> **curve only:** future guess = expected casualties from part 13
> **blend:** future guess = blended casualties from part 13

### Measure 1 — average error
> **mean absolute error = average of |guess − actual|** across all 2,848 roads
("|x|" means "ignore the minus sign" — an error of −3 counts as 3.)

**Rescaling first:** 2023–25 had fewer casualties overall, so every method over-guesses. To compare fairly,
each method's guesses are scaled so their total equals the real total:
> **rescaled guess = guess × (real total ÷ total of guesses)**

| method | average error (rescaled) |
|---|---:|
| past count | 1.143 |
| curve only | 1.287 |
| **blend** | **1.123** |

### Measure 2 — finding the worst roads
Pick each method's **top 10%** of roads using **past** data. Then count how many **future** casualties
happened on those roads.

| method | future casualties found | share of the best possible |
|---|---:|---:|
| past count | 2,404 | 81.8% |
| curve only | 2,180 | 74.1% |
| **blend** | **2,426** | **82.5%** |

("Best possible" = the top 10% of roads by **actual** future casualties.)

### Is the lead real? — the bootstrap
Differences this small could be luck. So:
1. Randomly pick 2,848 roads **with replacement** (some roads twice, some not at all).
2. Recalculate "blend's error minus the other method's error" on that pick.
3. Repeat **2,000** times.
4. Look at the middle **95%** of those 2,000 differences.

**Rule:** if the whole middle 95% shows the blend better, the lead is **real**. If it includes "no
difference", it's **within noise**.

| comparison | result |
|---|---|
| blend vs past count, error | **real** |
| blend vs curve only, error | **real** |
| blend vs curve only, top 10% roads | **real** |
| blend vs past count, top 10% roads | within noise |
| top 5% comparisons | within noise |

---

## 19. Who is hit hardest

### Groups of five
Sort all neighbourhoods by their share of households **without a car**, and cut into **5 equal groups**
(called **quintiles**). Then average the drop in each group.

| households without a car | drop |
|---|---:|
| fewest | 21.2% |
| second | 20.3% |
| middle | 21.0% |
| fourth | 23.1% |
| most | 26.2% |

### Rank correlation (Spearman)
**What it's for:** a single number for "do these two things go up together?"

**How:**
1. Rank all neighbourhoods by **carless share** (1st, 2nd, 3rd…).
2. Rank them again by **drop**.
3. Compare the two rankings.

| value | meaning |
|---:|---|
| +1 | identical rankings |
| 0 | no link |
| −1 | exactly opposite |

**Ours: +0.27** — a real but moderate link: more carless → bigger drop, with many exceptions.

**Correlation is not cause:** carless neighbourhoods are also denser and more walkable, which on its own
could explain a bigger drop.

---

## 20. How much the ranking changes

**Rank correlation (Spearman) between the ranking before and after:** **0.989** — almost identical order.

**Median rank move:** for each neighbourhood, how many places it moved; then take the middle value:
> **34 places** out of 2,170.

**Share that moved at all:** **99%**.

**What these three together say:** nearly everyone shifts a little, nobody shifts much.

---

## 21. What if the walking and biking numbers are wrong?

**Test:** re-run the whole score with the walking and biking crash costs changed, and watch the drop
(plain average of neighbourhoods).

| bike crash cost per mile | drop |
|---:|---:|
| $0.96 (a tenth) | 12.2% |
| $4.80 (half) | 22.3% |
| **$9.59 (ours)** | **24.7%** |
| $95.93 (ten times) | 24.0% |

**What it shows:**
- **Halving** the bike number barely changes the drop (24.7% → 23.1%).
- **Ten times higher** barely changes it (→ 24.0%).
- Only a **tenth** makes a real difference (→ 12.2%).

**Why:** of the "60% per dollar" rule (part 8). Once bike crash cost is above a few dollars, bikes keep
almost nothing anyway — so going from $10 to $100 hardly matters, but going down to $1 does.

**With both walking and biking at a tenth:** the drop is **11.5%**.
