# To do — everything not done yet

One list, most important first. When something is done, move it to `IDEAS.md` as ✅ and add a
line to `CORRECTIONS.md` if it fixed a mistake.

---

## 1. Before the interview (most important)

| # | task | why | size |
|---:|---|---|---|
| 1 | **Update the resume line** with current numbers | the drafted bullets use outdated figures (10.5%, 48×, 2,098 neighbourhoods) | small |
| 2 | **Turn the presentation into real slides** | `PRESENTATION.md` is a text outline | medium |
| 3 | **Make charts and maps** (at least: the drop by county, the drop by mode, a neighbourhood map) | a map project with no map | medium |
| 4 | **Build a version weighted by how people actually travel** | cycling is 17.7% of MEP's score but 1.8% of real trips; rough estimate ~13% vs 23% | medium |
| 5 | **Test how the answer changes with MEP's cost weight**, or give crash cost its own weight | the biggest untested choice | medium |

## 2. Fix the known small issues

| # | task | why | size |
|---:|---|---|---|
| 6 | **Save copies of the three downloads** that happen every run (steps 03, 05, 18) | a website change could shift a rerun | small |
| 7 | **Put the prediction test (step 36) in the run list and the report**, and fix its "6 of 6" summary | 3 of 6 are within noise | small |
| 8 | **Fix step 26's self-check** so it can actually fail | it compares a formula with itself | small |
| 9 | **Explain the population gap** (3,468,871 vs 3,399,162; $3,092 vs $3,155 per person) | unexplained | small |
| 10 | **Fix step 23's description** (names `mep_summary.csv`, which it doesn't make) | wrong description | tiny |
| 11 | **Move old scripts** (06–08, 10–15) to `archive/` | could be mistaken for current code | tiny |
| 12 | **Say in the report** that state roads carry 78.5% of driving | missing disclosure | tiny |
| 13 | **Explain the 1,670 EPA match** in the report | only in the code | tiny |

## 3. Improve the method

| # | task | why | size |
|---:|---|---|---|
| 14 | Try **bikes only on safer roads** | bikes can currently "use" 55 mph main roads | medium |
| 15 | Add **Uber/Lyft** as a mode | in MEP's default table; 1.0% of trips here | medium |
| 16 | **Heat and humidity** for walking and biking (your idea) | Florida's heat affects walking and biking | large |
| 17 | **EV scenario** (30% / 50% electric cars) | proposed in August | small |
| 18 | **Uncertainty ranges on trip shares** | doctor trips rest on 68 surveyed trips | medium |
| 19 | **People per car by vehicle type** (trucks) | car crash cost slightly too low | medium |
| 20 | **Proper bus-time averaging** (count missed departures) | currently generous to buses | small |
| 21 | **A stricter Minnesota check** (all injury levels) | a rough guess put it near the pass limit | medium |
| 22 | **Widen the run-twice check** beyond four numbers | thin check | small |
| 23 | **Review the bus-routing (RAPTOR) code line by line** | only its outputs were audited | medium |
| 24 | **A formal Poisson vs negative binomial test** | only the variance ratio is reported | small |
| 25 | **Local and county roads** in the safety model | no traffic counts; would need another source | large |
| 26 | **Congested travel times** | no free source | large |

## 4. Reserved for you

| # | task |
|---:|---|
| 27 | The `TODO(human)` in `src/10_screen_segments.py`: decide which road segments count as high-risk |
