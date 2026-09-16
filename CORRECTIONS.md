# Corrections — every mistake found and fixed

This is the full record of **every correction** made to the project, in plain language.

For each one:
- **What was wrong**
- **How it was found**
- **The fix**
- **What it changed** in the results

**Why keep this?** Anyone checking the work — including an interviewer — can see exactly what
went wrong and how it was handled. Mistakes found and fixed openly are a strength, not a weakness.

Other files: `WHAT_I_DID.md` (the story), `MATH.md`, `DATA.md`, `ASSUMPTIONS_AND_CHOICES.md`,
`HOW_IT_RUNS_VS_STANDARD_MEP.md`, `MEP.md`.

**Where corrections came from:**

| source | when |
|---|---|
| building and checking the work myself | throughout |
| **Audit 2** — an independent checking program that recalculated every number | 8 September |
| **Audit 3** — a deeper independent check against NREL's published reports | 9 September |
| **you** | several times — noted where it happened |

*(Audit 1, on 8 September, stopped early on a usage limit and found nothing.)*

---

## Part 1 — Corrections that changed the headline number

These moved the main result. In order:

| # | date | what was wrong | how found | fix | headline before → after |
|---:|---|---|---|---|---|
| 1 | 8 Sep | MEP's scaling numbers used **Tampa Bay's own totals**; MEP defines them from **national** totals. Arts got a silly weight of 52 | reading NREL's South Florida report | national totals | first run **18.8–25.6%** → **21.8–29.6%** (with the next few fixes) |
| 2 | 8 Sep | **Bus cost 0.86** instead of MEP's **0.85** | the same report's Table 7 | 0.85 | (part of the above) |
| 3 | 8 Sep | **People per car** came from old data (1.67), and an **AAA figure that doesn't exist** | **you caught it** with a screenshot; then measured | measured from the 2022 survey: **1.502** | (part of the above) |
| 4 | 8 Sep | **Walking and biking miles** were typed in from a scratch file — **2.8× and 3.5× too high**, and the percentages behind them added up to 110% at one end and 90% at the other | Audit 2 | measured from the 2022 survey | **21.8–29.6%** → **26.6–29.5%** |
| 5 | 8–9 Sep | Every neighbourhood had the **same** driving danger | known limit; built road-by-road model | each neighbourhood gets its own | → **26.3–29.3%** |
| 6 | 9 Sep | Neighbourhoods combined by a **plain average**; MEP's rule is **weighted by population** | Audit 3 | population-weighted | → **25.1–28.1%** |
| 7 | 9 Sep | The **safety curve** was fitted only on the **2,427 roads that had crashed**, leaving out the quiet ones | Audit 3 | all **2,848** roads | (with #8) → **24.9–27.9%** |
| 8 | 9 Sep | Each road's **share of deaths** used raw tiny numbers — 51 roads looked "100% deadly" | Audit 3 | pulled toward the regional average | (with #7) |
| 9 | 10 Sep | **Crash-caused traffic-jam minutes** were typed in by hand in two files; no step calculated them | Audit 3 flagged it; decided on 10 Sep | **deleted** | **24.9–27.9%** → **22.5%** |

---

## Part 2 — Corrections that changed other numbers

| # | date | what was wrong | how found | fix | what it changed |
|---:|---|---|---|---|---|
| 10 | before 8 Sep | Crash costs **per crash** applied to counts of **people**, all injury levels, per car-mile — **8× too high** | the Minnesota check failed | cost **per person**, deaths and serious injuries only, per passenger-mile | car crash cost now **$0.1059** a mile; check passes at **1.65×** |
| 11 | before 8 Sep | Car deaths estimated from **Florida's average** mix — **68% too high** (384.6 a year vs 229.3 counted) | checking the counts | counted directly from the crash file | correct car deaths |
| 12 | before 8 Sep | Crash bill **left out motorbikes** ($8.8B, $2,548 a person) | checking the totals | added | **$10.72B**, **$3,092** a person |
| 13 | before 8 Sep | **Tampa-only bus crash rate** rested on **2 deaths** | checking sample size | whole-US rate | a measurable bus rate |
| 14 | before 8 Sep | National bus rate **mixed in trains and crime** | checking what was counted | fixed-route buses, traffic crashes only — 12 deaths | a fair car-vs-bus comparison |
| 15 | before 8 Sep | Population from **EPA's older count** (3,173,134) — cost per person **9.3% too high** | checking the population | Census mid-2022, **3,468,871** | cost per person corrected |
| 16 | 8 Sep | **"188 to 1"** car-vs-bus compared deaths + injuries for cars against deaths only for buses | Audit 2 | like-for-like: **95 to 1** | the comparison halved |
| 17 | 8 Sep | **Travel time to your own neighbourhood was zero** — big rural areas got instant access to everything inside them | Audit 2 | a real time based on the area's size | lower walking and bus scores in large neighbourhoods |
| 18 | 8 Sep | **Walk-only paths counted as bus trips**, and bus reach was forced above zero | Audit 2 | a trip only counts if you actually got on a bus | correct bus reach |
| 19 | 9 Sep | **"Work" used as the reference place** instead of restaurants — every score **11× too big** | Audit 3 | restaurants, as MEP does | raw score **91,094 → 8,241**; percentages unchanged |
| 20 | 9 Sep | Report said biking costs **$2.76 a mile, 26× cars** — the old deleted number | Audit 3 | **$9.59 a mile, 91×** | corrected in the report |
| 21 | 9 Sep | **Safety-curve numbers** in the report came from the wrong version of the curve | Audit 3 | corrected | report matches the model |
| 22 | 9 Sep | **"601 neighbourhoods"** too big to walk across used a different formula from the one printed | Audit 3 | **319** | corrected |
| 23 | 9 Sep | **"91% of the bus band was self-counting — fixed"** — it wasn't; still **98.6%** | Audit 3 | wording corrected; limit stated | honest description |
| 24 | 9 Sep | Car-vs-bus deaths ratio **48×** came from a stale file | Audit 3 | **53.6×** | corrected |
| 25 | 10 Sep | Interview notes said **"93%"** of people killed walking were hit by a car. It traced to a number **typed into an old script**; nothing current could reproduce it | my own hole-hunt | measured properly: **99.0%** | Q&A corrected |
| 26 | 14 Sep | Driving danger range written as **$0.06–$0.41** — left over from before the safety curve was refitted | checking the results file | **$0.08–$0.40**, typical **$0.10** | documents corrected |

---

## Part 3 — Corrections to the checking tools

**Why these matter:** a broken checker is worse than none — it says "all fine" and stops anyone looking.

| # | date | what was wrong | how found | fix |
|---:|---|---|---|---|
| 27 | 8 Sep | The **test for a fake map passed on the fake map** — it could never fail | Audit 2 | rewritten to test the exact formula |
| 28 | 8 Sep | The **number checker "found" 20.3%** in the report — but it matched a **different** number (a trip share) | Audit 2 | a number must sit beside its label |
| 29 | 9 Sep | The checker couldn't tell **24%** from **124%** | Audit 3 | checks the whole number |
| 30 | 9 Sep | The checker's **self-test never ran the check** | Audit 3 | now runs the real check |
| 31 | 9 Sep | The Minnesota check's pass band (0.5–4.0×) was **so wide it could never fail** | review | tightened to **1.2–3.0×** |
| 32 | before 8 Sep | The Minnesota check compared **per-person-mile** with **per-car-mile** — the unit error lived inside the test built to catch unit errors | the third attempt at the test | units matched first |
| 33 | 10 Sep | The checker only checked the **report**, not the documents you speak from | my own hole-hunt (it's how the 93% survived) | now checks the Q&A, presentation and all explainer files |
| 34 | 10 Sep | When the checker failed, **it crashed** printing a special character | running it | fixed |
| 35 | 14 Sep | Two automatic tests only looked at **9 of the 27** steps, and one looked for a setting name that **doesn't exist** | Audit 3 had flagged it; fixed 14 Sep | now check every step; shown to catch a planted mistake |

---

## Part 4 — Corrections to how the project runs

| # | date | what was wrong | how found | fix |
|---:|---|---|---|---|
| 36 | 8 Sep | The **first map download** had only 31 of 88 pieces | a safety check stopped it | waited for all pieces |
| 37 | 8 Sep | A **Friday** bus timetable would have dropped every PSTA bus | checking the schedules | Thursday |
| 38 | 8 Sep | The **PSTA timetable link** was broken (a capital "G") | download failed | PSTA's own link |
| 39 | 9 Sep | **Florida DOT's road data changed between runs** (2,429 roads, then 2,427) | the run-twice check | saved a copy |
| 40 | 9 Sep | **Step 05 missing** from the run list — an old copy of its file was used | Audit 3 | added |
| 41 | 10 Sep | **Step 33 missing** from the run list | my own check | added, before step 29 |
| 42 | 10 Sep | **Step 01 missing** from the run list, and it downloaded live every time | checking `WHAT_I_DID.md` against the record | saved a copy; proved a fresh download identical; added |
| 43 | 10 Sep | Nothing could spot **old files** being used | after #40–42 | the run now lists every file it didn't rebuild |
| 44 | 10 Sep | In the walking-and-biking attempt, **zeros were rounded to tiny numbers**, hiding the effect | checking the results | only real observed values used |
| 45 | 11 Sep | **Duplicate road record** in Florida DOT's file (same stretch, two traffic counts) | the prediction test's own check | matched how step 09 treats it |

---

## Part 5 — Corrections to explanations

| # | date | what was wrong | how found | fix |
|---:|---|---|---|---|
| 46 | 8 Sep | Explanations were **too technical** | **you**: "I understood nothing" | rewritten in plain language — and now the rule for everything |
| 47 | 8 Sep | I said the project **had built MEP** — it had only changed one input to someone else's map | reviewing MEP's Table 1 with you | admitted, then built it properly |
| 48 | 8 Sep | Report said **"the floor is carried by driving"** — driving is only about a third of it | Audit 2 | corrected |
| 49 | 8 Sep | Report quoted the **largest** of three ways of averaging, without saying which | Audit 2 | the method is always named |
| 50 | 9 Sep | Report said the score size was **"unrescalable through three unknown factors"** — false | Audit 3 | removed |
| 51 | 9 Sep | Equity table said **"steadily rising"** when it wasn't | checking | the code now checks, not the sentence |
| 52 | 9 Sep | **"Nearly mixed up harm driving causes with harm drivers suffer"** — road rates counted everyone hurt; would have doubled driving's rate | a number twice as big as expected | people in vehicles only |
| 53 | 11 Sep | Prediction test summary said **"6 of 6 passed"** — 3 of the 6 are within noise | resampling test | **not yet fixed in the code** |
| 54 | 14 Sep | I described the unused Minnesota "full cost" figure and the traffic-jam problem as **my own discoveries** — Audit 3 had flagged both a day earlier | re-reading the audit | credit corrected |
| 55 | 14 Sep | I said the 93% was **"derived by nothing"** — it was typed into an old script | re-reading the old code | corrected |
| 56 | 14 Sep | A document row said switching to our own travel times **fixed the fake map** — it didn't | **your question** | corrected: it took giving each neighbourhood its own driving danger |
| 57 | 14 Sep | Documents said **"every data source is saved"** — three downloads aren't (transit database ×2, Census map points) | checking every step's downloads | corrected in all documents; saving them is on the to-do list |
| 58 | 14 Sep | Two "why people bike" labels were **wrong** at first ("Nonhub", "Other") — taken from the wrong part of the survey codebook | the labels made no sense | read the real codes |
| 59 | 14 Sep | First attempt at **crash times** read none of the dates | 0 of 1,540 read | used the right date format |

---

## Part 7 — 15 September 2026

| # | when | what was wrong | how it was found | what we did |
|---|---|---|---|---|
| 60 | 15 Sep | **Every casualty figure rested on one licensed file nobody else can open.** Not an error, but a single point of failure with no external check | asking what a reviewer could actually verify | step 37 checks it against Signal Four's **public** dashboard: 3,471 vs 3,526 killed, 20,305 vs 20,526 seriously injured — ratios 0.984 and 0.989, low as expected because our extract stops in November 2025 |
| 61 | 15 Sep | **Trip shares were national, and Tampa's are different** — the work share here is 27%, not our 20.3% | **your suspicion**, then the Tampa Bay Regional Travel Survey and BTS phone-trace data | tested all four sources: the drop is 22.4–22.6% in every case. Kept the national source and documented the test — see ASSUMPTIONS J1 |
| 62 | 15 Sep | **No check on whether Tampa Bay is typical of Florida** — the result could be waved away as a local curiosity | asking what an interviewer would attack | step 38: 17.9% of Florida's walking and cycling fatalities on 15.6% of its people, a concentration of 1.15. Cannot separate danger from exposure, and says so |
| 63 | 15 Sep | **Bus externality of $0.1532 per passenger-mile — three times a car — was wrong.** The numerator counted every bus (charter, shuttle, tour, coach); the denominator was HART and PSTA passenger-miles only | the number looked too bad to be true, so we checked what was in it | narrowed to transit buses (vehicle special function 13, 93% of them in the only two counties with fixed-route service): **$0.0649, 1.26× a car**. Kept out of the headline — it rests on three deaths |
| 64 | 15 Sep | **Static crash rates were never named as a limitation.** Injury rates per cyclist fall as cycling grows (Jacobsen 2003), so the model cannot score a scenario with more cycling | reading around the "nobody cycles here" objection | written into ASSUMPTIONS J2 and the presentation's limitations slide |
| 65 | 15 Sep | Claimed the low cycling rate here meant **MEP overstates cycling** — true, but one-sided | the same reading | both sides now stated: cycling is also **suppressed by** the danger being priced, so low uptake is not evidence the mode doesn't matter |
| 66 | 16 Sep | **Driving danger was attached by proximity, not by route.** Step 30 said so in its own docstring, and the map it produced was 77% county effect | **your request** to follow each trip's real route | step 40 routes 2,820,703 pairs and sums Empirical Bayes segment risk along each; shipped as the default. Headline 22.5% → **23.4%**; local share of the map 1.3% → **7.0%**. Regional crash cost per mile unchanged. See ASSUMPTIONS K |

**What 60–63 have in common.** None of them was a wrong calculation. Three were **missing
checks** — things no reviewer could verify — and one was a **denominator that did not cover its own
numerator**, which is the fourth time that exact shape has appeared in this project (after the
8× cost error, the local scaling factor, and the delay term's person-hours over vehicle-miles).

---

## Part 6 — Raised, but not yet fixed

For completeness — found, not corrected:

| what | raised by |
|---|---|
| step 26's self-check compares a formula with itself, so it can't fail | Audit 3 |
| cost per person uses 3,468,871 people, but the neighbourhood table totals 3,399,162 ($3,155 vs $3,092) | Audit 3 |
| the report doesn't say state roads carry only 78.5% of driving | Audit 3 |
| driving danger weighted toward roads near home is used for 40-minute trips | Audit 3 |
| no uncertainty ranges on the trip shares | Audit 2 |
| one people-per-car figure for trucks too | Audit 2 |
| bus times averaged generously | Audit 2 |
| a severity-matched Minnesota check | Audit 2 |
| the run-twice check compares only four numbers | Audit 3 |
| its "6 of 6" summary uses point estimates; three of the six are inside bootstrap noise | me |
| `23_mep.py` names a file it doesn't make | me |
| three downloads not saved | me |
