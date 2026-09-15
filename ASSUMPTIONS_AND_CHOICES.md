# Assumptions and choices — every one, explained from zero

Every project like this rests on **choices** ("we'll use this, not that") and
**assumptions** ("we'll treat this as true, because we can't measure it"). This file lists
**all of them**, explained simply.

For each one:
- **The choice** — what we did.
- **Why** — the reason.
- **The alternative** — what else we could have done.
- **If it's wrong** — what would change in the results.
- **Tested?** — whether we actually checked what difference it makes.

Other files: `MATH.md` (the calculations), `DATA.md` (the sources), `HOW_IT_RUNS_VS_STANDARD_MEP.md`
(how it runs, and how it compares with NREL's MEP).

| group | what it covers |
|---|---|
| A | what counts as harm |
| B | putting a dollar value on harm |
| C | how much travel happens |
| D | places people go |
| E | travel times |
| F | road danger |
| G | the MEP formula |
| H | combining and reporting results |
| I | summary: tested, and not tested |

**Two words first:**
- **Sensitivity test** — re-running the calculation with a different choice to see how much the answer
  moves. If it barely moves, the choice doesn't matter much.
- **Conservative** — a choice that makes our result **smaller** rather than bigger, so we're not
  overstating it.

---

## A. What counts as harm

### A1. Only deaths and serious injuries
- **The choice:** count people **killed** and **seriously injured**. Leave out minor injuries and
  damage-only crashes.
- **Why:** the crash file records injuries to people walking and cycling **only** at those two levels. To
  compare modes fairly, every mode must be counted the same way.
- **The alternative:** count all injury levels for cars (where they exist), but not for walking and
  biking.
- **If it's wrong:** crash costs are **too low**, especially for cars, which have many minor injuries. So
  our crash cost is a **lower limit** and the true drop is **bigger**. *Conservative.*
- **Tested?** No.

### A2. Count harm by who was hurt
- **The choice:** a person walking who is hit by a car counts as a **walking** casualty.
- **Why:** MEP charges each mode for what **its own travellers** pay — your own fuel, your own fare. So
  crash cost follows the same rule: the risk **you** take by travelling that way.
- **The alternative:** count it as a **driving** cost — the harm driving **causes**.
- **If it's wrong:** this choice **decides the headline**. Charged to driving, the car's crash cost rises
  from **$0.1059 to $0.1573** a mile, and cycling's own crash cost nearly disappears — and cycling causes
  most of the drop.
- **Tested?** **Yes** (step 35) — both ways are calculated and reported.

### A3. "People in vehicles" = total minus walking, cycling and motorbike
- **The choice:** the crash file doesn't directly say how many **car occupants** were hurt, so we
  subtract.
- **Why:** it's the only way with this file.
- **If it's wrong:** if the subtraction ever went below zero, occupants would be undercounted.
- **Tested?** **Yes** — the audit confirmed it never goes below zero.

### A4. Motorbikes are counted in the bill but not in the score
- **The choice:** motorbike harm ($1.89 billion a year, 697 deaths) is in the **total crash bill**, but
  not in the MEP score.
- **Why:** MEP has no motorbike mode and no energy or money settings for one.
- **If it's wrong:** the score can't include motorbikes without inventing settings.
- **Tested?** No — reported separately.

### A5. Bus harm: traffic collisions only, buses only
- **The choice:** count bus riders killed in **traffic crashes**, on **fixed-route buses**. Leave out
  assaults and robberies, trains, and dial-a-ride vans.
- **Why:** the car side only counts traffic crashes, so crime on buses would make an unfair comparison.
  Tampa has no trains.
- **If it's wrong:** crime was **57.8%** of bus rider deaths nationally; including it would roughly
  double the bus rate. But buses are **0.7%** of the score, so the drop would barely change.
- **Tested?** No.

### A6. Bus harm measured nationally
- **The choice:** use bus rider deaths across the **whole US**.
- **Why:** Tampa alone had only **2** bus rider deaths — too few to measure a rate.
- **If it's wrong:** Tampa's real bus rate could differ from the national one. Again, buses barely affect
  the score.
- **Tested?** The uncertainty is measured: the true national rate could be about **half to 1.7 times** ours.

---

## B. Putting a dollar value on harm

### B1. The US Department of Transportation's values
- **The choice:** **$13.7 million** per death, **$1,302,300** per serious injury.
- **Why:** the official values US governments use to decide whether safety projects are worth paying for.
- **The alternative:** other countries' values, or values based on medical and work costs only.
- **If it's wrong:** every crash cost scales up or down. Because of the "60% per dollar" rule (see
  `MATH.md`), biking would still lose almost everything unless the values were **far** lower.
- **Tested?** Indirectly — the bike sensitivity test (H4) shows the drop barely moves unless bike crash
  cost falls to about a tenth.

### B2. Per-person values, not per-crash values
- **The choice:** the government publishes two tables — **per injured person** and **per crash**. We use
  per person.
- **Why:** we count **people**. Using per-crash values on counts of people was one reason an early version
  came out **8 times too high**.
- **Tested?** **Yes** — the Minnesota check (B4) fails if the conventions are mixed.

### B3. A dollar of crash cost counts the same as a dollar of money cost
- **The choice:** crash cost is **added to the money cost** in MEP's formula, with the **same weight**
  (−0.5 per dollar).
- **Why:** MEP already has a weight for dollars. Using it needs no new evidence, and doesn't change MEP's
  formula.
- **The alternative:** give crash cost its **own** weight — people may care about crash risk more or less
  than money.
- **If it's wrong:** this is the biggest untested choice. At $10 a mile for biking, the same weight
  **switches cycling off** almost completely.
- **Tested?** **Only partly.** A Dutch study's much bigger weight (the "Amsterdam weight", 11.32) is kept
  as a side test. **Varying the weight properly is not done.**

### B4. Checking against Minnesota
- **The choice:** accept our car crash cost only if it's **1.2 to 3.0 times** the Minnesota study's.
- **Why:** Florida's roads are about **twice as deadly per mile** as Minnesota's. Below 1.2× would be
  suspiciously low; above 3× would suggest something counted twice.
- **If it's wrong:** the band could pass a slightly wrong number. It did catch the 8× error.
- **Tested?** **Yes** — result **1.65×**. A stricter version counting all injury levels on both sides was
  never done.

### B5. Adjusting old dollars to today's dollars
- **The choice:** multiply the Minnesota 2010 figure by **1.50** = today's value of a death ÷ theirs
  ($13,700,000 ÷ $9,134,786).
- **Why:** crash costs are mostly the value of a life, so adjusting by that value matches like with like.
- **The alternative:** general price inflation, which gives **1.44**.
- **If it's wrong:** the ratio would be about 1.72× instead of 1.65× — still passes.
- **Tested?** Both figures noted.

---

## C. How much travel happens

### C1. One year of traffic (2025) for seven years of crashes
- **The choice:** divide 2019–2025 crashes by **2025** traffic × 6.9 years.
- **Why:** Florida DOT's five-county figure is for one year.
- **If it's wrong:** traffic was lower in most earlier years, so **our crash rates are 8–12% too low**.
  *Conservative.*
- **Tested?** **Yes** (step 34) — measured, and deliberately left uncorrected.

### C2. One "people per car" figure for all vehicles
- **The choice:** **1.502**, measured from the travel survey, applied to all driving.
- **Why:** it's the best local measure available.
- **If it's wrong:** trucks and delivery vans usually carry only the driver. Counting them at 1.502
  **overstates** passenger-miles, so the car crash cost is a little **too low** (the audit guessed 5–8%).
- **Tested?** No.

### C3. People per car from drivers' trips only
- **The choice:** use only trips where the person was **driving**.
- **Why:** otherwise a car trip with 3 people is counted 3 times, and the answer comes out much too high.
- **Tested?** **Yes** — the audit rebuilt it with its own code: same answer.

### C4. Walking and biking miles from the travel survey
- **The choice:** miles per person from NHTS 2022 × population. Two versions: **national** and **regional**,
  reported as a range.
- **Why:** there's no count of walking or biking for Tampa Bay itself.
- **If it's wrong:** walking and biking crash costs move in the opposite direction. The regional biking figure
  rests on only **35 trips**.
- **Tested?** **Yes** — see H4. Halving or multiplying by ten barely changes the drop; only a tenth does.

### C5. Population in July 2022
- **The choice:** **3,468,871** people, the Census estimate for mid-2022.
- **Why:** crash cost is an **average over ~7 years**, so it should be divided by the **average** population.
  Mid-2022 is the middle of the period.
- **The alternative:** the 2024 figure (bigger), or the neighbourhood table's total (**3,399,162**).
- **If it's wrong:** a bigger population → more walking and biking miles → lower crash cost per mile. Using
  3,399,162 would make cost per person **$3,155** instead of $3,092.
- **Tested?** No — the gap between the two population figures isn't explained yet.

---

## D. Places people go

### D1. Jobs stand in for places
- **The choice:** a restaurant's "size" = how many people work there (LODES jobs).
- **Why:** there's no free, complete list of every place. Paid lists (CoStar, Google Places) can't be checked
  by anyone else.
- **The alternative:** count **places** (one restaurant = 1).
- **If it's wrong:** big places count more than small ones. Raw scores change size, but NREL found the
  **pattern** of scores matches either way — so we compare only percentages.
- **Tested?** Not by us. NREL's South Florida report compared both kinds of data and found similar patterns.

### D2. Which job types count as which places
- **The choice:** restaurants = food and hotels; fun = arts and entertainment; school = education **plus**
  "other services".
- **Why:** each is the closest single business type. "Other services" is the only type that includes
  religious organisations.
- **If it's wrong:** "school" also includes repair shops and hair salons. And "fun" is arts jobs, while most
  social trips are **visits to people's homes**.
- **Tested?** No. NREL's South Florida report uses the same match for "social".

### D3. Scaling by national totals, with restaurants as the reference
- **The choice:** each kind of place is scaled by **US** totals, with restaurants = 1.
- **Why:** MEP's own definition. National totals keep every city scaled the same way.
- **The alternative:** Tampa's own totals — which gave arts a silly weight of **52**; or "work" as the reference
  — which made every score **11 times too big**.
- **If it's wrong:** it would change the size of scores, not the percentages.
- **Tested?** **Yes** — both wrong versions were run, caught, and fixed.

### D4. Trip shares from "big South Atlantic cities"
- **The choice:** how often people go to each kind of place, from the NHTS 2022 survey for large cities in the
  South Atlantic region.
- **Why:** the 2022 survey has **no Florida-only field**. You chose the newest data over 2017 (which did have
  Florida figures).
- **If it's wrong:** trip shares may differ a little in Tampa Bay. Doctor visits rest on only **68 trips**.
- **Tested?** The survey code was checked (national trips per day = 2.28, exactly the published figure). The
  uncertainty of each share was **not** measured.

### D5. Neighbourhoods, not a grid of squares
- **The choice:** Census **block groups** (2,170).
- **Why:** crash, population and car data all come by neighbourhood already.
- **The alternative:** NREL's grid of small squares.
- **If it's wrong:** less detail inside large neighbourhoods.
- **Tested?** No.

### D6. One starting point per neighbourhood
- **The choice:** every trip starts from the Census **interior point**.
- **Why:** it's guaranteed to be inside the neighbourhood (the exact middle of a C-shaped area isn't).
- **If it's wrong:** in large neighbourhoods, people who live far from that point would really have
  different travel times.
- **Tested?** No, but places **inside** your own neighbourhood get a real travel time based on its size (E4).

---

## E. Travel times

### E1. Empty roads — no traffic jams
- **The choice:** car speeds = the speed limit (or a typical speed for that road type).
- **Why:** no free source of traffic data for every road.
- **If it's wrong:** everyone reaches **more** places than they really would at rush hour. Cars would lose the
  most minutes, which would make biking a bigger share of the score — so the drop would *probably* be
  **bigger**. *That's a guess.*
- **Tested?** No.

### E2. Bikes: 12 mph on every road except motorways and steps
- **The choice:** as stated.
- **Why:** NREL's South Florida report did the same in its basic version.
- **The alternative:** only roads with bike lanes, or safer quiet streets — which is how many cyclists
  actually ride.
- **If it's wrong:** bikes can "reach" places along busy 55 mph main roads nobody would ride on. That makes
  cycling's share of the score **bigger**, and so the drop bigger.
- **Tested?** Compared with NREL's method (same). A version limited to safer roads was **not** tried.

### E3. Walking at 3 mph, not on motorways
- **The choice:** as stated.
- **Why:** a normal walking pace.
- **Tested?** No.

### E4. A real travel time inside your own neighbourhood
- **The choice:** (2/3) × √(area ÷ π) ÷ speed, not zero.
- **Why:** with zero, big rural neighbourhoods got instant access to everything inside them — **319**
  neighbourhoods are too big to walk across in 10 minutes.
- **Tested?** **Yes** — the audit found the zero version, and it was fixed.

### E5. Trips stop at 40 minutes
- **The choice:** travel times are only worked out up to 40 minutes.
- **Why:** MEP's longest band is 40 minutes; nothing beyond it counts.
- **If it's wrong:** it doesn't change the score. But it means NREL's "faster driving" test can only show
  **direction**, not size (driving 3× faster can't add places that were never measured).
- **Tested?** Noted.

### E6. Bus trips on a Thursday
- **The choice:** Thursday 17 September 2026.
- **Why:** PSTA's weekday schedule runs Monday–Thursday; HART's Monday–Friday. Thursday is when **both** run
  normally.
- **If it's wrong:** weekend service is thinner; this represents a normal weekday only.
- **Tested?** No — but a Friday was checked and found to drop every PSTA bus.

### E7. Leaving at 7:45, 8:00 and 8:15, averaged
- **The choice:** three departure times.
- **Why:** with one time, a stop whose bus left at 7:59 would look terrible, unfairly.
- **If it's wrong:** a place reachable at 8:00 but **not** at 7:45 still counts as reachable, using just the
  8:00 time. That's **generous** to buses.
- **Tested?** No.

### E8. Up to 10 minutes' walk to a bus stop; up to two changes
- **The choice:** as stated; changes between stops up to 300 m apart, × 1.4 for street detours.
- **Why:** almost no real trips need three changes; most people won't walk far to a stop.
- **Tested?** No.

### E9. A bus trip only counts if you actually got on a bus
- **The choice:** as stated.
- **Why:** without it, some "bus trips" were really just walking to a stop and away again.
- **Tested?** **Yes** — the audit found it, and it was fixed.

---

## F. Road danger

### F1. State roads only
- **The choice:** the road-danger model uses the **2,848** state road segments with traffic counts.
- **Why:** local and county roads have no traffic counts, so no rate can be worked out.
- **If it's wrong:** state roads carry **78.5%** of driving. Whether local roads are safer or more dangerous per
  mile is unknown, so the direction of any error is **unknown**.
- **Tested?** No.

### F2. Road type from the nearest OpenStreetMap road
- **The choice:** Florida DOT's file has no road type, so each segment takes the type of the nearest major
  OpenStreetMap road.
- **Why:** the only source available.
- **If it's wrong:** a few segments could get the wrong type.
- **Tested?** Splitting by road type was **tested** — it fits better, even after a penalty for complexity.

### F3. Uneven crash counts (negative binomial)
- **The choice:** a model built for very uneven counts.
- **Why:** crash counts spread **23 times** more than a simple model expects.
- **Tested?** The spread was measured. A formal statistics test comparing the two models was **not** run.

### F4. Blending prediction with each road's real record (Empirical Bayes)
- **The choice:** the standard road-safety method — little history leans on the prediction, long history leans
  on the real count.
- **Why:** it's in the Highway Safety Manual, and it stops quiet roads with one unlucky crash from topping the list.
- **Tested?** **Yes** (step 36) — fitted on 2019–22, it predicted 2023–25 with **the smallest error** of three
  methods. At picking the very worst roads, it tied with raw past counts.

### F5. Pulling each road's share of deaths toward the regional average
- **The choice:** pretend every road had **10 extra casualties** at the regional death share (9.5%).
- **Why:** 51 roads came out "100% deadly" from one or two casualties.
- **The alternative:** a different number than 10, or the regional share for every road.
- **If it's wrong:** the spread of road danger would be a little different.
- **Tested?** Partly — the spread of road danger fell from 8× to 6×, as expected.

### F6. Neighbourhood driving danger = nearby busy roads
- **The choice:** a weighted average of road danger; roads count more if **busy** and **close**, using MEP's time
  weight (−0.08 per minute).
- **Why:** there's no data on people's actual routes.
- **If it's wrong:** roads within about 10 minutes dominate, but the result is used for **40-minute** trips too.
- **Tested?** No.

### F7. Walking and biking danger: one number for the whole region
- **The choice:** don't make walking and biking danger vary by neighbourhood.
- **Why:** tried (step 32) — nothing predicted *where* walking and biking crashes happen well enough.
- **If it's wrong:** walking and biking make **84%** of the drop, but their danger is the same everywhere. That's
  why the map is mostly about travel habits.
- **Tested?** **Yes** — six approaches tried; best signal too weak.

---

## G. The MEP formula

### G1. MEP's own settings, unchanged
- **The choice:** energy, money and time weights, and each mode's energy and money cost, exactly as in MEP's
  default table.
- **Why:** so the result is MEP, not a new score, and can be tested with NREL's own tests.
- **Tested?** **Yes** — passes NREL's tests.

### G2. Walking and biking have zero energy and zero money cost
- **The choice:** MEP's default.
- **Why:** it's MEP's setting.
- **If it's wrong:** this is **why** cycling gets so much credit in the normal score, and why adding crash cost
  changes it so much.
- **Tested?** No — kept as MEP's setting on purpose.

### G3. MEP counts what you **could** reach, not what people **do**
- **The choice:** kept as MEP designs it.
- **Why:** MEP measures **opportunity**, not behaviour.
- **If it's wrong for Tampa Bay:** cycling is **17.7%** of the score but only **1.8%** of real trips (0.5% of
  commutes). So most of the drop removes cycling people mostly don't do. A rough estimate weighted by real
  travel gives a drop of about **13%**, not 23%.
- **Tested?** **Only roughly.** A proper version is not built.

### G4. Four modes only
- **The choice:** car, bus, walk, bike.
- **Why:** MEP's four core modes.
- **The alternative:** MEP's default table also includes Uber/Lyft and dial-a-ride.
- **If it's wrong:** Uber/Lyft is **1%** of trips here. Effect on the drop is unknown.
- **Tested?** No. **No reason was written down** for leaving Uber/Lyft out.

### G5. No crash-caused traffic-jam time
- **The choice:** no extra minutes for jams caused by crashes.
- **Why:** it was built, but the minutes were typed in by hand and no step calculated them, so they couldn't be
  defended.
- **If it's wrong:** with it, the drop was **24.9%** instead of 22.5%. *Conservative.*
- **Tested?** **Yes** — both measured.

---

## H. Combining and reporting results

### H1. Weight neighbourhoods by population
- **The choice:** MEP's rule — more people, more weight.
- **Tested?** **Yes** — three ways compared: population-weighted **22.5%**, plain average **23.8%**, average of each
  neighbourhood's own drop weighted by people **20.6%**.

### H2. Report percentages and rankings, never raw scores against other cities
- **Why:** the raw score depends on how places are counted (NREL: 11,983 vs 122.35 for one region).

### H3. Leave the traffic-year correction unapplied
- **Why:** so the result stays **conservative** (C1).

### H4. Walking and biking crash cost reported as a range
- **Tested?** **Yes**:

  | bike crash cost per mile | drop (plain average) |
  |---:|---:|
  | $0.96 (a tenth) | 12.2% |
  | $4.80 (half) | 22.3% |
  | **$9.59 (ours)** | **23.8%** |
  | $95.93 (ten times) | 24.0% |

  With **both** walking and biking at a tenth, the drop is **11.5%**.

### H5. "Not a crash-danger map"
- **The choice:** never present the neighbourhood map as showing where crashes are worst.
- **Why:** only **1.3%** of the differences between neighbourhoods come from local danger.
- **Tested?** **Yes** — measured.

---

## I. Summary: tested, and not tested

### Tested — we know what difference it makes

| choice | what we found |
|---|---|
| who pays when a car hits someone (A2) | changes the answer a lot — both reported |
| per-person vs per-crash values (B2) | mixing them gave 8× — fixed |
| one year of traffic (C1) | our rates 8–12% too low — conservative |
| walking and biking miles (C4, H4) | only a tenth changes the drop much |
| scaling reference (D3) | wrong reference = 11× score size; percentages unchanged |
| own-neighbourhood travel time (E4) | zero was wrong — fixed |
| road types (F2) | better fit |
| blend vs other methods (F4) | smallest prediction error |
| walking and biking danger by place (F7) | too weak to use |
| MEP's settings (G1) | passes NREL's tests |
| traffic-jam minutes (G5) | 24.9% with, 22.5% without |
| combining neighbourhoods (H1) | 20.6–23.8% depending on method |

### Not tested — the open questions

| choice | why it matters |
|---|---|
| **same weight for crash dollars and money dollars (B3)** | the biggest untested choice — decides how completely cycling is "switched off" |
| **what people could reach vs what they do (G3)** | only a rough estimate (~13%) |
| **bikes on every road except motorways (E2)** | may overstate cycling's share |
| no traffic jams (E1) | probably makes the drop bigger — a guess |
| minor injuries left out (A1) | makes crash cost a lower limit |
| one people-per-car for trucks too (C2) | car crash cost a little too low |
| state roads only (F1) | direction unknown |
| near-home road weighting for long trips (F6) | unknown |
| generous bus averaging (E7) | flatters buses slightly |
| trip-share uncertainty (D4) | doctor visits rest on 68 trips |
| Uber/Lyft (G4) | unknown; no reason recorded |
| population figure gap (C5) | $3,092 vs $3,155 per person |
