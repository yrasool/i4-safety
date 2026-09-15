# What I did — explained from the beginning

Last updated: 14 September 2026

This file explains the whole Tampa Bay crash project **as if you have never heard
of any of it**. Every idea is explained once, in plain words, with small examples
and the reason behind it.

**How to read it:** go top to bottom. Each part builds on the one before.

| part | what it tells you |
|---|---|
| 1 | the words you need to know |
| 2 | the results — every number, and what each one says |
| 3 | why the score drops |
| 4 | what the results mean — and what they do **not** mean |
| 5 | every dataset: what it is, what we took from it, its limits |
| 6 | the calculations, following one neighbourhood from start to finish |
| 7 | how our version is different from NREL's MEP |
| 8 | how we know it is right |
| 9 | everything that went wrong and got fixed |
| 10 | what is still weak or not done, and what to say |
| 11 | what we left out on purpose — why, and what it changes |
| 12 | how the headline number changed over time |
| 13 | what happened each day |
| 14 | what every file is |

---

# Part 1 — The words you need

Read these first. Everything else uses them.

**MEP** — a score made by NREL (a US government energy lab). For each
neighbourhood it asks: *"If you live here, how many useful places can you get to,
and how easily?"* A higher score means better connected.

**Neighbourhood** — the Census splits the country into small areas called
**block groups**, usually a few hundred to a few thousand people. Our five
counties have **2,170** of them. In this file, "neighbourhood" means one of these.

**The five counties** — Hillsborough, Pinellas, Pasco, Hernando and Citrus. This
is Florida's transport District 7, the Tampa Bay area.

**Mode** — a way of travelling. MEP uses four: **car, bus, walking, bike**.

**Places / destinations** — somewhere people go: work, shops, restaurants,
doctors, schools, fun places.

**Crash harm** — people **killed** or **seriously injured** in traffic crashes.

**Crash cost** — to add crash harm to MEP, we turn it into dollars, using the
amounts the US Department of Transportation uses for its own decisions:
**$13.7 million per death** and **$1,302,300 per serious injury**. These are not
"what a life is worth" — they are the standard figures governments use to decide
whether a safety project is worth paying for.

**Passenger-mile** — one person travelling one mile. A car with 2 people driving
10 miles = **20 passenger-miles**.

**Crash cost per mile** — the crash cost of a mode ÷ the passenger-miles people
travel that way. It lets us compare modes fairly.

**Pipeline** — the chain of 26 small programs that do the whole project in order.
Each one is a **step** with a number, like "step 23".

---

# Part 2 — The results

## The main result

| | MEP score |
|---|---:|
| the normal way, without crash cost | **7,567** |
| with crash cost added | **5,863** |
| **drop** | **22.5%** |

**What this says:** when you count the cost of people being killed and hurt, Tampa
Bay is about **a fifth less connected** than the normal MEP score makes it look.

**How the region's score is made:** every neighbourhood gets its own score, then
they are combined, **giving more weight to neighbourhoods where more people live**
— MEP's own rule. A neighbourhood with 3,000 people counts three times as much as
one with 1,000.

**Two other ways of combining, for comparison:**

| way of combining | drop |
|---|---:|
| weighted by population (**MEP's rule — the one we use**) | **22.5%** |
| using the higher walking and biking crash costs | 22.6% |
| plain average, every neighbourhood equal | 23.8% |

**What this says:** the answer barely changes (22.5–23.8%), so it doesn't depend on a
lucky choice of method.

**Two warnings:**
- There is **no official MEP score for Tampa Bay**. We calculated **both** numbers.
- Only compare **percentages**, never the raw score with another city. NREL's own
  tool gave **11,983** for one region counting jobs and **122.35** for the same region
  counting buildings. The raw number depends on how you count.

## By county

| county | normal | with crash cost | drop |
|---|---:|---:|---:|
| Hillsborough | 11,017 | 8,322 | 24.5% |
| Pinellas | 8,861 | 6,748 | 23.8% |
| Pasco | 3,569 | 2,950 | **17.3%** |
| Hernando | 1,339 | 986 | 26.4% |
| Citrus | 487 | 346 | **28.9%** |

**What this says:**
- **Hillsborough and Pinellas have the highest scores** — they are cities, with lots of
  places close together.
- **Pasco drops least** because its score is mostly driving, and driving loses little.
- **Citrus drops most** — its score leans more on biking and walking, which lose almost
  everything once crash cost is added (Part 3).

## Neighbourhoods

| neighbourhood | normal | with crash cost | drop |
|---|---:|---:|---:|
| best-connected (in Hillsborough) | 25,095 | 14,253 | **43%** |
| a middle one (in Hillsborough) | 8,434 | 6,607 | 22% |
| the lowest | 0 | 0 | — |

**What this says:**
- **The best-connected places lose the most.** Dense city centres have many places you
  could bike or walk to, and that's exactly what crash cost removes.
- **The zeros are water** — Census areas that are mostly lake or bay, with nobody living
  there.

**Does the order of neighbourhoods change?**
- **99%** of neighbourhoods move at least one place in the ranking.
- But the **typical move is only 34 places** out of 2,170.
- The before and after rankings match **0.991** (1.000 would be identical).

**What this says:** almost every neighbourhood shifts a little, but the best places stay
near the top and the worst near the bottom.

## Which mode causes the drop

| mode | share of the drop |
|---|---:|
| **bike** | **79.5%** |
| car | 15.4% |
| walk | 5.1% |
| bus | about 0% |

**What this says:** four-fifths of the drop is **cycling**. Part 3 explains why.

## Who is hit hardest

We split neighbourhoods into five equal groups, from fewest to most households
**without a car**:

| households without a car | drop |
|---|---:|
| fewest | 20.4% |
| second | 20.3% |
| middle | 21.0% |
| fourth | 23.1% |
| most | **24.9%** |

**What this says:** neighbourhoods where more people have **no car** lose more — the
people with the fewest choices are the ones whose access MEP was overstating most.

**Careful:** the bottom two groups are basically tied, so it's a trend, not a perfect
staircase. And it is a **link, not a cause** — carless neighbourhoods are also denser and
more walkable, which could explain it on its own.

## The crash bill

| who was hurt | killed | seriously injured | crash cost per year |
|---|---:|---:|---:|
| people in vehicles | 1,582 | 14,774 | $5.93 billion |
| people walking | 915 | 1,612 | $2.12 billion |
| people on motorbikes | 697 | 2,656 | $1.89 billion |
| people cycling | 277 | 1,263 | $0.79 billion |
| **total** | **3,471** | **20,305** | **$10.72 billion** |

**What this says:**
- That's about **$3,092 for every person living here, every year**.
- **34.3%** of all people killed were walking or cycling — although very few trips are
  made that way.

## Crash cost next to what MEP already charges

- For **driving**, crash cost is **22.1%** of the money MEP already charges (petrol,
  car costs).
- Comparing **deaths only** with buses: crash cost is **11.7%** of driving's money cost,
  but only **0.12%** of the bus fare cost — about **95 to 1**.

**What this says:** leaving crash cost out treats driving and buses very unevenly. It
flatters the car much more than the bus.

## Driving danger by neighbourhood

Each neighbourhood gets its own driving crash cost, from the roads near it:

| | crash cost per passenger-mile |
|---|---:|
| safest neighbourhood | $0.08 |
| typical neighbourhood | $0.10 |
| most dangerous | $0.40 |

| county | typical neighbourhood |
|---|---:|
| Hernando | **$0.17** |
| Citrus | $0.15 |
| Pasco | $0.13 |
| Pinellas | $0.10 |
| Hillsborough | **$0.09** |

**What this says:** driving in rural Hernando is about **twice as dangerous per mile** as in
Hillsborough — faster roads, longer distances.

**But:** only **1.3%** of the differences between neighbourhoods' scores come from this
local danger. The other **98.7%** comes from **which modes each place relies on**. And
three-quarters of the local danger is simply **which county you're in**. So this is a
county-level adjustment, **not a crash-danger map**.

## Who pays when a car hits someone walking or cycling? (step 35)

- **99.0%** of people killed while walking, and **98.6%** of people killed while cycling,
  were in a crash involving a car.

| way of counting | driving's crash cost per mile |
|---|---:|
| harm to people **inside** the car (what we use) | $0.1059 |
| harm driving **causes** to everyone | $0.1573 |
| harm driving does to people **outside** the car | **$0.0514** — $2.88 billion a year |

**What this says:** we charge each mode for what **its own travellers** suffer, the same
way MEP charges your own fuel and fare. But if you charge driving for the people it
hits instead, cycling's own crash cost almost disappears. **This choice changes the
answer**, so we show both.

## Is one year of traffic fair for seven years of crashes? (step 34)

- We divide 7 years of crashes by traffic from **one** year, 2025.
- Florida drove **8.1% less in 2020**, and didn't get back to 2019 levels until 2022.
- So 2025's traffic is **higher** than most of those years.

**What this says:** our crash rates are **8–12% too low**, not too high. Our numbers are
**on the cautious side**. We left it that way on purpose.

**Also found:** in 2020, crashes fell **21%** but deaths **rose 5%** — emptier roads,
faster driving. That's in our own records, not borrowed from elsewhere.

## Does the road-danger model predict the future? (step 36)

We trained it on **2019–2022** only, then asked it to predict **2023–2025**, road by road,
and compared with what really happened:

| method | average error per road | share of casualties found on its "worst 10%" of roads |
|---|---:|---:|
| just use the road's past count | 1.143 | 81.8% |
| just use traffic and length | 1.287 | 74.1% |
| **our blend of both** | **1.123** | **82.5%** |

*(Lower error is better. All three are first adjusted to the real 2023–25 total, so a
safer period can't favour any method.)*

**What this says:**
- **Our method has the smallest error** — and when we re-tested 2,000 times with shuffled
  roads, that stayed true. **It's real.**
- **At picking the very worst roads, it ties with the past count** — the difference is too
  small to claim.

**Also:** 2023–25 really was different — deaths in cars fell 22%, serious injuries 33%, but
cycling casualties **rose 5%**.

---

# Part 3 — Why the score drops

## Step 1: a score is points from each mode

Imagine one neighbourhood with **100 points**, split the way our whole region is:

| mode | points |
|---|---:|
| car | 80 |
| bike | 18 |
| walk | 1 |
| bus | 1 |

**Where this split comes from:** not a report or a standard number. **Our own calculation**,
from how many places each mode can reach within 40 minutes (Part 6).

## Step 2: the more a mile costs, the fewer points a mode keeps

MEP's rule works out to: **every extra $1 per mile keeps only about 60% of the points left.**

| cost per mile | points kept |
|---:|---:|
| $0 | 100% |
| $1 | 61% |
| $2 | 37% |
| $5 | 8% |
| $10 | under 1% |

## Step 3: crash cost per mile — tiny for cars, huge for bikes

| mode | crash cost per year | miles per year | crash cost per mile |
|---|---:|---:|---:|
| car | $5.93 billion | 56 billion | **$0.11** |
| bike | $0.79 billion | 82 million | **$9.59** |

**Why is the bike number so high?** Bikes cause less harm in total, but it's spread over
**far fewer miles**. A $100 bill split between 50 people is $2 each; a $50 bill split
between 2 people is $25 each. Cycling is the second table.

## Step 4: put it together

| mode | points before | crash cost per mile | points kept | points after |
|---|---:|---:|---:|---:|
| car | 80 | $0.11 | 95% | 75.9 |
| **bike** | **18** | **$9.59** | **0.8%** | **0.15** |
| walk | 1 | $11.57 | 0.3% | 0.00 |
| bus | 1 | $0.001 | 99.9% | 1.0 |
| **total** | **100** | | | **77.0** |

The score falls about **23 points**, and **about 18 of them are bike points**.

---

# Part 4 — What the results mean

## What they DO mean

**1. MEP, as normally used, makes Tampa Bay look better connected than it is.**
It treats walking and biking as free and ignores crashes. Counting crash harm, the region
is about a fifth less connected.

**2. The missing cost is not even.** It is small for cars and buses, but enormous per mile
for walking and biking. So the normal MEP score is most wrong about exactly the modes it
praises most.

**3. It lands hardest on people with fewer choices.** Neighbourhoods with more carless
households lose more. For them, walking, biking and the bus aren't a lifestyle choice —
and those are the modes whose danger MEP hides.

**4. Making cycling safer would count as better access.** If bike crash cost per mile
fell, cycling would get its points back. In this way of thinking, a safety project is also
an access project. *(That's what the formula implies — we haven't tested any real project.)*

## What they do NOT mean

**1. Not "a fifth of Tampa Bay's access is lost to crashes" in everyday life.** MEP counts
where people **could** go, not how they **actually** travel. Cycling is **18%** of the score
but only **1.8%** of real trips here. So most of the drop removes cycling that people mostly
don't do. Weighted by real travel, a rough estimate is about **13%**, not 23%.

**2. Not a map of where crashes are worst.** Only 1.3% of the differences between
neighbourhoods come from local danger.

**3. Not "cycling is bad" or "people shouldn't cycle".** It means cycling **here** is very
dangerous per mile, and a score that ignores that is misleading.

**4. Not comparable with other cities' MEP numbers.** Only percentages and rankings.

## The cycling picture, checked

**Why people bike here** (travel survey):

| what the bike trip was for | whole US (298 trips) | our region (35 trips) |
|---|---:|---:|
| exercise, fun, social | 37.5% | **68.7%** |
| going home | 32.8% | 15.7% |
| school | 11.0% | 0% |
| shopping or errands | 6.3% | 8.3% |
| **work** | 6.6% | **0%** |

Most bike trips here are **exercise or fun**, and none of the surveyed trips were to work.
*Only 35 trips were surveyed here — a strong hint, not proof.*

**When cyclists are killed or badly hurt here** (our crash records, 1,540 people):

| when | share hurt | share killed |
|---|---:|---:|
| weekday rush hour | 28.1% | 25.6% |
| weekday daytime | 28.4% | 17.0% |
| weekend daytime | **14.2%** | 15.2% |
| night | 29.3% | **42.2%** |

Weekend daytime — typical exercise time — is only **14%**. And **42% of cyclists killed
died at night.** Many of the people hurt seem to be riding **to get somewhere**, perhaps
without a car. *That's a hint from timing, not proof of who they were.*

**Putting both together:** most **bike trips** here are exercise, but much of the **serious
harm** happens to people who look like they're using a bike to get around. MEP overstates
cycling as an everyday option **and** hides how dangerous it is for those who depend on it.

## How to say it in the interview

> "MEP measures what people *could* reach, not how they travel. Here, cycling is 18% of
> the score but under 2% of trips, so most of my correction lands on a mode few people use
> — weighted by real travel it would be roughly half. But the crash timing suggests the
> people who do bike are often riding to get somewhere, often at night, so for them MEP's
> 'cycling is free' is badly wrong."

---

# Part 5 — Every dataset

Everything is **free and public**, except the crash records, which we are allowed to use
but **must not share**. Almost every file is saved on the computer (three downloads aren't — see `DATA.md`), so the same answer comes out every time.

### 1. Crash records
- **What it is:** police reports of every traffic crash, from Signal Four Analytics (a
  University of Florida system).
- **Covers:** January 2019 to November 2025 — about **6.9 years**. **602,110 crashes**, 527 MB.
- **What we take:** how many people were killed or seriously injured, whether they were in a
  vehicle, walking, cycling or on a motorbike, the date and time, the road and the map
  location.
- **What we never take:** vehicle ID numbers or driver ages.
- **Limits:** it records injuries to people walking and cycling only as "killed" or
  "seriously injured", not minor ones. November 2025 isn't complete.

### 2. Road and footpath map
- **What it is:** OpenStreetMap — a free world map built by volunteers, like Wikipedia for
  maps.
- **What we take:** every road and path in the five counties, its type (motorway, main
  road, footpath...), and its speed limit where recorded. **495,508 roads.**
- **Limits:** only **10%** of roads have a speed limit recorded, so the rest get a typical
  speed for that kind of road.

### 3. Bus timetables
- **What it is:** the published schedules of HART (Hillsborough) and PSTA (Pinellas), in the
  standard format apps like Google Maps use.
- **What we take:** every stop, route and departure time. **6,232 stops, 4,308 trips** on
  our chosen day.
- **Limits:** a schedule, not real arrival times — buses running late aren't included.

### 4. Jobs by type and place (LODES)
- **What it is:** a Census count of **how many jobs are in each tiny area** (about a city
  block), built from records employers already send to the government.
- **Year:** 2023, the newest.
- **What we take:** jobs in our five counties, sorted by type of business — **1,570,813 jobs**
  — plus national totals for scaling.
- **Why:** there's no free list of every shop and restaurant, so jobs stand in for places. A
  restaurant with 30 staff counts as 30.
- **Limits:** measures the **size** of places, not how many there are; misses self-employed
  people; the Census adds small random changes to protect privacy.

### 5. Travel survey (NHTS)
- **What it is:** a national survey where households record every trip they make for a day.
- **Year:** 2022, the newest. You asked for the latest data, not 2017.
- **What we take:** how often people make each kind of trip; how many people are in a car;
  how far people walk and bike in a year.
- **Limits:** there's no Florida-only breakdown, so we use "big cities in the South Atlantic
  region". Some answers rest on few trips — biking on **35**.

### 6. Population, cars and commuting (Census ACS)
- **What it is:** a Census survey averaged over 2019–2023, reported for each neighbourhood.
- **What we take:** how many people live there, how many households have no car, how people
  get to work.
- **Limits:** "how people get to work" only covers commuting, not shopping or fun.

### 7. Traffic on state roads (Florida DOT)
- **What it is:** Florida's list of state road stretches with daily traffic counts.
- **What we take:** **2,848 road stretches** — where each starts and ends, and how many vehicles
  use it a day.
- **Limits:** state roads only, not local streets; one year (2025); no road type.

### 8. Total driving in the five counties (Florida DOT)
- **What it is:** one number — **102 million vehicle-miles a day**, on all public roads.
- **What we take:** it, to work out how much driving happens.

### 9. Florida driving by year (federal highway statistics)
- **What it is:** total miles driven in Florida each year, 2019–2024.
- **What we take:** how much driving went up and down over the years.
- **Limits:** statewide, not just our five counties.

### 10. Bus crashes and bus miles (National Transit Database)
- **What it is:** the federal record of safety events and passenger-miles for every US
  transit agency.
- **What we take:** bus riders killed in traffic crashes, and bus passenger-miles, across the
  whole US, 2015–2024: **12 deaths**.
- **Limits:** records no serious bus injuries at all; a national rate, not Tampa's.

### 11. EPA accessibility data
- **What it is:** an EPA dataset estimating jobs reachable within 45 minutes by car and by bus
  for each neighbourhood.
- **What we take:** used **only to check** our own travel times.
- **Limits:** built on older (2018) neighbourhood boundaries, so only 1,670 match ours.

### 12. Population in mid-2022 (Census estimates)
- **What it is:** the Census's yearly population estimate.
- **What we take:** **3,468,871** people, for July 2022.
- **Why July 2022, when 2023 and 2024 exist:** crash cost is an **average over about 7 years**.
  To share an average fairly, divide by the average population over those years — and
  mid-2022 is the **middle** of the period. It's used for cost per person, and for total
  walking and biking miles (miles per person × population).

### 13. Crash costs (US Department of Transportation)
- **What it is:** the official dollar figures for deaths and injuries, 2024 dollars.
- **What we take:** **$13.7 million per death**, **$1,302,300 per serious injury**.

### 14. MEP settings (NREL/FIU South Florida report)
- **What it is:** the report where NREL and Florida International University ran MEP on South
  Florida.
- **What we take:** MEP's energy and money cost for each mode, the weights in the formula, bikes
  at 12 mph, and restaurants as the reference place.

### 15. Comparison study (Cui & Levinson, Minnesota)
- **What it is:** a published study measuring crash cost per mile in the Minneapolis area.
- **What we take:** one number, to check ours isn't crazy (Part 8).

---

# Part 6 — The calculations, following one neighbourhood

Here we follow **one made-up neighbourhood, "Maple"**, through every stage. The numbers for
Maple are **invented to be easy to follow**; the method and the regional numbers are real.

## Stage 1 — Crash cost per mile for each mode (steps 02–05, 17)

**Count the harm** (whole region):

| | killed | seriously injured |
|---|---:|---:|
| people in cars | 1,582 | 14,774 |
| people cycling | 277 | 1,263 |

**Turn it into dollars per year:**
> **(killed × $13.7 million + seriously injured × $1.3 million) ÷ 6.9 years**

- **Cars:** (1,582 × $13.7M) + (14,774 × $1.3M) = $21.7B + $19.2B = **$40.9 billion**, ÷ 6.9 =
  **$5.93 billion a year**.
- **Bikes:** (277 × $13.7M) + (1,263 × $1.3M) = $3.8B + $1.6B = **$5.4 billion**, ÷ 6.9 =
  **$0.79 billion a year**.

**Work out how much travel happens:**
- **Cars:** 102 million vehicle-miles a day × 365 = **37.3 billion vehicle-miles a year** × **1.502
  people per car** = **56 billion passenger-miles**.
- **Bikes:** the survey says one person bikes **23.7 miles a year** × 3,468,871 people = **82
  million passenger-miles**.

**Divide:**
- **Cars:** $5.93 billion ÷ 56 billion miles = **$0.1059 a mile**
- **Bikes:** $0.79 billion ÷ 82 million miles = **$9.59 a mile**

*Why "people in cars" and not "all harm cars cause"? MEP asks what risk **you** take by choosing
a mode — so a person walking who is hit by a car counts under walking. Part 2 shows the other way.*

*Why 1.502 people per car? From the survey, using **only drivers' reports** — otherwise one car trip
with 3 people would be counted 3 times.*

**Safety check:** our car number is compared with the Minnesota study. Theirs is per **car**-mile:
$0.1059 × 1.502 = **$0.159 per car-mile**, against theirs of **$0.097** = **1.65 times**. Florida
roads are about twice as deadly per mile as Minnesota's, so ours *should* be higher. The step
**refuses to finish** unless it's between 1.2 and 3 times.

**Maple's driving danger:** Maple gets its **own** driving crash cost from the roads near it
(stage 4). Say it's **$0.10 a mile**. Walking and biking use the regional numbers.

## Stage 2 — What Maple can reach (steps 16, 17, 18, 25)

**Maple's starting point:** the Census "interior point" — a dot guaranteed to be *inside* Maple.
(The exact middle of a C-shaped area can land in the neighbouring one.)

**Say that within 10 minutes of Maple:**

| | shop jobs | restaurant jobs |
|---|---:|---:|
| by car | 300 | 100 |
| by bike | 60 | 20 |

*(Real neighbourhoods have all six kinds of place; we use two to keep it simple.)*

**Jobs don't all count the same.** Two things set each kind's weight:

**(a) Scaling number** — so common kinds (like all jobs) don't swamp rare ones (like arts). Using
US totals, with restaurants as the reference:
> **scaling number = US restaurant jobs ÷ US jobs of that kind**

- restaurants = **1**
- shops = **0.885**

**(b) How often people go** (travel survey):
- restaurants = **15.2%** of trips
- shops = **28.1%** of trips

**Weight = scaling number × how often people go:**
- restaurants: 1 × 0.152 = **0.152**
- shops: 0.885 × 0.281 = **0.249**

**Maple's "reach points" within 10 minutes:**
- **By car:** 300 × 0.249 + 100 × 0.152 = 74.7 + 15.2 = **89.9**
- **By bike:** 60 × 0.249 + 20 × 0.152 = 14.9 + 3.0 = **18.0**

## Stage 3 — How long it takes (steps 19–22)

To know what Maple can reach in 10 minutes, we need travel times:

- **Car, walking, bike:** the program builds a road network from the map (495,508 roads →
  827,133 junctions) and finds the **quickest route** from Maple to every other neighbourhood —
  like a GPS. It stops at **40 minutes**, MEP's longest band.
  - Cars must follow one-way streets and can't use footpaths.
  - Bikes can use everything except motorways and steps, at **12 mph**.
  - Speeds are speed limits — **no traffic jams**.
- **Bus:** buses only come at certain times, so a different method (called **RAPTOR**) works in
  rounds: first "where can I get with one bus?", then "with one change?", then "with two
  changes?". It uses the real timetables for **Thursday 17 September 2026**, leaving at **7:45,
  8:00 and 8:15** (averaged), with up to **10 minutes' walk** to a stop.
- **Places inside Maple itself** aren't "0 minutes away". If Maple were a circle, the average
  distance inside is about two-thirds of the way to the edge. *For an area of 3.14 km²: edge 1 km
  away → average 0.67 km → about 8 minutes' walk.*

## Stage 4 — Maple's own driving danger (steps 09, 33, 29, 30)

**1. Crashes on each state road.** Each crash is placed on its road stretch using the milepost on
the police report. Traffic on each stretch = **vehicles a day × length × 365 × 6.9 years**.

**2. A "typical road" prediction.** For each type of road (freeway, main road...), the program
learns how many casualties a road with that traffic and length **usually** has.

**3. The blend.** A quiet road with 2 deaths in 7 years might just be bad luck; a busy road with 200
has a reliable record. So:
- **little history → lean on the "typical road" prediction;**
- **long history → lean on the road's real count.**

*Example:* a quiet road predicted 1 casualty, really had 3 → blend ≈ **2**. A busy road predicted
50, really had 60 → blend ≈ **59.8**.

**4. Maple's number.** A weighted average of nearby roads' danger. **Busier** and **closer** roads
count more:

| minutes from Maple | how much a road counts |
|---:|---:|
| 0 | 100% |
| 10 | 45% |
| 20 | 20% |
| 40 | 4% |

*Example:* Road A is 5 minutes away, $0.20 a mile; Road B is 20 minutes away, $0.05 a mile (same
traffic). Maple ≈ (0.67 × 0.20 + 0.20 × 0.05) ÷ (0.67 + 0.20) = **$0.17 a mile** — close to Road
A, because it's nearer.

## Stage 5 — The penalty for each mode (step 23, Equation 2)

MEP turns energy, time and money into a **penalty**:

> **penalty = −0.5 × energy − 0.08 × minutes − 0.5 × (money + crash cost)**

| mode | energy per passenger-mile | money per passenger-mile |
|---|---:|---:|
| car | 0.90 | $0.48 |
| bike | 0 | $0 |

The penalty becomes a **"keep" percentage**: a penalty of 0 keeps 100%, and the bigger the penalty,
the less you keep — but never below zero.

**Car, 10 minutes:**
- without crash cost: −0.5 × 0.90 − 0.08 × 10 − 0.5 × 0.48 = −0.45 − 0.80 − 0.24 = **−1.49 → keeps
  22.5%**
- with crash cost ($0.10): −0.45 − 0.80 − 0.5 × 0.58 = **−1.54 → keeps 21.4%**

**Bike, 10 minutes:**
- without crash cost: 0 − 0.80 − 0 = **−0.80 → keeps 44.9%**
- with crash cost ($9.59): −0.80 − 0.5 × 9.59 = **−5.60 → keeps 0.37%**

## Stage 6 — Maple's score (step 23, Equations 1 and 3)

> **score = reach points × keep %**, added up for every mode

**10-minute band:**

| mode | reach points | keep (normal) | points (normal) | keep (with crash cost) | points (with crash cost) |
|---|---:|---:|---:|---:|---:|
| car | 89.9 | 22.5% | 20.26 | 21.4% | 19.27 |
| bike | 18.0 | 44.9% | 8.09 | 0.37% | 0.07 |
| **total** | | | **28.35** | | **19.34** |

- Maple's 10-minute score falls from **28.35 to 19.34** — a **32%** drop.
- Of the **9.0 points lost**, **8.0 are bike points** (89%).

**The other bands** (20, 30, 40 minutes) work the same way, with one rule: **only places newly
reached** in that band count. A shop 5 minutes away counts once, in the 10-minute band — not again
at 20, 30 and 40. Longer bands also have a bigger time penalty (−0.08 × 20 minutes, and so on), so
far places count less.

## Stage 7 — Combining neighbourhoods into one region

**Weighted by how many people live in each.** Say the region were only two neighbourhoods:

| | people | normal score | with crash cost |
|---|---:|---:|---:|
| Maple | 2,000 | 28.35 | 19.34 |
| Oak | 500 | 10.00 | 9.00 |

- **Normal:** (2,000 × 28.35 + 500 × 10) ÷ 2,500 = **24.7**
- **With crash cost:** (2,000 × 19.34 + 500 × 9) ÷ 2,500 = **17.3**
- **Drop: 30%.** Maple counts four times as much as Oak, because four times as many people live
  there.

Our real region does exactly this, for **2,170** neighbourhoods and all four modes. The result is
**7,567 → 5,863**, a **22.5%** drop.

---

# Part 7 — How our version is different from NREL's MEP

## What is the same

| | NREL's MEP | ours |
|---|---|---|
| the three equations | ✓ | ✓ same |
| energy and money cost per mode | MEP's default table | ✓ same table |
| weights (−0.5 energy, −0.08 per minute, −0.5 per dollar) | ✓ | ✓ same |
| time bands | 10, 20, 30, 40 minutes | ✓ same |
| reference place for scaling | restaurants | ✓ same |
| combining neighbourhoods | weighted by population | ✓ same |
| bikes | 12 mph, not on motorways (South Florida base case) | ✓ same |

**Why this matters:** our result is MEP, not something we invented — which is also why we could
run NREL's own tests on it (Part 8).

## What we ADDED

| addition | why |
|---|---|
| **crash cost**, added to the money part of the penalty | the whole point of the project. It's the **only change to the formula** — no new equation, no new weight |
| driving danger that **varies by neighbourhood** | so the map shows more than travel habits |
| **checks** NREL's tool doesn't have: comparison with Minnesota, the prediction test, automatic number checking, run-twice check | so every number can be defended |

## What we did DIFFERENTLY, and why

| | NREL's MEP | ours | why we changed it |
|---|---|---|---|
| **areas** | a grid of small squares | neighbourhoods (Census block groups) | our crash, population and car data already come by neighbourhood |
| **places** | counts of places from a paid business list (CoStar) — or, in South Florida, jobs from a regional traffic model | job counts from LODES | free, so anyone can rebuild our numbers. *Effect:* raw scores are on a different scale, so only percentages are compared |
| **road network** | a paid map (TomTom), or a regional traffic model's network in South Florida | OpenStreetMap | free, includes footpaths |
| **speeds** | the South Florida run used a regional traffic model | speed limits, no traffic | no free traffic data. *Effect:* every mode's reach is an upper limit |
| **bus routing** | a program called OpenTripPlanner | our own program (RAPTOR) on the real timetables | built and checked ourselves |
| **how often people go places** | a published survey table (2017 in the South Florida report) | calculated from the 2022 survey's raw data | newest data; work trips fell from 214 to 153 a year per person since 2017 |
| **modes** | default table also includes Uber/Lyft and dial-a-ride | car, bus, walk, bike only | not built; no reason written down (Part 11) |
| **time to reach your own area** | — | a real time based on its size | so big rural areas don't get "instant" access to everything inside them |

---

# Part 8 — How we know it is right

## Checks that passed

| check | what had to happen | result |
|---|---|---|
| **NREL's own tests** | better fuel economy → score up | **+27.6%** ✓ |
| | faster driving → score up | up ✓ |
| | driving costs more → score **down** (my addition) | **−30.1%** ✓ |
| | change nothing → identical (my addition) | identical ✓ |
| **Minnesota comparison** | our car crash cost 1.2–3× theirs | **1.65×** ✓ |
| **Survey code** | trips per person match the government's 2.28 | **2.28** ✓ |
| **Our travel times vs EPA's** | neighbourhoods ranked in a similar order | car **0.90**, bus **0.62** (1.00 = perfect) ✓ |
| **Run it twice** | identical numbers | identical ✓ |
| **Crash map placement** | crashes land in the right place | 913 of 915 walking, 277 of 277 biking ✓ |
| **Separate road types** | worth the extra complexity | yes ✓ |
| **Blend** | removes bad luck | 13 of 25 "worst" roads were luck ✓ |
| **Predicting the future** | fit on 2019–22, predict 2023–25 | smallest error ✓; ties at picking the very worst roads |

**Why "NREL's own tests" matter most:** the people who invented MEP published the tests *they* used
to prove it works. Passing them shows ours really is MEP.

**Why "driving costs more → score down" was added:** a score that goes up whenever anything changes
might just go up on *everything*. Cost must push it the other way.

## Independent checks (audits)

Twice, a separate checking program went through the whole project, **recalculating every number
itself**:

| when | what it found wrong | what it confirmed right |
|---|---|---|
| **8 September** | **6 problems** (all real) | the crash counts (it re-read the whole 527 MB file), the car crash cost, people per car, the trip shares, the scaling numbers, the road network, the timetables |
| **9 September** | **11 problems** (all real) | the whole score rebuilt from scratch, the bus crash rate, the safety-curve maths, the blend formula (exactly the official road-safety handbook's) |

All 17 problems are in Part 9. A few smaller points are still open (Part 10).

## What stops it breaking again

| protection | what it does |
|---|---|
| **run everything with one command** | runs all 26 steps in order and **stops** if the main numbers change between runs |
| **old-file list** | after each run, lists any data file that wasn't rebuilt, so old leftovers can't sneak in |
| **the number checker (step 28)** | checks **29 numbers** in the report — plus this file, the interview Q&A and the presentation — against the real data |
| **20 automatic tests** | each one fails if a known past mistake comes back |
| **saved copies of most data** | a website changing its data can't change our answer — **except three downloads that happen every run** (bus miles and bus deaths from the transit database, and the Census neighbourhood points). See `DATA.md` Part 6 |

---

# Part 9 — Everything that went wrong, and how it was fixed

Each item: **what was wrong → why it mattered → how it was fixed.**

## Wrong numbers

| what was wrong | why it mattered | fix |
|---|---|---|
| **Crash costs per crash applied to people** | the government has two tables — per crash and per person — and we mixed them: **8× too high** | cost per person; deaths and serious injuries only; per passenger-mile |
| **Car deaths estimated from Florida's average** | Tampa kills far more pedestrians than Florida's average, so car deaths came out **68% too high** | counted directly from the crash reports |
| **People per car: 1.67, then a made-up figure** | 1.67 was old data. A quoted AAA figure ($0.796) **doesn't exist** — you caught it | measured from the 2022 survey: **1.502** |
| **Walking and biking miles typed in from a scratch file** | **2.8× and 3.5× too high**, so walking and biking crash costs were far too low | measured from the survey |
| **Tampa-only bus crash rate** | based on just **2 deaths** — noise | the whole US, **12 deaths** |
| **Bus rate mixed in trains and crime** | Tampa has no trains; crime was **58%** of bus rider deaths, but the car side only counts crashes | buses only, traffic crashes only |
| **Bus fare cost 0.86 or 1.05** | sources disagreed | **0.85**, MEP's own table |
| **EPA's older population** | before 2020; cost per person **9.3% too high** | Census mid-2022 |
| **"Work" as the reference place, not restaurants** | every score **11 times too big** (91,094 instead of 8,241). Percentages were fine, which is why it hid | restaurants, as MEP does |
| **Scaling numbers from Tampa's own totals** | MEP uses national totals; it gave arts a silly weight of **52** | national totals |
| **Time to your own neighbourhood = 0** | big rural neighbourhoods got instant access to everything inside them | real travel time inside each one |
| **Plain average of neighbourhoods** | MEP's rule weights by population | population-weighted |
| **"188 to 1" car vs bus** | compared deaths + injuries for cars with deaths only for buses | like-for-like: **95 to 1** |
| **Report said bikes cost $2.76 a mile, 26× cars** | that was the old, deleted number | fixed, and now checked automatically |
| **Safety-curve numbers in the report** | came from the wrong version of the curve | fixed |
| **The "93%" in the interview notes** | typed by hand into an old script; nothing could reproduce it | measured properly: **99.0%** of people killed walking were hit by a car |

## A map that looked real but wasn't

**What was wrong:** the first version used EPA's "jobs within 45 minutes" and **one** crash cost per
mode for the whole region. Every neighbourhood's loss then depended **only** on how much it used
buses. It was really a map of bus use, coloured in and called "crash harm". Proof: changing the
crash numbers never changed the order of neighbourhoods.

**First fix — didn't work:** we built our own travel times. But with one crash cost per mode, the
maths is the same. The 8 September check proved it was **still** a map of travel habits.

**Second fix — worked, partly:** giving each neighbourhood its **own** driving danger. Now crash data
differs by place — **but** local danger is only **1.3%** of the differences. So it's a regional
correction, **not a crash-danger map**.

## Crash-caused traffic jams (built, then deleted)

**The idea:** crashes cause jams, jams make trips longer, so add a few minutes to every car trip.

**How many minutes?** We needed "what share of jam time is caused by crashes":

| try | why it was dropped |
|---|---|
| 55% | covered **all** surprise delays — road works, weather, events too |
| 25% | a general national headline, not measured here |
| 12.5% | from Fort Lauderdale, not Tampa |
| 13–30% (road sensors) | the best evidence — but the minutes it gave (**under 1 minute** on a 30-minute drive) were **typed in by hand**, and no step calculated them |

**A maths mistake along the way:** delay was measured in hours **per person** but divided by miles
**per car**. A car usually carries 1.5 people, so the result came out **1.67 times too big**.

**Deleted on 10 September** because we couldn't show how the minutes were calculated — and a number
you can't rebuild, you can't defend. It moved the headline from **24.9% to 22.5%**. Removing it made
the result *smaller*, the opposite of inflating it.

## The checker itself was broken

| what was wrong | fix |
|---|---|
| it "found" a number in the report that wasn't there — it matched a different number that looked the same | numbers must sit next to their label |
| it couldn't tell **24%** from **124%** | it now checks the whole number |
| its self-test never actually tested anything | the self-test now runs the real check |
| a test meant to catch a fake map passed on the fake map | rewritten |
| it only checked the report, not the documents you speak from | now checks the Q&A, presentation and this file too |
| two automatic tests only looked at **9 of the 27** steps | fixed 14 September; proven to catch a planted mistake |

## Steps missing from the run list (the same bug, three times)

**What was wrong:** some steps weren't in the list of steps to run. Each was the only step making a
file another step needed. Because an **old copy** of that file was still on the computer, nothing
broke — the project just quietly used old data.

| missing step | what it makes |
|---|---|
| 05 | the bus crash rate |
| 33 | the road types |
| 01 | EPA's data (used to check travel times) |

**Fix:** added them in the right order, and the run now **lists any file it didn't rebuild**.

## Other things fixed

| what was wrong | fix |
|---|---|
| Florida DOT's road data changed between runs (2,429 roads, then 2,427) | saved a copy |
| first map download: only 31 of 88 pieces had arrived | a safety check caught it; waited for all pieces |
| a Friday timetable would have dropped every PSTA bus | Thursday |
| the PSTA timetable link was broken (a capital "G") | the bus company's own link |
| the safety curve was fitted only on roads that had crashed | all 2,848 roads |
| 51 roads looked "100% deadly" from tiny numbers | pulled toward the average |
| the walking-and-biking test rounded zeros to tiny numbers, hiding the effect | only real observed values |
| motorbikes missing from the crash bill ($8.8B) | added ($10.72B) |
| the "faster driving" test claimed a +153% result | it can only show *direction* (travel times stop at 40 minutes, so no new places get added) |

---

# Part 10 — What is still weak or not done

## The weak points — and what to say

| weak point | what to say |
|---|---|
| **MEP counts what you *could* reach, not what people do.** Cycling is 18% of the score but under 2% of trips. | "Most of my correction lands on a mode few people use here. Weighted by real travel it would be roughly half." |
| **At $10 a mile, cycling is almost switched off**, rather than smoothly penalised. At a tenth of the measured risk, the drop is 11.5% instead of 23.8%. | "Pricing cycling's real risk removes it as an option in MEP." |
| **The local cycling figure rests on 35 surveyed trips.** | "The national figure, on 298 trips, is close." |
| **Walking, biking and bus danger don't vary by place.** | "I tried; the data isn't strong enough. It needs counts of people walking and biking, which cost money." |
| **The map is only 1.3% local danger.** | "It's a regional correction, not a crash-danger map." |
| **Who pays when a car hits someone walking?** We charge the person hit. | "It's a choice, and it changes the answer — I show both." |
| **The bus crash rate is for the whole US.** | "Tampa has too few bus deaths to measure." |
| **Travel times assume empty roads.** | "Every mode's reach is an upper limit." |
| **Motorbikes are in the $10.7 billion but can't be in MEP.** | "They're 17.6% of the crash bill, reported separately." |
| **One year of traffic for seven years of crashes.** | "It makes my rates 8–12% too low — cautious, not inflated." |
| **"Social" trips use arts and entertainment jobs,** but most social trips are visits to homes. | "NREL's version does the same." |
| **Scores can't be compared with other cities.** | "Percentages and rankings only." |

## Not done — easy basics

1. ~~Nothing is saved in git~~ — **done 14 September**: private repo `github.com/yrasool/i4-safety`, code and documents only.
2. **No charts or maps** anywhere.
3. **The presentation is a text outline**, not slides.
4. **The resume line isn't written.**
5. **Your task in `src/10_screen_segments.py`** (marked `TODO(human)`) — left for you on purpose.
6. **Nine old scripts** (06–08, 10–15) sit in the folder unused; they should go into an `archive/` folder.
7. **The prediction test (step 36)** isn't in the run list or the report, and its summary still says "6 of 6 passed" when 3 are too close to call.
8. **Step 23's description** mentions a file (`mep_summary.csv`) it doesn't make.

## Not done — method

9. **A version of the score weighted by how people really travel** (the rough ~13%).
10. **Test how the answer changes with MEP's cost weight**, or give crash cost its own weight.
11. **Uber/Lyft as a mode.**
12. **Cost per person uses 3,468,871 people**, but the neighbourhood table adds up to 3,399,162 — which would give **$3,155** instead of $3,092. Not explained yet.
13. **The report doesn't say** state roads carry only **78.5%** of driving, or whether leaving out local roads pushes the car rate up or down.
14. **Car danger is weighted toward roads near home**, but used for 40-minute trips too.
15. **The EPA check only matches 1,670** of our neighbourhoods — explained in the code, not the report.
16. **No uncertainty ranges on the trip shares** (doctor trips rest on 68 surveyed trips).
17. **No formal statistics test** for choosing the uneven-counts model.
18. **Nobody has checked the bus-route code line by line** — only its results.
19. **The "run it twice" check compares only four numbers.**
20. **Step 26's self-check can't fail** — it compares a formula with itself.
21. **A stricter version of the Minnesota comparison** (all injury levels) was never done.
22. **Bus times are averaged generously**: reachable at 8:00 but not 7:45 still counts.
23. **One people-per-car figure for all vehicles**, trucks included.

---

# Part 11 — What we left out on purpose

For each: **why** we left it out, and **what that changes** in the results.

### NREL's grid of small squares
- **Why left out:** our crash, population and car data already come by neighbourhood. Cutting them
  into squares and back would add work and error.
- **What it changes:** the neighbourhood-level detail is coarser than a fine grid. The regional
  result is likely similar, but this was **not tested**.

### Paid lists of places (CoStar, Google Places)
- **Why left out:** they cost money, and nobody else could check our work.
- **What it changes:** we count **jobs**, not places, so a big supermarket counts more than a small
  shop, and **raw scores are on a different scale**. NREL found the *pattern* of scores matches either
  way, which is why we only compare percentages.

### The 2017 survey with Florida-only figures
- **Why left out:** nine years old, and you chose the newest data. The 2022 survey has no Florida-only
  breakdown.
- **What it changes:** our trip shares are for big South Atlantic cities, not Florida exactly. Using
  2017 would have **overweighted trips to work** (people now make far fewer).

### Traffic jams in travel times
- **Why left out:** no free source of traffic data for every road.
- **What it changes:** every mode reaches **more** places than it really would at rush hour. Cars would
  lose the most minutes to jams, which would make biking a bigger share of the score — so the drop
  would *probably* be **bigger**. *That's a guess, not tested.*

### Uber/Lyft and dial-a-ride buses
- **Why left out:** MEP's default settings include them, but they were never built. **No reason was
  written down at the time** — say so honestly if asked.
- **What it changes:** Uber/Lyft is only **1%** of trips here. Because MEP counts what you *could*
  reach, adding it could add car-like points; the effect on the drop is **unknown**.

### Motorbikes in the score
- **Why left out:** MEP has no motorbike mode and no energy or cost figures for one.
- **What it changes:** **697 deaths and $1.89 billion a year** are in the crash bill but **not** in the
  score. The drop would be different if motorbikes were a mode, but there's no MEP way to add them.

### Minor injuries
- **Why left out:** the crash file only records injuries to people walking and cycling as "killed" or
  "seriously injured", so modes can only be compared fairly at that level.
- **What it changes:** crash costs are **too low**, especially for cars (which have many minor
  injuries). So our crash costs are a **lower limit**, and the true drop would be bigger.

### Crime on buses
- **Why left out:** the car side only counts traffic crashes; counting assaults and robberies for buses
  would be unfair.
- **What it changes:** bus crash cost is lower than "all harm to bus riders". Buses are only **0.7%** of
  the score, so the effect on the drop is **tiny**.

### Trains
- **Why left out:** Tampa Bay has none.
- **What it changes:** nothing here.

### Local and county roads in the road-danger model
- **Why left out:** Florida DOT publishes no traffic counts for them, so no crash rate can be worked out.
- **What it changes:** neighbourhood driving danger is based on state roads only (**78.5%** of driving).
  Whether that makes it too high or too low is **unknown**.

### People's exact driving routes
- **Why left out:** would need data on who travels from where to where, which we don't have.
- **What it changes:** each neighbourhood's driving danger is "busy roads nearby", not the roads its
  people actually use.

### Where drivers live
- **Why left out:** home addresses aren't in the crash file.
- **What it changes:** danger is counted where crashes **happen**, not where the people involved live.

### Walking and biking danger by neighbourhood
- **Why left out:** tried (step 32) — nothing predicted *where* walking and biking crashes happen well
  enough.
- **What it changes:** walking and biking, which make **84%** of the drop, use **one number for the whole
  region**. That's the main reason the map is mostly about travel habits.

### Crash-caused traffic jam minutes
- **Why left out:** we couldn't show how the minutes were calculated (Part 9).
- **What it changes:** the drop is **22.5%** instead of 24.9%.

### A Dutch way of valuing deaths
- **Why left out:** based on a Dutch study, with no US version.
- **What it changes:** nothing in the main result; kept only as a side test.

### Friday bus timetables
- **Why left out:** PSTA doesn't run its weekday timetable on Fridays.
- **What it changes:** nothing — Thursday is a normal weekday for both bus companies.

### Bus trips with three or more changes
- **Why left out:** almost nobody makes them.
- **What it changes:** a handful of very long bus trips aren't counted — tiny effect.

### Correcting for one year of traffic
- **Why left out:** measured it (our rates are 8–12% too low), but left it alone so our numbers stay
  **cautious**.
- **What it changes:** the true crash costs, and the true drop, are slightly **bigger** than we report.

---

# Part 12 — How the headline number changed over time

Several fixes often happened together; this is the main reason each time.

| when | drop | main reason |
|---|---:|---|
| 7 Sep, evening | 18.8–25.6% | first time calculating MEP fully |
| 8 Sep, ~1 am | 21.8–29.6% | five corrections from NREL's own report |
| 8 Sep, morning | 26.6–29.5% | walking and biking miles measured properly (the old ones were too high) |
| 9 Sep, midday | 26.3–29.3% | driving danger made to vary by neighbourhood |
| 9 Sep, afternoon | 25.1–28.1% | switched to MEP's rule: weight by population |
| 9 Sep, evening | 24.9–27.9% | safety curve refitted on all roads; death share smoothed |
| **10 Sep onward** | **22.5%** | crash-caused traffic jams deleted |

On 9 September the raw score also fell from **91,094 to 8,241** when "work" was swapped for
"restaurants" as the reference place. That changed the size of the score but **not** any percentage.

---

# Part 13 — What happened each day

*(Times are Tampa time.)*

**Sunday 7 – Monday 8 September — building MEP properly.** Explained the project and wrote the
interview questions (then rewrote them in plain language when you said you didn't understand). Admitted
the project hadn't really built MEP; you said "do it". Built the destinations, trip shares, starting
points, road map, road network, car/walk/bike travel times (bike because you asked) and bus travel
times. Fixed the scaling numbers, bus cost and people per car. The first independent check found 6
problems; fixed them. Made driving danger vary by place.

**Tuesday 9 September — checking against NREL.** Confirmed the data had gone through MEP. Found NREL's
own team had the same score-size issue. Passed NREL's tests. Caught Florida DOT's data changing between
runs. The second independent check found 11 problems; fixed them. Wrote the interview Q&A, the reading
guide and the learning resources.

**Wednesday 10 September — holes and fixes.** Wrote the presentation outline. Tried walking and biking
danger by place (didn't work). Added road types. Deleted the traffic-jam minutes. Tested traffic by year.
Found and fixed the 93%. Made the checker read the documents you speak from. Found and fixed the missing
steps. Ran everything — identical numbers. *(Outside this project: your CMOS drawings and HSPICE lab
files.)*

**Thursday 11 September — proper evaluation.** Built the prediction test: fit on 2019–22, predict 2023–25.

**Sunday 14 September — understanding the numbers.** Showed every neighbourhood has a real score.
Explained where the drop comes from. Found that MEP counts what people *could* reach, not how they
travel. Checked the cycling data. Compared our method with NREL's South Florida report. Fixed the two
tests that only looked at 9 steps. Rewrote this file in simple language.

---

# Part 14 — What every file is

```
DOCUMENTS
WHAT_I_DID.md          this file (checked against the data)
MEP.md                 what MEP is, from zero (checked)
MATH.md                every calculation, with worked examples (checked)
DATA.md                every data source, how they connect, what's saved (checked)
ASSUMPTIONS_AND_CHOICES.md   every choice, why, and what it changes (checked)
HOW_IT_RUNS_VS_STANDARD_MEP.md   how it runs; same/different/added vs NREL (checked)
CORRECTIONS.md         every correction, how found, what it changed (checked)
data/README.md         guide to every data file
REPORT.md              the technical report (checked against the data)
INTERVIEW_QA.md        17 likely interview questions, with plain answers (checked)
PRESENTATION.md        20-minute talk, 14 slides, as text (checked)
READING_GUIDE.md       what to read to understand each part
LEARNING_RESOURCES.md  books, papers and websites, with links
METHOD.md              older method notes
../docs/i4-safety-build-log.md   lessons about building software, learned here

THE PIPELINE — the 26 steps, in the order they run
src/01             EPA data (for checking)
src/02             count people killed and hurt
src/03             miles travelled
src/18, 24         starting points; population and cars
src/16, 17, 25     places to go; how often people go; scaling numbers
src/04, 05         crash cost per mile; bus crash rate
src/19, 20         download the map; build the road network
src/21, 22         travel times by car/walk/bike; by bus
src/09, 33, 29, 30 crashes per road; road types; the blend; danger by neighbourhood
src/32             walking and biking danger by place (didn't work)
src/23             the MEP score
src/26             validation tests
src/27             who is hit hardest
src/28             the number checker
src/31             NREL's own tests
src/34             traffic by year
src/35             who pays when a car hits someone
src/run_all.py     runs all 26 and checks nothing changed

NOT IN THE PIPELINE YET
src/36             the prediction test

OLD, NOT USED
src/06-08, 10-15   the first version

DATA
data/raw/          every downloaded file, saved
data/interim/      in-between results (travel-time tables, road networks, trip shares)
data/final/        final results
data/final/mep_by_blockgroup.csv   the answer: one row per neighbourhood
```
