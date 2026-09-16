# How it runs — and how it compares with standard MEP

This file explains, from zero:
- **Part 1:** how the project actually runs, step by step, on the computer.
- **Part 2:** what "standard MEP" is, and how NREL normally runs it.
- **Part 3:** side by side — what we run the same, what we run differently, what we
  added, and what standard MEP does that we **don't** run.
- **Part 4:** what that means when comparing our results with NREL's.

Other files: `MATH.md` (the calculations), `DATA.md` (the sources),
`ASSUMPTIONS_AND_CHOICES.md` (why each choice was made).

---

# Part 1 — How the project runs

## The short version

Everything runs with **one command**, typed in the `i4-safety` folder:

```bash
python src/run_all.py
```

It runs **26 small programs ("steps")** one after another. Each step reads files made by
earlier steps, does one job, and writes new files. The whole run takes about **30 minutes**
(the last full run: **33.5 minutes**).

**Why many small steps instead of one big program?** Each step does one thing, so it can be
checked on its own, and a mistake can be found in one place.

## What happens, in order

The steps run in this order — **not** in number order. The numbers are just when each step was
written; the order is what each one needs from the others.

| # | step | what it does | needs | planned minutes |
|---:|---|---|---|---:|
| 1 | **01** | EPA accessibility data (for checking only) | saved EPA file | 1 |
| 2 | **02** | counts people killed and seriously injured, by mode and year | crash file | 3 |
| 3 | **03** | how many passenger-miles by car and bus | Florida DOT figure; transit database (downloaded) | 1 |
| 4 | **18** | one starting point per neighbourhood | Census map service (downloaded) | 1 |
| 5 | **24** | population and carless households per neighbourhood | Census tables | 2 |
| 6 | **16** | jobs of each kind per neighbourhood | LODES Florida | 1 |
| 7 | **17** | trip shares, people per car, walking and biking miles | travel survey | 2 |
| 8 | **25** | scaling numbers for each kind of place | LODES national | 3 |
| 9 | **04** | crash cost per mile by mode; the Minnesota check | steps 02, 03, 17 | 1 |
| 10 | **05** | bus crash rate | transit database (downloaded) | 2 |
| 11 | **19** | the road map (downloads only missing pieces) | OpenStreetMap | 1 |
| 12 | **20** | builds the car, walking and bike road networks | step 19 | 2 |
| 13 | **21** | travel times by car, walking and bike | steps 18, 20 | **15** |
| 14 | **22** | travel times by bus | steps 18, 20; timetables | **10** |
| 15 | **09** | casualties and traffic on each state road | crash file; Florida DOT roads | 5 |
| 16 | **33** | road types, and a separate curve for each | step 09; map | 3 |
| 17 | **29** | the safety curve and the blend | steps 09, 33 | 1 |
| 18 | **30** | each neighbourhood's driving danger | steps 21, 29 | 2 |
| 19 | **32** | walking and biking danger by place (tried; not used) | steps 17, 18, 24, 29 | 4 |
| 20 | **23** | **the MEP score** — normal and with crash cost | steps 04, 05, 16, 17, 21, 22, 24, 25, 30 | 2 |
| 21 | **26** | validation tests | steps 01, 23 | 3 |
| 22 | **27** | who is hit hardest | steps 23, 24 | 1 |
| 23 | **28** | the number checker | nearly everything | 1 |
| 24 | **31** | NREL's own tests | steps 21, 22, 23 | 1 |
| 25 | **34** | traffic-by-year check | step 02; federal traffic files | 1 |
| 26 | **35** | who pays when a car hits someone | steps 02, 03 | 2 |

**Not in the run yet:** **step 36**, the prediction test. It runs on its own:
`python src/36_holdout.py`.

**Not run at all:** old steps 06–08 and 10–15, from the first version.

## Why the order matters

A step must run **after** every step whose files it reads.

*Example:* step 29 (the blend) reads the road types made by step 33. If 29 ran first, it would use
**last time's** road types — or crash if there were none.

**This went wrong three times.** Steps 05, 33 and 01 were each missing from the list. Each time, an
**old copy** of their file was still on the computer, so nothing crashed — the project just quietly
used old data. Now they're all in the list, in the right order.

## What happens if a step fails

The run **stops immediately** and shows the last lines the failed step printed.

**Why stop?** Every later step would otherwise run on **old or missing** files and produce wrong
numbers that look fine.

Some steps are built to **stop themselves** when something is wrong:

| step | stops if… |
|---|---|
| 01 | the number of EPA rows doesn't match what EPA says it has |
| 04 | the Minnesota check isn't between 1.2 and 3.0 |
| 05 | it doesn't get exactly 12 bus deaths, or its download doesn't match the website's own total |
| 19 / 21 | too much of the road map is missing |
| 26 | the deleted traffic-jam minutes are ever turned back on |
| 28 | any number in the documents doesn't match the data |

## What happens at the end

**1. Did anything change?** The run compares **four numbers** with the previous run:

| number | last value |
|---|---|
| plain-average normal score | 8,241.1632 |
| plain-average score with crash cost (low case) | 6,276.9914 |
| car crash cost per mile | 0.105924 |
| number of neighbourhoods | 2,170 |

If any change, it prints **"MOVED"** and stops with an error. **Why:** running the same project twice
must give the same answer. If it doesn't, something changed underneath — a website's data, or a step
that isn't consistent.

**2. Which files weren't rebuilt?** It lists every data file that's **older** than this run. On the last
run: 4 files, all from old retired steps, read by nothing.

## A faster run

```bash
python src/run_all.py --fast
```

Skips the two slow steps (**21** and **22**, travel times) and reuses their saved results. Use it when
only crash data or later steps changed. **Don't** use it after changing the road map, timetables or
starting points.

## Before quoting any number

```bash
python src/28_check_report.py
python -m pytest tests -q
```

- The **checker** re-checks **29 numbers** in the report, and every number in the interview Q&A, the
  presentation, `WHAT_I_DID.md` and the four explainer files, against the real data.
- The **tests** (20 of them) each fail if a known past mistake comes back.

## What's saved, and what's downloaded every run

Most data is **saved on the computer** after the first download, so websites changing can't change the
answer. **Three downloads are not saved** and happen every run:

| step | downloads | protection |
|---|---|---|
| 03 | HART and PSTA passenger-miles | the end-of-run comparison |
| 05 | national bus deaths and bus miles | stops unless exactly 12 deaths; checks against the website's own total |
| 18 | Census neighbourhood points | the end-of-run comparison (2,170 neighbourhoods) |

**This is a gap:** if those websites change or go offline, a rerun could fail or shift. Saving copies is on
the to-do list.

---

# Part 2 — What standard MEP is

## Who made it, and what it measures

**MEP** (Mobility Energy Productivity) was created by **NREL**, a US government energy lab, and described
in **Hou et al. (2019)**. For each area it measures:

> **how many useful places people can reach, weighted by how quickly, cheaply and energy-efficiently they
> can get there.**

**Why NREL made it:** to have one score that rewards transport that is fast, cheap **and** energy-efficient
— so that, for example, a new bus line or bike network shows up as a better score.

## What standard MEP needs

According to NREL and the South Florida report, the key inputs are:

1. **Isochrones** — areas reachable within 10, 20, 30 and 40 minutes, by each mode.
2. **Land use and employment** — what places exist and where.
3. **Energy and cost per mode** — a default table.
4. **Activity frequency** — how often people go to each kind of place.
5. **Population density** — to weight areas by where people live.

## How NREL normally runs it

| part | standard MEP |
|---|---|
| **areas** | a grid of small squares, combined up to bigger areas by population |
| **road network** | a commercial map (TomTom) |
| **places** | a commercial list of places (CoStar) — counts of **places** |
| **bus travel times** | a program called **OpenTripPlanner**, using timetables |
| **how often people go places** | the national travel survey |
| **modes** | car, bus, walk, bike — and the default table also includes Uber/Lyft and dial-a-ride |
| **settings** | a default table of energy and cost per mode; weights −0.5 energy, −0.08 per minute, −0.5 per dollar; restaurants ("meals") as the scaling reference |
| **combining** | weighted by population |
| **crash harm** | **not included** |

## How it was run in South Florida (the report we used)

NREL and Florida International University ran MEP for **Miami-Dade, Broward and Palm Beach** counties
(FDOT report BDV29-977-66, 2023). Differences from the standard setup:

- They tried **two** data setups and compared them:
  - **standard data** (TomTom roads + CoStar places) → region score **122.35**;
  - a **regional traffic model's** road network and **job counts** → region score **11,983**.

  **What that shows:** the raw score depends hugely on how you count places, but the **pattern** across the
  map was similar.
- **Bikes:** in the basic version, all roads except limited-access highways, at **12 mph**. In a "bike lane"
  version, **18 mph** on roads with bike lanes — the bike score rose **141%**.
- **Buses:** a scenario testing **electric buses** on future routes.
- **Trip shares:** from a published table based on the **2017** survey.

---

# Part 3 — Side by side

## What we run the SAME

| | standard MEP | ours |
|---|---|---|
| the three equations | ✓ | ✓ |
| time bands | 10, 20, 30, 40 min | ✓ same |
| energy and money cost per mode | default table | ✓ same table (car 0.90 / $0.48; bus 0.65 / $0.85; walk and bike 0 / $0) |
| weights | −0.5, −0.08, −0.5 | ✓ same |
| scaling reference | restaurants | ✓ same |
| scaling basis | national totals | ✓ same |
| "newly reached" in each band | ✓ | ✓ same |
| combining areas | by population | ✓ same |
| bikes | 12 mph, no motorways (South Florida basic) | ✓ same |

**Why sameness matters:** it makes our result genuinely **MEP**. That's also why NREL's own tests can be run on
it — and it passes them.

## What we run DIFFERENTLY

| | standard MEP | ours | why | what it changes |
|---|---|---|---|---|
| **areas** | grid of squares | 2,170 Census neighbourhoods | crash, population and car data already come by neighbourhood | less detail inside large neighbourhoods |
| **places** | counts of places (CoStar, paid) | job counts (LODES, free) | anyone can rebuild ours | raw scores on a different scale — compare percentages only |
| **road network** | TomTom (paid) | OpenStreetMap (free) | free; includes footpaths | our walking network is probably more complete |
| **speeds** | the South Florida run used a regional traffic model | speed limits, no traffic | no free traffic data | reach is an upper limit |
| **bus routing** | OpenTripPlanner | our own program (RAPTOR) on real timetables | built and checked ourselves | the audit checked its results, not every line of code |
| **trip shares** | published table (2017 in the South Florida report) | calculated from the 2022 survey's raw data | newest data; checked against the published 2.28 trips a day | work trips count less (people commute less since 2017) |
| **time inside your own area** | — | a real time based on its size | stops big rural areas getting instant access to everything inside them | lower walking and bus scores in large neighbourhoods |
| **modes** | 4 + Uber/Lyft + dial-a-ride in the default table | 4 only | not built; no reason recorded | unknown; Uber/Lyft is 1% of trips here |

## What we ADDED that standard MEP doesn't have

| addition | what it is | why |
|---|---|---|
| **crash cost** | crash cost per mile added to each mode's money cost | the whole purpose. **The only change to MEP's formula** — no new equation, no new weight |
| **driving danger by neighbourhood** | each neighbourhood's car crash cost from nearby roads | so the map shows more than travel habits |
| **the Minnesota check** | our crash cost compared with a published study; the run stops if it's far off | proves the crash cost is sensible |
| **the number checker** | every number in the documents checked against the data | stops documents drifting away from the results |
| **run-twice check and old-file list** | the run compares its answer with last time and lists files it didn't rebuild | proves the answer is repeatable |
| **extra tests** | "driving costs more → score down" and "change nothing → same score", on top of NREL's two | a score that rises on everything would pass NREL's tests alone |
| **analyses** | who pays when a car hits someone; traffic by year; prediction test; who is hit hardest | to answer the questions an expert would ask |

## What standard MEP does that we DON'T run

| standard MEP feature | why we don't run it | what we lose |
|---|---|---|
| **Uber/Lyft and dial-a-ride modes** | never built; no reason written down | two modes' contributions |
| **a grid of squares** | our data is by neighbourhood | finer detail |
| **paid road network and place list** | cost, and no one could check our work | a direct comparison with NREL's raw scores |
| **congested travel times** (from a traffic model) | not freely available | realistic rush-hour reach |
| **scenario studies** (new bike lanes, electric buses) | not our question — our "scenario" is adding crash cost | nothing needed |
| **faster bikes on bike lanes** (18 mph) | that was a scenario, not the basic setup | — |

---

# Part 4 — What this means for comparing results

## You CAN compare

- **Percentages** — "crash cost removes 16.2%" doesn't depend on how places are counted.
- **Rankings** — which neighbourhoods score higher or lower.
- **Behaviour** — our version passes NREL's own tests: better fuel economy → score up (+27.6%); faster driving
  → up; higher driving cost → down (−30.1%); no change → same score.

## You CANNOT compare

- **Our raw score (7,567 by standard MEP, 6,908 on realistic bike and walk networks) with NREL's numbers** for other places.
  - NREL's own South Florida run gave **122.35** with place counts and **11,983** with job counts — for the **same**
    region.
  - We use job counts, so our score is on the **11,983** kind of scale — but it's still not directly comparable.
- **The size** of the "faster driving" test result — our travel times stop at 40 minutes, so only the direction
  can be tested.

## What to say if asked "is this really MEP?"

> "Yes. Same equations, same default settings and weights, same time bands, same scaling reference and same
> population weighting. It passes NREL's own validation tests from Hou et al. The differences are in the data —
> free, rebuildable sources instead of paid ones — and the one change to the formula is adding crash cost to the
> money term. Because the data differs, I only compare percentages and rankings, never raw scores."
