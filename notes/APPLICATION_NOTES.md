# Application notes — resume, letters, interview

Notes on how this project is presented in applications.

> ⚠️ **Outdated numbers warning.** The resume bullets below were written in **August**, on the first
> version of the project. **Several numbers have since changed.** Before using any of them, update them
> from `WHAT_I_DID.md` (the table at the bottom shows what changed).

*Contact names and emails from outreach aren't stored here, on purpose.*

---

## 1. Who the project is for

- **The role:** NREL's Center for Integrated Mobility Sciences — graduate / year-round intern work on
  mobility data, travel surveys, transit data (GTFS), accessibility and energy. NREL was renamed in job
  postings as "NLR".
- **What they build:** MEP (Mobility Energy Productivity), the South Florida MEP study with FIU, Level of
  Traffic Stress (2023), the Walking Comfort Index (2025).
- **Why this project fits:** it rebuilds their own metric from scratch on real data, adds something they
  don't price (observed crash harm, in dollars), and checks everything against their published tests.

---

## 2. Resume bullets — history

### Version you settled on (16 August) — ⚠️ outdated numbers
> Extended NREL's Mobility Energy Productivity metric with a collision-cost term absent from its published
> formulation, processing 602,110 Florida crash records across 2,098 census block groups to quantify a
> systematic bias toward driving worth 10.5% of the metric's existing driving charge against 0.12% for
> transit; identified 25% of the region's car-free households as having no transit access to employment,
> and validated both modal rates against published studies, reproducing benchmark bus fatality rates
> within 10%.

### What your feedback on the bullets was
- Too long: "no one will read this long".
- Needs a **result**.
- Not too technical, but **name MEP**.
- Should be proper **resume style**; two or three bullets, short.

### Project heading drafted
- *Interstate Corridor Crash Data Analysis* | Python, pandas, Geospatial Analysis, OpenStreetMap, Data Quality
  (for the earlier I-4 work)
- *The Cost of Access — Tampa Bay* | Python, pandas, EPA / NTD / Census APIs (for version 1 of this project)

### What changed since those bullets

| in the August bullets | now |
|---|---|
| 2,098 block groups (EPA's 2018 areas) | **2,170** neighbourhoods (2020 areas) |
| EPA's accessibility data | **our own MEP calculation**: OpenStreetMap, LODES, NHTS 2022, bus timetables |
| deaths only ("collision-fatality term") | **deaths and serious injuries** |
| 10.5% of driving's cost vs 0.12% for transit | **22.1%** of driving's cost (deaths + injuries); deaths-only like-for-like: **11.7% vs 0.12%, about 95 to 1** |
| 48× car vs bus fatality cost | **53.6×** on current inputs |
| a quarter of car-free households with no transit access to jobs | not recalculated on the new build — **don't quote** without checking |
| no headline MEP result | **pricing crash harm removes 22.5% of Tampa Bay's MEP score** |

**Still to do:** write a new bullet from the current numbers (`TODO.md` #1).

---

## 3. Cover letter rules (from your feedback)

- **Sound human**, not perfect English — no AI slop, **no em dashes**, no "this / that" academic filler.
- **Show passion through specifics** — what you found and what you got wrong — not by saying you're passionate.
- **Mention the errors you caught**: academic readers trust self-correction.
- **Don't overclaim**: you've used ArcGIS but don't claim fluency.
- **Include relevant experience**: Nucor (data internship), TKAI Lab research, physics interest where relevant.
- The telecom/infrastructure internship was **Sanguine Info Tech**, never "Jio".

---

## 4. Interview preparation

- **Format:** a 20-minute presentation and about 40 minutes of technical questions from people who built MEP.
- **Documents:** `PRESENTATION.md` (outline), `INTERVIEW_QA.md` (17 questions with plain answers),
  `WHAT_I_DID.md` Part 10 (weak points and what to say).
- **The questions most likely to hurt, and the short answers:**

| question | short answer |
|---|---|
| "Is this really MEP?" | Same equations, defaults, weights, bands, scaling reference and population weighting; passes Hou et al.'s own tests. Only the data sources differ, and one change: crash cost added to money cost |
| "Your raw score is nothing like ours." | Raw scores depend on how places are counted — your South Florida study got 11,983 and 122.35 for one region. I compare percentages only |
| "Isn't most of your drop just cycling?" | Yes — cycling is 18% of the score and about 79% of the drop. MEP counts potential access; here cycling is under 2% of real trips, so weighted by real travel it'd be roughly half. But 42% of cyclists killed died at night, which suggests they're riding to get somewhere |
| "Who pays when a car hits a pedestrian?" | I charge the person hit, like every MEP cost; charged to the driver instead, driving's crash cost goes from $0.1059 to $0.1573 a mile. It's a choice, and I show both |
| "Is your map a crash-risk map?" | No — only 1.3% of neighbourhood differences come from local danger |
| "What did you get wrong?" | Plenty, openly — see `CORRECTIONS.md`: the 11× reference-place error, the fake map, the delay term I deleted |
