# The data — every source, explained from zero

This file explains **every piece of data** in the project, as if you have never seen any
of it. For each source: **what it is**, **where it comes from**, **what we take from it**,
**what we make from it**, **how it was checked**, and **its limits**.

Other files: `MATH.md` (the calculations), `ASSUMPTIONS_AND_CHOICES.md` (why each choice
was made), `HOW_IT_RUNS_VS_STANDARD_MEP.md` (how it runs, and how it compares with NREL's
MEP).

| part | what it covers |
|---|---|
| 1 | a few words you need |
| 2 | every source, one card each |
| 3 | numbers we typed in (with their source) |
| 4 | how the sources connect to each other |
| 5 | how many records each result rests on |
| 6 | which data is saved, and which is downloaded every time |
| 7 | privacy — what we never touch |
| 8 | every file the project makes |

---

## 1. A few words you need

**Dataset** — a collection of records, like a big spreadsheet.

**Record / row** — one entry. One crash, one road, one survey trip.

**Column / field** — one kind of information in every row, like "year" or "number killed".

**ID** — a code that names something exactly, so two datasets can be matched. A Census
neighbourhood has a 12-digit ID, for example `120570051012`.

**Vintage** — which year the data describes.

**Download** — fetching data from a website. **Saved copy** — keeping it on the computer
so we don't need the website again.

**Neighbourhood** — a Census **block group**. Our five counties have **2,170**.

---

## 2. Every source

### 2.1 Crash records — Signal Four Analytics

- **What it is:** police reports of every traffic crash in the five counties, collected by
  Signal Four Analytics, a University of Florida system.
- **Covers:** 1 January 2019 to 27 November 2025 — **6.9 years**.
- **Size:** **602,110 crashes**, one row each, 527 MB.
- **Where it lives:** outside the project folder, at
  `C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv`.
- **Licence:** we are **allowed to use** it, but **must not share or publish** the records.
- **What we take from each crash:**

  | information | used for |
  |---|---|
  | people killed and seriously injured — walking, cycling, motorbike, total | counting harm by mode |
  | year, date and time | harm by year; when cyclists are hurt; the prediction test |
  | road ID and milepost | placing crashes on state roads |
  | map coordinates | placing walking and cycling casualties |
  | number of vehicles, motorbikes, mopeds | "was a car involved?" |

- **What we make from it:** casualties by mode (`casualties_by_mode.csv`), crashes by year and
  severity (`crashes_kabco.csv`), casualties per road, car involvement, and more.
- **Checks:**
  - The first independent audit **re-counted every casualty** with a different program — exact match.
  - "People in vehicles" is worked out as *total minus walking, cycling and motorbike*. It could
    never go below zero — and it never needed to.
  - 229 rows marked "non-traffic fatality" carry zero deaths, so leaving them out drops nobody.
- **Limits:**
  - Injuries to people walking and cycling are only recorded as **killed** or **seriously
    injured** — no minor injuries. So we price only those two levels, for every mode.
  - November 2025 is incomplete.
  - **547,205** crashes (91%) have a road ID and milepost; the rest can't be placed on a road.
    But those 547,205 include **95.7%** of all deaths.

### 2.2 Road and footpath map — OpenStreetMap

- **What it is:** a free world map built by volunteers — like Wikipedia, but for maps.
- **Vintage:** downloaded September 2026.
- **How it was downloaded:** in **96 square pieces** (0.15° each, about 16 km), because the whole
  region at once is too big for the map server. Each piece is saved only when **complete**.
- **Saved at:** `data/raw/osm/` — 96 files, 26 MB.
- **What we take:** every road and path — its shape, its type (motorway, main road, residential
  street, footpath, cycleway, steps…), whether it's one-way, and its speed limit if recorded.
- **Numbers:**
  - **501,243** road pieces downloaded
  - **5,735** duplicates removed (roads crossing the edge of two pieces appear in both)
  - **495,508** roads left
  - **827,133** junctions and **1,115,278** links in the network
- **What we make from it:** three road networks — car, walking, bike — and travel times.
- **Checks:** the audit rebuilt the network counts from the saved files and got exactly the same.
  Average car speed along the way comes out around **36 mph** — sensible.
- **Limits:**
  - Only **10.3%** of links have a speed limit recorded; the rest get a typical speed for that type
    of road.
  - Volunteers may have missed some paths.
  - **No traffic information** at all.

### 2.3 Bus timetables — HART and PSTA

- **What it is:** the published schedules of the two bus companies — HART (Hillsborough) and PSTA
  (Pinellas) — in **GTFS**, the standard format that apps like Google Maps use.
- **Saved at:** `data/raw/gtfs/hart.zip` and `psta.zip` — 12 MB.
- **What we take:** every stop, route, trip and departure time, and which days each schedule runs.
- **For our chosen day** (Thursday 17 September 2026):
  - **6,232** stops
  - **4,308** trips running
  - **69** bus routes plus **2** streetcar routes
- **Checks:** the audit re-counted stops, trips and routes — exact match. Two optional files
  (`frequencies.txt` and `transfers.txt`) are empty, so nothing in them was missed.
- **Limits:**
  - A **schedule**, not real arrival times — late buses aren't counted.
  - **PSTA's weekday schedule runs Monday–Thursday**, so a Friday would silently lose every PSTA bus.
  - The link listed on the Mobility Database website was broken (a capital "G"); we used PSTA's own.

### 2.4 Jobs by type and place — Census LODES

- **What it is:** a Census count of **how many jobs are in each census block** (an area about the
  size of a city block), built from records employers already send to the government. The part we
  use is called **WAC** — "workplace area characteristics".
- **Vintage:** **2023**, the newest release.
- **Two uses, two downloads:**

  | | file(s) | used for |
  |---|---|---|
  | Florida | `data/raw/fl_wac_2023.csv.gz` | jobs in our five counties |
  | all states | `data/raw/lodes_national/` — 51 files | national totals for scaling |

- **What we take:** for each block, total jobs and jobs in each business type:

  | MEP kind of place | business type(s) |
  |---|---|
  | work | all jobs |
  | restaurants | accommodation and food services |
  | fun / arts | arts, entertainment and recreation |
  | shopping | retail |
  | doctor | health care and social assistance |
  | school | educational services **plus** "other services" (the only type that includes religious organisations) |

- **Numbers:** **137,473** Florida blocks → **21,859** in our five counties → added up into
  neighbourhoods → **1,570,813 jobs**.
- **How a block joins a neighbourhood:** a block's 15-digit ID starts with its neighbourhood's
  12-digit ID. So the first 12 digits say which neighbourhood it belongs to.
- **Checks:** the audit rebuilt all the national totals from the 51 saved files — exact match.
- **Limits:**
  - Counts **jobs**, not **places**. A supermarket with 200 staff counts 200; a shop with 3 counts 3.
  - Self-employed people aren't included.
  - The Census adds **small random changes** to protect privacy.
  - "Other services" in "school" also includes repair shops and hair salons.
  - Two states' newest files are older: **Alaska 2016**, **Michigan 2021**. Only affects national
    totals, very slightly.

### 2.5 Travel survey — NHTS 2022

- **What it is:** the National Household Travel Survey. Households record **every trip** they make
  on a given day — why, how, how far, who was in the car.
- **Vintage:** **2022**, the newest. You chose this over 2017.
- **Saved at:** `data/raw/nhts2022_csv.zip` (4.5 MB) and its codebook `nhts2022_codebook.pdf` (the
  guide to what each code means).
- **The trip file:** **31,074** trips nationally.
- **What each trip tells us:**

  | information | code in the file | used for |
  |---|---|---|
  | how the trip was made | `TRPTRANS` (01–04 car/van/SUV/pickup, 08 bus, 16 Uber/Lyft, 18 bike, 20 walk) | mode shares, walking and biking miles |
  | why | `WHYTRP1S` (10 work, 40 shopping, 50 social/recreation, 80 meals…) | trip shares; why people bike |
  | how far | `TRPMILES` | miles walked and biked |
  | were you driving? | `DRVR_FLG` | people per car |
  | region | `CDIVMSAR` (51 and 52 = big cities in the South Atlantic region) | our regional figures |
  | how many real trips this one stands for | `WTTRDFIN` (the **weight**) | every total |

- **What we make from it:**

  | | national | South Atlantic big cities |
  |---|---:|---:|
  | households | 7,893 | 836 |
  | driver trips for "people per car" | 20,415 | 2,091 |
  | people per car | 1.523 | **1.502** |
  | walking miles per person per year | 52.9 (2,016 trips) | 49.0 (203 trips) |
  | biking miles per person per year | 19.3 (298 trips) | 23.7 (**35 trips**) |

  Plus the six trip shares (shopping 28.1%, work 20.3%, social 19.5%, restaurants 15.2%, school
  13.8%, doctor 3.2%).
- **Check:** the same code run on the whole country gives **2.28 trips per person per day** —
  exactly the government's published figure (FHWA, *Summary of Travel Trends 2022*). So the
  weighting is right.
- **Limits:**
  - **No state field** in the 2022 file. The closest we can get to Florida is "big cities in the South
    Atlantic region" (from Delaware down to Florida).
  - Some regional numbers rest on **very few trips**: biking **35**, doctor visits **68**.
  - People may forget or misreport trips.

### 2.6 Population, cars and commuting — Census ACS

- **What it is:** the American Community Survey, averaged over **2019–2023**, published for every
  neighbourhood.
- **Saved at:** `data/raw/` — three tables, 170 MB:

  | table | what it counts | used for |
  |---|---|---|
  | `B01003` | total people | weighting neighbourhoods |
  | `B25044` | households, by number of cars | households with **no car** |
  | `B08301` | how workers get to work | walking and biking shares; real commute shares |

- **Why the summary files, not the Census website's data service:** the service now requires a
  personal **key** (like a password). A project that needs a secret key can't be rerun by anyone else.
- **Why `B25044` and not the more obvious car table (`B08201`):** `B08201` isn't published for
  neighbourhoods, only for bigger areas.
- **Numbers:** all **2,170** neighbourhoods; **3,399,162** people in total; **1,582,400** workers.
- **Real commute shares (our five counties):** car 78.0%, work from home 17.6%, walk 1.2%, bus 0.8%,
  bike 0.5%, taxi/Uber 0.2%.
- **Limits:**
  - A **5-year average**, not one year.
  - "How workers get to work" only covers **commuting** — not shopping or fun.
  - Estimates for small areas have wide margins of error.

### 2.7 Traffic on state roads — Florida DOT

- **What it is:** Florida DOT's **Roadway Characteristics Inventory** — its list of state road
  stretches (called **segments**), each with a traffic count.
- **Vintage:** 2025 counts.
- **Saved at:** `data/raw/fdot_rci_segments.json` (the list) and `fdot_segment_geometry.json` (the
  shapes, for maps).
- **What we take per segment:** road ID, where it starts and ends (**mileposts**), county, and
  **AADT** — "annual average daily traffic", the average number of vehicles a day.
- **Numbers:** **2,848** segments used.
- **Checks:** this was the source that **changed between two runs** (2,429 segments one day, 2,427 the
  next). Since then a saved copy is used every time.
- **Limits:**
  - **State roads only.** Local and county roads have **57%** of crashes but no traffic counts.
  - State roads carry about **78.5%** of all driving.
  - **One year** of traffic for seven years of crashes.
  - **No road type** — 24 fields checked. We borrow the road type from the nearest OpenStreetMap road.
  - One stretch (road 14121000, mileposts 0 to 4.36) appears **twice** with two different traffic counts.
    Both are kept, as two segments; neither had any casualties.

### 2.8 Florida traffic by year — FHWA Highway Statistics

- **What it is:** the federal highway agency's yearly table (**VM-2**) of miles driven in each state.
- **Saved at:** `data/raw/vm2_2019.xls` … `vm2_2024.xlsx` — 6 files.
- **What we take:** Florida's total miles driven each year:

  | year | Florida (millions of miles) | vs 2019 |
  |---|---:|---:|
  | 2019 | 226,514 | — |
  | 2020 | 208,076 | −8.1% |
  | 2021 | 217,566 | −4.0% |
  | 2022 | 227,757 | +0.5% |
  | 2023 | 239,188 | +5.6% |
  | 2024 | 249,474 | +10.1% |

- **Check:** our five counties' traffic figure is **14.9%** of Florida's total, and the five counties
  have about 16% of Florida's people — so the two sources measure the same kind of thing.
- **Limits:** statewide, not just our five counties. **2025 isn't published yet**, so two versions are
  tested (hold 2025 at 2024's level, or grow it at the recent rate).

### 2.9 Bus crashes and bus miles — National Transit Database (NTD)

- **What it is:** the federal record of every US transit agency's safety events and passenger-miles.
- **Three parts used:**

  | part | used for |
  |---|---|
  | safety events | bus riders killed in traffic crashes, whole US |
  | passenger-miles by mode | bus passenger-miles, whole US |
  | service data | HART and PSTA passenger-miles (115 million a year) |

- **What we keep:**
  - **fixed-route buses only** (not trains, not dial-a-ride vans);
  - **traffic collisions only** — **not** assaults or robberies, because the car side counts only traffic
    crashes;
  - years **2015–2024**.
- **Numbers:** **12** bus rider deaths; **156.9 billion** bus passenger-miles over 10 years.
- **Checks:**
  - The download comes in pages. It's checked against a total **worked out by the website itself** —
    because once, paging silently dropped and duplicated 237 rows.
  - The step **stops** unless exactly **12** deaths come back.
- **Limits:**
  - **Downloaded fresh every run — not saved** (Part 6).
  - Records **no** serious bus injuries at all.
  - A **national** rate, not Tampa's — Tampa alone had only 2 bus rider deaths.
  - Crime was **57.8%** of bus rider deaths nationally; leaving it out makes the bus rate lower.

### 2.10 EPA accessibility data — Smart Location Database

- **What it is:** an EPA dataset estimating, for each neighbourhood, **jobs reachable within 45
  minutes** by car and by transit, plus population and car ownership.
- **Saved at:** `data/raw/sld_epa_rows.json` — 788 KB.
- **Numbers:** **2,098** neighbourhoods.
- **What we take:** jobs within 45 minutes by car (`D5AR`) and by transit (`D5BR`).
- **What it's used for:** **only to check our own travel times.** It isn't used in the MEP score.
- **Special code:** EPA writes **−99999** for "no data". We turn that into a blank so it can never be
  averaged as a real number. **837** neighbourhoods have no transit value.
- **Check:** a fresh download on 10 September matched the old saved file **row for row**.
- **Limits:**
  - The ID column is called `GEOID20`, which sounds like 2020 — but EPA's own notes say it's **2018**
    neighbourhood boundaries, with **2014–2018** survey values.
  - So only **1,670** of its 2,098 neighbourhoods match our 2,170.

### 2.11 Neighbourhood starting points — Census TIGERweb

- **What it is:** the Census's online map service. For each 2020 neighbourhood it publishes an
  **interior point** — a location guaranteed to be inside the neighbourhood's shape.
- **What we take:** the ID and interior point of all **2,170** neighbourhoods in our counties.
- **What we make:** `data/interim/centroids.csv`.
- **Limits:** **downloaded fresh every run — not saved** (Part 6). The point is one spot, not where
  people actually live within the neighbourhood.

### 2.12 Reference papers — saved on disk

| file | what it is | used for |
|---|---|---|
| `osti_1531145_mep.pdf` | Hou et al. 2019, NREL — the original MEP method | the equations, the population-weighting rule, NREL's own validation tests |
| `fdot_mep_report.txt` | FDOT report BDV29-977-66 (2023), FIU and NREL — MEP applied to South Florida | MEP's default settings (Table 7), "meals" as reference, bike network rules |
| `trb_young_mep.pdf` | Young et al., TRB — MEP applied | background |
| `cui_levinson_2019_full_cost_by_auto.pdf` | Cui & Levinson 2019, Minneapolis — full cost of travel | the benchmark for crash cost per mile (Table 3) |
| `cui_levinson_2018_fca_framework.pdf` | Cui & Levinson 2018 — the framework | background |

---

## 3. Numbers we typed in (with their source)

Some inputs are single numbers from a published document. They're typed into **one** file
(`src/constants.py`) **once**, each with a note saying where it comes from.

| number | value | source |
|---|---|---|
| value of a death | $13,700,000 | USDOT Benefit-Cost Analysis Guidance, 2026 update, Table A-1a (2024 dollars) |
| value of a serious injury | $1,302,300 | same table |
| five-county traffic | 102,108,727 vehicle-miles a day | FDOT, *Public Road Mileage and Miles Traveled* 2025 |
| population in mid-2022 | 3,468,871 | Census population estimates, 2024 release, July 2022 |
| study length | 6.9 years | measured from the crash dates (the audit got 6.9072) |
| car energy and money cost | 0.90 kWh, $0.48 per passenger-mile | FDOT BDV29-977-66, Table 7 |
| bus energy and money cost | 0.65 kWh, $0.85 per passenger-mile | same |
| walk and bike | 0, $0 | same |
| MEP weights | −0.5 energy, −0.08 per minute, −0.5 per dollar | same report, after Hou et al. |
| bike speed | 12 mph | same report, section 4.1 |
| walking speed | 3 mph | our choice |
| Minnesota car crash cost | $0.040 per vehicle-km (2010 dollars) | Cui & Levinson 2019, Table 3 |
| Minnesota value of a death | $9,134,786 (2010 dollars) | same paper, from Blincoe et al. 2015 |

**Why this matters:** an earlier version kept some numbers typed into **several** files. When one
copy changed and another didn't, nothing broke — the project just quietly used different values. Now
there's **one copy** of each.

---

## 4. How the sources connect to each other

Datasets only work together if they can be **matched**. Three kinds of matching are used.

### By neighbourhood ID (12 digits)
Used by: LODES jobs, ACS population and commuting, Census starting points, EPA data, our results.

| match | result |
|---|---|
| LODES blocks → neighbourhoods | first 12 digits of the block ID |
| ACS → our neighbourhoods | all 2,170 match |
| EPA → our neighbourhoods | only **1,670** match — EPA uses 2018 boundaries |

### By road ID and milepost
Used by: crash records and Florida DOT road segments.

A crash at "road X, milepost 12.4" goes onto the segment of road X whose mileposts include 12.4.
The program finds it quickly using **binary search** — like finding a name in a phone book: open the
middle, go left or right, repeat.
**547,205** crashes placed this way.

### By map location
Used by: walking and cycling casualties (their coordinates), road segment midpoints, OpenStreetMap
roads, neighbourhood points.

- A walking or cycling casualty goes to the **nearest** neighbourhood point (913 of 915 walking deaths
  and 277 of 277 cycling deaths placed).
- A road segment gets the road type of the **nearest** major OpenStreetMap road.
- A road segment's travel time from a neighbourhood uses the neighbourhood its midpoint is nearest to.

**Limit of "nearest":** it's an approximation. A casualty near a boundary can be put in the
neighbourhood next door.

---

## 5. How many records each result rests on

| result | rests on | enough? |
|---|---|---|
| car crash cost per mile | 1,582 deaths, 14,774 serious injuries | yes |
| walking crash cost per mile | 915 deaths, 1,612 serious injuries; 203 surveyed walking trips (regional) | fairly |
| **biking crash cost per mile** | 277 deaths, 1,263 serious injuries; **35 surveyed bike trips** (regional) | **thin** |
| bus crash cost per mile | **12** deaths nationwide | thin, but bus barely affects the score |
| people per car | 2,091 driver trips (regional) | yes |
| doctor trip share | **68** surveyed trips | thin |
| road-danger model | 2,848 roads, 14,179 casualties | yes |
| "why people bike here" | **35** surveyed trips | a hint, not proof |
| "when cyclists are hurt" | 1,540 people | yes |

**Why this matters:** a number from 35 records can be far from the truth just by chance. A number from
thousands usually isn't. The biking figure is the thinnest input — and biking causes most of the drop.

---

## 6. Which data is saved, and which is downloaded every time

**Why it matters:** if a website changes its data, a step that downloads every time could give a
**different answer** without anyone noticing. That happened once (Florida DOT's roads).

| data | step | saved? |
|---|---|---|
| crash records | 02 and others | on disk (licensed file) |
| OpenStreetMap | 19 | **saved** — downloaded only if missing |
| bus timetables | 22 | **saved** |
| LODES jobs (Florida and national) | 16, 25 | **saved** — downloaded only if missing |
| NHTS survey | 17 | **saved** — downloaded only if missing |
| ACS tables | 24, 32 | **saved** — downloaded only if missing |
| Florida DOT road segments and shapes | 09, 30, 32, 33 | **saved** |
| FHWA traffic by year | 34 | **saved** |
| EPA data | 01 | **saved** |
| **National Transit Database** | **03, 05** | **not saved — downloaded every run** |
| **Census neighbourhood points** | **18** | **not saved — downloaded every run** |

**How the unsaved ones are protected:**
- Step 05 **stops** unless it gets exactly **12** bus deaths, and checks its download against the
  website's own total.
- The whole-project check compares the headline numbers before and after every run and stops if they
  change.

**Still, it's a gap:** if the transit database or the Census map service changed, or went offline, a
rerun could fail or shift. Saving copies of these three downloads is on the to-do list.

---

## 7. Privacy — what we never touch

The crash file contains **vehicle ID numbers (VINs)** and **driver ages**.

- **No output file** contains a vehicle ID, a driver age, or a single crash record — only **totals**
  (by mode, by year, by road, by neighbourhood).
- The first independent audit **checked every output file** for this.
- Nothing from the crash file is published or shared. The project is private, for your interview and a
  resume mention only.

---

## 8. Every file the project makes

### In-between results (`data/interim/`)

| file | made by | what's in it |
|---|---|---|
| `sld.parquet` | 01 | EPA data, 2,098 rows |
| `casualties_by_mode.csv` | 02 | killed and seriously injured, by mode |
| `crashes_kabco.csv` | 02 | crashes by year and severity |
| `exposure_by_mode.csv` | 03 | passenger-miles by mode |
| `centroids.csv` | 18 | 2,170 neighbourhood IDs, points, counties |
| `acs_blockgroups.csv` | 24 | population and carless households |
| `opportunities.csv` | 16 | jobs of each kind, per neighbourhood |
| `activity_freq.csv` | 17 | trip shares |
| `occupancy.csv` | 17 | people per car |
| `nonmotorised_exposure.csv` | 17 | walking and biking miles per person |
| `spatial_equivalency.csv` | 25 | scaling numbers |
| `graph_drive.npz`, `graph_walk.npz`, `graph_bike.npz`, `graph_nodes.npy` | 20 | road networks |
| `tt_drive.npy`, `tt_walk.npy`, `tt_bike.npy`, `tt_transit.npy` | 21, 22 | travel times, 2,170 × 2,170 minutes each |

### Final results (`data/final/`)

| file | made by | what's in it |
|---|---|---|
| `injury_cost_by_mode.csv` | 04 | crash cost per mile by mode |
| `injury_rate_by_mode.csv`, `mep_weights.csv` | 05 | bus crash rate |
| `segment_rates.csv` | 09 | casualties and traffic per road |
| `spf_by_facility.csv`, `segment_facility.csv` | 33 | road types and their curves |
| `segment_eb.csv` | 29 | blended casualties and crash cost per road |
| `origin_risk.csv` | 30 | driving danger per neighbourhood |
| `nonmotor_risk_by_place.csv` | 32 | walking and biking attempt (not used) |
| **`mep_by_blockgroup.csv`** | **23** | **the answer — both scores for every neighbourhood** |
| `validation.csv` | 26 | validation tests |
| `equity_2020.csv` | 27 | who is hit hardest |
| `nrel_scenarios.csv` | 31 | NREL's tests |
| `exposure_by_year.csv` | 34 | traffic-by-year check |
| `externality.csv` | 35 | who pays when a car hits someone |
| `holdout_eval.csv` | 36 | prediction test |

**Old files not rebuilt any more** (from the first version, read by nothing): `decision_test.csv`,
`equity.csv`, `mode_results.csv`, `transit_access.csv`.


---

## 9. Sources added 15 September 2026 — checking only

None of these feed the pipeline. Every one exists to test a number that was already computed.

### Signal Four **public** dashboard — signal4analytics.com

**What it is.** The same organisation as our licensed extract, but a free dashboard with no login:
fatalities and serious injuries by county and year, 2014 to date.

**Why it matters.** Our crash figures came from one licensed file that a reviewer cannot open.
Anyone can reproduce this dashboard in a browser in two minutes.

**What we took.** Killed and seriously injured, by county, 2014–2026, for all five counties; and
pedestrian-and-cyclist casualties statewide by year, 2019–2025.

**Result.** Our extract is at **0.984** and **0.989** of the dashboard — slightly low, which is
right, because our extract stops in November 2025 and the dashboard runs to July 2026. Steps 37
and 38.

**Caveat.** It is a **snapshot**. The dashboard is revised as reports are filed, so the numbers are
recorded with their date (2026-09-15) rather than treated as fixed.

### Tampa Bay Regional Travel Survey — ActivityViz

**What it is.** FDOT's own household travel survey for this region, run by RSG. **4,565
households, 9,099 people, 76,226 trips.** Published as an ActivityViz dashboard; the underlying
CSVs are at `github.com/RSGInc/ActivityViz_data/tree/master/data/tampa`.

**What we took.** Trip destinations, which give local trip-purpose shares — work 27.0%, shopping
35.1%, social 16.3%, meals 10.4%, school 7.1%.

**Why we did not switch to it.** It has no published uncertainty, it does not separate medical from
shopping, and the MEP drop is 16.0% with it against 16.2% without. See ASSUMPTIONS J1.

### BTS Passenger Origin–Destination, 2020–2022

**What it is.** Phone-location trip data, metro to metro, from the Bureau of Transportation
Statistics. The Tampa metro's own row covers **2.98 billion trips inside the metro**, 97% of all
trips starting here.

**What we took.** Work share of trips: **19.0%** (2020), **21.0%** (2021), **27.2%** (2022). The
2020 figure is a lockdown year and the rise afterwards is people returning to offices.

**Limit.** It splits trips only into work and non-work, so it cannot replace a travel survey.

### Pinellas Trail User Survey 2023 — Forward Pinellas

**What it is.** 2,391 responses, run every four to five years by the county's planning agency.

**What it tells us.** Why people ride: **69% exercise, 22% recreation, 3% restaurant, 2% work,
0.25% school.** This is local evidence for the biggest limitation in the project — that MEP counts
cycling as access to destinations when most cycling here is not going anywhere.

### Hillsborough County Citizen Survey 2024

**What it is.** 1,300 telephone interviews, pre-stratified to match Census demographics, ±2.72%.

**What it tells us.** Residents rate **pedestrian safety 9.21/10** and **cyclist safety 9.19/10**
for importance — 2nd and 4th of 23 priorities, above traffic flow and parks. Bicyclist safety rose
from 8.77 in 2021, the second-largest rise of anything measured. It answers "why should an
accessibility metric care about this?"

### Looked at and not used

| source | why not |
|---|---|
| NREL TSDC household travel data | the Tampa Bay survey in it is from **1996** |
| PSRC household travel survey | Seattle, not Florida — useful only as a future comparison region |
| League of American Bicyclists city data | big cities only, no Tampa; and it is ACS commute data we already have |
| FDOT county highway maps (6 PDFs) | map images, no extractable data |
| `fti_2025.mdb` (FDOT traffic counts) | 1,860 count sites in our counties, but 2025 only — duplicates AADT we already hold |
| City/County road mileage 1992–2025 | background context, no role in any calculation |
| floridacyclinglaw.com blog | a law firm's summary; the underlying idea (safety in numbers) was taken to Jacobsen 2003 instead |
