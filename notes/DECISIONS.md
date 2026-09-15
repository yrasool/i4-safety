# Decisions — what, who, when, why

Every real decision in the project. **Who** is either **you** (Yusra) or **Claude** (a
choice made while building, with the reason written down). Where an audit pushed a decision,
it says so.

---

## Decisions you made

| when | decision | why |
|---|---|---|
| 6 Aug | Don't publish Signal Four crash data on a public website | It's licensed, not yours to publish |
| 6 Aug | No "generalist" positioning | Not a good look for the roles you want |
| 6 Aug | An **outcome-based** project, not a literature review | Like the parks, grid and paperstack projects |
| 7 Aug | High-risk **roads**, not intersection attribution | That was the original goal |
| 11 Aug | Map style: **Google Maps / satellite**, not the stylised designs | The designs looked bad |
| 15 Aug | "NLR" in the job posting = **NREL** | Confirmed |
| 15 Aug | **Tampa MEP** is the project's spine | Fits the NREL Center for Integrated Mobility Sciences role |
| 15 Aug | Build the cost project **privately**; mention it on the **resume only**; **no website** | Licensed data |
| 16 Aug | Go **step by step with heavy reviews** | The interview will be demanding |
| 7 Sep | Focus on **the five counties** of FDOT District 7 | The crash file covers them |
| 7 Sep | **Basic language** in every explanation | So you can understand and defend it |
| 7 Sep | Put **both deaths and injuries** into the cost | Injuries are real harm too |
| 8 Sep | **Build MEP properly** ("do it") | It hadn't really been built |
| 8 Sep | **Latest data**, not 2017 | Current travel behaviour |
| 8 Sep | **Bikes in the travel-time calculation** | Complete set of MEP modes |
| 8 Sep | Use the South Florida report for **method only** — don't copy their study | Our data, counties and safety focus differ |
| 9 Sep | Prepare for a **40-minute technical grilling**; review everything | NREL MEP experts |
| 14 Sep | **Four explainer files** + a MEP file + data guide + corrections file + learning document | Everything in one place, simply explained |
| 14 Sep | **GitHub: private**, **code and documents only**, name **i4-safety**, commits credited **only to you** | Safety of licensed data; your name only |
| 14 Sep | Keep **everything from the chat** in sorted files | So no one needs to read chat logs |

---

## Decisions Claude made while building (with reasons)

### What counts, and how it's priced

| when | decision | why |
|---|---|---|
| before 8 Sep | **US DOT per-person values** ($13.7M death, $1.3M serious injury) | Official values; we count people |
| before 8 Sep | **Deaths and serious injuries only** | The only level every mode is recorded at |
| before 8 Sep | **Charge harm to the person hurt** (a pedestrian hit by a car = a walking cost) | Every other MEP cost is what the traveller pays |
| 10 Sep | **Also report the other way** (harm charged to the driver) | It changes the answer, so it must be shown |
| before 8 Sep | **Crash cost added to MEP's money cost**, same weight | No new equation or weight needed |
| before 8 Sep | **Bus rate from national data, buses only, traffic collisions only** | Tampa had 2 bus deaths; fair comparison with cars |
| before 8 Sep | **Accept the car crash cost only if 1.2–3.0× the Minnesota figure** | Florida is ~2× as deadly per mile |

### Data

| when | decision | why |
|---|---|---|
| 8 Sep | **LODES job counts** as places | Free and rebuildable |
| 8 Sep | **Trip shares from "big South Atlantic cities"** | The 2022 survey has no Florida field |
| 8 Sep | **People per car measured** from drivers' trips (1.502) | The AAA figure didn't exist |
| 8 Sep | **Walking and biking miles measured** from the survey, reported as a range | No local count exists |
| 9 Sep | **Census mid-2022 population** | Middle of the crash period |
| 9 Sep | **Save a copy** of every download | FDOT's data changed between runs |
| 10 Sep | **Leave the traffic-by-year correction unapplied** | Keeps rates conservative (8–12% low) |

### MEP build

| when | decision | why |
|---|---|---|
| 8 Sep | **Neighbourhoods** (block groups), not NREL's grid | Data already comes that way |
| 8 Sep | **National scaling totals** | MEP's definition |
| 9 Sep | **Restaurants ("meals")** as the scaling reference | MEP tool's default (audit found "work" was wrong) |
| 8 Sep | **Real travel time inside each neighbourhood** | Audit found zero was wrong |
| 8 Sep | **OpenStreetMap, free-flow speeds** | Free; no traffic data available |
| 8 Sep | **Bikes 12 mph on all roads except motorways** | Same as NREL's South Florida basic setup |
| 8 Sep | **Own bus routing (RAPTOR), Thursday 17 Sep 2026, 7:45/8:00/8:15** | Both bus companies run full weekday service on Thursdays |
| 9 Sep | **Population-weighted** region score | MEP's rule (audit) |
| 10 Sep | **Delete the traffic-jam delay term** | Couldn't be reproduced (audit recommended) |

### Road danger

| when | decision | why |
|---|---|---|
| 8 Sep | **Safety curve + Empirical Bayes** on FDOT state roads | The standard road-safety method |
| 9 Sep | **Fit on all 2,848 roads**, including zero-casualty ones | Audit: leaving them out biased the curve |
| 9 Sep | **Pull each road's death share toward the regional average** | 51 roads looked "100% deadly" |
| 10 Sep | **Separate curves by road type** | Fits better |
| 10 Sep | **Don't use walking/biking danger by place** | Signal too weak |

### Checking and running

| when | decision | why |
|---|---|---|
| 8 Sep | **A number checker** for the documents | Numbers drifted from the data |
| 9 Sep | **Run-twice check** in `run_all.py` | Catches changes underneath |
| 10 Sep | **Checker reads the documents you speak from**, not just the report | That's how the 93% survived |
| 10 Sep | **Runtime stale-file list**, not reading scripts' descriptions | A description was itself wrong |
| 14 Sep | **Allow-list `.gitignore`** (only `.py` and `.md`) | No data file can be uploaded by accident |
| 14 Sep | **Tests scan every pipeline step**, read from the run list | They only scanned 9 of 27 before |

---

## Decisions still waiting

| decision | options | who should decide |
|---|---|---|
| Build a version weighted by real travel? | yes / no | you |
| Test other weights for crash cost? | yes / no | you |
| Add Uber/Lyft as a mode? | yes / no | you |
| Charts, maps and a slide deck? | yes / no, and what style | you |
| Archive the old scripts? | yes / no | you |
| Update the resume line with current numbers? | yes / no | you |
