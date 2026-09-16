# Tampa Bay MEP with crash harm

NREL's **Mobility Energy Productivity (MEP)** score measures how many useful places people can reach
from where they live, charging each way of travelling for its energy, time and money. It charges
**nothing** for the people it kills.

This project calculates MEP from scratch for Florida DOT District 7 — Hillsborough, Pinellas, Pasco,
Hernando and Citrus counties, 2,170 Census block groups — and adds the one missing cost: **crash death
and serious injury**, priced per passenger-mile.

**Result: counting crash harm removes 16.2% of the region's MEP score.**

That is with driving danger summed along the real route to each destination, bikes limited to roads
people would actually ride, and walks capped at 20 minutes. With bikes allowed on any road, as standard
MEP assumes, it is 23.0%.

---

## Folders

```
README.md       this page
REPORT.md       the technical report
interview/      what to say: presentation script and 31 interview questions
docs/           how it works: every calculation, dataset, choice and correction
learn/          the project taught from zero: concepts and a 51-lesson study plan
notes/          the project's memory: ideas, decisions, rules, timeline, to-do
src/            the pipeline: numbered steps run in order by run_all.py
tests/          tests that fail if a known past mistake comes back
data/           downloads and results (not committed — see data/README.md)
archive/        superseded code, kept for history, not run
```

---

## Where to start

| if you want | read |
|---|---|
| **to prepare for the interview** | [`interview/INTERVIEW_QA.md`](interview/INTERVIEW_QA.md), [`interview/PRESENTATION.md`](interview/PRESENTATION.md) |
| the whole story, from zero | [`docs/WHAT_I_DID.md`](docs/WHAT_I_DID.md) |
| what MEP is | [`docs/MEP.md`](docs/MEP.md) |
| every calculation, with worked examples | [`docs/MATH.md`](docs/MATH.md) |
| every data source | [`docs/DATA.md`](docs/DATA.md) |
| every choice and assumption | [`docs/ASSUMPTIONS_AND_CHOICES.md`](docs/ASSUMPTIONS_AND_CHOICES.md) |
| how it differs from standard MEP | [`docs/HOW_IT_RUNS_VS_STANDARD_MEP.md`](docs/HOW_IT_RUNS_VS_STANDARD_MEP.md) |
| every mistake found and fixed (71) | [`docs/CORRECTIONS.md`](docs/CORRECTIONS.md) |
| every concept, taught from zero | [`learn/LEARN.md`](learn/LEARN.md) |
| a lesson-by-lesson study plan | [`learn/STUDY_PLAN.md`](learn/STUDY_PLAN.md) |
| ideas, decisions, rules, timeline, to-do | [`notes/`](notes/README.md) |

---

## The code worth reading

34 steps run in the pipeline. You do not need all of them. These are the ones that carry the result,
in the order the data flows:

| step | file | what it does |
|---|---|---|
| settings | `src/constants.py` | **every fixed number in one place** — dollar values, MEP weights, which road network each mode uses, the 20-minute walk cap |
| crashes | `src/02_crashes_by_mode.py` | counts people killed and seriously injured, by who was hurt |
| crash cost | `src/04_injury_cost.py` | turns casualties into dollars per passenger-mile per mode |
| road safety | `src/29_spf_eb.py`, `src/33_spf_stratified.py` | the safety curve and Empirical Bayes, road by road |
| routes | `src/40_route_assignment.py` | sums road danger along the real route to 2.8 million destinations |
| bike and walk networks | `src/42_bike_lts.py` | builds the low-stress networks people would actually use |
| travel times | `src/21_isochrones.py`, `src/22_transit.py` | how long it takes to reach everywhere, by car, bike, foot, bus |
| **MEP** | **`src/23_mep.py`** | **the three MEP equations, with crash cost added** |
| checks | `src/26_validate.py`, `src/28_check_report.py` | proves the result, and checks every number in the documents against the data |

**If you read only two:** `src/constants.py` and `src/23_mep.py`.

Every step opens with a comment block saying **why it exists** and **what went wrong before it**.

---

## Trying other versions

Every alternative is one setting, and none of them overwrite the real results:

```bash
MEP_BIKE_NETWORK=any python src/23_mep.py     # bikes on any road (standard MEP) -> 23.0%
MEP_BIKE_NETWORK=lts python src/23_mep.py     # strictly low-stress bikes        -> 10.9%
MEP_CONVENTION=B python src/23_mep.py         # harm charged to the car          ->  8.2%
MEP_DRIVE_RISK=proximity python src/23_mep.py # nearby roads instead of routes
MEP_WALK_MAX_MIN=40 python src/23_mep.py      # walks up to 40 minutes
```

---

## What is in this repository — and what is not

**In:** the pipeline code (`src/`), the tests (`tests/`), and the documents.

**Not in:** any data.

- **The crash records are licensed** (Signal Four Analytics) and must not be shared. They are kept
  outside this folder, and nothing built from individual crash records is committed.
- **Public downloads** (OpenStreetMap, Census LODES and ACS, NHTS 2022, HART and PSTA timetables, FDOT,
  FHWA, EPA) are not committed because of their size. See [`data/README.md`](data/README.md).

The repository uses an **allow-list** `.gitignore`: only `.py` and `.md` files can be committed, so a
data file cannot be added by accident.

---

## How to run it

```bash
python src/run_all.py          # all 34 steps, about two hours
python src/28_check_report.py  # check every number in the documents against the data
python -m pytest tests -q      # 20 tests
```

**Needs:** Python 3.12; `pip install numpy scipy pandas pyarrow xlrd openpyxl pytest`; and a copy of the
**Signal Four crash extract** at the path set in `src/constants.py`.

---

*Private project. Built for study and interview preparation.*
