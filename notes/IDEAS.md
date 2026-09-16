# Ideas — yours, Claude's, and the rejected ones

Every idea raised in this project, with **what happened to it** and **why**.

**Status key:**
- ✅ **done** — built and in the project
- 🟡 **partly** — some of it done
- 🔵 **open** — a good idea, not done yet
- ❌ **rejected** — decided against, with the reason
- ↩️ **replaced** — done at first, then swapped for something better

---

# Part 1 — Your ideas

### The crash project itself

| # | your idea | when | status | what happened, and why |
|---:|---|---|---|---|
| 1 | Build a **cost project** on the Florida crash data, privately, and mention it on the resume only — **no website** | 15 Aug | ✅ | This is the project. It stays private because the crash data is licensed |
| 2 | Use **Tampa MEP as the spine** of the project for the NREL role | 15 Aug | ✅ | Everything builds on NREL's MEP score |
| 3 | Focus on **the five counties** of FDOT District 7 | 7 Sep | ✅ | Hillsborough, Pinellas, Pasco, Hernando, Citrus |
| 4 | Use the **full crash file** (547,205 crashes with road locations) and **FDOT's road data** to find which roads are dangerous | 7 Sep | ✅ | Became the road-by-road safety model. It makes driving danger vary by neighbourhood |
| 5 | Put a **money penalty** on crashes, based on the value of lives lost | 7 Sep | ✅ | The core of the project: crash cost per mile added to MEP's money cost |
| 6 | **Include injuries**, not just deaths | 7 Sep | ✅ | Serious injuries are included, at $1.3 million each |
| 7 | Add a **time penalty**: a crash that kills a cyclist or pedestrian causes **delay for everyone** on the road, and "the traveller pays with time" | 7 Sep | ↩️ ❌ | Built as a traffic-jam delay term. **Deleted 10 Sep**: the minutes were typed in by hand and no step could calculate them. It moved the headline 2.4 points |
| 8 | Use **Florida's own delay figures** (5% motorways, 12.5% main roads) instead of the US average (25%) | 7 Sep | ↩️ | Used at the time, then the whole delay term was deleted |
| 9 | Don't compare bus and driving so much: **few people use buses here; people use Uber/Lyft more.** Is Uber included in driving? | 7 Sep | 🟡 | Buses stay in the score but barely affect it (0.7%). **Uber/Lyft was never added as a mode**: it is 1.0% of trips here (see Part 2, #20) |
| 10 | For walking and biking, consider **heat, humidity, heat warnings and how unwalkable the city is** | 7 Sep | 🔵 | Not done. No weather or comfort factor exists in MEP. NREL's own "Walking Comfort Index" (2025) is a related approach |
| 11 | Check **motorbike deaths**, which were missing | 7 Sep | ✅ | Added to the crash bill: $10.72B a year. Motorbikes can't be in the score (no MEP mode) |
| 12 | Don't use a national average when **Florida data exists** — "you have so much data" | 7 Sep | ✅ | Became a general rule: measure locally wherever possible |
| 13 | **Crime inside buses** is harm too, not in the road crash data | 16 Aug | 🟡 ❌ | Considered carefully. **Left out** of the bus rate so cars and buses are compared fairly: the car side only counts traffic crashes. Crime was 57.8% of bus rider deaths nationally |

### Building MEP properly

| # | your idea | when | status | what happened, and why |
|---:|---|---|---|---|
| 14 | Actually **build MEP from its own recipe** ("did we even do this?" — MEP's Table 1) — "do it" | 8 Sep | ✅ | All three equations built from scratch: destinations, trip shares, travel times by 4 modes, bus routing |
| 15 | Use the **latest data**, not 2017 | 8 Sep | ✅ | NHTS 2022, LODES 2023, ACS 2023. Cost: no Florida-only survey figures in 2022 |
| 16 | Put **bikes in the travel-time calculation** too | 8 Sep | ✅ | Bike network at 12 mph |
| 17 | Use the **HART/PSTA timetable feed** from the Mobility Database | 8 Sep | ✅ | Used (PSTA's link there was broken, so PSTA's own was used) |
| 18 | Compare with NREL's **South Florida report** for **how** they ran MEP — but **don't copy** their study: our data, counties and safety focus are different | 8 Sep | ✅ | Took settings and method; kept our own analysis |
| 19 | Keep going until there's a **finished report like the South Florida one** | 8 Sep | ✅ | `REPORT.md` |

### Checking and defending it

| # | your idea | when | status | what happened, and why |
|---:|---|---|---|---|
| 20 | Keep **heavy reviews** going, step by step; review the maths, code and functions **before** running | 16 Aug | ✅ | Multiple independent audits and a growing test suite |
| 21 | Run **three separate reviews** so the maths numbers don't get mixed up | 16 Aug | ✅ | Done at the time |
| 22 | Keep **updating the review agent** with literature, NREL data and mistakes caught | 16 Aug | ✅ | The audit agent's instructions list the project's past mistakes |
| 23 | Run **"the deepest audit in the world"**: NREL experts will grill you; compare against NREL's MEP reports (**Denver and South Florida**) | 9 Sep | ✅ | The 9 Sep audit found 11 real problems, all fixed. The reports on disk were Hou et al. (Columbus), the FDOT South Florida report, and Young et al. (TRB); a Denver-specific report was not among them |
| 24 | Fix the **safety curve fitted only on crashed roads**, and the **deaths-vs-injuries split** | 9 Sep | ✅ | Both fixed |
| 25 | Make this **an actual project with the best evaluation** | 11 Sep | ✅ | Built the prediction test (fit 2019–22, predict 2023–25) |
| 26 | **Find holes** in the project | 10 Sep | ✅ | Found the unbacked 93% claim, the unchecked documents, motorbikes, the national bus rate |
| 27 | **Florida people drive** — how can MEP give walking and biking such a big share? | 14 Sep | 🟡 | You were right: cycling is 17.7% of the score but 1.8% of real trips. A rough version weighted by real travel gives ~13% instead of 23%. **A proper version isn't built yet** |
| 28 | **Biking in Florida is mostly exercise**, because of the heat | 14 Sep | ✅ | Checked: 68.7% of surveyed bike trips here are exercise/recreation, none to work. But 42% of cyclists killed died at night, suggesting many are riding to get somewhere |
| 29 | Is the drop only **because of already-published MEP scores**? | 14 Sep | ✅ | Answered: no. There is no published MEP for Tampa Bay; both numbers are ours |

### Documents and learning

| # | your idea | when | status | what happened |
|---:|---|---|---|---|
| 30 | **Simple language, always** — explain like you know nothing | 8 Sep onward | ✅ | Now a permanent rule (see `RULES.md`) |
| 31 | A **critique document** of what the authors will ask, with simple answers | 9 Sep | ✅ | `INTERVIEW_QA.md` |
| 32 | A **reading guide** | 9 Sep | ✅ | `READING_GUIDE.md` |
| 33 | **Learning resources** with links: O'Reilly *Data Science from Scratch*, blogs, papers | 10 Sep | ✅ | `LEARNING_RESOURCES.md` |
| 34 | A **20-minute presentation** | 10 Sep | 🟡 | `PRESENTATION.md` exists as a text outline; **no slide file yet** |
| 35 | Keep **"what I did"** updated — everything, big and small, including what was discarded and why | 10–14 Sep | ✅ | `WHAT_I_DID.md` |
| 36 | **Four files:** maths, data, assumptions/choices, how it runs vs standard MEP | 14 Sep | ✅ | `MATH.md`, `DATA.md`, `ASSUMPTIONS_AND_CHOICES.md`, `HOW_IT_RUNS_VS_STANDARD_MEP.md` |
| 37 | A **MEP file** | 14 Sep | ✅ | `MEP.md` |
| 38 | A **data folder** guide and a **corrections file** | 14 Sep | ✅ | `data/README.md`, `CORRECTIONS.md` |
| 39 | A **GitHub repo** | 14 Sep | ✅ | Private, `yrasool/i4-safety`, code and documents only |
| 40 | Keep **everything from the chat** in sorted files | 14 Sep | ✅ | This folder |
| 41 | A **learning document** — why, what, how, who, from zero | 14 Sep | ✅ | `LEARN.md` |

### Earlier projects (August), before the MEP project

| # | your idea | when | status | what happened |
|---:|---|---|---|---|
| 42 | An **HTML crash map** of the I-4 study with zoom, showing crashes near intersections (250 ft) — and teach me the code | 5 Aug | ✅ | Built. Separate from the MEP project |
| 43 | The **"many crashes stacked on one point"** problem — "maybe this is the problem to work on" | 5 Aug | ✅ | Investigated and handled in the I-4 maps |
| 44 | A **static exhibit**: crash concentration by milepost, for the report | 5 Aug | ✅ | `I4_Crash_Concentration_by_Milepost` |
| 45 | A **really good project for traffic analyst roles**, not redoing what was done | 6 Aug | ✅ | Led to the high-risk roads work |
| 46 | A **high-risk roads map** | 6 Aug | ✅ | Built on open Allegheny County data (`road-risk/`), with critical rate and Empirical Bayes |
| 47 | **Not** assigning crashes to intersections — "I wanted the original risk roads" | 7 Aug | ✅ | Kept the risk-roads approach |
| 48 | A **3D map** (three.js) with mainline, ramp and intersection crashes in different colours | 10 Aug | ✅ | Built; many styles tried |
| 49 | **Google Maps / satellite style** instead — "all the designs are hideous" | 11 Aug | ✅ | Satellite-style map built |
| 50 | Free ways to show **HCS / ArcGIS** experience | 7 Aug | 🔵 | Discussed; not a deliverable here |
| 51 | **EV scenario**: recompute energy with 30% or 50% electric cars | 15 Aug | 🔵 | Proposed as a quick addition; never built in the current project |
| 52 | **NTD ridership** data | 15 Aug | 🟡 | NTD passenger-miles used for the bus rate; ridership analysis not done |
| 53 | A **literature review** section | 15 Aug | ✅ | In `REPORT.md` and `READING_GUIDE.md` |

---

# Part 2 — Claude's ideas

| # | Claude's idea | when | status | what happened, and why |
|---:|---|---|---|---|
| 1 | Use **EPA's "jobs within 45 minutes"** instead of building a routing engine, and just add the injury term | 15 Aug | ↩️ ❌ | The first version. **Replaced**: with one crash cost per mode, the map was only a picture of bus use (proved to 16 decimal places) |
| 2 | **Break-even exposure** for walking and biking, instead of guessing their miles | 15 Aug | ↩️ | Replaced by measuring walking and biking miles from the 2022 survey |
| 3 | **Pool the bus rate nationally**, since Tampa had only 2 bus deaths | 15 Aug | ✅ | Kept, then refined to buses-only, collisions-only |
| 4 | **Tests that check failures**, not just "does it run" | 16 Aug | ✅ | 20 tests now |
| 5 | A **road-by-road safety model** (safety curve + Empirical Bayes) to make driving danger vary by place | 8 Sep | ✅ | Works; with routes followed (step 40), local danger is 7.0% of the map, up from 1.3% |
| 6 | Match the **Minnesota study** (Cui & Levinson) before trusting the car crash cost | 15–16 Aug | ✅ | Passes at 1.65× |
| 7 | Run **NREL's own validation tests** on our version | 9 Sep | ✅ | Passes, plus two extra tests |
| 8 | A **checker** that compares every number in the documents with the data | 8 Sep | ✅ | Checks 29 report figures plus 10 documents |
| 9 | **Delete the delay term** rather than defend it | 10 Sep | ✅ | Also recommended by the 9 Sep audit |
| 10 | **Separate safety curves by road type** | 10 Sep | ✅ | Fits better |
| 11 | **Walking and biking danger by neighbourhood** (step 32) | 10 Sep | ❌ | Tried six ways; the signal was too weak, so it wasn't used |
| 12 | **Traffic-by-year check** | 10 Sep | ✅ | Our rates are 8–12% too low — conservative |
| 13 | **Charge crashes both ways** (to the victim vs to the driver) | 10 Sep | ✅ | Both reported; the choice changes the answer |
| 14 | **Prediction test** with resampling | 11 Sep | ✅ | Built; **not yet in the run list** |
| 15 | **Stale-file list** after every run | 10 Sep | ✅ | Catches steps missing from the run list |
| 16 | **Test how the answer changes with MEP's cost weight**, or give crash cost its own weight | 14 Sep | 🔵 | The biggest untested choice |
| 17 | **A version weighted by how people actually travel** | 14 Sep | 🔵 | Only a rough estimate (~13%) so far |
| 18 | **Bikes only on safer roads** as a comparison | 14 Sep | 🔵 | Not tried |
| 19 | **Save copies** of the three downloads that happen every run | 14 Sep | 🔵 | Not done |
| 20 | **Uber/Lyft as a mode** (MEP's default table has it) | — | 🔵 | Never built; no reason written down |
| 21 | **Move old scripts** to an `archive/` folder | 14 Sep | 🔵 | Not done |
| 22 | **Charts and maps** | 14 Sep | 🔵 | Not done |
| 23 | **A real slide deck** | 14 Sep | 🔵 | Not done |
| 24 | **An allow-list** `.gitignore` so no data file can be uploaded by accident | 14 Sep | ✅ | Done |
| 25 | **Congested travel times** | — | 🔵 | No free source |
| 26 | **People per car by vehicle type** (trucks) | 8 Sep | 🔵 | Not done |
| 27 | **Proper bus-time averaging** (count missed departures) | 8 Sep | 🔵 | Not done |

---

# Part 3 — Rejected ideas, and why

Grouped by reason.

### Rejected because it was wrong

| rejected idea | why | replaced by |
|---|---|---|
| EPA's 45-minute job counts as the geography | the map could only show bus use, not danger | our own MEP calculation |
| Car deaths from Florida's statewide average | 68% too high for Tampa Bay | counted from the crash file |
| An AAA figure of $0.796 per car-mile | **doesn't exist** — you caught it | measured people per car |
| People per car worked backwards from MEP's energy setting (1.5) | inferred, not measured | 1.502 from the survey |
| FHWA "ATF" count for walking | mixes walking, biking and ferries | survey miles |
| Crash costs **per crash** on counts of **people** | 8× too high | cost per person |
| "Work" as MEP's reference place | 11× too big | restaurants ("meals") |
| Tampa's own totals for scaling | gave arts a weight of 52 | national totals |
| Delay share 55% | covered all irregular delay, not just crashes | — (delay term deleted) |
| Delay share 25% | a national headline | — |
| Delay share 12.5% | a Broward County figure | — |
| Plain average of neighbourhoods | not MEP's rule | population-weighted |
| Zero travel time inside your own neighbourhood | gave big areas instant access | a real time based on size |
| Safety curve on crashed roads only | left out quiet roads | all roads |
| Walking and biking distances from a scratch file | 2.8× and 3.5× too high | survey |
| Test that couldn't fail | passed on the fake map | a test of the exact formula |
| "The fake-map problem is solved by our own travel times" | it wasn't | local driving danger (1.3%, then 7.0% once routed) |

### Rejected because it couldn't be defended

| rejected idea | why |
|---|---|
| Crash-caused traffic-jam minutes | typed in by hand; no step could calculate them |
| The "93%" claim | typed into an old script; nothing current reproduced it — measured as 99.0% |
| A Tampa-only bus crash rate | only 2 deaths |
| Walking and biking danger by neighbourhood | signal too weak |

### Rejected to keep comparisons fair

| rejected idea | why |
|---|---|
| Crime inside buses in the bus rate | the car side counts traffic crashes only |
| Trains in the bus rate | Tampa has none |
| Minor injuries | walking and biking injuries are only recorded as killed or seriously injured |
| The "Amsterdam weight" as the main result | a Dutch study with no US equivalent — kept as a side test only |

### Rejected because of the licence or privacy

| rejected idea | why |
|---|---|
| A public website serving the Signal Four crash records | the data is licensed for specific projects; publishing it would breach that |
| Any data files on GitHub | licensed data; also too big — code and documents only |

### Rejected because of what you wanted

| rejected idea | who / why |
|---|---|
| A "generalist" claim on the resume | you: not a good idea |
| A literature-review-only project | you: "sounds like literature", wanted an outcome-based project like the parks or grid projects |
| Assigning crashes to intersections | you: wanted the risk-roads map instead |
| The first 3D map colours and designs | you: "hideous" — wanted Google Maps or satellite style |
| A technical, jargon-heavy explanation | you: "I understood nothing" — simple language instead |
| Copying the South Florida study's approach | you: our data, counties and focus are different |
| NHTS 2017 | you: the latest data |

### Rejected for technical reasons

| rejected idea | why |
|---|---|
| Friday bus timetables | PSTA's weekday schedule doesn't run Fridays |
| The Mobility Database link for PSTA | broken |
| The statsmodels library | not installed; fitted with scipy instead |
| Reading scripts' descriptions to find missing steps | a description was itself out of date |
| FDOT's live road database | changed between runs; saved a copy instead |

### A worry that turned out fine

| worry | outcome |
|---|---|
| (29 Aug) Our MEP formula might be a simple weighted sum, not NREL's real equation — "the thing that could sink you" | Checked against NREL's actual equations: MEP's penalty **is** −0.5 × energy − 0.08 × minutes − 0.5 × money, turned into a keep share, inside the band-by-band sum. Our version follows it exactly |
