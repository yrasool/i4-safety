# Reading guide

Everything this project uses, what it means in plain words, where it lives in
the code, and what to read if you want to understand it properly.

Ordered by **how likely you are to be asked about it**, not by difficulty.

---

# Tier 1 — you must be able to explain these

## 1. Accessibility, and why MEP is one

**Plain version:** accessibility is "how much can you get to from here". Not how
fast you can drive, not how many roads there are — how many actual destinations
are within reach.

The key idea: a person who drives 60 miles to work is not more mobile than
someone who walks 10 minutes to everything. Old measures (vehicle-miles,
congestion, average speed) miss that completely.

**Where it lives:** `src/23_mep.py`

**Read:**
- Hou et al. (2019), the MEP paper — `data/raw/osti_1531145_mep.txt`. Read the
  Introduction and Literature Review. It is 4 pages and it sets up everything.
- The five categories of accessibility measure in that literature review:
  infrastructure-based, location-based, person-based, utility-based,
  activity-based. **Know which one MEP is** (location-based, gravity/isochrone
  hybrid) and be ready to say why.

**Likely question:** "Where does MEP sit in the accessibility literature?"

---

## 2. The three MEP equations

```
Eq 1   o_ikt = Σ_j  o_ijkt · (A*/A_k) · (f_k / Σ f_k)
Eq 2   M_ikt = α·e_k + β·t + σ·c_k
Eq 3   MEP_i = Σ_k Σ_t (o_ikt − o_ik,t−10) · exp(M_ikt)
```

**Plain version:**

- **Eq 1** — count what you can reach, but weight each *kind* of destination.
  Reaching 100 restaurants is not worth the same as 100 hospitals. Two weights:
  one puts rare and common destination types on the same scale (`A*/A_k`), the
  other weights by how often people actually make that kind of trip (`f_k`).
- **Eq 2** — score each travel mode on energy, time and money. All three
  coefficients are negative, so more of any is worse.
- **Eq 3** — add it all up, but **as a band difference**. `o_ikt − o_ik,t−10` is
  what you reach *between* 20 and 30 minutes, not everything within 30. Summing
  cumulative counts would count your nearest shop four times.

**The one thing to notice:** there is **no `i` on the right-hand side of Eq 2.**
All of MEP's geography lives in Eq 1. That single observation explains why our
first map was fake, and it is worth being able to say out loud.

**Where it lives:** `src/23_mep.py`, the `mep()` function — about 15 lines.

**Read:** Hou et al., the "MEP Metric Formulation" section, and FDOT
BDV29-977-66 §2.1 (`data/raw/fdot_mep_report.txt`).

---

## 3. Value of a Statistical Life (VSL) and KABCO

**Plain version:** VSL is the official price of one life, **$13.7 million**. It
is not a moral claim. It is what federal agencies use to decide whether a safety
project is worth building — if a guardrail costs $2M and prevents one death, it
pays.

**KABCO** is the injury scale on every US police crash report:

| | meaning |
|---|---|
| **K** | killed |
| **A** | incapacitating / serious injury |
| B | non-incapacitating |
| C | possible injury |
| O | no injury |

We use **K and A only** — "KSI", killed or seriously injured. Because
pedestrians and cyclists barely appear at B and C, so including them would make
the modes non-comparable.

**The trap that cost this project an 8× error:** USDOT values attach to an
**injured person**. FHWA values attach to a **crash**. Our numerator counts
people, so it must use the USDOT table. Using the FHWA one on person counts
overcounts, and it looks completely reasonable.

**Where it lives:** `src/constants.py`, `COST_PER_PERSON`

**Read:** USDOT Benefit-Cost Analysis Guidance, Appendix A, Table A-1a. Two
pages. Read the *definitions* of the columns, not just the numbers.

---

## 4. Exposure, and why the denominator is everything

**Plain version:** you cannot compare walking and driving using total deaths,
because people drive vastly further than they walk. You divide by miles
travelled. That bottom number is **exposure**.

**Every soft spot in this project is in the denominator, not the numerator.** The
death counts come from 602,110 police reports and are not arguable. The miles
are estimated, and that is where every attack lands.

Watch for two units that look identical and are not:
- **vehicle-miles** — how far the car went
- **passenger-miles** — how far the *people* went

They differ by occupancy (1.502 here, measured from the travel survey). MEP's
cost term is per passenger-mile, so ours must be too.

**The number this produces:** driving's crash cost is **$0.1059 per
passenger-mile**. Know it. Multiply by occupancy and you get $0.1591 per
vehicle-mile, which is what the Cui & Levinson check compares against — and that
conversion is why the check never depended on the occupancy value at all.

**Where it lives:** `src/03_exposure_by_mode.py`, `src/04_injury_cost.py`

**Read:** FHWA, *Synthesis of Methods for Estimating Pedestrian and Bicyclist
Exposure to Risk*. Chapter 4 is the one that matters. This is the literature
behind our biggest weakness.

---

# Tier 2 — the statistics

## 5. Overdispersion, Poisson vs negative binomial

**Plain version:** if you count rare events (crashes on a road, calls to a call
centre), the natural model is **Poisson**, which assumes the variance equals the
mean. Crash data does not behave that way at all.

Ours:

```
mean 4.98        variance 114.7        ratio 23.0
```

Twenty-three times more spread than Poisson allows. Use Poisson anyway and every
p-value is wildly overconfident.

**Negative binomial** adds one parameter, `k`, that lets variance exceed the
mean: `Var = μ + k·μ²`. That `k` is not a nuisance — it is the number Empirical
Bayes needs in the next section.

**Where it lives:** `src/29_spf_eb.py`, `nb_negloglik()`

**Read:**
- Any introduction to count data regression — the Poisson/NB comparison. Cameron
  & Trivedi is the standard text; the first chapter is enough.
- Highway Safety Manual, Part C, on why crash models are negative binomial.

**Likely question:** "Why negative binomial?" Answer with the ratio, not with
theory.

---

## 6. Empirical Bayes and regression to the mean

**This is the most impressive thing in the project. Learn it properly.**

**Plain version:** a quiet dead-end street with 2 deaths looks like the most
dangerous road in the region if you divide by its tiny traffic. It is almost
certainly just bad luck. Next year it will probably have zero.

Empirical Bayes blends what you *observed* with what a road *like this* normally
sees:

```
w = 1 / (1 + k·μ)               μ = prediction, k = overdispersion
N_eb = w·μ + (1 − w)·observed
```

- Busy road, long record → `w` small → trust its own data
- Short quiet road → `w` near 1 → pull it back toward the average

**What it did here:** knocked **13 of the 25** "worst" roads off the list. They
were noise.

**The subtle bit we got wrong first:** EB smooths the *count*, but the count then
gets split into deaths and serious injuries to be priced — and a death costs
10.5× a serious injury. Using each road's raw fatal share handed the noise
straight back. 51 roads had a raw fatal share of exactly 1.0, on one or two
casualties. It needed shrinking too.

**Where it lives:** `src/29_spf_eb.py`

**Read:**
- Hauer, *Observational Before-After Studies in Road Safety* — the origin of EB
  in this field.
- Highway Safety Manual Part C Appendix A.2.4 — the exact formula we use.
- For the general idea, look up **Stein's paradox** / James-Stein estimator. Same
  mathematics, far more famous, and it makes EB feel inevitable rather than
  arbitrary.

---

## 7. Selection on the outcome variable

**Plain version:** if you want to know how dangerous cars are, do not survey only
people who have crashed.

We fitted the safety curve on 2,429 road segments — but those were only the roads
that had **already had a crash**. The 421 roads with none were silently dropped,
and those are the quiet ones.

The bias landed exactly where theory says:

```
selected sample    a = -7.7239   b = 0.7300
all segments       a = -8.3884   b = 0.7892
```

Intercept biased up, slope biased down. And then EB shrank quiet roads *toward
an inflated expectation* — the opposite of its purpose.

**A zero is data.** It says: this much exposure produced nothing.

**Where it lives:** `src/09_segment_rates.py`, the `seg_keys` loop

**Read:** any treatment of selection bias / Heckman correction. You do not need
the maths, you need the reflex: *what got excluded from this sample, and is it
excluded for a reason related to what I am measuring?*

---

## 8. Degenerate results — when a map is just its own inputs

**Plain version:** we produced a beautiful 2,170-neighbourhood map that turned
out to be an exact rearrangement of data we already had. No new information.

The algebra:

```
loss_i = Σ_k (1 − g_k) · s_ik
```

where `g_k` is a constant per mode and `s_ik` is that neighbourhood's mode mix.
If crash risk is one number per mode, the map **can only** show mode mix. Four
numbers cannot make a 2,170-row map.

Verified to `6e-16` — that is machine precision, i.e. exactly.

**Two lessons here, and the second is the better one:**

1. Ask whether your output actually *depends* on the input you added.
2. **A test that cannot fail is worse than no test.** Our first identity test
   passed when fed the deleted fake map. It retired the suspicion that would have
   made someone check by hand.

**Where it lives:** `src/26_validate.py`, TEST 1

**Read:** nothing specific. This is a habit, not a literature. The habit is:
after any check passes, feed it a case that **must** fail and confirm it does.

---

# Tier 3 — the algorithms

## 9. Shortest paths — Dijkstra

**Plain version:** given a network of roads and how long each takes, find the
fastest route from A to everywhere else. Dijkstra's algorithm does this by
expanding outward from the start, always taking the cheapest unexplored option.

**What made it feasible here:**

- **Graph contraction.** OpenStreetMap stores a curve as dozens of points. Only
  the points where roads *meet* matter for routing. Collapsing the rest took
  927k points down to 297k junctions.
- **A cutoff.** We stop at 40 minutes. A 40-minute walk reaches almost nothing,
  so the search ends early.

**Where it lives:** `src/20_build_graph.py`, `src/21_isochrones.py`

**Read:** any algorithms textbook chapter on Dijkstra. Then look at
`scipy.sparse.csgraph.dijkstra` — we call the library, we did not implement it.

**Likely question:** "How did you build the network?" Answer with the contraction
and the cutoff, because those are the engineering.

---

## 10. Transit routing — RAPTOR

**Plain version:** a bus trip is not a shortest path. You have to *wait*. When
the next bus leaves depends on when you arrived at the stop, which depends on how
long you walked.

**RAPTOR** (Round-bAsed Public Transit Optimized Router) works in rounds:

- Round 1 — where can you get with no transfers?
- Round 2 — with one transfer?
- Round 3 — with two?

We stop at three, which covers almost every real bus trip.

**Four choices that change the answer**, all written into the file:

1. **Which day.** Thursday, because PSTA's weekday service runs Mon–Thu and
   HART's Mon–Fri. A Friday would silently drop every PSTA route.
2. **Which departure time.** Three, averaged. One departure rewards a stop for
   the bus that happened to leave at 08:00.
3. **Walking to the stop** on the real network, not straight-line.
4. **You must actually board.** Otherwise a "transit" trip can be two walks.

**Where it lives:** `src/22_transit.py`

**Read:** Delling, Pajor & Werneck (2015), *Round-Based Public Transit Routing*.
The first four pages give you the algorithm. Also skim the **GTFS** spec — it is
the format every transit agency publishes, and knowing `stops.txt`,
`stop_times.txt`, `trips.txt` and `calendar.txt` is genuinely useful.

---

# Tier 4 — the Python

## 11. What the code actually uses

Deliberately thin. Every dependency is something that can silently change a
number between versions.

| library | what for |
|---|---|
| `csv` | streaming 602,110 crash rows without loading them |
| `numpy` | all the array maths |
| `scipy.sparse` | the road network as a matrix |
| `scipy.sparse.csgraph.dijkstra` | shortest paths |
| `scipy.spatial.cKDTree` | nearest-neighbour lookups |
| `scipy.optimize.minimize` | fitting the safety curve |
| `pandas` | small joined tables only, never the crash file |
| `bisect` | finding which road segment a milepost falls in |

**No geopandas, no statsmodels, no sklearn.** Not needed.

### Three patterns worth understanding

**Streaming vs loading.** The crash file is 527 MB. `csv.DictReader` reads it a
row at a time. `pandas.read_csv` would load it all into memory. For one pass,
streaming wins.

**Sparse matrices.** The road network has 827,133 nodes. A dense matrix would be
827,133² = 684 billion cells. Almost all zero. Sparse formats store only the
connections that exist — 1.6 million.

**Binary search.** Matching 602,110 crashes to 2,850 road segments by scanning is
1.7 billion comparisons. Sorting each road's segments once and binary-searching
makes it minutes instead of hours. That is `bisect` in
`src/09_segment_rates.py`.

**Read:** the numpy broadcasting rules, properly. It is the one piece of numpy
that causes silent wrong answers rather than errors, and this project relies on
it (a scalar and a 2,170-length vector both work in the same expression).

---

## 12. The defensive patterns

These are what make it a project rather than a script, and they are worth being
able to point at.

**Fail closed.** If an input looks wrong, stop. `sys.exit` rather than a warning.
A warning scrolls past.

**Guard the join.** After any merge or snap, ask what the operation had to do to
succeed. Our snap check measures how far each neighbourhood reached to find a
road — median 57 m on the good network, 784 m when half the map was missing.
Nothing else distinguished them.

**Read, never retype.** If the pipeline can compute a value, no other file may
hold a copy. Every drift bug in this project was a second copy of a number.

**Pin every input.** Anything fetched live can change under you. FDOT's road
database gave us 2,429 segments one day and 2,427 the next, and the headline
moved. Everything is now saved to a file first.

**Meta-test your tests.** Feed each check a case it must fail. Both of ours were
tautologies until an audit found them.

**Where these live:** `src/01_fetch_sld.py` (fail closed),
`src/21_isochrones.py` (snap guard), `src/28_check_report.py` (meta-tests),
`src/run_all.py` (reproducibility diff)

---

# Tier 5 — the domain literature

Worth having read enough to name.

| what | why it matters here |
|---|---|
| **Hou et al. (2019)** | the MEP paper itself. Non-negotiable. |
| **FDOT BDV29-977-66** | MEP applied to South Florida, with Garikapati. Our reference implementation, and the source of the 122.35 vs 11,983 scale story. |
| **Cui & Levinson (2019)**, *Full cost accessibility* | the only published framework that puts crash cost into accessibility. Our external benchmark and our theoretical cover. |
| **Skabardonis, Varaiya & Petty (2003)** | measured what share of congestion is caused by incidents, 13–30%, with loop detectors. Replaced three guesses. |
| **Savage (2013)** | fatality rates by mode. Our bus rate reproduces his. |
| **Highway Safety Manual, Part C** | safety performance functions and Empirical Bayes. The standard every US DOT uses. |
| **Mekuria, Furth & Nixon**, Level of Traffic Stress | NREL's own safety work. Know what it does *and* that it is barely validated against actual crashes — that gap is your best proposal. |

Both NREL/FDOT reports are on disk as text in `data/raw/`.

---

# If you only have one evening

1. Hou et al. Introduction and MEP Formulation — **40 minutes**
2. The three equations until you can draw them from memory, and notice there is
   no `i` in Eq 2 — **20 minutes**
3. Empirical Bayes: the weight formula and why a dead-end street with 2 deaths is
   noise — **20 minutes**
4. Overdispersion: variance 114.7 vs mean 4.98, so not Poisson — **10 minutes**
5. `src/23_mep.py`, the `mep()` function. It is 15 lines and it is the whole
   metric — **20 minutes**
6. `INTERVIEW_QA.md`, Part 1 — **30 minutes**

That is about two and a half hours and it covers everything you are likely to be
asked in the first twenty minutes.
