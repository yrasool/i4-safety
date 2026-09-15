# The Missing Term

**Traffic-collision fatality cost in Mobility Energy Productivity — Tampa Bay**

NREL's MEP metric weights travel modes by energy, time and money. It has no term
for injury. This adds one, computes it from 602,110 police crash records, and
reports what changes.

**Status: v4.** Rewritten after three independent reviews. v3's headline figures
were wrong in four separate ways and its central output was an arithmetic
identity. What each review broke, and why, is recorded in §9 — the errors are
more instructive than the result.

---

## 1. The claim

MEP's published modal weighting factor (Hou, Garikapati, Nag, Young & Grushka,
*TRR* 2673(10); restated in NREL/TP-5400-95445):

```
MEP_i = Σ_k Σ_t ( o_ikt − o_ik(t−10) ) · exp(M_ikt)
M_k   = α·e_k + β·t + σ·c_k          α = −0.5   β = −0.08   σ = −0.5
```

`e_k` in kWh per passenger-mile, `c_k` in dollars per passenger-mile. Driving is
charged $0.48/PMT, transit $0.86/PMT. Driving is not charged for the collisions
it causes.

This adds `δ·r_k`, where `r_k` is traffic-collision fatality cost per
passenger-mile. The authors invite exactly this:

> "It is not the intent of the authors to determine or advocate weighting
> factors through this research. Rather, the weighting factors should be
> determined and plugged in for specific use cases by researchers utilizing the
> metric."

## 2. What this is, and is not

**Is:** an application of an established full-cost accessibility method to a US
metro that has not had it, with a term its originators have not implemented.

**Is not:** a new metric. Cui & Levinson (2018, 2019) established full-cost
accessibility. Asadi et al. (2025) monetised crash risk inside an accessibility
impedance with an income split, for Amsterdam, in August 2025. **Never describe
this as novel.**

**Not NREL's "safety" work either.** Their Level of Traffic Stress and Walking
Comfort Index are lookup tables over speed limit, lane count and sidewalk
presence that slow assumed walk/bike link speeds. No crash data, no
monetisation. They infer discomfort from geometry; this measures what happened.

---

## 3. Modes, not places — and why no map is possible

Assigning a crash to the block group it occurred in and calling that a cost
borne by residents is a named error (Asadi et al. 2024). Both legitimate repairs
are unavailable: **Home-Based Analysis** needs the involved person's home
address, verified absent from this extract; **route-based** needs the routing
engine this design exists to avoid.

So `r_k` is a single regional number per mode, and the project makes **no
place-level injury claim**.

**v3 believed this still permitted a map, with spatial variation entering
through EPA's accessibility. That was wrong, and provably so.** With
`f_k = exp(δ·r_k)` and `s` the weighted transit share:

```
loss_pct = (1 − f_d) + s·(f_d − f_t)
```

Verified to **3.5e-16** across all 2,098 block groups. The rows enter only
through `s`. The surface was **rank-invariant under every injury rate tested** —
`(0.0953, 0.0115)`, `(0.30, 0.02)`, `(0.012, 0.0001)` all give the identical
ordering. The injury data contributed **two scalars to a 2,098-row map**.

**This is a theorem, not a bug.** A mode-constant `r_k` makes loss a function of
modal composition alone. There is no implementation that fixes it. The map has
been deleted; §8 says what replaced it.

---

## 4. Study area and period

Five counties, FDOT District 7: Hillsborough, Pinellas, Pasco, Hernando, Citrus.
**2,098 block groups**, mid-period population **3,468,871** (Census PEP, July
2022 — the study midpoint falls in mid-June 2022, so no interpolation).

Crashes January 2019 – November 2025 = **6.9 years** (verified 6.898 from parsed
dates). **Never quote a 2025 total** — December is absent and November
incomplete. Raw year-over-year reads as −13.0%; on complete months it is −2.7%,
essentially flat.

---

## 5. Data

| Input | Source | Note |
|---|---|---|
| Crashes | `C:\Users\yusra\claude\traffic-data\signal4_district7_2019_2025.csv` | 602,110 rows. **Embedded NULs — strip per line.** |
| Road exposure | FDOT *Public Road Mileage and Miles Traveled 2025* | five-county DVMT **102,108,727** → **37.27 B VMT/yr** |
| Occupancy | NHTS 2022, computed by step 17 | **1.502** — measured from driver-reported trips, South Atlantic large-MSA. US figure 1.523 on 10x the sample. The 1.67 that stood here was NHTS 2017 and is superseded. |
| Bus fatalities | NTD **`9ivb-8ae9`** | fixed-route modes `MB,RB,CB,TB,PB`; collisions only |
| Bus exposure | NTD **`npsm-38gk`** | **required**: `6y83-7vuw` has no `mode` column. **LONG format** — filter `field='Passenger Miles Traveled'`, sum `value` |
| Costs | USDOT BCA 2026 Update, Table A-1a | per **injured person**, 2024 $. K = $13,700,000 |
| Accessibility | EPA SLD layer 1 | `D5AR` auto, `D5BR` transit |

### 5.1 Handling rules that are not optional

**Strip VINs on first read.** `V1_VIN`, `V2_VIN` and driver ages are identifying,
inside licensed data.

**`-99999` is a sentinel.** In `D5BR` for 837 of 2,098 block groups (39.9%),
never in `D5AR`. It means *no transit-reachable jobs* — Citrus 83.9%, Hernando
60.4%, Pasco 56.4%, Hillsborough 47.7%, Pinellas 15.0%. It is a true zero for a
**sum** and must never be averaged as a rate.

**Fill rates before use.** `FUNC_CLASS` is 99.4% empty (use
`ROAD_SYSTEM_IDENTIFER`). `V1_BODY_TYPE_CD` is 100% empty (use
`V1_VHCL_BDY_TYP_CD`). ArcGIS field names are case-sensitive: `TotPop`, not
`TOTPOP`. NTD's year field is `report_year` (a **string**, must be quoted) in the
service dataset and `year` (numeric) in the safety dataset.

**Bound every date window at both ends.** An unbounded `year >= 2019` divided by
a fixed 6.9 years made the rate grow on every rerun.

---

## 6. The cost convention, and its three corrections

**USDOT BCA Table A-1a, value per injured person, 2024 dollars.** Chosen because
the numerator is casualties, not crashes. FHWA-SA-25-021's per-crash values must
never be applied to person counts.

The benchmark is **Cui & Levinson (2019)**, Twin Cities, *JTLU* 12(1), Table 3.
Three mismatches had to be corrected before it was comparable, each found only
after a version of the test had already printed PASS:

| | | |
|---|---|---|
| **Units** | their figure is per vehicle-km; `r_drive` is per passenger-mile | × `KM_PER_MILE`, × `OCCUPANCY` |
| **Dollars** | their costs are Blincoe et al. 2015, **2010 dollars** | × **1.50** (value per death; CPI gives 1.44) |
| **Scope** | their internal/external split **is** this project's occupant/non-motorist split | each spec gets its own comparator |

> "Crash cost borne by involved travellers" · "collisions that injure or kill
> non-motorists" — Cui & Levinson, Figure 1

**Roughly half of what looked like a Florida safety penalty was currency
inflation.** Corrected: internal **1.65×**, external-inclusive **1.56×**. Two
independent specifications agreeing within 6% is cross-validation, and it means
there is no flattering choice left to make. **Report both, each printed beside
its matched benchmark component.**

**Acceptance band 1.2–3.0.** The old 0.5–4.0 passed the mis-united 1.49×, the
unit-fixed 2.49× *and* the external-inclusive 3.7× alike. **A test that cannot
fail is not a test.**

---

## 7. The injury term

### 7.1 Fatality-only, on both sides. This is forced.

**All fourteen NTD serious-injury columns are zero for Bus and Ferry in every
year 2014–2026**, while bus rider *injuries* run to 22,054. Serious injury is a
**rail-only** concept, inherited from State Safety Oversight (49 CFR Part 674),
which covers rail fixed-guideway. There is no alternative field and no
defensible imputation.

So the A term is dropped from **both** modes. It supplies 47% of the drive side's
cost, and keeping it while bus structurally cannot have it inflated the ratio by
1.89× on that basis alone. **When a severity level is absent from one side, drop
it from both.**

```
r_drive    = (1,582/6.9) × $13.7M / 55,979,067,403   = $0.056112 /PMT
r_transit  = (12/10)     × $13.7M / 15,691,994,175   = $0.001048 /PMT
                                                       54×
```

95% CI on 12 bus deaths (Poisson): **$0.000541–$0.001830**, i.e. **31× to 104×**.

These moved when occupancy was corrected from 1.67 to a measured 1.502: the
denominator shrank, so `r_drive` rose 11% and the ratio went 48× to 54×.
Report the interval; never the point estimate bare.

### 7.2 What this is called

**Traffic-collision fatality cost.** Not "safety", not "injury risk".

Onboard crime is excluded from both modes, because a crash database cannot see
car-occupant assault. Including it on one side only would be the worse error.
**Nationally that exclusion removes 52 of 71 bus rider deaths (73%). In Tampa
Bay it removes none** — HART and PSTA recorded **zero** rider fatalities across
753 events and 1.17 billion passenger-miles over ten years, including 18 security
events. State the exclusion, its national size and its local size.

A symmetric treatment would price crime on both modes using FDLE Uniform Crime
Reports, which is a different data lineage. **v2.**

### 7.3 Validation

**Savage (2013)**, *Research in Transportation Economics* 43:9–22, measured bus
passenger fatalities independently on 2000–2009 data:

| | this project | Savage |
|---|---|---|
| Bus per bn PMT | 0.076 collision-only · **0.121** incl. falls | **0.11** |
| Car per bn PMT | 3.684 (Tampa Bay occupants) | 7.3 (national) |
| Ratio | **48×** | **66×** |

An independent published study, a decade earlier, different data, same regime.
**This is the strongest evidence in the project** — every internal check can be
wrong in the same direction as the person who wrote it.

### 7.4 Walk and bike

11,018 pedestrian and 12,006 cyclist crashes are in the data, and **92.7% of
pedestrian KSI and 92.0% of cyclist KSI are confirmed motor-vehicle-involved**
across all 602,110 rows. But **Tampa Bay publishes no walk or cycle exposure.**

**[CHOICE]** Report **break-even exposure** rather than estimating a denominator:
what the region would have to travel by that mode for its cost per mile to match
driving's. That needs no estimate. ⚠️ Two break-even bases exist — KSI-count and
cost — and they differ by 2.3×. **Use the cost basis**, since dollars per
passenger-mile is the project's currency. Never state "walking is N× more
dangerous per mile" — that has no denominator and reintroduces in prose the
estimate break-even exists to avoid.

### 7.5 Motorcycles

**Never folded into drive.** A motorcyclist bears their own injury, so they are
neither internal nor external under the benchmark's definition. Reported as a
separate mode, as walk and bike are.

### 7.6 δ

**[CHOICE] δ = σ = −0.5 base case** — a dollar of injury is a dollar, so it takes
the weight the metric already gives to dollars. Sensitivity at the **Amsterdam
weight 11.32** (Asadi et al. 2025, from Mouter et al. 2017). Adding dollars 1:1
is a substantive choice; **making it silently is the error.**

---

## 8. Build and output

```
constants.py             every shared value, defined once
01_fetch_sld.py          2,098 block groups
02_crashes_by_mode.py    602,110 rows → casualties by mode      <- slow stage
03_exposure_by_mode.py   denominators, and break-even where none exist
04_injury_cost.py        r_k, with the acceptance test
05_mep_weights.py        bus rate, and the term inside MEP
06_results.py            the mode-level result + transit availability
07_equity.py             who has neither option
tests/test_pipeline.py   13 tests, all asserting FAILURE modes
```

### 8.1 What may be reported

**Percentages only — but the "unrescalable" claim below was FALSE and is
corrected here.** One of the three scalars was known exactly: MEP's spatial
equivalency benchmark. The tool defaults to **meals**; this project used
**work**, an exact 11.0536x factor on every score. Fixing it moved the mean from
91,094 to 8,241, which is the same order as the reference implementation's own
11,983 for South Florida. Rankings and percentages were invariant throughout,
which is why no internal test could see it.

The remaining scale gap against the published 122.35 is destination counting:
the reference's own report gets **122.35 with CoStar destinations and 11,983
with MAZ employment counts for the same region**. This project uses LODES
employment, so it sits on the employment scale. Percentages remain the only
comparable quantity, for that reason rather than the one originally given:

1. the omitted `exp(β·t)`, which **must not** be applied because SLD is already
   time-decayed and `t=45` is a **cutoff, not a duration**;
2. the omitted Eq. 1 normalisation, unknown without `N*` and the NHTS frequency
   vector;
3. SLD's decay-weighted sums against MEP's raw isochrone counts, which is not a
   scalar difference at all.

**Retire the phrase "opportunities lost."** The project cannot produce a
defensible count of opportunities.

### 8.2 The three results

1. **Driving carries 48× the traffic-collision fatality cost per passenger-mile
   of a fixed-route bus** (28–93×), replicating Savage.
2. **MEP's omission is asymmetric by 86×** — the missing term is 10.5% of the
   cost it already charges driving and 0.12% of transit's. Omitting it flatters
   the car.
3. **25.3% of car-free households live where no bus reaches a job** — Citrus
   85.1%, Hernando 57.7%. They cannot take the safer mode, because taking it
   requires a bus that goes somewhere.

---

## 9. Known weaknesses

1. **Replication with transfer, not a new method.** Asadi et al. (2025) did the
   closer version four months earlier.
2. **12 bus fatalities is the binding constraint.** Sample size, not method, sets
   the precision. The 28–93× interval is irreducible without more years.
3. **The transit rate is national; the drive rate is local.** Defensible — bus
   safety is dominated by vehicle design and operator training — and Tampa Bay's
   own record is consistent with it. But it is an asymmetry, and a reviewer will
   ask first.
4. **No spatial injury output, and none is possible** (§3).
5. **Walk and bike exposure is unmeasured** (§7.4).
6. **`D5BR = min(transit, walk ≤15 min)`** — an unknown share of the transit
   surface is walk access, priced at transit's rate, the safest in the model.
   Biases toward **understating** the gap.
7. **`D5BR = max(forward, reverse)` while `D5AR` is single-directed.** This is
   why transit exceeds driving in 345 block groups. `D5BR_Flag` marks which rows
   used the reverse value and is **not yet pulled** in step 01.
8. **SLD is 45-minute only**, not MEP's 10/20/30/40 bands, and rests on 2017
   LEHD with 2020 GTFS.
9. **Period mismatch.** Crashes 2019–2025, bus 2015–2024, road VMT 2025, SLD
   2017/2020. Each is the most recent available; none share a window.
10. **Police underreporting** of slight-injury and non-motorist crashes is
    systematic and understates walk/bike most.
11. **Renderer output is not a citation.** A WebFetch summary fabricated a
    supporting quote from the EPA user guide — text appearing zero times in
    114,924 characters. Verify against downloaded source.

---

## 10. Provenance

The Signal Four extract is **licensed, not open**, and contains VINs and driver
ages. The corridor documents in `F:\Yusra` are **Merrick & Company deliverables
for FDOT District 7 authored by others** — no result or figure from them appears
here. Public guidance only carries over: USDOT and FHWA cost tables, HSM Part D,
the CMF Clearinghouse convention.

**Private build. No publication, no deployment.** Any description must say
*"applied an established full-cost accessibility method"*, never *"developed a
new metric"*.

## 11. Prior art to read before scoping is final

- **UMN Accessibility Observatory, "The Connection Between Jobs and Transit in
  Tampa Bay" (2018)** — closest existing work on the accessibility half.
- **FDOT BDV29-977-66** (FIU + NREL, June 2023) — MEP assessed for *South*
  Florida. Tampa not covered; safety absent.
- Nothing found monetises crashes anywhere in Tampa Bay.
