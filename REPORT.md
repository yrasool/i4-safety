# Pricing Crash Harm in the Mobility Energy Productivity Metric

### Tampa Bay, FDOT District 7

Yusra Rasool · September 2026

---

## Summary

The Mobility Energy Productivity metric scores how much of a region a person can
reach, and charges each travel mode for the energy, time and money it costs.
It does not charge any mode for the people it kills.

In Tampa Bay that omission is not neutral. Over 6.9 years, 3,471 people died and
20,305 were seriously injured in traffic crashes across the five counties of
FDOT District 7. Priced at USDOT values, that is **$10.7 billion a year**, or
about **$3,092 per resident per year**, that the metric currently treats as
free.

This report computes MEP for 2,170 block groups from primary data, then adds
crash harm to the term MEP already uses for dollars. Nothing else changes: no
new equation, no new weight.

**Pricing crash harm removes 23.4% to 23.5% of Tampa Bay's accessibility
score.**

That is on MEP's own aggregation rule: Hou et al. (2019) p.9, "the population
proportion weighted summation of MEP across tracts or block groups", which is
how Columbus's published 162 is computed. An unweighted mean of block groups
gives 24.7% to 24.8%, and a population-weighted mean of per-block-group ratios
gives 21.7%. All three are defensible statistics; only the first is MEP's, and
an earlier draft led with the largest without naming which it used.

The correction is not spread evenly. It falls hardest on cycling, which MEP
prices at zero energy and zero cost while it carries about 90 times driving's
crash cost per mile. And it falls hardest on the places where the most households have
no car, rising from 21.2% in the lowest zero-car quintile to 26.2% in the
highest, though the bottom two quintiles are effectively tied.

---

## 1. What MEP omits, and why it matters here

MEP asks three questions of every mode: how much energy, how much time, how much
money. A mode that scores well on all three raises the accessibility of every
place it serves.

Under the published defaults, walking and cycling are given **zero energy and
zero cost**. They are, in the metric's own terms, free. So in a region with
short distances they score higher than any other mode.

Tampa Bay is a region where 915 people died walking and 277 died cycling in
under seven years.

A metric that leaves a cost out does not stay silent about it. It prices it at
zero. The crash cost this project computes is **22.1% of what MEP already
charges driving**, counting deaths and serious injuries together.

Comparing that to transit needs care, and an earlier draft of this report got it
wrong. The transit rate can only be fatality-only: the national transit database
records no bus serious injuries at all, because serious injury there is a
rail-only concept inherited from the State Safety Oversight regime under 49 CFR
Part 674. Putting a deaths-and-injuries figure for driving beside a deaths-only
figure for transit nearly doubles the apparent gap, because serious injuries are
47% of the driving rate.

**Like-for-like, both fatality-only: 11.7% of driving's cost term against 0.12%
of transit's, an asymmetry of about 95 to 1.** That is the defensible
comparison, and it is still large. Omitting crash cost is not even-handed. It
flatters the car, and it flatters walking and cycling more, since for them the
omitted cost is the *only* cost MEP would charge at all.

---

## 2. Study area and data

Five counties: Hillsborough, Pinellas, Pasco, Hernando and Citrus. 2,170 census
block groups, about 3.4 million residents.

| Input | Source | Vintage |
|---|---|---|
| Crashes | Signal Four Analytics, 602,110 records | Jan 2019 to Nov 2025 |
| Casualty values | USDOT BCA Guidance, per injured person | 2024 dollars |
| Vehicle-miles | FDOT Public Road Mileage and Miles Traveled | 2025 |
| Road and path network | OpenStreetMap, 96 Overpass tiles | Sept 2026 |
| Opportunities | LEHD LODES 8 Workplace Area Characteristics | 2023 |
| Activity frequencies, occupancy | NHTS, computed from microdata | 2022 |
| Transit timetables | HART and PSTA GTFS, live feeds | Sept 2026 |
| Population, vehicle access | ACS 5-year, 2020 block groups | 2023 |

Everything is federal, free and versioned. No commercial point-of-interest data
and no proprietary travel-demand model, so any reader can rebuild it.

### Casualties by mode

Counted from the crash file in a single pass, not derived from a statewide
share.

| mode | deaths | serious injuries | cost per year |
|---|---:|---:|---:|
| in a vehicle | 1,582 | 14,774 | $5.93B |
| walking | 915 | 1,612 | $2.12B |
| on a motorbike | 697 | 2,656 | $1.89B |
| cycling | 277 | 1,263 | $0.79B |
| **total** | **3,471** | **20,305** | **$10.72B** |

34.3% of the deaths here are pedestrians and cyclists. An earlier version of
this work used Florida's statewide share instead of counting, and inflated
vehicle-occupant deaths by 68%.

---

## 3. Method

MEP is three equations. This project computes all three and modifies one term.

```
Eq 1   o_ikt = SUM_j  o_ijkt · (A*/A_k) · (f_k / SUM f_k)
Eq 2   M_ikt = α·e_k + β·t + σ·c_k
Eq 3   MEP_i = SUM_k SUM_t (o_ikt − o_ik,t−10) · exp(M_ikt)
```

with α = −0.5 (energy), β = −0.08 per minute (time), σ = −0.5 (cost).

**The change is to Eq 2, and only to its inputs:**

```
c_k  ->  c_k + r_k     crash cost, dollars per passenger-mile,
                       the unit MEP's cost term already carries
```

**One input. Nothing else.** A second term — crash-caused delay added to `t` —
was built and then deleted. See "The delay term, and why it was deleted" below.

There is precedent for editing inputs rather than equations. Garikapati et al.
added ride-hailing to MEP by changing three input values and no maths.

### Computing r_k

```
r_k = (K_k · VSL + A_k · A_val) / years / passenger-miles_k

VSL   = $13,700,000   per fatality
A_val = $1,302,300    per serious injury
```

USDOT values attach to an **injured person**; FHWA values attach to a **crash**.
This numerator counts people, so it must use the USDOT table. Pairing FHWA
per-crash values with person counts, over all five KABCO levels, divided by
vehicle-miles, was an error that compounded to 8x in an earlier version.

Passenger-miles, not vehicle-miles, because MEP's cost term is already per
passenger-mile. Occupancy is **1.502**, measured from NHTS 2022 driver-reported
trips in cars, vans, SUVs and pickups for the South Atlantic large-MSA cut. The
US figure on ten times the sample is 1.523, so the regional value is not an
artefact of sample size.

**Result: `r_drive` = $0.1059 per passenger-mile.**

### Whose cost is a pedestrian killed by a driver?

**Both conventions are defensible. Mixing them is not.**

- **Version A** charges each mode what its own travellers suffer. A pedestrian
  killed by a driver is a cost of *walking*.
- **Version B** charges each mode what it *causes*. That death is a cost of
  *driving*.

Measured from the crash records, **99.0% of pedestrian deaths and 98.6% of
cyclist deaths here involve a car** (motorcycles and mopeds excluded, since they
are not a MEP mode and cannot be charged). The "involves any vehicle" figure is
100%, and is not evidence of anything — a police-reportable traffic crash has a
vehicle in it by construction.

| | driving, per passenger-mile |
|---|---:|
| version A — what occupants suffer | **$0.1059** |
| version B — what drivers cause | **$0.1573** |
| **the externality** | **$0.0514** |

That gap is **$2.88 billion a year**, 33% of driving's total under version B.

**This report uses version A**, because every other term in MEP's cost function
is what the traveller personally carries — fuel, fare, depreciation. It is a
metric about what you can reach, priced by what you bear.

**The choice is load-bearing, and pretending otherwise would be dishonest.**
Under A, cycling supplies 79% of the headline loss. Under B, cycling retains
only 1.4% of its own rate and nearly all of that harm becomes driving's. Anyone
preferring B can take the externality figure above and reassign it; no other
part of the pipeline changes.

**Each version checks against its own published benchmark.** Cui & Levinson
split safety cost into internal and external for precisely this reason:

| | this analysis | Cui & Levinson | ratio |
|---|---:|---:|---:|
| version A | $0.1591 /veh-mi | internal $0.0966 | **1.65x** |
| version B | $0.2363 /veh-mi | full $0.1521 | **1.55x** |

Both sit near Florida's roughly 2x fatality rate over Minnesota's, and both are
lower bounds — this project prices K and A only, while Cui & Levinson price
every severity. Two conventions agreeing with two independently published
components is a stronger check than either alone.

### Motorcycles are counted in the harm and absent from the metric

The casualty table above includes **697 motorcyclist deaths and 2,656 serious
injuries, $1.89B a year — 17.6% of the $10.72B total.** MEP has four modes:
drive, transit, walk, bike. There is no motorcycle mode, so that harm is
**counted in the regional total and never priced into any MEP score.**

This is stated rather than quietly dropped, because the two numbers are
otherwise inconsistent: the $10.7B figure describes what the metric ignores,
while the correction applies to $8.8B of it. Adding a motorcycle mode would
require an energy default, a cost default and a regional exposure figure, none
of which exist in the MEP defaults table. It is left out, visibly.

### The delay term, and why it was deleted

An earlier version of this work also added crash-caused delay to travel time:
0.39 to 0.89 extra minutes on a 30-minute drive, from Skabardonis, Varaiya and
Petty (2003), who put loop detectors on the road and found incidents at 13% to
30% of peak-period congestion, applied to TTI's 112.4 million annual delay hours
for Tampa-St Petersburg.

**It is gone, and the headline is 2.4 points smaller because of it.**

The reason is not that the literature is weak. It is that those two numbers were
typed as a literal into two separate files and derived by **no script in this
project**. Every other input here is either read from a computed file or
declared once in `constants.py` with its source. That one was neither, so it
could not be re-derived, and a number that cannot be re-derived cannot be
defended in a room.

Three things follow, and all three are improvements:

1. **Nothing rested on it.** 2.4 points of a 25-point result.
2. **It moved the result in the flattering direction**, so deleting it argues
   against this project's own conclusion. That is the safe direction to err.
3. **It retires the free-flow-speeds argument entirely.** The delay term was
   only admissible because the isochrones contain no congestion (see below). No
   term, no argument to defend.

`src/constants.py` sets `DELAY_MINUTES = (0.0, 0.0)` and `src/26_validate.py`
**exits with a failure** if that is ever made non-zero while this report says
the term is retired. Test 4 there still re-measures what the deleted term was
worth, so the decision carries a number rather than a claim.

### Building the isochrones

Travel times are computed, not borrowed.

```
495,508 distinct OSM ways   ->   827,133 junctions   ->   1,115,278 edges
drive     911,197 usable edges     1,637,947 arcs
walk    1,099,311 usable edges     2,151,236 arcs
bike    1,109,318 usable edges     2,171,186 arcs
```

Transit uses RAPTOR over the live HART and PSTA timetables for Thursday
17 September 2026: 6,232 stops, 187 distinct stop patterns, 4,308 trips, three
rounds so up to two transfers, averaged over departures at 07:45, 08:00 and
08:15. Walk access to stops is computed on the real pedestrian network and
capped at 10 minutes.

**Speeds are free-flow.** These travel times contain no congestion. That once
mattered a great deal, because it was the only thing making the delay term
admissible. With the delay term deleted it is simply a stated property of the
network: reach here is an upper bound, and a congested skim would shrink every
mode's isochrone, not just driving's.

**The diagonal is a real travel time, not zero.** Every travel-time matrix has a
cell for reaching your own block group, and setting it to zero says a resident of
a 200 km² rural block group can reach everything inside it instantly, on foot.
319 of 2,170 block groups here are larger than a ten-minute walk can cover.

A zero diagonal therefore hands those places their entire local opportunity count
inside the shortest time band, for every mode, and it does so hardest in exactly
the rural block groups that then appear to lose the most. Before this was fixed,
**98.9% of the region's ten-minute transit band was origins counting
themselves, and with the fix it is still 98.6%.** The intrazonal time is the
correct treatment, but it does not rescue transit reach: the median origin's
ten-minute transit band is essentially its own block group either way. That is
a statement about Tampa Bay's bus coverage, not about the method.

The intrazonal time used is the mean distance from the centre of an equal-area
disc to a random point in it, `(2/3)·√(area/π)`, divided by the mode's local
speed. Intra-block-group trips are walked, so transit uses walking speed.

### Weighting opportunities

MEP counts six kinds of destination, not "jobs". Each is weighted by a spatial
equivalency factor `A*/A_k`, computed on **national** totals, and by how often
people make that kind of trip, from NHTS 2022.

| activity | local total | f_k | A*/A_k | weight |
|---|---:|---:|---:|---:|
| work | 1,570,813 | 20.3% | 1.00 | 0.203 |
| meals | 153,936 | 15.2% | 11.05 | 1.676 |
| social | 30,150 | 19.5% | 55.48 | 10.799 |
| shopping | 176,536 | 28.1% | 9.78 | 2.747 |
| medical | 234,403 | 3.2% | 6.51 | 0.205 |
| school | 145,973 | 13.8% | 8.37 | 1.154 |

The equivalency factor is national because the reference defines the denominator
across multiple US cities and requires the factor to be constant for a given
city. A locally derived factor would inflate whatever the study region happens
to lack, and would make two cities' scores incomparable, which is the property
the factor exists to provide.

The activity frequencies are computed from NHTS 2022 microdata rather than taken
from a table, and they can be checked against the reference implementation's own
values, which use NHTS 2017:

| activity | this, 2022 | reference, 2017 | difference |
|---|---:|---:|---:|
| work | 20.3% | 30% | −9.7 pt |
| shopping | 28.1% | 35% | −6.9 pt |
| social | 19.5% | 15% | +4.5 pt |
| meals | 15.2% | 12% | +3.2 pt |
| school | 13.8% | 6% | +7.8 pt |
| medical | 3.2% | 3% | +0.2 pt |

The two largest gaps move in the direction FHWA's own published trend requires.
Annual work trips per person fell from 214 in 2017 to 153 in 2022, and shopping
trips from 473 to 293. Using 2017 shares would overweight commuting by about
half in a post-pandemic region. School is the one category where the reference's
figure looks low against FHWA's published 10.9% for 2017, and this analysis does
not resolve that.

Equation 3 is a **band difference**, `o_ikt − o_ik,t−10`, not a cumulative sum.
Summing cumulative counts would count the same nearby destination once in each
of the four bands and would inflate dense places most.

---

### Place-varying crash risk

Everything above gives each mode ONE regional crash rate. That is enough to
correct the metric, and not enough to make a map: with four scalars the loss at
every block group reduces to its mode mix, which Section 5 proves. Two further
steps make the driving rate vary by place.

**A Safety Performance Function**, the Highway Safety Manual form, fitted by
negative binomial regression over 2,429 FDOT segments:

```
mu = exp(a) · AADT^b · L · years

a = -8.3884     b = 0.7892     k = 0.9282 (overdispersion)
```

The data justifies the model before it is fitted: segment KSI has **variance
114.7 against a mean of 4.98**, a ratio of 23.0. Poisson assumes that ratio is
1, and would have reported far more confidence than the counts support.

`b = 0.71` is the standard result. A road with twice the traffic carries 1.63
times the casualties, not twice, which is exactly why a raw rate per mile falls
as volume rises and why ranking on raw rates puts quiet roads on top.

The fit uses **all 2,848 segments, including the 47% with zero casualties.** An
earlier version emitted only segments a crash had matched to, which is selection
on the outcome variable. It biased `exp(a)` up and `b` down exactly as theory
predicts, and Empirical Bayes then shrank quiet roads *toward an inflated
expectation* — the opposite of its purpose:

| | a | b | k |
|---|---:|---:|---:|
| selected sample, 2,427 segments | −7.7239 | 0.7300 | 0.7344 |
| **all segments, 2,848** | **−8.3884** | **0.7892** | **0.9282** |

A zero-crash segment is data. It says this much exposure produced no casualties.

**Empirical Bayes** then blends prediction with observation:

```
w = 1 / (1 + k · mu)          N_eb = w · mu + (1 - w) · N_observed
```

A short quiet segment with two deaths is mostly noise and gets pulled back
toward what its class normally does; a busy segment with a long record is
trusted on its own. **Thirteen of the twenty-five worst segments by raw rate drop
out once this is applied.** The regional KSI total is unchanged to within 0.0%,
because EB redistributes risk rather than inventing it.

**The severity split is shrunk too.** Empirical Bayes smooths the casualty
count, but the count then has to be divided back into deaths and serious
injuries to be priced, and a death costs 10.5 times a serious injury. Using each
segment's raw observed ratio handed the variance straight back: 51 segments had
a raw fatal share of exactly 1.0, on one or two casualties. The ratio is now
shrunk toward the regional 0.095 with a Beta-binomial prior of 10
casualty-equivalents, which cut its standard deviation from 0.151 to 0.035 and
left no segment above 0.9. The p90/p10 spread of segment risk fell from 8x to
6x, so part of what looked like real spatial variation was severity noise — and
most of it was not.

The segments are tallied for **vehicle occupants only**, not all casualties. The
all-mode count on these roads is 19,999 KSI against 16,356 occupant KSI
region-wide, and those answer different questions: all-mode is what driving
*causes*, `r_drive` is what drivers *suffer*. Substituting the first into MEP's
drive cost term would switch specification silently. The first version of this
step did exactly that and produced a rate twice `r_drive`.

**Attaching segments to origins.** Each origin's driving risk is the segment
risk it can reach, weighted by traffic volume and by MEP's own time decay:

```
r_i = Σ_s VMT_s · exp(β·t_is) · r_s  /  Σ_s VMT_s · exp(β·t_is)
```

The decay matters. A 40-minute drive from almost anywhere in Tampa Bay reaches
almost the same road network, so an unweighted mean inside an isochrone returns
nearly the same number everywhere and the identity survives in all but name.
Using `exp(β·t)`, the same discount MEP applies to distant opportunities, makes
near roads count for more.

**This is exposure-weighted proximity, not route assignment.** A real assignment
would route each origin-destination pair and accumulate risk along the path
taken, which needs an OD matrix this project does not have. What it does capture
is whether the roads near you are the ones that kill people.

Result, over 2,161 of 2,170 origins:

| | `r_drive` per passenger-mile |
|---|---:|
| p10 | $0.0931 |
| median | $0.0999 |
| p90 | $0.1587 |
| range | $0.0622 to $0.4137 |

Coefficient of variation 0.243, and the mean is 1.05× the regional figure, so
the weighting is not distorting the level. By county:

| county | median `r_i` |
|---|---:|
| Hernando | $0.1785 |
| Citrus | $0.1653 |
| Pasco | $0.1267 |
| Pinellas | $0.0987 |
| Hillsborough | $0.0957 |

Rural counties carry roughly twice the crash cost per passenger-mile of the two
urban ones. That is the expected direction and it is the variation a single
regional number cannot express.


## 4. Results

### Reach by mode

Median weighted opportunities reached from a block group:

| mode | 10 min | 20 min | 30 min | 40 min |
|---|---:|---:|---:|---:|
| drive | 82,340 | 343,654 | 800,341 | 1,198,385 |
| bike | 5,070 | 26,017 | 72,771 | 133,032 |
| walk | 193 | 892 | 2,415 | 4,966 |
| transit | 130 | 239 | 727 | 984 |

Transit reaches less than walking for the median block group. That is not an
error: only 40.6% of block groups have any bus stop within a ten-minute walk, so
for the median origin transit reaches almost nothing.

### MEP before and after

| | mean | change |
|---|---:|---:|
Population-weighted, MEP's own rule:

| | city score | change |
|---|---:|---:|
| published | 7,567.3 | |
| with crash harm, low | 5,796.1 | **−23.4%** |
| with crash harm, high | 5,788.6 | **−23.5%** |

Unweighted mean of block groups, for comparison only:

| | mean | change |
|---|---:|---:|
| published | 8,241.2 | |
| with crash harm, low | 6,206.4 | −24.7% |
| with crash harm, high | 6,197.7 | −24.8% |

Decomposed:

| term | change | shipped? |
|---|---:|---|
| injury only | −24.7% | **yes, this is the model** |
| [deleted] delay only, 30% incident share | −5.5% | no |
| [deleted] injury and delay, high | −29.2% | no |

The injury term carries the entire result, because it is now the only term.
The rows above are a **historical** measurement of the deleted delay term, kept
so the decision to drop it is on the record with a number. Nothing in the
shipped headline contains them.

### Which mode supplies the loss

| mode | alone | share of drop | 40-min reach |
|---|---:|---:|---:|
| bike | −18.9% | **76.8%** | 12,035 |
| drive | −4.5% | 18.2% | 108,416 |
| walk | −1.2% | 5.0% | 449 |
| transit | −0.0% | 0.0% | 89 |

Cycling dominates, and it is worth being precise about why. A mode's share of
the drop is its **reach times its rate**, not its rate alone. Walking has the
higher crash cost per mile but reaches too little to move the regional total.
Cycling reaches 27 times more, and MEP prices it at zero on both of its other
terms, so it carries a large share of the base score and has the furthest to
fall.

**MEP currently scores cycling in Tampa Bay as free.** Cycling here costs $9.59
to $11.79 per passenger-mile in crash harm, 91 to 111 times driving's. An
earlier draft of this report said $2.76 and 26x, which was the superseded
literal-exposure figure this same report describes replacing.

### Where the score falls

| county | population | MEP loss per resident |
|---|---:|---:|
| Citrus | 158,693 | 25.9% |
| Hernando | 201,512 | 26.5% |
| Pinellas | 960,565 | 23.7% |
| Hillsborough | 1,489,634 | 20.6% |
| Pasco | 588,758 | 18.4% |

### Who bears it

| zero-car quintile | block groups | population | zero-car share | MEP loss |
|---|---:|---:|---:|---:|
| 1 (lowest) | 434 | 645,028 | 0.0% | 21.2% |
| 2 | 434 | 764,952 | 0.7% | 21.3% |
| 3 | 434 | 773,532 | 3.4% | 22.1% |
| 4 | 433 | 638,015 | 7.2% | 24.4% |
| 5 (highest) | 433 | 577,635 | 19.7% | **26.2%** |

The top quintile loses 5.0 percentage points more than the bottom, Spearman
+0.27, and the progression now rises at every quintile. Before driving danger was
routed, the bottom two were tied at 20.4% and 20.3%; routing is what separated
them. It is still a correlation, not a cause.

Mean loss is 23.0% per block group, and 21.7% per resident. The gap between
those two is the reminder that a block group is not a person: the rural block
groups losing most are also the emptiest.

The households with no car are the ones whose remaining options are walking,
cycling and the bus. Those are the modes whose true cost the metric was
understating most.

**This is an association, not an attribution.** Places with many carless
households are also dense and walkable, and density drives both the zero-car
share and the mode mix. The direction is not established here.

---

## 5. Validation

Five tests, each answering a question a reviewer would ask.

### Is the surface an identity?

**With a single regional rate per mode: yes, unavoidably. With place-varying
driving risk: no. Both are tested, every run.**

An earlier version of this project produced a block-group map that was an exact
arithmetic restatement of its own inputs. It was deleted, and a test was written
so it could not happen again.

**That test did not work.** It checked that two different rate vectors produce
different rankings, which is true whenever the vectors differ, identity or not.
Fed the deleted v1 surface, it passed. It could not fail.

Tested properly, the closed form is exact whenever every `r_k` is a scalar.
Because MEP sums over modes and `r_k` enters only mode `k`'s term:

```
MEP_harm_i = Σ_k  g_k · B_ik          g_k = exp(σ·r_k)
loss_i     = Σ_k (1 − g_k) · s_ik     s_ik = B_ik / Σ_k B_ik
```

| | max error against the constant-`g` form | identity |
|---|---:|---|
| scalar `r_drive` | 6.1e-16 | **holds** |
| place-varying `r_drive` | 7.6e-02 | **broken** |

The first row is arithmetic, not a modelling choice, so the run fails if it does
*not* hold — that would mean the check itself is broken.

**But "not exactly an identity" is a very low bar, and the honest size of the
break is small.** The residual is algebraically `(ḡ_d − g_d(i))·s_di`, which is
non-zero for *any* rate vector with non-zero variance, however meaningless. So
the surface is decomposed rather than declared fixed:

| | |
|---|---:|
| variance explained by mode mix alone | **93.0%** |
| variance from local crash risk | **7.0%** |
| R² of loss on mode mix alone | 0.9867 |
| Spearman against the scalar-rate surface | 0.9902 |

**Local risk, routed, contributes 7.0% of the surface's
variance. Calling this a crash-risk map would not survive a reviewer.**

It is also not block-group-scale. Regressing `r_i` on county dummies alone gives
**R² = 0.23** for route-assigned risk, against **0.77** for the proximity estimate it
replaced. Proximity was mostly a five-category county effect smeared by distance
decay; routing each origin to each destination made the risk genuinely
block-group-scale. Step 40, and section K1 of ASSUMPTIONS_AND_CHOICES.md.

The correlation between local driving risk and MEP loss is **−0.20**, negative,
because the highest-risk roads are rural and rural places have little walking or
cycling, which is where most of the loss lives. The two effects pull opposite
ways — which is why one regional number could not stand in for both, and also
why the correction is small.

**What it still is not.** Driving risk varies by place; walking, cycling and
transit risk do not. Exposure-weighted proximity is not route assignment. So
this is a first-order spatial correction, not a validated crash-risk surface.

### Do the isochrones agree with an independent surface?

EPA's Smart Location Database publishes jobs reachable in 45 minutes, computed
by someone else from different networks.

| | n | Spearman |
|---|---:|---:|
| drive vs `D5AR` | 1,670 | **0.8985** |
| transit vs `D5BR` | 980 | 0.6161 |

Only rank is tested. Levels cannot be compared: SLD is time-decayed and this is
a cutoff count.

The weaker transit agreement is in the direction the definitions predict.
`D5BR` is `min(transit, walk ≤ 15 min)` and `max(forward, reverse)`; this is
transit only, one direction, with a 10-minute walk cap. EPA finds 41.3% of block
groups without transit access; this finds 60.0%.

### Does the crash cost reconcile with published work?

Against Cui and Levinson (2019), Twin Cities, once units and dollar year are
matched:

```
this analysis    $0.1059 per passenger-mile
                 $0.1591 per vehicle-mile      (× 1.502 occupancy)
Cui & Levinson   $0.0966 per vehicle-mile      (2010 $ × 1.50 deflator)
ratio            1.65x
```

Florida's fatality rate per vehicle-mile is about twice Minnesota's, so 1.65x is
where a correct method should sit. This prices K and A only while Cui and
Levinson price all five severity levels, so a fully matched ratio would be
higher: 1.65x is a lower bound.

This test took three attempts. The first version compared dollars per
passenger-mile against dollars per vehicle-mile and printed PASS. The unit error
was living inside the test written to catch unit errors.

Note the vehicle-mile figure is occupancy-independent, so this validation never
depended on the occupancy value at all.

### Do the activity frequencies reproduce the published survey?

The national daily trip rate computed from the microdata is **2.28**. FHWA's
Summary of Travel Trends 2022, Table 4-5, publishes **2.28**. The regional cut
is trustworthy only because the same code, run on the whole country, lands on a
figure published independently.

### How wrong can the weakest inputs be?

Walk and bike exposure was the weakest number in the project, and until an
adversarial review of this build it was not measured at all. It was a pair of
literals carried over from a scratch script, resting on an unsourced active-
travel trip count multiplied by assumed mode shares and assumed trip lengths.
Those shares did not even sum: 90% walk plus 20% bike at one end of the stated
"range", 80% plus 10% at the other, so neither end was a coherent scenario.

It is now measured, from the same NHTS 2022 file this project already reads for
`f_k` and for occupancy:

| | old literals implied | NHTS 2022 US | NHTS 2022 South Atlantic |
|---|---:|---:|---:|
| walk, miles/person/year | 138.6 | 52.9 | 49.0 |
| bike, miles/person/year | 82.3 | 19.3 | 23.7 |

The literals overstated walking by 2.8× and cycling by 3.5×, which understated
both crash rates by the same factor. The range reported here is now the spread
between two real measurements, national and regional, rather than between two
guesses. The regional cycling figure rests on 35 surveyed trips, which is why
the national figure is reported beside it rather than discarded.

| `r_walk` | MEP change | | `r_bike` | MEP change |
|---:|---:|---|---:|---:|
| 1.16 | −23.3% | | 0.96 | −12.4% |
| 11.57 | −24.0% | | 9.59 | −24.0% |
| 12.49 | −24.0% | | 11.79 | −24.1% |
| 115.66 | −24.0% | | 95.93 | −24.2% |

Walk exposure barely matters: two orders of magnitude move the result by one
point. Bike exposure matters a great deal, which is the honest weak point of the
headline.

With **both** non-motorised rates at a tenth of the published low, MEP still
falls **11.5%**. Driving supplies 3.7 points of that, about 32%; walking and
cycling at a tenth of measured exposure still supply the other 65%. An earlier
draft claimed driving carried the whole floor, which was wrong.

---

### The safety performance function, stratified and with standard errors

The pooled curve gives an interstate and a collector the same expected
casualties at the same traffic and length. They are not the same road, and
Highway Safety Manual practice fits a separate curve per facility type.

FDOT's AADT layer carries **no functional class field** — 24 fields, checked
against the service metadata, none of them class. But the OSM network already
built for the isochrones does: every way carries a `highway` tag. Each FDOT
segment midpoint is matched to the nearest major OSM way, median distance
**65 m**, with the 7.1% matched beyond 500 m flagged as guessed rather than
dropped.

**Pooled, with standard errors** from the numerically-differentiated Hessian:

| | estimate | std err | z vs 0 | z vs 1 |
|---|---:|---:|---:|---:|
| `a` intercept | −8.3884 | 0.2083 | −40.3 | |
| `b` AADT elasticity | 0.7892 | 0.0216 | 36.6 | **−9.8** |
| `k` overdispersion | 0.9282 | | | |

`b` sits **ten standard errors below 1**, so casualties scale less than
proportionally with traffic. That was previously an assertion; it now has a
number attached.

**By facility type:**

| facility | segments | KSI | `b` | std err | `k` |
|---|---:|---:|---:|---:|---:|
| collector | 943 | 3,256 | 0.6278 | 0.0426 | 1.2131 |
| minor arterial | 445 | 3,142 | 0.7400 | 0.0576 | 0.6870 |
| principal arterial | 673 | 4,027 | 0.8092 | 0.0521 | 0.6890 |
| freeway | 787 | 3,754 | 0.8282 | 0.0467 | 1.0045 |

Collectors and freeways differ by more than three standard errors. Stratifying
is justified on AIC — **10,693.6 against 10,765.4 pooled**, an improvement of
89.8 on nine extra parameters — so Empirical Bayes now shrinks each segment
toward the curve for its own road type rather than a regional average.

**It barely moves the headline, and that is worth stating.** The
population-weighted result was unchanged at −22.5% to −22.6% at the time, because driving was
15% of the loss and the stratification only refines driving. What it buys is
defensibility of the method, not a different answer.


### The denominator: one 2025 traffic count for seven years of crashes

Every rate here divides ~6.9 years of casualties by FDOT's **2025** five-county
VMT. Two objections follow, and both are testable without new assumptions.

**Was 2020 different?** Yes, measurably, and the test needs no exposure figure
at all — deaths per 1,000 crashes is a ratio in which exposure cancels.

| year | crashes | fatal | deaths per 1,000 | vs 2019 |
|---|---:|---:|---:|---:|
| 2019 | 97,154 | 455 | 4.68 | |
| 2020 | 76,824 | 479 | 6.24 | **+33.1%** |
| 2021 | 89,884 | 562 | 6.25 | +33.5% |
| 2022 | 89,829 | 496 | 5.52 | +17.9% |
| 2023 | 87,189 | 472 | 5.41 | +15.6% |
| 2024 | 86,117 | 461 | 5.35 | +14.3% |

**2020 had 20.9% fewer crashes than 2019 and 5.3% more deaths.** That is the
documented pandemic pattern — emptier roads, higher speeds — and it is present
in this region's own records rather than imported from the literature. It did
not revert in 2021; severity stayed a third above 2019 and has decayed since.

**Does the flat denominator bias the rate?** The arithmetic is exact, because
the casualty numerator is identical on both sides and cancels:

```
r_true / r_now = (V_2025 · YEARS) / SUM_y V_y
```

Annual Florida VMT comes from FHWA Highway Statistics **Table VM-2**, one
downloaded file per year, no figure typed by hand. Traffic fell 8.1% in 2020 and
did not pass 2019 until 2022. The five-county level stays FDOT's; only the
year-to-year *shape* is taken from the statewide series, and the two sources are
checked to be commensurable first — FDOT's five counties are 14.9% of FHWA's
Florida total against about 16% of its population.

| scenario | true denominator | rates are understated by |
|---|---:|---:|
| 2025 held at 2024's level | 238.0 B veh-miles | **8.1%** |
| 2025 grown at the 2023→2024 rate | 229.6 B veh-miles | **12.0%** |
| *(flat, as used)* | *257.2 B veh-miles* | — |

**The bias runs against this report's own conclusion.** Traffic in 2019–2023 was
below the 2025 count applied to it, so the true denominator is smaller and every
crash rate here is 8% to 12% too *low*. Correcting it would make the MEP penalty
larger. It is left uncorrected: a conservative denominator needs no defending,
and the correction is smaller than the walk and bike exposure uncertainty it
would sit inside.

### Non-motorist risk by place: attempted, and a negative result

Driving risk varies by block group. Driving is 15% of the loss. **Cycling and
walking are 84%, and they carried one regional number.** Closing that was the
top item in Section 7, so it was attempted.

Two datasets made it possible, neither previously used:

- **The crash file carries `LATITUDE` and `LONGITUDE`.** Every pedestrian and
  cyclist casualty is placed directly, with no road-segment intermediary. The
  segment route matches 73% of crashes; coordinates place **99.9%**.
- **ACS table B08301 is published at block group level** — all 2,170 — giving
  walk and cycle commute share as an exposure allocator.

Placement validates against the counts computed independently in Section 2:

| | placed | actual | |
|---|---:|---:|---:|
| walk deaths | 913 | 915 | −0.2% |
| walk serious | 1,611 | 1,612 | −0.1% |
| bike deaths | 277 | 277 | 0.0% |
| bike serious | 1,261 | 1,263 | −0.2% |

**Then the model failed, informatively.** The elasticity of pedestrian casualties
to resident walking exposure is **0.017** — indistinguishable from zero. Six
allocators were fitted on a common sample of 1,913 block groups:

| allocator | elasticity | −2logL |
|---|---:|---:|
| population | −0.099 | 5838.7 |
| road density (`D3A`) | −0.010 | 5833.9 |
| nearby road VMT, 800 m | +0.012 | 5804.7 |
| **nearby road VMT, 1.5 km** | **+0.215** | **5784.2** |
| nearby road VMT, 3 km | +0.246 | 5804.6 |
| population x nearby VMT | +0.170 | 5801.1 |

With both covariates together, **nearby traffic volume predicts pedestrian
casualties about 12 times better than resident walking exposure, and cycling
casualties about 22 times better.** But the strongest elasticity reached is
**0.21**, against **0.79** for the road-segment model.

**The reading: people walk where they live, and are struck where they cross
arterials.** Those are different places, and no areal measure available here
separates them.

**Why this does not feed the headline.** With an elasticity that weak, Empirical
Bayes correctly shrinks nearly every block group toward a near-constant
expectation. The variation surviving in the rate is then dominated by
one-over-exposure — arithmetic, not risk. Publishing it as a pedestrian risk map
would repeat the identity error of Section 5 in a new costume. The rates are
written to `data/final/nonmotor_risk_by_place.csv`, labelled exploratory, and
the code refuses to substitute them into the metric.

The work is not wasted: the exposure-weighted means reconcile with the
independently-computed regional rates — walk **$12.65** against $11.57 to
$12.49, bike **$9.86** against $9.59 to $11.79 — so the machinery is right and
only the predictor is missing.

**What would change it** is a measurement, not a modelling choice: counted
non-motorist exposure at sub-regional geography, from StreetLight, Replica, or
FHWA's scalable risk assessment method.


## 6. Limitations

Stated plainly, worst first.

**The map is not a crash-risk map, and the loss surface is an identity.** The
loss at each block group reduces exactly to `Σ_k (1 − g_k)·s_ik`, a function of
mode mix alone, verified to 6.1e-16. Crash cost contributes four scalars. The
surface is informative about modal composition, which is computed here from real
routing, and it says nothing about where crashes occur. Section 5 gives the
proof. **Do not present it as a safety map.**

**Crash cost does not vary by place**, which is why the above is true. `r_k` is
one regional number per mode. Segment-level rates exist in this project for
2,429 FDOT roads, but attributing them to origins needs route assignment that is
not built.

**Cycling carries 76.8% of the loss, and its regional exposure rests on 35
surveyed trips.** The regional cycling estimate comes from 35 NHTS trip records. The
national estimate, on 298 trips, is reported alongside it and the two bracket
the range. This is the thinnest sample any headline figure depends on.

**Non-motorised exposure was wrong until an adversarial review of this build.**
It was a pair of literals from a scratch script, overstating walking by 2.8× and
cycling by 3.5×, and the mode shares behind the stated range did not sum to
100%. It is now measured from NHTS 2022. This is recorded because the figure it
produced was published in a draft and was wrong by that factor.

**AADT is a single year applied across seven.** Segment rates divide 2019 to
2025 crashes by 2025 traffic counts. 2020 is in that period.

**Deaths are counted where they happened, not where the traveller lives.** The
home address field is absent from the licensed extract, so a block group is
credited with the risk of its own roads rather than of its residents' trips.

**"Social" is the weakest activity mapping and carries the largest weight.**
NHTS "social and recreational" is dominated by visiting friends and relatives.
Those destinations are homes. The proxy is arts and entertainment employment,
which is right for a cinema and wrong for a sister's house, and it receives the
heaviest spatial equivalency factor because it is the rarest.

This is inherited, not introduced. The reference implementation maps
Social/Recreational to the same NAICS 71, so the analysis is consistent with it
by construction. But consistency with a questionable choice is not a defence of
the choice, and a population-based proxy would be more faithful to what the
survey category actually measures. Changing it unilaterally would have broken
comparability with every other MEP run, so it is reported rather than silently
fixed.

**Transit access includes two streetcar routes** whose crash cost is priced at
the fixed-route bus rate. About 2.7 miles of a 6,232-stop network.

**Departure averaging is a union, not a mean.** Travel time is averaged over the
departures at which a destination was reachable within 40 minutes. A destination
reachable at 08:00 but not at 07:45 is scored on one departure rather than
penalised for the miss, which biases marginal destinations optimistic.

**`r_transit` is a NATIONAL rate, not a Tampa Bay one.** Step 05 queries NTD
with no agency filter: all US fixed-route bus rider fatalities in collisions,
over all US bus passenger-miles, 2015-2024. That is deliberate and it is the
only defensible choice — HART and PSTA together would contribute a single-digit
number of rider deaths over a decade, and an earlier version of this project
did publish a rate resting on two events. But it means transit risk here does
**not** vary with local conditions in the way driving risk does, and a reader
comparing the two should know the geographies differ. METHOD.md carries the
arithmetic; this is the disclosure the main report was missing.

**Transit and driving are compared on different severity bases throughout.**
`r_transit` can only be fatality-only. Every driving-versus-transit statement in
this report uses the fatality-only driving rate for that reason; every statement
about driving alone uses the full deaths-and-injuries rate. The two are labelled
wherever they appear and must not be read against each other.

**The crash data is licensed.** Signal Four Analytics records contain VINs and
driver ages. Aggregates are reportable; the records are not redistributable.

---

## 7. What would change the answer

In order of how much they would move it.

1. **Place-specific crash risk.** This is now the top item, because without it
   the block-group surface is an identity in mode mix and cannot be presented as
   a safety map. Safety Performance Functions with Empirical Bayes, the Highway
   Safety Manual method, over the 2,429 FDOT segments already built here, plus
   route assignment so each origin inherits the risk of the roads its trips
   actually use. That is the change that turns four scalars into a surface.

2. **Regional non-motorised exposure with a usable sample.** NHTS 2022 gives
   Tampa's census division 35 cycling trips. StreetLight, Replica, or the FHWA
   scalable risk assessment method would replace the thinnest input behind the
   headline. Note this is no longer about *whether* it is measured, only about
   sample size.

3. **A congested skim instead of free-flow speeds.** This no longer affects any
   term — the delay term that depended on it is gone — but it would shrink every
   mode's reach, and not by the same proportion. Driving loses most in absolute
   minutes; walking loses nothing. Since cycling supplies 79% of the loss, a
   congested skim would most likely make the correction LARGER, not smaller.
   That is a prediction, and it is untested here.

4. **A destination proxy for social trips** based on population rather than
   employment, which would depart from the reference implementation and should
   be run alongside it rather than instead of it.

5. **Occupancy stratified by vehicle type.** FDOT's DVMT includes heavy trucks
   at an occupancy near 1.0, and a household-vehicle occupancy of 1.502 is
   currently applied to all of it, which understates `r_drive` somewhat. The
   Cui and Levinson validation is unaffected, since it is occupancy-independent.

---

## 8. Reproducing this

```
src/02_crashes_by_mode.py     casualties from 602,110 records
src/03_exposure_by_mode.py    denominators
src/04_injury_cost.py         r_k, and the Cui & Levinson acceptance test
src/16_opportunities.py       LODES 2023 by activity type
src/17_activity_freq.py       NHTS 2022 f_k and vehicle occupancy
src/18_centroids.py           2,170 origins
src/19_fetch_osm.py           96 Overpass tiles
src/20_build_graph.py         routable graph, three modes
src/21_isochrones.py          travel time matrices
src/22_transit.py             RAPTOR over live GTFS
src/24_acs.py                 ACS 2023 on 2020 block groups
src/25_spatial_equivalency.py national A*/A_k
src/23_mep.py                 all three equations
src/26_validate.py            the five tests in section 5
src/27_equity.py              section 4, who bears it
```

Every constant is declared once in `src/constants.py`. Every figure in this
report is printed by one of these scripts.

---

## References

Cui, M. and Levinson, D. (2019). Measuring full cost accessibility by auto.
*Journal of Transport and Land Use* 12(1), 649-672.

Delling, D., Pajor, T. and Werneck, R. (2015). Round-based public transit
routing. *Transportation Science* 49(3).

Hou, Y., Garikapati, V., Nag, A., Young, S. and Grushka, T. (2019). Novel and
practical method to quantify the quality of mobility: Mobility Energy
Productivity metric. *Transportation Research Record* 2673(10).

Savage, I. (2013). Comparing the fatality risks in United States transportation
across modes and over time. *Research in Transportation Economics* 43(1), 9-22.

Skabardonis, A., Varaiya, P. and Petty, K. (2003). Measuring recurrent and
nonrecurrent traffic congestion. *Transportation Research Record* 1856.

US DOT (2026). Benefit-Cost Analysis Guidance for Discretionary Grant Programs,
Appendix A.
