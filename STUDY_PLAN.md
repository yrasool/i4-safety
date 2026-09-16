# Study plan — learn everything in this project

**51 lessons in 10 units.** Each lesson covers:

- **What** — the idea
- **Why** — why it matters here
- **How** — how it works
- **Mistake / lesson** — what went wrong or was learned in this project
- **Result** — the number or outcome
- **You should be able to answer** — check yourself before moving on

**How to study:** one lesson at a time, in the chat. Claude teaches, asks questions, you answer in your own
words, then Claude corrects and moves on. Tick the box when a lesson makes sense.

**Where to read more:** `LEARN.md` (concepts), `WHAT_I_DID.md` (the story), `MATH.md`, `DATA.md`,
`ASSUMPTIONS_AND_CHOICES.md`, `CORRECTIONS.md`, `notes/`.

| unit | topic | lessons |
|---|---|---|
| 1 | the big picture | 1–4 |
| 2 | the earlier crash work (August) | 5–7 |
| 3 | version 1, and why it was replaced | 8–10 |
| 4 | the data | 11–19 |
| 5 | the maths of MEP | 20–26 |
| 6 | road danger | 27–33 |
| 7 | the results | 34–39 |
| 8 | the honest problems | 40–42 |
| 9 | keeping it correct | 43–47 |
| 10 | tools, writing, interview | 48–51 |

---

# Unit 1 — The big picture

### ☐ Lesson 1. What MEP is
- **What:** NREL's score for how many useful places people can reach, counting time, money and energy.
- **Why:** it's the score the team you're applying to created.
- **How:** reachable places count more when trips are fast, cheap and low-energy; everything is added up.
- **Mistake / lesson:** early on, the project talked about MEP without really building it (see lesson 10).
- **Result:** our region scores 7,567 the normal way.
- **You should be able to answer:** What does MEP measure? What three things does it check? Who made it, and why?

### ☐ Lesson 2. The gap: crashes
- **What:** MEP charges nothing for people killed or hurt in crashes, and treats walking and biking as free.
- **Why:** 3,471 people were killed and 20,305 seriously injured in our five counties in under seven years.
- **How:** we put crash harm into dollars and add it to MEP's money cost.
- **Mistake / lesson:** NREL's own safety work (Level of Traffic Stress, Walking Comfort Index) rates how safe streets
  **look**, not how many people were **actually** hurt. That difference is our contribution.
- **Result:** $10.72 billion a year, about $3,092 per person living here.
- **You should be able to answer:** What does MEP leave out? How is NREL's safety work different from ours?

### ☐ Lesson 3. The role, and why this project
- **What:** NREL's Center for Integrated Mobility Sciences (the posting says "NLR").
- **Why:** the work is travel surveys, transit data, accessibility and energy — this project uses all four.
- **How:** rebuild their metric, add a real gap, check everything against their published tests.
- **Mistake / lesson:** the project must be defensible in a 40-minute grilling by people who built MEP.
- **Result:** Tampa MEP chosen as the spine (15 August).
- **You should be able to answer:** Why does rebuilding MEP show more than just using it?

### ☐ Lesson 4. How the project grew, and the licence rules
- **What:** I-4 crash maps (5 Aug) → high-risk roads (6 Aug) → 3D maps (10 Aug) → NREL MEP idea (15 Aug) → full MEP
  build (8 Sep) → audits → documents → GitHub (14 Sep).
- **Why:** each step taught something used later.
- **How:** see `notes/TIMELINE.md`.
- **Mistake / lesson:** Signal Four crash data is **licensed** — no website, no publishing, resume mention only,
  private repo with code and documents only.
- **Result:** private repo `yrasool/i4-safety`.
- **You should be able to answer:** Why can't the crash data go online? What does the allow-list `.gitignore` do?

---

# Unit 2 — The earlier crash work (August)

### ☐ Lesson 5. The I-4 crash map and stacked crashes
- **What:** an interactive map of crashes in an FDOT I-4 study, with 250 ft rings around intersections.
- **Why:** to see where crashes really happen.
- **How:** crashes plotted from their coordinates.
- **Mistake / lesson:** **many crashes were stacked on exactly the same point** — the recorded location isn't
  always where the crash happened. And the ramp classifier could only label a crash as a ramp crash when its
  location and the police report agreed.
- **Result:** 29 ramp crashes identified.
- **You should be able to answer:** Why would many crashes share one point? Why can't a computer always tell a ramp crash?

### ☐ Lesson 6. The milepost exhibit, and a false hotspot
- **What:** a chart of crash concentration along the corridor by milepost.
- **Why:** to show where crashes cluster (MP 24.1).
- **How:** count crashes per milepost segment, after cleaning.
- **Mistake / lesson:** without cleaning, **MP 21.8 would have looked like a hotspot** when it wasn't.
- **Result:** a report-ready exhibit.
- **You should be able to answer:** Why clean data before calling a place a hotspot?

### ☐ Lesson 7. High-risk roads: count vs rate
- **What:** ranking roads in Allegheny County (open data) by danger.
- **Why:** a busy road has more crashes just because more people use it.
- **How:** crash **rate** = crashes ÷ traffic; critical rate; Empirical Bayes.
- **Mistake / lesson:** the top 25 roads **by count** and the top 25 **by rate** shared **one** road — they answer
  different questions.
- **Result:** a high-risk roads project.
- **You should be able to answer:** Why is a crash count not the same as danger?

---

# Unit 3 — Version 1, and why it was replaced

### ☐ Lesson 8. Version 1: EPA's "jobs within 45 minutes"
- **What:** instead of calculating travel times, use EPA's published count of jobs reachable within 45 minutes
  by car and by transit, and add a crash cost per mode.
- **Why:** quick; no routing needed.
- **How:** crash cost shrank car and bus access by a fixed share each.
- **Mistake / lesson:** it used EPA's **2018** neighbourhoods (2,098), which don't match 2020 ones.
- **Result:** early findings (later changed): 10.5% of driving's cost, 48× car vs bus.
- **You should be able to answer:** What was version 1's shortcut?

### ☐ Lesson 9. The fake map
- **What:** version 1's neighbourhood map only showed **how much each place uses buses**.
- **Why:** with **one** crash cost per mode for the whole region, nothing about crashes differed between places.
- **How:** loss = (1 − car keep) + bus share × (car keep − bus keep); only "bus share" varies.
- **Mistake / lesson:** proven to 16 decimal places; the ranking never changed with different crash costs. **And the
  test written to catch this couldn't fail** — it passed on the fake map.
- **Result:** map deleted.
- **You should be able to answer:** Why can't one crash number per mode make a real crash map?

### ☐ Lesson 10. "Did we even build MEP?"
- **What:** looking at MEP's recipe (Table 1: isochrones, land use, energy and cost, trip frequency, population).
- **Why:** the project had only changed one input to someone else's map.
- **How:** you said "do it" — everything was built from scratch.
- **Mistake / lesson:** admit a gap early rather than defend it.
- **Result:** the full MEP build (8 Sep).
- **You should be able to answer:** What five inputs does MEP need?

---

# Unit 4 — The data

### ☐ Lesson 11. Crash records: counting by who was hurt
- **What:** 602,110 police crash reports, Jan 2019 – Nov 2025.
- **Why:** the source of all crash harm.
- **How:** count killed and seriously injured by **who was hurt**: walking, cycling, motorbike, in a vehicle.
- **Mistake / lesson:** car deaths were first **estimated from Florida's average** — **68% too high**. Counting is better
  than estimating. Motorbikes were missing at first ($8.8B → $10.72B).
- **Result:** in vehicles 1,582 killed; walking 915; motorbike 697; cycling 277.
- **You should be able to answer:** Why is a pedestrian hit by a car counted as a walking casualty?

### ☐ Lesson 12. KSI, and why no minor injuries
- **What:** KABCO injury grades; KSI = killed + seriously injured.
- **Why:** walking and cycling injuries are only recorded at those two levels.
- **How:** price K and A for every mode.
- **Mistake / lesson:** comparing driving's deaths **and** injuries with buses' deaths **only** gave "188 to 1"; like-for-like
  it's **95 to 1**.
- **Result:** crash cost is a **lower limit**.
- **You should be able to answer:** What do K and A mean? Why compare like with like?

### ☐ Lesson 13. Putting a dollar value on harm
- **What:** US DOT values: $13.7M per death, $1,302,300 per serious injury.
- **Why:** MEP measures cost in dollars.
- **How:** per **person**, since we count people.
- **Mistake / lesson:** using the government's **per-crash** values on counts of **people**, with all injury levels, per car-mile
  → **8× too high**. Caught because the Minnesota check failed.
- **Result:** the check now passes.
- **You should be able to answer:** What's the difference between a per-person and a per-crash value?

### ☐ Lesson 14. How much driving: VMT and people per car
- **What:** 102 million vehicle-miles a day in the five counties × 365 × people per car.
- **Why:** crash cost per mile needs miles travelled.
- **How:** people per car measured from the travel survey, **drivers' trips only**.
- **Mistake / lesson:** an **AAA figure ($0.796) that doesn't exist** was used to justify 1.67 — **you caught it**. Then 1.5 was
  worked backwards from MEP's settings — still not measured.
- **Result:** 1.502 people per car; 55.98 billion passenger-miles a year.
- **You should be able to answer:** Why only drivers' trips? What's a passenger-mile?

### ☐ Lesson 15. Walking and biking miles
- **What:** miles one person walks and bikes a year, from NHTS 2022, × population.
- **Why:** no local count of walking or biking exists.
- **How:** survey trip lengths × survey weights ÷ people.
- **Mistake / lesson:** the first numbers were **typed in from a scratch file** — walking **2.8×** and biking **3.5×** too high, with
  percentages adding to 110%. The survey was already downloaded.
- **Result:** walking 49.0, biking 23.7 miles a year (biking rests on **35 trips**).
- **You should be able to answer:** Why is a figure from 35 trips risky?

### ☐ Lesson 16. The bus rate
- **What:** crash cost per bus passenger-mile.
- **Why:** buses are one of MEP's four modes.
- **How:** 12 bus rider deaths nationally in traffic crashes, 2015–2024, ÷ bus miles.
- **Mistake / lesson:** a Tampa-only rate rested on **2 deaths**; national pooling first **mixed in trains and crime** (crime was
  57.8% of rider deaths). Your idea: crime on buses is real harm — left out to compare fairly with cars.
- **Result:** $0.00105 per mile; true value could be about half to 1.7×.
- **You should be able to answer:** Why national? Why leave out crime?

### ☐ Lesson 17. Jobs (LODES) and trip shares (NHTS 2022)
- **What:** jobs by business type as places; how often people make each kind of trip.
- **Why:** MEP's "what can you reach" and "how often do you go".
- **How:** 1,570,813 jobs sorted into six kinds; trip shares from big South Atlantic cities.
- **Mistake / lesson:** you chose **the latest data** (2022, not 2017) — but 2022 has **no Florida field**. Jobs measure **size**,
  not number, of places.
- **Result:** shopping 28.1%, work 20.3%, social 19.5%, restaurants 15.2%, school 13.8%, doctor 3.2%. Check: 2.28
  trips a day matches the published figure.
- **You should be able to answer:** Why use jobs for places? What does the 2.28 check prove?

### ☐ Lesson 18. Population in mid-2022
- **What:** 3,468,871 people, July 2022.
- **Why:** used for cost per person **and** walking/biking miles.
- **How:** the middle of the crash period stands in for the average.
- **Mistake / lesson:** EPA's older count made cost per person **9.3% too high**. And the neighbourhood table totals 3,399,162
  — still unexplained.
- **Result:** $3,092 per person (would be $3,155 on the other figure).
- **You should be able to answer:** Why the middle year, not the newest?

### ☐ Lesson 19. Saved data, live data, mismatched maps
- **What:** most downloads are saved; three aren't (bus miles, bus deaths, neighbourhood points).
- **Why:** a website changing its data can change your answer.
- **How:** save copies; compare results between runs.
- **Mistake / lesson:** **FDOT's road data changed between two runs** (2,429 roads, then 2,427). EPA's data uses **2018**
  boundaries, so only 1,670 of 2,170 match. Documents wrongly said "all data saved".
- **Result:** saved copies; the run stops if results move.
- **You should be able to answer:** Why does saving data matter for defending results?

---

# Unit 5 — The maths of MEP

### ☐ Lesson 20. Crash cost per mile
- **What:** crash cost per year ÷ passenger-miles per year.
- **Why:** the number added into MEP.
- **How:** (killed × $13.7M + injured × $1.3M) ÷ 6.9 years ÷ miles.
- **Mistake / lesson:** biking is high because harm is spread over **far fewer miles** (the restaurant-bill example).
- **Result:** car $0.1059; bike $9.59–11.79; walk $11.57–12.49; bus $0.00105.
- **You should be able to answer:** Work out the car figure from the numbers.

### ☐ Lesson 21. The Minnesota check
- **What:** compare our car crash cost with Cui & Levinson's Minneapolis figure.
- **Why:** proves our number isn't crazy.
- **How:** convert per person to per car (× 1.502), per km to per mile (× 1.609), 2010 to 2024 dollars (× 1.50).
- **Mistake / lesson:** the first version compared **per-person-miles** with **per-car-miles** — the unit mistake was **inside the test
  built to catch unit mistakes**. The pass band was 0.5–4.0×, so wide it couldn't fail.
- **Result:** 1.65×, inside the tightened band of 1.2–3.0×.
- **You should be able to answer:** Why should Florida's number be higher than Minnesota's?

### ☐ Lesson 22. Scaling numbers, and the 11× mistake
- **What:** scaling so common kinds of places (all jobs) don't swamp rare ones (arts).
- **Why:** unscaled, work would be 98% of every score.
- **How:** US restaurant jobs ÷ US jobs of that kind.
- **Mistake / lesson:** first used **Tampa's own totals** (arts weight 52); then **"work" as the reference** instead of restaurants —
  **every score 11× too big** (91,094 instead of 8,241). Percentages were fine, which is why it hid.
- **Result:** restaurants 1, arts 5.02, work 0.09.
- **You should be able to answer:** Why national totals? Why did the 11× mistake hide?

### ☐ Lesson 23. Travel times by car, walking and bike
- **What:** quickest route from each of 2,170 neighbourhoods to every other.
- **Why:** MEP needs what you can reach in 10, 20, 30, 40 minutes.
- **How:** OpenStreetMap network (827,133 junctions), Dijkstra's method, stop at 40 minutes, speed limits (no traffic).
- **Mistake / lesson:** travel time **inside your own neighbourhood was zero** — big rural areas reached everything instantly; 319 are
  too big to walk across in 10 minutes. First map download had only 31 of 88 pieces.
- **Result:** typical neighbourhood reaches 1,444 by car, 114 by bike, 9 on foot.
- **You should be able to answer:** Why isn't time inside your own area zero?

### ☐ Lesson 24. Bus travel times (RAPTOR)
- **What:** real journeys on HART and PSTA timetables.
- **Why:** buses only run at certain times.
- **How:** rounds: one bus, one change, two changes; Thursday; 7:45, 8:00, 8:15; walk up to 10 minutes.
- **Mistake / lesson:** **Friday would drop every PSTA bus**; some "bus trips" were **only walking** until the "you boarded" check.
  98.6% of the 10-minute bus band is still neighbourhoods counting themselves.
- **Result:** 6,232 stops, 4,308 trips.
- **You should be able to answer:** Why Thursday? What did the "boarded" check fix?

### ☐ Lesson 25. The penalty and the "keep" share
- **What:** penalty = −0.5 × energy − 0.08 × minutes − 0.5 × (money + crash cost); keep = e^penalty.
- **Why:** turns time, money and energy into how much each place still counts.
- **How:** each extra $1 per mile keeps about 61% of what's left.
- **Mistake / lesson:** a worry (29 Aug) that our formula wasn't NREL's — checked: it matches.
- **Result:** car keeps 95% after crash cost; bike keeps 0.8%.
- **You should be able to answer:** Why does $10 a mile almost wipe out biking?

### ☐ Lesson 26. The score, and combining neighbourhoods
- **What:** places newly reached in each band × keep, added up; then a population-weighted average.
- **Why:** count each place once; people-heavy places count more.
- **How:** band differences (100, 250 → 150 newly reached).
- **Mistake / lesson:** the headline first used a **plain average**; MEP's rule is **population-weighted**.
- **Result:** 7,567 → 5,796, a 23.4% drop.
- **You should be able to answer:** Why count a place only once? Why weight by population?

---

# Unit 6 — Road danger

### ☐ Lesson 27. Raw rates and regression to the mean
- **What:** casualties ÷ traffic on each of 2,848 state roads.
- **Why:** to make driving danger vary by neighbourhood (fixing the fake map).
- **How:** traffic = vehicles a day × length × 365 × 6.9.
- **Mistake / lesson:** a quiet road with one unlucky crash gets a huge rate — bad luck looks like danger.
- **Result:** 547,205 crashes placed on roads (95.7% of deaths).
- **You should be able to answer:** What is regression to the mean?

### ☐ Lesson 28. The safety curve
- **What:** a formula for a **typical** road's casualties from traffic and length.
- **Why:** tells you what "normal" is.
- **How:** negative binomial model; doubling traffic multiplies casualties by 2^b.
- **Mistake / lesson:** crash counts spread **23×** more than a simple (Poisson) model expects.
- **Result:** b = 0.789 (standard error 0.022).
- **You should be able to answer:** What does b = 0.8 mean in plain words?

### ☐ Lesson 29. The curve fitted on the wrong roads
- **What:** the curve was fitted only on roads that **had** a crash.
- **Why:** 47% of roads had none — and they're the quiet ones.
- **How:** refit on all 2,848.
- **Mistake / lesson:** "selecting on the outcome" — like studying car safety only by asking people who crashed.
- **Result:** b moved from 0.730 to 0.789, as theory predicts.
- **You should be able to answer:** Why are roads with zero crashes evidence?

### ☐ Lesson 30. The blend (Empirical Bayes) and the death share
- **What:** mix prediction with each road's history.
- **Why:** fixes bad luck.
- **How:** w = 1 ÷ (1 + k × expected); blended = w × expected + (1 − w) × actual. Death share pulled toward 9.5%.
- **Mistake / lesson:** **51 roads looked "100% deadly"** from one or two casualties.
- **Result:** 13 of the 25 "worst" roads were luck.
- **You should be able to answer:** Work out the blend for a quiet road (expected 1, actual 3, k = 1).

### ☐ Lesson 31. Road types, standard errors, AIC
- **What:** separate curves for collectors, minor arterials, principal arterials, freeways.
- **Why:** a freeway and a small road aren't equally dangerous.
- **How:** road type from the nearest OpenStreetMap road (FDOT's file has none).
- **Mistake / lesson:** is extra complexity worth it? AIC says yes.
- **Result:** AIC 10,765 → 10,694; b from 0.628 (collectors) to 0.828 (freeways).
- **You should be able to answer:** What does a standard error tell you? What does AIC compare?

### ☐ Lesson 32. Neighbourhood driving danger: 1.3%, then 7.0% with real routes
- **What:** a weighted average of nearby roads' danger, by traffic and closeness.
- **Why:** gives each neighbourhood its own car crash cost.
- **How:** weight = traffic × e^(−0.08 × minutes).
- **Mistake / lesson:** the nearby-roads version explained **1.3%** of the map, 77% of it just county. Following each trip's real route (step 40) raised it to **7.0%**, mostly within counties.
- **Result:** $0.08 to $0.40 a mile; Hernando $0.17, Hillsborough $0.09.
- **You should be able to answer:** Why did following real routes raise 1.3% to 7.0%?

### ☐ Lesson 33. Walking and biking danger by place — a negative result
- **What:** tried to make walking and biking danger vary by neighbourhood.
- **Why:** they cause 84% of the drop.
- **How:** placed casualties by coordinates; tried six predictors.
- **Mistake / lesson:** zeros were **rounded to tiny numbers**, hiding the effect; and in the end the signal was too weak. **A negative result is still
  a result.**
- **Result:** nearby car traffic predicted walking casualties best, but weakly; not used.
- **You should be able to answer:** Why not use a weak signal anyway?

---

# Unit 7 — The results

### ☐ Lesson 34. The headline, counties and neighbourhoods
- **What:** 23.4% drop; counties 19.1% (Pasco) to 29.0% (Citrus); best neighbourhood −43%.
- **Why:** the main finding.
- **How:** population-weighted; compare percentages only.
- **Mistake / lesson:** raw scores can't be compared with other cities (NREL: 11,983 vs 122.35 for one region).
- **Result:** rankings barely change (0.989).
- **You should be able to answer:** Why does Pasco drop least?

### ☐ Lesson 35. Why the drop is mostly cycling
- **What:** cycling is 18% of the score but about 79% of the drop.
- **Why:** MEP treats biking as free; its crash cost is ~$10 a mile.
- **How:** the 100-point neighbourhood example.
- **Mistake / lesson:** the result is mostly cycling being **switched off**, not a smooth penalty.
- **Result:** bike 76.8%, car 18.2%, walk 5.0% of the drop.
- **You should be able to answer:** Explain the 100-point example.

### ☐ Lesson 36. Who is hit hardest
- **What:** neighbourhoods with more carless households lose more (21.2% → 26.2%).
- **Why:** people with fewer choices depend on the modes MEP overstates.
- **How:** five groups; rank correlation +0.27.
- **Mistake / lesson:** the table once said "steadily rising" when it wasn't; and **correlation isn't causation**.
- **Result:** a moderate link.
- **You should be able to answer:** What else could explain the link?

### ☐ Lesson 37. Who pays when a car hits someone — and the 93%
- **What:** charge harm to the person hit (what we use) or to the driver.
- **Why:** it changes the answer.
- **How:** car crash cost $0.1059 vs $0.1573; difference $0.0514 a mile, $2.88B a year.
- **Mistake / lesson:** interview notes claimed **"93%"** and "I ran it both ways" — neither was true of the live project; 93% came from a
  number typed into an old script. Measured properly: **99.0%**. The checker now reads the documents you speak from.
- **Result:** both ways reported.
- **You should be able to answer:** Why do we charge the person hit?

### ☐ Lesson 38. One year of traffic, and 2020
- **What:** 7 years of crashes divided by 2025 traffic.
- **Why:** traffic changed over the years.
- **How:** true rate ÷ our rate = (2025 traffic × 6.9) ÷ each year's traffic added up.
- **Mistake / lesson:** leave it uncorrected on purpose — conservative.
- **Result:** our rates are 8–12% too low. 2020: 21% fewer crashes but 5% more deaths.
- **You should be able to answer:** Why does a bigger bottom number make a rate smaller?

### ☐ Lesson 39. The prediction test
- **What:** fit on 2019–22, predict 2023–25.
- **Why:** a model always looks good on its own data.
- **How:** compare error and hotspot-finding; 2,000 bootstrap reshuffles.
- **Mistake / lesson:** the summary said **"6 of 6 passed"** — 3 are within noise.
- **Result:** the blend has the smallest error (real); ties past counts at finding the worst roads.
- **You should be able to answer:** What is a bootstrap for?

---

# Unit 8 — The honest problems

### ☐ Lesson 40. MEP counts what you *could* reach, not what people do
- **What:** you said it: Florida drives.
- **Why:** cycling 17.7% of MEP's score vs 1.8% of real trips (0.5% of commutes).
- **How:** compare MEP's split with the survey and Census.
- **Mistake / lesson:** most of the drop removes cycling people mostly don't do.
- **Result:** a rough real-travel version: ~13% instead of 23% (not built properly).
- **You should be able to answer:** What's the difference between opportunity and behaviour?

### ☐ Lesson 41. Checking the cycling data
- **What:** why people bike here, and when cyclists are hurt.
- **Why:** you suspected biking here is mostly exercise.
- **How:** survey trip purposes; crash timing; compare bike network with NREL's.
- **Mistake / lesson:** survey labels were read wrong at first; crash dates didn't parse at first.
- **Result:** 68.7% of bike trips here are exercise/recreation, none to work; but **42% of cyclists killed died at night**; our bike
  network matches NREL's basic setup.
- **You should be able to answer:** Why do the two findings point different ways?

### ☐ Lesson 42. Weak points, left out, and differences from standard MEP
- **What:** everything we can't claim, left out, or did differently.
- **Why:** say it before interviewers do.
- **How:** see `WHAT_I_DID.md` Parts 7, 10, 11 and `HOW_IT_RUNS_VS_STANDARD_MEP.md`.
- **Mistake / lesson:** Uber/Lyft left out with no written reason; no traffic jams; bus rate national.
- **Result:** a clear list of weak points and what to say.
- **You should be able to answer:** Name three things we do differently from standard MEP, and why.

---

# Unit 9 — Keeping it correct

### ☐ Lesson 43. The crash-delay term saga
- **What:** extra minutes for crash-caused traffic jams (your idea: delay affects everyone).
- **Why:** crashes cost time too.
- **How:** tried 55%, 25%, 12.5%, then 13–30% of jam time from road-sensor research.
- **Mistake / lesson:** 55% included all delays; person-hours ÷ car-miles made it 1.67× too big; the final minutes were **typed in by hand**.
  **If you can't rebuild a number, you can't defend it.**
- **Result:** deleted; headline 24.9% → 22.5%.
- **You should be able to answer:** Why is deleting it a strength in an interview?

### ☐ Lesson 44. When the checker was broken
- **What:** a program that checks document numbers against the data.
- **Why:** numbers drifted from the results.
- **How:** each number must sit next to its label; whole numbers matched.
- **Mistake / lesson:** it passed a number that wasn't there; couldn't tell 24% from 124%; its self-test tested nothing; it only
  checked the report. **A broken checker is worse than none.**
- **Result:** checks 29 report figures and 10 documents.
- **You should be able to answer:** Why must a check be shown to fail?

### ☐ Lesson 45. Steps missing from the run list
- **What:** steps 05, 33 and 01 weren't in the run list.
- **Why:** each was the only maker of a file another step needed.
- **How:** old copies sat on the computer, so nothing crashed.
- **Mistake / lesson:** the same bug **three times**; reading scripts' descriptions to detect it was rejected because a description was
  itself wrong. **Check what actually happened, not what the docs say.**
- **Result:** the run lists every file it didn't rebuild.
- **You should be able to answer:** Why didn't anything crash?

### ☐ Lesson 46. The audits
- **What:** two independent checks that recalculated every number.
- **Why:** you can't see your own blind spots.
- **How:** audit 2 (8 Sep) and audit 3 (9 Sep).
- **Mistake / lesson:** audit 2 found 6 problems, audit 3 found 11 — all real. The audits also got things wrong (601 vs 319; a spread
  prediction). Credit: audit 3 found the delay term and the unused benchmark before "I" did.
- **Result:** every must-fix item closed; some smaller ones open.
- **You should be able to answer:** Name two problems audits found that tests couldn't.

### ☐ Lesson 47. Tests that must fail
- **What:** 20 tests, each built around a past mistake.
- **Why:** so mistakes can't come back.
- **How:** feed the test a known-wrong case and confirm it fails.
- **Mistake / lesson:** two tests only scanned **9 of 27 steps**; one checked a setting name that doesn't exist. Fixed and proven on a
  planted mistake.
- **Result:** 20 tests pass.
- **You should be able to answer:** Why feed a test something wrong on purpose?

---

# Unit 10 — Tools, writing, interview

### ☐ Lesson 48. How the pipeline runs
- **What:** 26 Python steps, one command, about 30 minutes.
- **Why:** small checkable pieces; repeatable.
- **How:** `python src/run_all.py`; numpy, pandas, scipy, pyarrow; CSV, parquet, npy files.
- **Mistake / lesson:** order matters — a step must run after the steps whose files it reads.
- **Result:** identical numbers on every full run since the fixes.
- **You should be able to answer:** What happens if a step fails?

### ☐ Lesson 49. Git, GitHub and data safety
- **What:** version control; private repo.
- **Why:** history, backup, and a way to show the work.
- **How:** commit, push; allow-list `.gitignore` (only `.py` and `.md`).
- **Mistake / lesson:** the folder held files built from licensed crash records; a pre-push scan found no vehicle IDs or ages.
- **Result:** `yrasool/i4-safety`, private, credited to you.
- **You should be able to answer:** Why an allow-list instead of a block-list?

### ☐ Lesson 50. Writing about the project
- **What:** resume bullets, cover letters, emails.
- **Why:** readers skim; academics trust specifics and self-correction.
- **How:** short, result-first, name MEP; human voice, no em dashes; don't overclaim ArcGIS.
- **Mistake / lesson:** the August bullets use **outdated numbers** (10.5%, 48×, 2,098).
- **Result:** new bullet still to write.
- **You should be able to answer:** Which numbers in the old bullet are wrong now?

### ☐ Lesson 51. The interview
- **What:** a 20-minute presentation and ~40 minutes of questions from people who built MEP.
- **Why:** the goal of the whole project.
- **How:** `PRESENTATION.md`, `INTERVIEW_QA.md`, practice grilling in the chat.
- **Mistake / lesson:** say the weak points first: cycling "switched off", potential vs real travel, 7.0% local, who pays.
- **Result:** ready once you can answer every lesson's questions out loud.
- **You should be able to answer:** Give the 30-second answer to "Is this really MEP?"
