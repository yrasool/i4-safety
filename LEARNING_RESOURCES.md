# Learning resources

Every item names **the exact section to read**, **what line of our code it
explains**, and **which interview question it answers**.

Interview questions referenced as **Q1–Q17** are in `INTERVIEW_QA.md`.

Nothing here is listed unless I verified it exists. Where I am approximating a
chapter number rather than certain of it, I say so.

---

# EVERY LINK, IN ONE PLACE

All checked on 9 Sept 2026. **Free** unless marked otherwise.

## The four-hour version

| what | link |
|---|---|
| Hou et al., the MEP paper | on disk: `data/raw/osti_1531145_mep.txt` · also https://www.osti.gov/servlets/purl/1531145 |
| Robinson, empirical Bayes with baseball | http://varianceexplained.org/r/empirical_bayes_baseball/ |
| FDOT South Florida MEP report, §3.8 | on disk: `data/raw/fdot_mep_report.txt` |
| our `mep()` function | `src/23_mep.py` |

## Python

| what | link |
|---|---|
| McKinney, *Python for Data Analysis* 3e | https://wesmckinney.com/book/ |
| NumPy broadcasting rules | https://numpy.org/doc/stable/user/basics.broadcasting.html |
| scipy sparse graph routines | https://docs.scipy.org/doc/scipy/reference/sparse.csgraph.html |
| Grus, *Data Science from Scratch* 2e | **paid** · O'Reilly, ISBN 978-1492041139 |
| Slatkin, *Effective Python* 2e | **paid** · ISBN 978-0134853987 |

## Statistics

| what | link |
|---|---|
| Robinson's full empirical Bayes series | http://varianceexplained.org/r/ (posts titled "Understanding…") |
| Robinson's e-book | **paid** · https://gumroad.com/l/empirical-bayes |
| Efron & Morris, Stein's Paradox (1977) | https://efron.ckirby.su.domains/other/Article1977.pdf |
| McElreath, *Statistical Rethinking* lectures | https://www.youtube.com/@rmcelreath — find the count-model / "God Spiked the Integers" lecture in the playlist |
| Cameron & Trivedi, *Regression Analysis of Count Data* | **paid** · Cambridge, ISBN 978-1107667273 |

## Road safety

| what | link |
|---|---|
| USDOT Benefit-Cost Analysis Guidance | https://www.transportation.gov/mission/office-secretary/office-policy/transportation-policy/benefit-cost-analysis-guidance — *blocks automated checks, opens fine in a browser* |
| FHWA safety performance functions | https://highways.dot.gov/safety — search "safety performance function" |
| Highway Safety Manual | **paid** · AASHTO. Free FHWA summaries cover Part C. |
| Hauer, *Observational Before-After Studies* | **paid** · his papers are free: search "Hauer regression to the mean road safety" |

## Accessibility and transport

| what | link |
|---|---|
| Levinson et al., *Elements of Access* | https://ses.library.usyd.edu.au/handle/2123/21628 |
| Levinson et al., *Transport Access Manual* | https://transportist.org/2020/12/01/transport-access-manual-a-guide-for-measuring-connection-between-people-and-places/ |
| Geurs & van Wee (2004) | https://projectwaalbrug.pbworks.com/f/Transp+Accessib+-+Geurs+and+Van+Wee+(2004).pdf |
| **Cui & Levinson, full cost accessibility** | https://jtlu.org/index.php/jtlu/article/download/1495/1590 |
| Cui & Levinson, the 2018 framework paper | https://www.jtlu.org/index.php/jtlu/article/view/1042/1105 |
| Levinson's blog | https://transportist.org |
| Jarrett Walker, *Human Transit* | https://humantransit.org |

## Algorithms

| what | link |
|---|---|
| Bast et al., Route Planning in Transportation Networks | https://arxiv.org/abs/1504.05140 |
| **Delling et al., RAPTOR** | https://www.microsoft.com/en-us/research/wp-content/uploads/2012/01/raptor_alenex.pdf |
| GTFS specification | https://gtfs.org/schedule/reference/ |

## Spatial data and habits

| what | link |
|---|---|
| *Geocomputation with R* | https://r.geocompx.org |
| *Geocomputation with Python* | https://py.geocompx.org |
| Gelman's blog | https://statmodeling.stat.columbia.edu |

---

# THE FOUR-HOUR VERSION

If you read nothing else.

### 1. Hou et al. (2019), the MEP paper — 45 min
**File:** `data/raw/osti_1531145_mep.txt` (already on disk)
**Read:** "INTRODUCTION" and "MEP METRIC FORMULATION" sections only. Skip the
literature review on a first pass.
**You will be able to answer:** Q9 (why block groups not pixels), and the
opening "explain MEP to me".
**The line to notice:** in Equation 2, `M_ikt = α·e_k + β·t + σ·c_k`, there is
**no `i` on the right-hand side.** All of MEP's geography lives in Equation 1.
That single fact explains Q8 entirely.

### 2. David Robinson, "Understanding empirical Bayes estimation (using baseball statistics)" — 30 min
**Free:** http://varianceexplained.org/r/empirical_bayes_baseball/
**Read:** the whole post, it is one blog post.
**Explains:** `src/29_spf_eb.py` lines computing `w = 1/(1 + k*mu)` and
`n_eb = w*mu + (1-w)*y`.
**You will be able to answer:** Q3, and specifically why a dead-end street with
2 deaths is not the most dangerous road in Tampa Bay.
**The sentence to steal:** a player who went 3-for-3 is not a better hitter than
one who went 200-for-600. Substitute "road with 2 crashes" and you have our
argument.

### 3. FDOT BDV29-977-66, §3.8 "Test Run Results" — 15 min
**File:** `data/raw/fdot_mep_report.txt`, search for `103.01`
**Read:** the two paragraphs around "SERPM network MEP 11983" and "TomTom
network MEP 122.35".
**You will be able to answer:** Q5, the hardest question in the set, by quoting
their own report back at them.

### 4. Our own `src/23_mep.py`, the `mep()` function — 30 min
**Read:** just that one function. It is about 15 lines.
**Why:** it is the entire metric. If you can read those 15 lines and say what
each does, you can answer any "how did you implement it" question.

---

# 1. PYTHON

## Joel Grus, *Data Science from Scratch*, 2nd ed. (O'Reilly, 2019)

The one you asked about. It builds everything in plain Python with no libraries,
which is the right preparation because `29_spf_eb.py` writes its own likelihood
function instead of calling a stats package.

| chapter | what it gives you | where it shows up here |
|---|---|---|
| **Ch 5, Statistics** | mean, variance, correlation from scratch | the `variance 114.7 vs mean 4.98` line in `29_spf_eb.py` |
| **Ch 6, Probability** | distributions, what a likelihood is | `nb_negloglik()` |
| **Ch 8, Gradient Descent** | how optimisers find a minimum | `scipy.optimize.minimize` in `29_spf_eb.py` |
| **Ch 14, Simple Linear Regression** | fitting, residuals | the county R² in `26_validate.py` |
| **Ch 15, Multiple Regression** | design matrices | `np.linalg.lstsq` on county dummies |

**Skip** the machine learning chapters (16–19). Nothing here uses them.

## Wes McKinney, *Python for Data Analysis*, 3rd ed.
**Free online:** https://wesmckinney.com/book/

Read **after** Grus. Grus makes you build it; McKinney teaches the tools.

- **Ch 4, NumPy Basics** — arrays, vectorised operations. This is 80% of our code.
- **Ch 5–8, pandas** — read only if you want to modify `04_injury_cost.py` or
  `27_equity.py`. Most of our code deliberately avoids pandas on large files.

## NumPy broadcasting rules
**Free:** https://numpy.org/doc/stable/user/basics.broadcasting.html
**Read:** the whole page, it is short.
**Explains:** why `23_mep.py` line with `r_drive if r_drive_i is None else
r_drive_i` works whether `r` is a single number or a 2,170-length array.
**Why it matters:** broadcasting is the one NumPy feature that gives you a wrong
answer rather than an error.

## scipy.sparse.csgraph docs
**Free:** https://docs.scipy.org/doc/scipy/reference/sparse.csgraph.html
**Read:** the `dijkstra` function signature, specifically the `indices` and
`limit` arguments.
**Explains:** `21_isochrones.py`. The `limit=MAX_MIN*60` argument is why 2,170
shortest-path searches finish in four minutes — and it is also the cause of the
truncation in Q4.

---

# 2. STATISTICS

## Empirical Bayes — read these three in order

**(a) David Robinson's blog series** · **free**
http://varianceexplained.org/r/empirical_bayes_baseball/

Ten posts. Read the first four:
1. "Understanding the beta distribution (using baseball statistics)"
2. "Understanding empirical Bayes estimation"
3. "Understanding credible intervals"
4. "Understanding the Bayesian approach to false discovery rates"

Posts 1–2 are what our code does. The R does not matter; the reasoning does.

**(b) Efron & Morris (1977), "Stein's Paradox in Statistics", *Scientific
American*** · **free PDF, search the title**

Six pages. Shows that shrinking individual estimates toward a common mean beats
using them raw — startling until you see it, and exactly what we do to 2,848
road segments.

**(c) Ezra Hauer, *Observational Before–After Studies in Road Safety* (1997)**

**Read:** the chapters on regression to the mean and the Empirical Bayes method.
This is where EB entered road safety.
**If the book is hard to get:** search "Hauer regression to the mean road safety"
— his papers cover the same ground in ~15 pages, many free.
**Answers:** Q3, and the follow-up "why not just rank by crash rate?"

## Count data — Poisson vs negative binomial

**Richard McElreath, *Statistical Rethinking*, 2nd ed.**
**Lectures free on YouTube** — search "Statistical Rethinking 2023 McElreath"

- **Lecture on Poisson / count GLMs** (it is in the second half of the course,
  around lectures 11–12 in most years — check the playlist titles rather than
  trusting my numbering)
- **Book Ch 11, "God Spiked the Integers"** — count regression

**Explains:** why `29_spf_eb.py` uses a negative binomial and not Poisson.
**The number to remember:** our variance is 114.7 against a mean of 4.98, a ratio
of 23. Poisson assumes that ratio is 1.

**Cameron & Trivedi, *Regression Analysis of Count Data*, 2nd ed. (2013)**
Only if you want the formal version. **Ch 1** motivates count models; the
negative binomial derivation is in the early chapters. This is reference, not
reading.

## Selection bias

**Search:** "selection on the dependent variable" or "Heckman selection bias"
— any econometrics lecture notes will do.

**Explains:** why fitting our safety curve on only the 2,427 roads that had
crashes biased `b` from its true 0.7892 down to 0.7300.
**Answers:** Q3.
**You do not need the maths.** You need the reflex: *what got excluded from this
sample, and was it excluded for a reason connected to what I am measuring?*

---

# 3. ROAD SAFETY

## Highway Safety Manual (AASHTO), Part C

**The specific bit:** Part C, Appendix A, section on the Empirical Bayes method.
That is the exact `w = 1/(1 + k·μ)` formula in our code.

**Getting it free:** the full HSM is expensive, but search **"FHWA safety
performance functions SPF Part C Empirical Bayes"** — FHWA and several state
DOTs publish free guides covering the same material.

**Answers:** Q3, specifically "is that the HSM weight formula?" (yes).

## USDOT Benefit-Cost Analysis Guidance

**Free:** search "USDOT Benefit-Cost Analysis Guidance for Discretionary Grant
Programs"
**Read:** Appendix A, Table A-1a, and **the column definitions above it.**

**This is where $13,700,000 and $1,302,300 come from.**

**Read the definitions, not just the numbers.** The difference between "value per
injured **person**" and "value per **crash**" is the 8× error this project made
and fixed. That distinction is the whole of Q17's first example.

## KABCO

**Search:** "KABCO injury classification scale"
Five minutes. K killed, A incapacitating, B non-incapacitating, C possible, O
none. We use K and A only.
**Answers:** "why KSI and not all severities?" — because pedestrians and cyclists
barely appear at B and C, so including them makes the modes non-comparable.

---

# 4. ACCESSIBILITY AND TRANSPORT

## Levinson, Marshall & Axhausen, *Elements of Access*
**Free PDF:** https://ses.library.usyd.edu.au/handle/2123/21628

336 pages, heavily illustrated. **Do not read it cover to cover.** Skim for the
sections on accessibility and on land use / transport interaction. It is the best
free introduction that exists.

## Levinson et al., *Transport Access Manual* (2020)
**Free:** https://transportist.org/2020/12/01/transport-access-manual-a-guide-for-measuring-connection-between-people-and-places/

**This is the most directly relevant book to what we built** — a committee-written
guide on how to actually measure accessibility. If you read one transport book,
this one.

## Geurs & van Wee (2004)
"Accessibility evaluation of land-use and transport strategies: review and
research directions", *Journal of Transport Geography* 12(2), 127–140.
**Free PDF:** https://projectwaalbrug.pbworks.com/f/Transp+Accessib+-+Geurs+and+Van+Wee+(2004).pdf

**Read:** the section classifying accessibility measures, and the four components
(land-use, transportation, temporal, individual).

**Answers:** "where does MEP sit in the accessibility literature?" — it is
location-based, a hybrid of isochrone/cumulative-opportunity and gravity, because
it counts opportunities within time bands *and* weights them by a decay function.

## Cui & Levinson (2019), "Full cost accessibility"
*Journal of Transport and Land Use* 12(1), 649–672. **JTLU is open access —
free at jtlu.org.**

**Read:** the framework section defining internal vs external costs.

**This is our theoretical cover for adding a safety term at all**, and our
external benchmark — their $0.040 per vehicle-km is what our $0.1591 per
vehicle-mile is checked against (ratio 1.65×).
**Answers:** Q7 and Q10.

## Skabardonis, Varaiya & Petty (2003)
"Measuring Recurrent and Nonrecurrent Traffic Congestion", *TRR* 1856.

**The finding:** incident-related delay is **13–30% of peak-period
congestion**, measured with loop detectors.

**We no longer use it — read it anyway.** The delay term it supported was
deleted, not because this paper is weak (it is the strongest source in the
category; it replaced three guesses, including a 12.5% figure from a **Broward
County** study) but because our own code could not re-derive the minutes. Know
it well enough to explain that distinction if it comes up: the literature was
fine, the plumbing was not. See Q6.

## Blogs

**David Levinson — transportist.org** · free
The centre of the accessibility research world. He is also a co-author of Cui &
Levinson, which is our benchmark.

**Jarrett Walker — humantransit.org** · free
**Read specifically:** anything on **frequency versus coverage**. That framing
explains our finding that 60% of Tampa Bay block groups reach nothing by bus —
it is a coverage choice, not a failure.

---

# 5. ALGORITHMS

## Bast et al. (2016), "Route Planning in Transportation Networks"
**Free:** https://arxiv.org/abs/1504.05140

**Read:** Section 2 (Dijkstra and basic techniques) and the section on graph
contraction. Roughly the first 15 pages.

**Explains:** `20_build_graph.py`. Why we collapse 927k OSM points to 297k
junctions — contraction is the standard first move, and it is what makes 2,170
searches finishable.

## Delling, Pajor & Werneck (2015), "Round-Based Public Transit Routing"
*Transportation Science* 49(3). RAPTOR.

**Read:** the algorithm description, first ~4 pages. The round structure is all
you need.
**Explains:** `22_transit.py`, the `for _ in range(MAX_ROUNDS)` loop. Round k =
best arrival using at most k−1 transfers.

## GTFS specification
**Free:** https://gtfs.org/schedule/reference/

**Read:** the field definitions for `stops.txt`, `stop_times.txt`, `trips.txt`,
`calendar.txt`, `calendar_dates.txt`. One hour.

**Explains:** why we run on a **Thursday** — PSTA's weekday service is Mon–Thu
and HART's is Mon–Fri, which you can only see by reading `calendar.txt`. A Friday
would have silently dropped every PSTA route.

---

# 6. SPATIAL AND TRANSPORT DATA IN PRACTICE

## Lovelace, Nowosad & Muenchow, *Geocomputation with R*
**Free:** https://r.geocompx.org
**Python edition:** https://py.geocompx.org (also free)

**Read:** the **transport chapter** (Ch 13 in the R edition). It is a full case
study — routing, desire lines, network analysis on real data. Even in R it
teaches the concepts.

---

# 7. THE HABIT THAT FOUND EVERY REAL ERROR

**Andrew Gelman's blog** — https://statmodeling.stat.columbia.edu · free
**Search his site for:** "garden of forking paths".

**Why:** it is the best available training in suspecting your own results. Every
error in this project produced a plausible number and raised nothing — the 8×,
the 11× benchmark, the made-up walking distances, the checker that could not tell
24% from 124%.

**Simmons, Nelson & Simonsohn (2011), "False-Positive Psychology"** · free PDF
Short. On researcher degrees of freedom. It is the reason our pipeline writes
every choice into the code rather than a notebook.

---

# A FOUR-WEEK ROUTE

**Week 1 — vocabulary**
- *Elements of Access*, skim. Free.
- Geurs & van Wee (2004), the classification section. Free.
- Hou et al., Introduction + Formulation. On disk.

**Week 2 — the statistics that carry the project**
- Robinson's empirical Bayes posts 1–2. Free.
- Efron & Morris, Stein's paradox. Six pages, free.
- McElreath, count-model lecture. Free.

**Week 3 — the code**
- Grus, chapters 5, 6, 8, 14, 15.
- NumPy broadcasting page.
- Then read `src/23_mep.py` and `src/29_spf_eb.py` and check you recognise
  everything.

**Week 4 — depth**
- Hauer on regression to the mean.
- HSM Part C / FHWA SPF guide.
- Bast et al., first 15 pages.
- Cui & Levinson, *Full cost accessibility*. Free.

**Ongoing:** Transportist, Human Transit, Gelman.
