# Tampa Bay MEP with crash harm

NREL's **Mobility Energy Productivity (MEP)** score measures how many useful places people
can reach from where they live, charging each way of travelling for its energy, time and
money. It charges **nothing** for the people it kills.

This project calculates MEP from scratch for Florida DOT District 7 — Hillsborough, Pinellas,
Pasco, Hernando and Citrus counties, 2,170 Census block groups — and adds the one missing
cost: **crash death and serious injury**, priced per passenger-mile.

**Result: counting crash harm removes 22.5% of the region's MEP score**, mostly because MEP
treats cycling as free while it is very dangerous per mile here.

---

## Where to start

| if you want | read |
|---|---|
| the whole story, from zero | [`WHAT_I_DID.md`](WHAT_I_DID.md) |
| what MEP is | [`MEP.md`](MEP.md) |
| every calculation, with worked examples | [`MATH.md`](MATH.md) |
| every data source | [`DATA.md`](DATA.md) |
| every choice and assumption | [`ASSUMPTIONS_AND_CHOICES.md`](ASSUMPTIONS_AND_CHOICES.md) |
| how it runs, and how it compares with standard MEP | [`HOW_IT_RUNS_VS_STANDARD_MEP.md`](HOW_IT_RUNS_VS_STANDARD_MEP.md) |
| every correction made | [`CORRECTIONS.md`](CORRECTIONS.md) |
| the technical report | [`REPORT.md`](REPORT.md) |

---

## What is in this repository — and what is not

**In:** the pipeline code (`src/`), the tests (`tests/`), and the documents.

**Not in:** any data. Specifically:

- **The crash records are licensed** (Signal Four Analytics) and must not be shared. They are
  kept outside this folder, and nothing built from individual crash records is committed.
- **Public downloads** (OpenStreetMap, Census LODES and ACS, NHTS 2022, HART and PSTA
  timetables, FDOT, FHWA, EPA) are not committed because of their size. Most steps download
  them automatically on first run. See [`data/README.md`](data/README.md).

The repository uses an **allow-list** `.gitignore`: only `.py` and `.md` files can be committed,
so a data file cannot be added by accident.

---

## How to run it

```bash
python src/run_all.py          # all 26 steps, about 30 minutes
python src/28_check_report.py  # check every number in the documents against the data
python -m pytest tests -q      # 20 tests
```

**Needs:**
- **Python 3.12**
- the libraries: `pip install numpy scipy pandas pyarrow xlrd openpyxl pytest`
  (`pyarrow` reads and writes the EPA table; `xlrd` and `openpyxl` read the federal traffic
  spreadsheets; `pytest` runs the tests)
- a copy of the **Signal Four crash extract**, at the path set in `src/constants.py`

---

## Folder guide

```
src/        the pipeline: numbered steps, run in order by src/run_all.py
tests/      tests that fail if a known past mistake comes back
data/       raw downloads, in-between results, final results (not committed)
*.md        documents
*.py (top level)   earlier I-4 corridor exploration scripts (August 2026), kept for history
```

---

*Private project. Built for study and interview preparation.*
