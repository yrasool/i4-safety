# Learn — every idea in this project, taught from zero

This is a **teaching document**. It assumes you know **nothing** about transport, road safety,
statistics or programming. Every idea is taught with four questions:

- **What** is it?
- **Why** does it matter here?
- **How** does it work? (with a small example)
- **Who** made it, or who uses it? (where that helps)

Read it top to bottom. Each part builds on the ones before. At the end there's a quiz to test yourself.

| part | topic |
|---|---|
| 1 | why this project exists |
| 2 | who's who — organisations and researchers |
| 3 | transport basics |
| 4 | road-safety basics |
| 5 | data basics |
| 6 | statistics basics |
| 7 | programming basics |
| 8 | MEP in five minutes |
| 9 | how to keep learning |
| 10 | quiz yourself |

---

# Part 1 — Why this project exists

**What:** a project that takes a well-known US transport score (MEP) and adds something it leaves out:
**people killed and hurt in crashes**.

**Why:** you're applying to work with the team at NREL that created MEP. The best way to show you
understand their work is to rebuild it yourself, find a real gap, and fill it carefully.

**How:** calculate MEP for Tampa Bay from public data, work out how much crashes cost per mile for each way
of travelling, add that cost into MEP, and see how much the score changes. **Answer: it drops 23.4%.**

**Who:** you, with Claude building and explaining, and independent checking programs reviewing the work.

---

# Part 2 — Who's who

## Organisations

| name | what it is | why it matters here |
|---|---|---|
| **NREL** — National Renewable Energy Laboratory | a US Department of Energy research lab in Golden, Colorado | created MEP; the team you're applying to |
| **FDOT** — Florida Department of Transportation | runs Florida's state roads | road traffic counts; paid for the South Florida MEP study |
| **FDOT District 7** | FDOT's Tampa Bay region | our five counties |
| **Signal Four Analytics** | a University of Florida system that collects police crash reports | our crash data (licensed) |
| **US Census Bureau** | counts people and businesses | population (ACS), jobs (LODES), neighbourhood maps (TIGER) |
| **FHWA** — Federal Highway Administration | the federal roads agency | the national travel survey (NHTS), yearly traffic statistics |
| **FTA** — Federal Transit Administration | the federal transit agency | runs the National Transit Database (NTD) |
| **US DOT** — Department of Transportation | the parent federal transport department | official dollar values for deaths and injuries |
| **EPA** — Environmental Protection Agency | the federal environment agency | the Smart Location Database (used as a check) |
| **HART** and **PSTA** | the bus companies for Hillsborough and Pinellas | bus timetables |
| **OpenStreetMap** | a free world map made by volunteers | our road and path network |
| **FIU** — Florida International University | a university in Miami | ran the South Florida MEP study with NREL |
| **TTI** — Texas A&M Transportation Institute | a transport research institute | publishes traffic-jam (congestion) reports |

## Researchers and their ideas

| who | what they did | where it shows up |
|---|---|---|
| **Hou et al. (2019)**, NREL | created **MEP**, tested it on Columbus, Ohio | the whole project |
| **Cui & Levinson (2019)** | measured the **full cost of car travel** in Minneapolis, including crashes | our benchmark for crash cost per mile |
| **Blincoe et al. (2015)** | calculated the **economic cost of US crashes** | the value Cui & Levinson used |
| **Savage (2013)** | compared **death rates** of different ways of travelling | our bus-vs-car check |
| **Skabardonis, Varaiya & Petty (2003)** | measured how much **traffic delay comes from crashes**, using road sensors | the (deleted) delay term |
| **Mekuria, Furth & Nixon** | invented **Level of Traffic Stress** for cyclists | NREL's 2023 safety approach |
| **Dijkstra (1959)** | invented the **shortest-path method** | our car, walking and bike travel times |
| **Delling, Pajor & Werneck (2015)** | invented **RAPTOR**, a fast method for timetable journeys | our bus travel times |
| **AASHTO** | publishes the **Highway Safety Manual** | our road-danger method (Empirical Bayes) |
| **Cheng & Washington (2005, 2008)** | tests for **how well methods find dangerous places** | our prediction test |
| **Joel Grus** | wrote *Data Science from Scratch* (O'Reilly) | your reading plan |

---

# Part 3 — Transport basics

### Trip
- **What:** one journey from one place to another, like home to the shops.
- **Why:** MEP and the travel survey are built on trips.

### Mode
- **What:** a way of travelling: car, bus, walking, bike, Uber/Lyft, motorbike.
- **Why:** each mode has its own speed, cost, energy use and danger.

### Accessibility
- **What:** how many useful places you can reach.
- **Why:** it's what people actually care about: "can I get to work, the shops, the doctor?"
- **How:** count the places reachable within a certain time.
- **Example:** from home you can reach 50 shops in 10 minutes by car, but only 3 on foot. Your car
  accessibility is higher.

### Isochrone
- **What:** the area you can reach within a set time. From Greek *iso* (same) + *chrone* (time).
- **Why:** MEP counts places inside isochrones of 10, 20, 30 and 40 minutes.
- **How:** start at home and spread outward along roads until the time runs out, like a ripple in water.

### Vehicle-miles (VMT) and passenger-miles (PMT)
- **What:** **vehicle-miles** = miles driven by vehicles. **Passenger-miles** = miles travelled by people.
- **Why:** crash costs have to be per **passenger**-mile to match MEP's costs.
- **Example:** a car with 2 people drives 10 miles = **10 vehicle-miles**, **20 passenger-miles**.

### Occupancy
- **What:** the average number of people in a car.
- **Why:** it converts vehicle-miles into passenger-miles.
- **Here:** **1.502**, measured from the travel survey.

### AADT — Annual Average Daily Traffic
- **What:** how many vehicles use a road on an average day.
- **Why:** it measures how much a road is used, so crashes can be turned into a rate.
- **Example:** AADT 20,000 = 20,000 vehicles a day.

### Free-flow vs congested
- **What:** **free-flow** = empty roads, driving at the speed limit. **Congested** = with traffic jams.
- **Why:** our travel times are free-flow, so reach is an upper limit.

### GTFS — General Transit Feed Specification
- **What:** the standard file format for bus and train timetables.
- **Why:** it's how we get HART's and PSTA's real schedules.
- **Who:** started by Google and a US transit agency; now used worldwide.

### Census geography
- **What:** the Census splits the US into nested areas: **blocks** (about a city block) → **block groups**
  (a few hundred to a few thousand people) → **tracts** → **counties**.
- **Why:** our "neighbourhoods" are **block groups**. Our five counties have **2,170**.
- **How:** each area has an ID. A block's 15-digit ID starts with its block group's 12-digit ID.

---

# Part 4 — Road-safety basics

### KABCO — how injuries are graded
- **What:** the police scale for crash injuries:

  | letter | means |
  |---|---|
  | **K** | killed |
  | **A** | serious (incapacitating) injury |
  | **B** | minor injury |
  | **C** | possible injury |
  | **O** | property damage only |

- **Why:** we price **K and A** — the only levels recorded for people walking and cycling.
- **KSI** = "killed or seriously injured" = K + A.

### Crash rate and exposure
- **What:** **exposure** = how much travel happens. **Crash rate** = crashes ÷ exposure.
- **Why:** a busy road has more crashes just because more people use it. A rate makes roads comparable.
- **Example:** road A has 10 crashes over 100 million vehicle-miles; road B has 10 over 10 million. **Road B
  is 10 times more dangerous per mile.**

### Value of a statistical life (VSL)
- **What:** the dollar amount governments use for the benefit of preventing one death. **US DOT: $13.7
  million.**
- **Why:** it lets deaths be added into cost calculations like MEP's.
- **How it's worked out:** from how much people pay to reduce small risks — for example, extra pay for riskier
  jobs. **It isn't "what a person is worth"**; it's a planning figure.

### Regression to the mean
- **What:** something unusually high by chance tends to come back toward normal next time.
- **Why:** a quiet road with 2 deaths in a bad year will probably have fewer next year, even with no changes.
  Ranking roads by raw counts picks out unlucky roads, not dangerous ones.
- **Example:** you roll a die and get 6. Your next roll will probably be lower — not because anything changed.

### Hotspot
- **What:** a place with more crashes than expected.
- **Why:** agencies fix hotspots first. Finding **real** ones — not lucky ones — is the challenge.

### Safety Performance Function (SPF) — the "safety curve"
- **What:** a formula predicting how many crashes a **typical** road of a certain type, traffic and length has.
- **Why:** it tells you what "normal" is, so you can spot roads that are worse.
- **Who:** the Highway Safety Manual (AASHTO).
- **Example:** a typical 1-mile main road with 20,000 cars a day might expect 3 serious crashes in 7 years.

### Empirical Bayes (EB) — "the blend"
- **What:** mixing the safety curve's prediction with a road's own crash history.
- **Why:** fixes regression to the mean. Short histories are mostly luck; long histories are mostly real.
- **How:** little data → trust the prediction more; lots of data → trust the history more.
- **Example:** a quiet road predicted 1 crash, actually had 3 → the blend says about 2.

### Externality
- **What:** a cost you cause someone else, which you don't pay for.
- **Why:** when a driver hits a pedestrian, the pedestrian is hurt — the driver's own cost doesn't include it.
- **Here:** harm driving does to people outside the car = **$0.0514 per mile**, **$2.88 billion a year**.

### Level of Traffic Stress (LTS) and the Walking Comfort Index (WCI)
- **What:** ways of rating how stressful or comfortable a street **feels** for cycling or walking, from its
  design (speed limit, lanes, sidewalks).
- **Why:** NREL's own safety work uses these. They measure **how safe a street looks**, not **how many people
  were actually hurt** — which is what this project adds.
- **Who:** LTS — Mekuria, Furth & Nixon; used by NREL in 2023. WCI — NREL, 2025.

---

# Part 5 — Data basics

### Dataset, row, column
- **What:** a **dataset** is a table. Each **row** is one thing (a crash, a trip). Each **column** is one kind
  of information (year, number killed).
- **Example:** the crash file has **602,110 rows** — one per crash.

### ID and join
- **What:** an **ID** names something exactly. A **join** matches rows from two datasets by their IDs.
- **Why:** to combine population (Census) with MEP scores (ours), you match neighbourhood IDs.
- **Watch out:** if two datasets use different versions of the map, IDs don't all match. EPA's data matches
  only **1,670** of our 2,170 neighbourhoods.

### Survey and weights
- **What:** a **survey** asks a sample of people, not everyone. A **weight** says how many real people or trips
  each answer stands for.
- **Why:** the travel survey asks thousands of households but stands for the whole country.
- **Example:** one surveyed trip might have weight 10,000 = it represents 10,000 real trips.

### Sample size
- **What:** how many records a number is based on.
- **Why:** small samples can be far off just by chance.
- **Here:** the regional biking figure rests on only **35 trips** — thin.

### Vintage
- **What:** which year the data describes.
- **Why:** mixing years can give wrong answers. EPA's data uses **2018** neighbourhoods; ours uses **2020**.

### Licence
- **What:** the terms under which you're allowed to use data.
- **Why:** Signal Four crash data is licensed — **use it, but never share or publish it.**

### Reproducibility
- **What:** getting **exactly the same answer** every time you run the project.
- **Why:** if the answer changes on its own, you can't trust or defend it.
- **How:** save copies of downloaded data, and compare results between runs.

### Proxy
- **What:** something measured in place of what you really want.
- **Why:** there's no free list of every shop, so **jobs** stand in for places.
- **Watch out:** a proxy has weaknesses — a supermarket with 200 staff counts more than a shop with 3.

---

# Part 6 — Statistics basics

### Average and weighted average
- **Average:** add up, divide by how many. Average of 10 and 20 = **15**.
- **Weighted average:** some things count more. If 10 counts 3 times as much as 20:
  (3 × 10 + 20) ÷ 4 = **12.5**.
- **Here:** the region's MEP score is a weighted average of neighbourhoods, by population.

### Variance
- **What:** how spread out numbers are.
- **How:** for each number, (number − average)², then average those.
- **Example:** 4, 5, 6 → average 5 → (1 + 0 + 1) ÷ 3 = **0.67**. Small spread.
  0, 5, 10 → (25 + 0 + 25) ÷ 3 = **16.7**. Big spread.

### Distribution
- **What:** the pattern of how often each value happens.
- **Poisson distribution:** for counts of rare random events, where spread ≈ average.
- **Negative binomial distribution:** like Poisson but allows **more** spread — used for crashes.
- **Here:** crash counts per road spread **23 times** more than Poisson expects, so negative binomial is used.

### Fitting a model (maximum likelihood)
- **What:** finding the numbers in a formula that best match the data.
- **How:** try many values; keep the ones that make the real data **most likely**.
- **Example:** fitting the safety curve found that doubling traffic multiplies crashes by about 1.73 (b = 0.789).

### Standard error
- **What:** how uncertain a fitted number is.
- **How:** roughly, the true value is very likely within **2 standard errors** either side.
- **Example:** b = 0.789, standard error 0.022 → very likely between **0.75 and 0.83**.

### AIC — Akaike Information Criterion
- **What:** a score for comparing models: fit, minus a penalty for complexity. **Lower is better.**
- **Why:** a more complex model always fits a bit better; AIC asks if it's **worth** the extra complexity.
- **Here:** separate curves by road type won (10,694 vs 10,765).

### Correlation and rank correlation (Spearman)
- **What:** a number from −1 to +1 saying whether two things go up together.
- **Spearman** compares **rankings**, so it's not fooled by extreme values.
- **Here:** carless households vs MEP drop: **+0.27** (moderate). Before vs after rankings: **0.989** (almost identical).

### Correlation is not causation
- **What:** two things going together doesn't mean one causes the other.
- **Example:** ice-cream sales and drownings both rise in summer. Ice cream doesn't cause drowning — heat
  causes both.
- **Here:** carless neighbourhoods lose more MEP — but they're also denser and more walkable, which could be the
  real reason.

### Confidence interval
- **What:** a range where the true value very likely lies (often 95%).
- **Here:** bus crash cost $0.00105 per mile, 95% range **$0.00054 to $0.00183** — wide, because it rests on 12 deaths.

### Holdout test (train/test split)
- **What:** fit a model on **some** data, then test it on data it **hasn't seen**.
- **Why:** a model tested on its own training data always looks good.
- **Here:** fit on **2019–2022**, predict **2023–2025**.

### Bootstrap
- **What:** re-running a test many times on random reshuffles of the data, to see if a result is real or luck.
- **How:** pick records at random **with replacement** (some twice, some not at all), recalculate, repeat
  thousands of times.
- **Here:** 2,000 reshuffles showed the blend's lower error is **real**.

### Sensitivity analysis
- **What:** changing one input to see how much the answer moves.
- **Why:** shows which inputs matter.
- **Here:** halving bike crash cost barely changes the drop; cutting it to a tenth halves it.

---

# Part 7 — Programming basics

### Python
- **What:** a programming language, popular for data work.
- **Why:** every step in this project is a Python script.

### Script and step
- **What:** a **script** is a file of instructions (`.py`). Each of our scripts is one **step**.
- **Example:** `src/04_injury_cost.py` works out crash cost per mile.

### Pipeline
- **What:** a chain of steps where each one uses what earlier ones made.
- **Why:** big jobs split into small, checkable pieces.
- **Here:** 26 steps, run in order by `src/run_all.py`.

### Libraries
- **What:** ready-made code you can use instead of writing from scratch.

| library | what it does |
|---|---|
| **numpy** | fast maths on big tables of numbers |
| **pandas** | spreadsheet-like tables in Python |
| **scipy** | science maths: fitting models, statistics, shortest paths |
| **pyarrow** | reads and writes the `.parquet` file format |
| **pytest** | runs tests |

### File types

| type | what it is |
|---|---|
| `.csv` | a plain-text table, commas between columns |
| `.parquet` | a compressed table, faster than CSV |
| `.npy` / `.npz` | saved numpy number tables |
| `.json` | structured text data, used by websites |
| `.md` | Markdown — plain text with simple formatting (these documents) |
| `.py` | Python code |

### Graph and shortest path
- **What:** a **graph** is points (**junctions**) connected by lines (**links**). A **shortest path** is the
  quickest route between two points.
- **How (Dijkstra's method):** start at your point; always extend from the closest place found so far; stop
  when everything reachable has its quickest time.
- **Here:** 827,133 junctions and 1,115,278 links.

### RAPTOR
- **What:** a method for finding journeys on timetables.
- **How:** in rounds — one bus, then one change, then two changes.
- **Who:** Delling, Pajor & Werneck, 2015.

### Tests
- **What:** small programs that check the main code works.
- **Why:** they catch mistakes before they reach the results.
- **Here:** 20 tests, each built around a **past mistake** so it can't come back.
- **Run:** `python -m pytest tests -q`

### Git and GitHub
- **What:** **git** saves versions of your files. **GitHub** stores them online.

| word | meaning |
|---|---|
| **repository (repo)** | a project folder tracked by git |
| **commit** | a saved snapshot of the files, with a message |
| **push** | upload commits to GitHub |
| **private repo** | only you can see it |
| **`.gitignore`** | a list of files git should ignore |
| **allow-list** | ignore everything except what's listed — here, only `.py` and `.md` |

- **Here:** `github.com/yrasool/i4-safety` — private, code and documents only.

---

# Part 8 — MEP in five minutes

**What:** a score for how well connected a place is — how many useful places people can reach, counting
time, money and energy.

**Why:** to judge transport by what people can actually get to, and to reward efficient travel.

**How, in three steps:**
1. **Count** reachable places, for each mode and time band, weighted by how often people go there.
2. **Penalise** each mode for energy, time and money: penalty = −0.5 × energy − 0.08 × minutes − 0.5 × money,
   turned into a "keep" share.
3. **Add up** places × keep share, then combine neighbourhoods by population.

**Who:** NREL (Hou et al., 2019).

**The gap this project fills:** MEP charges nothing for crash deaths and injuries — and treats walking and
biking as completely free. We add crash cost per mile to the money part.

**Full explanation:** `MEP.md`. **All the maths:** `MATH.md`.

---

# Part 9 — How to keep learning

## Suggested reading order (this repo)

1. **`LEARN.md`** — this file (concepts)
2. **`MEP.md`** — what MEP is
3. **`WHAT_I_DID.md`** — the whole project story
4. **`MATH.md`** — every calculation
5. **`DATA.md`** — every data source
6. **`ASSUMPTIONS_AND_CHOICES.md`** — every choice
7. **`HOW_IT_RUNS_VS_STANDARD_MEP.md`** — how it runs, and how it compares
8. **`CORRECTIONS.md`** — every mistake and fix
9. **`INTERVIEW_QA.md`** — likely questions
10. **`READING_GUIDE.md`** and **`LEARNING_RESOURCES.md`** — outside reading, with links

## From *Data Science from Scratch* (Joel Grus)

The chapters most useful here:
- **Statistics** — averages, spread, correlation
- **Probability** — distributions
- **Hypothesis and inference** — confidence intervals, testing
- **Working with data** — cleaning, joining
- **Gradient descent** — how models are fitted

---

# Part 10 — Quiz yourself

Cover the answers and try each one.

**1. What does MEP measure?**
> How many useful places people can reach, counting time, money and energy.

**2. What does MEP leave out that this project adds?**
> The cost of people killed and seriously injured in crashes.

**3. A car with 3 people drives 10 miles. How many vehicle-miles and passenger-miles?**
> 10 vehicle-miles, 30 passenger-miles.

**4. Why is crash cost per mile so much higher for bikes than cars?**
> Bikes cause less harm in total, but it's spread over far fewer miles.

**5. What does KSI mean?**
> Killed or seriously injured.

**6. A quiet road had 2 deaths last year. Is it definitely dangerous?**
> Not necessarily — it could be bad luck (regression to the mean). Blend it with a prediction.

**7. Why use a weighted average for the region's score?**
> Neighbourhoods with more people should count more.

**8. What's the difference between correlation and causation? Give an example from this project.**
> Going together isn't causing. Carless neighbourhoods lose more MEP, but they're also denser — density could be the real cause.

**9. Why test a model on data it hasn't seen?**
> A model always looks good on the data it was built from.

**10. Why can't our raw MEP score be compared with another city's?**
> The raw score depends on how places are counted. NREL got 11,983 and 122.35 for the same region.

**11. Why is the neighbourhood map not a crash-danger map?**
> Only 7.0% of the differences come from local danger (1.3% before routes were followed); the rest is which modes people use.

**12. Why does MEP give cycling so much weight in Tampa Bay, even though few people bike?**
> MEP counts where you **could** go by bike, not whether anyone does.

**13. What does a private GitHub repo with an allow-list `.gitignore` protect against?**
> Other people seeing the project, and data files (like licensed crash data) being uploaded by accident.
