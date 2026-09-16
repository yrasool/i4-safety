# Timeline — the whole story

From the first crash map in August to the GitHub repo in September.

*Dates come from the session log (UTC), so evening work in Tampa can show as the next day.*

---

## Phase 1 — The I-4 corridor crash study (5 August)

**Starting point:** a folder of an existing FDOT I-4 safety analysis (Python notebooks, a crash
CSV, reports), in the read-only `Yusra` folder.

- You wanted to understand the existing code and see the crashes on a map.
- Built an **HTML crash map** with zoom, showing crashes near intersections (250 ft rings).
- Studied the **ramp classifier**: it could only identify ramp crashes where the location and the
  police report agreed; 29 ramp crashes.
- Found the **"stacked crashes"** problem: many crashes recorded at exactly the same point.
- Built a **static exhibit** of crash concentration by milepost (MP 24.1), with cleaned counts so a
  false hotspot (MP 21.8) wasn't shown.
- Looked at eastbound vs westbound crashes.

## Phase 2 — A portfolio project for traffic analyst roles (6–12 August)

- You wanted a **really good project** for traffic analyst jobs, not a redo.
- **Licence issue:** Signal Four data can't be published on a website.
- City choice between Tampa Bay, Pittsburgh/Allegheny County (open data) and Baltimore → a
  **high-risk roads** project.
- Built **road-risk** screening on open Allegheny County data (critical crash rate, Empirical Bayes).
  Ranking by crash count and by rate gave top-25 lists sharing just one road.
- Map design feedback: clicking a road gave too little; no paragraphs or lists; wanted risk roads, not
  intersections.
- Built a **3D map** (three.js) of I-4 with mainline, ramp and intersection crashes in separate
  colours; tried many styles; settled toward **satellite / Google Maps style**.

## Phase 3 — The NREL idea (15–18 August)

- **The job:** NREL's Center for Integrated Mobility Sciences (the posting says "NLR").
- Decided **Tampa MEP as the spine**.
- Checked licence: **private build, resume mention only, no website**.
- **Version 1** of the project: EPA's "jobs within 45 minutes" + a crash-injury term per mode, bus
  rate from NTD, car rate checked against Cui & Levinson (Minnesota) and bus rate against Savage.
- Heavy reviews; tests that check failures (15 tests).
- First findings (later changed): crash cost 10.5% of driving's cost, 48× car vs bus, a quarter of
  carless households with no bus access to jobs.
- Resume bullets and outreach emails drafted; cover letters (see `APPLICATION_NOTES.md`).
- A separate study session on an industrial fuel-optimisation project.

## Phase 4 — Interview preparation (29 August)

- Wanted the most detailed version of the project.
- Prepared for grilling by the NREL team, based on their published work.
- **A worry:** was our formula really MEP's? (Resolved later: it matches NREL's equations.)

## Phase 5 — Reading, and a rethink (7 September)

- Reading plan from *Data Science from Scratch*.
- Looked at NREL's own safety work: **Level of Traffic Stress** (2023) and the **Walking Comfort Index**
  (2025) — both based on road design, not on actual crashes or their cost.
- Decided to use the **full crash file** and **FDOT road data** to find dangerous roads.
- Focused on **the five counties**.
- Your ideas: a **time penalty** (crash delay affects everyone), a **money penalty** (lives and injuries),
  Uber/Lyft vs buses, heat and walkability.
- An early run found problems: the made-up AAA figure, missing motorbikes, a national delay figure.

## Phase 6 — Building MEP for real (7–8 September)

- Admitted the project **hadn't actually built MEP**. You said "do it".
- Built everything from scratch: **LODES** destinations, **NHTS 2022** trip shares, starting points,
  the **OpenStreetMap** network, travel times by car/walk/**bike**, and **bus routing** on HART/PSTA
  timetables.
- Fixed from NREL's South Florida report: national scaling, bus cost 0.85, measured occupancy 1.502.
- **Audit 2** (8 Sep): 6 real problems — made-up walking/biking miles, a test that couldn't fail, 188:1
  really 95:1, a checker false pass, bus reach, zero travel time inside neighbourhoods. All fixed.
- Built the **road-by-road safety model** (safety curve + Empirical Bayes).

## Phase 7 — Checking against NREL, and the deep audit (9 September)

- Confirmed the data had gone through MEP.
- Found NREL's own team hit the same score-size issue (11,983 vs 122.35).
- Passed **NREL's own tests**.
- The **run-twice check** caught FDOT's live data changing; saved a copy.
- **Audit 3** (9 Sep): 11 real problems — the biggest: "work" instead of "meals" (11× scores). All fixed.
- Refitted the safety curve on all roads; smoothed death shares; population weighting.
- Wrote the **interview Q&A**, **reading guide** and **learning resources**.

## Phase 8 — Holes and fixes (10 September)

- Wrote the **presentation outline**.
- Tried walking/biking danger by place (didn't work); road types (worked).
- **Deleted the delay term** → headline **22.5%**.
- **16 Sep: driving danger follows real routes** (step 40) → headline **23.4%**; local danger 1.3% → 7.0% of the map.
- Traffic-by-year check; **who pays** when a car hits someone (93% → 99.0%).
- Checker now reads the spoken documents; motorbikes and the national bus rate disclosed.
- Found **three steps missing** from the run list; fixed; added the stale-file list.
- Full run: identical numbers.
- Started the **build log**.

## Phase 9 — Evaluation (11 September)

- Built the **prediction test**: fit 2019–22, predict 2023–25, with resampling.

## Phase 10 — Understanding and documenting (14 September)

- Confirmed every neighbourhood has a real MEP score; explained where the drop comes from.
- **Your key point:** Tampa Bay drives; MEP counts what people *could* reach, not what they do.
- Checked the **cycling data**: mostly exercise trips, but many night-time deaths.
- Rewrote `WHAT_I_DID.md` in simple language, several times.
- Wrote **`MEP.md`**, **`MATH.md`**, **`DATA.md`**, **`ASSUMPTIONS_AND_CHOICES.md`**,
  **`HOW_IT_RUNS_VS_STANDARD_MEP.md`**, **`CORRECTIONS.md`**, **`data/README.md`**.
- Fixed the two tests that only scanned 9 steps.
- Created the **private GitHub repo** `yrasool/i4-safety`.
- Wrote these **notes** and **`LEARN.md`**.
