# The data folder — a guide

Every data file the project uses or makes lives here, in three sub-folders. **Don't move or
rename files** — the 26 steps look for them in exactly these places.

| folder | what's in it | made by |
|---|---|---|
| `raw/` | **downloads** — data exactly as it came from its source | downloaded once, then reused |
| `interim/` | **in-between results** — tables and networks the steps build | the pipeline |
| `final/` | **answers** — the results | the pipeline |

For what each source *is*, see `../DATA.md`.

---

## ⚠ The crash records are NOT in this folder

The police crash file is **licensed**: we may use it, but must **not share or publish** it. It is
kept **outside** the project, on purpose, so it can never be uploaded by accident:

```
C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv   (527 MB)
```

The steps read it from there (the location is set once, in `src/constants.py`). **Nothing in this
folder contains a single crash record, a vehicle ID number or a driver age** — only totals.

---

## `raw/` — downloads

| file or folder | what it is | size | step |
|---|---|---:|---|
| `osm/` (96 files) | OpenStreetMap road and path map, in square pieces | 26 MB | 19 |
| `gtfs/hart.zip`, `gtfs/psta.zip` | bus timetables | 12 MB | 22 |
| `fl_wac_2023.csv.gz` | jobs by type, Florida, 2023 (LODES) | 3.3 MB | 16 |
| `lodes_national/` (51 files) | jobs by type, every state (LODES) | 54 MB | 25 |
| `nhts2022_csv.zip` | national travel survey 2022 | 4.5 MB | 17 |
| `nhts2022_codebook.pdf` | guide to the survey's codes | 0.4 MB | — |
| `acs2023_b01003.dat` | Census: population | 18 MB | 24 |
| `acs2023_b25044.dat` | Census: households by number of cars | 63 MB | 24 |
| `acs2023_b08301.dat` | Census: how people get to work | 88 MB | 32 |
| `fdot_rci_segments.json` | Florida DOT state roads with traffic counts | 0.4 MB | 09 |
| `fdot_segment_geometry.json` | shapes of those roads | 0.2 MB | 30, 32, 33 |
| `sld_epa_rows.json` | EPA accessibility data (for checking only) | 0.8 MB | 01 |
| `vm2_2019.xls` … `vm2_2024.xlsx` | Florida miles driven, by year | 6 files | 34 |
| `osti_1531145_mep.pdf` + `.txt` | Hou et al. 2019 — the original MEP paper | 1.7 MB | reference |
| `fdot_mep_report.txt` | FDOT/NREL South Florida MEP report | 0.1 MB | reference |
| `trb_young_mep.pdf` + `.txt` | Young et al. — MEP applied | 4.3 MB | reference |
| `cui_levinson_2019_full_cost_by_auto.pdf` + `.txt` | Minnesota crash cost study | 1.3 MB | reference, checked by a test |
| `cui_levinson_2018_fca_framework.pdf` + `.txt` | the framework behind it | 2.1 MB | reference |

### Downloaded every run — NOT saved here

| data | step | why it matters |
|---|---|---|
| National Transit Database — HART and PSTA passenger-miles | 03 | if the website changes, a rerun could change |
| National Transit Database — national bus deaths and bus miles | 05 | protected: stops unless exactly 12 deaths |
| Census map service — neighbourhood points | 18 | protected by the end-of-run check |

Saving copies of these is on the to-do list.

---

## `interim/` — in-between results

| file | step | what's in it |
|---|---|---|
| `sld.parquet` | 01 | EPA data, 2,098 neighbourhoods |
| `casualties_by_mode.csv` | 02 | people killed and seriously injured, by mode |
| `crashes_kabco.csv` | 02 | crashes by year and severity |
| `exposure_by_mode.csv` | 03 | passenger-miles by car and bus |
| `centroids.csv` | 18 | 2,170 neighbourhood IDs, points and counties |
| `acs_blockgroups.csv` | 24 | population and carless households |
| `opportunities.csv` | 16 | jobs of each kind, per neighbourhood |
| `activity_freq.csv` | 17 | how often people go to each kind of place |
| `occupancy.csv` | 17 | people per car |
| `nonmotorised_exposure.csv` | 17 | walking and biking miles per person |
| `spatial_equivalency.csv` | 25 | scaling numbers |
| `graph_drive.npz`, `graph_walk.npz`, `graph_bike.npz` | 20 | road networks |
| `graph_nodes.npy` | 20 | junction locations |
| `tt_drive.npy`, `tt_walk.npy`, `tt_bike.npy`, `tt_transit.npy` | 21, 22 | travel times: 2,170 × 2,170 minutes each |

---

## `final/` — results

| file | step | what's in it |
|---|---|---|
| **`mep_by_blockgroup.csv`** | **23** | **the answer: normal and with-crash-cost MEP score for all 2,170 neighbourhoods** |
| `injury_cost_by_mode.csv` | 04 | crash cost per mile by mode |
| `injury_rate_by_mode.csv`, `mep_weights.csv` | 05 | bus crash rate |
| `segment_rates.csv` | 09 | casualties and traffic per state road (totals only) |
| `spf_by_facility.csv` | 33 | safety curve per road type |
| `segment_facility.csv` | 33 | road type per road |
| `segment_eb.csv` | 29 | blended casualties and crash cost per road |
| `origin_risk.csv` | 30 | driving danger per neighbourhood |
| `nonmotor_risk_by_place.csv` | 32 | walking and biking attempt — **not used** |
| `validation.csv` | 26 | validation tests |
| `equity_2020.csv` | 27 | who is hit hardest |
| `nrel_scenarios.csv` | 31 | NREL's tests |
| `exposure_by_year.csv` | 34 | traffic-by-year check |
| `externality.csv` | 35 | who pays when a car hits someone |
| `holdout_eval.csv` | 36 | prediction test |

**Old files, no longer rebuilt, read by nothing:** `decision_test.csv`, `equity.csv`, `mode_results.csv`,
`transit_access.csv` — left over from the first version.
