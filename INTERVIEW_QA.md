# The questions they will ask, and what to say

For a 40-minute technical defence with people who built MEP.

Answers are in plain language. Every number here is checked by
`python src/28_check_report.py`.

**The three rules that hold all of this together:**

1. **Concede first, always.** Agree with the criticism, then say what you did so
   it does not sink the project.
2. **Say the bad number before they find it.** They will find it.
3. **Never defend something you cannot reproduce.** Drop it instead.

---

# Part 1 — the five you are most likely to lose on

These are ranked by how much damage they do. Learn these first.

---

## Q1. "Only driving risk varies by place. What about the other 84%?"

**This was the strongest attack on the project. I went and did the work, and the
answer is now a finding rather than a concession.**

### What they mean

Driving risk varies by neighbourhood. Driving is **15%** of the loss. Cycling is
**79%**, walking **5%** — and those carried one regional number.

### What you say

> "I built it, and it does not work — which is itself the answer.
>
> Two datasets made it possible. The crash file carries latitude and longitude,
> so every pedestrian and cyclist casualty can be placed directly: 913 of 915
> walk deaths and 277 of 277 bike deaths, with 0.1% dropped. And ACS table
> B08301 is published at block group level, giving walk and cycle commute share
> per neighbourhood as an exposure allocator.
>
> Then I fitted the safety performance function, and the elasticity came out at
> **0.017**. Effectively zero. Resident walking does not predict where
> pedestrians are struck.
>
> So I tested five other allocators. Nearby road traffic volume is the best, and
> it predicts pedestrian casualties **twelve times better** than resident
> walking — twenty-two times for cycling. But it still only reaches 0.21, against
> 0.79 for the road-segment model in the driving work.
>
> The reading is: **people walk where they live, and are struck where they cross
> arterials.** Those are different places, and no areal measure I have separates
> them well enough."

### The part that matters most

> "With an elasticity that weak, Empirical Bayes correctly shrinks almost every
> block group toward a near-constant expectation. What variation survives in the
> rate is then just one-over-exposure — arithmetic, not risk. Publishing that as
> a pedestrian risk map would repeat the identity mistake in a new costume.
>
> So the rates are written out and labelled exploratory, and the code refuses to
> substitute them into the headline."

### What would fix it

> "Counted non-motorist exposure at sub-regional geography. StreetLight,
> Replica, or FHWA's scalable risk assessment method. That is a measurement, not
> a modelling choice, and it is the single thing that would turn this from a
> documented limit into a working surface."

### Why this works

You attempted the hardest criticism, produced a quantified negative result, and
know exactly which measurement would change it. That is a stronger position than
having a spatial surface you cannot defend.

**One check that proves the work was real:** the exposure-weighted means
reconcile with the independently-computed regional rates — walk $12.65 against
$11.57–$12.49, bike $9.86 against $9.59–$11.79. Same casualties, same exposure
total, just distributed.

---

## Q2. "Your cycling number carries the whole result and it rests on 35 people."

### What they mean

Cycling is 67.8% of the answer. The cycling crash rate is deaths and injuries
divided by miles cycled. Miles cycled comes from the national travel survey —
and in our region only **35 people** reported a bike trip.

### What you say

> "35 trips in the regional cut, yes. Two things stop that being fatal.
>
> First, the national figure is computed on 298 trips and lands close: $11.79
> per mile against the regional $9.59. Two independent samples of very different
> size agreeing is worth more than either alone. I report both as a range rather
> than picking one.
>
> Second, I ran the sensitivity. Push the cycling rate down by a factor of ten
> and the total correction falls from 24% to 11.5%. It does not vanish. Of that
> floor, driving supplies about a third and it is measured by FDOT, so it is not
> in doubt.
>
> So the headline is sensitive to this input and the *finding* is not."

### Do not say

"It's fine." It is the thinnest input in the project and they know it.

---

## Q3. "What facility type is your safety curve for? Where are the standard errors?"

### What they mean

Real road-safety practice fits a separate curve for each kind of road: rural
two-lane, urban arterial, freeway. We fit **one curve for everything**.

So an interstate segment and a country lane with the same traffic and length get
the same predicted casualties. They are not the same road.

### What you say

> "One curve, no stratification, and no standard errors. Both are real gaps.
>
> What I did get right is the shape and the sample. It is a negative binomial,
> not Poisson, because the data is heavily overdispersed — variance 114.7 against
> a mean of 4.98. Poisson assumes those are equal, so it would have reported far
> more confidence than the counts support.
>
> And it is fitted on all 2,848 segments including the 47% with no casualties at
> all. An earlier version fitted only segments that had already had a crash,
> which is selection on the outcome variable. It biased the curve exactly the way
> theory says: the intercept up and the slope down, 0.73 against the true 0.79.
>
> Stratifying by road system is the obvious next step and the data supports it —
> FDOT publishes the road class."

### Why this works

You concede the gap and then show you found and fixed a subtler version of the
same class of error. That is more convincing than getting it right first time.

---

## Q4. "Your travel-time scenario — show me the destinations that became reachable."

### What they mean

We claim to reproduce their scenario where driving gets three times faster. If
driving gets faster, places that were too far away should come into range.

### What you say

> "None. Zero new destinations, and the test says so itself.
>
> My travel-time matrices stop at 40 minutes — beyond that is stored as
> unreachable, not as a number. So scaling times by 0.3 gives the identical set
> of reachable places. What the test actually measures is re-binning: the same
> destinations moving into shorter time bands.
>
> So it is a valid directional check and a lower bound, and the code refuses to
> print the magnitude as a scenario result. To run it properly I would need the
> matrix computed out to 133 minutes."

### Why this works

They will spot the truncation immediately if they know the method — and they
built it. Volunteering it turns a trap into a demonstration that you understand
your own limits.

---

## Q5. "Your scores are eight thousand. Ours are one hundred and sixty."

### What they mean

Columbus scores 162. South Florida scores 122. We score 8,241. Are we even
computing the same thing?

### What you say

> "Same metric, different destination counts, and your own report documents the
> same gap.
>
> Your South Florida work produced **122.35 with CoStar buildings and 11,983 with
> MAZ employment counts, for the same region**, and explains why: an office block
> with 500 jobs is one destination and five hundred jobs. I use LODES employment,
> so I sit on the employment scale, as your SERPM run did. My 8,241 against your
> 11,983 for a less dense region is the right ballpark.
>
> Your own conclusion on that comparison is the one I follow: 'although the
> absolute scores come in different magnitudes, the patterns align reasonably
> well.' So I report percentages and rankings only, never an absolute score."

### The bit to be honest about

> "I had this wrong until an audit. I was using **jobs** as the reference
> category for the spatial equivalency factor. Your tool's configuration says
> meals by default. That is an exact 11.05 times scalar on every score — it moved
> me from 91,094 to 8,241 and changed no percentage or ranking at all, which is
> why none of my internal tests could see it."

### Why this works

It is the single best answer in the set. You quote their own report back, and
you volunteer a mistake that only external benchmarking could catch.

---

# Part 2 — questions about the method

---

## Q6. "Does your time term already contain congestion? Are you double counting?"

**The short answer is that there is nothing left to double count.** The project
used to add crash-caused delay to travel time. That term is deleted.

> "I had a delay term. I removed it, and the headline got 2.4 points smaller
> because of it.
>
> Not because the source was weak — Skabardonis put loop detectors on real roads
> and measured incidents at 13 to 30 percent of peak congestion. I removed it
> because in my own code those minutes were a number I had typed into two files
> by hand. Nothing computed them. Everything else in the project is either read
> from a file the pipeline wrote, or declared once with its source. That one
> number was neither, so I couldn't rebuild it, and I'm not going to defend a
> number I can't rebuild.
>
> It also means I don't need the free-flow argument at all any more. That
> argument was only ever there to justify the delay term. No term, nothing to
> argue about."

**If they ask why you didn't just fix it instead:** because it wasn't worth the
work. 2.4 points out of 25. And deleting it moves the result *against* my own
conclusion — the finding got smaller, not bigger. That is the safe direction to
be wrong in.

**If they ask whether you can prove it's really off:** yes. `26_validate.py`
stops the run with an error if anyone sets the delay back above zero while the
report still says it's retired, and there's a test that fails if either file
starts declaring its own copy again. The old term's size is still measured
there, labelled `[retired]`, so the decision is on the record with a number
instead of a promise.

---

## Q7. "You're adding a value-of-life number to an out-of-pocket cost term."

> "You are right that they are different kinds of dollars. Your 48 cents a mile
> is depreciation, insurance and maintenance. Mine is society's valuation of
> risk.
>
> My defence is that your 48 cents is not out of pocket either — nobody hands
> over 48 cents when they start the car. It is a real cost, carried, not felt per
> trip. Crash risk is the same shape.
>
> If you reject that, the honest home for this is full-cost accessibility, which
> is Cui and Levinson's frame rather than yours. I would rather be told which
> frame you want than guess."

---

## Q8. "Is your block-group map a real map, or a restatement of mode share?"

**Say the number first.**

> "It is 91.1% mode mix and 8.9% local crash risk, now that driving danger follows the
> actual route to each destination. Before routing it was 1.3%, and 77% of that local risk was
> really a county effect. So it is a first-order, county-scale correction, and I
> would not present it as a crash-risk map.
>
> The reason is structural. With one crash rate per mode, the loss at every
> neighbourhood reduces exactly to its mode shares — I proved that algebraically
> and verified it to 6e-16. Four numbers cannot make a 2,170-row map.
>
> An earlier version of this project shipped exactly that map, and the test I
> wrote to prevent a repeat could not fail: I fed it the deleted map and it
> passed. The current test checks the closed form directly and carries a
> meta-test on a constructed identity."

---

## Q9. "Why block groups? We use square kilometre pixels."

> "Because everything else here is already on block groups: the crash rates, the
> vehicle-ownership data, the population, the EPA surface I validate against.
> Resampling to pixels and back would add a step with no information in it.
>
> It is a departure from your method and I would switch if comparability across
> cities mattered more than the equity analysis."

---

## Q10. "Whose cost is a pedestrian killed by a driver?"

> "Both, and you must pick one and never both. I ran it both ways — step 35.
>
> Version A charges each mode what its own travellers suffer. Version B charges
> each mode what it causes. **99.0% of pedestrian deaths here involve a car, and
> 98.6% of cyclist deaths.**
>
> Version A gives driving **$0.1059** per passenger-mile. Version B gives
> **$0.1573**, 48% more. **The gap is the externality: $0.0514 per
> passenger-mile, $2.88 billion a year.**
>
> I use A, because everything else in MEP's cost term is what the traveller
> personally carries — fuel, fare, depreciation. A metric about what you can
> reach, priced by what you bear.
>
> I nearly got this wrong in the segment work. My road segments counted everyone
> hurt, including pedestrians — that is version B — while my driving rate counts
> only people in cars, which is version A. Substituting one into the other would
> have silently changed the question. The only symptom was a rate twice as big as
> expected, which I had already explained away in a comment."

**Volunteer this, because it is the strongest part of the answer.** The headline
attribution does **not** survive the switch. Under A, cycling supplies 79% of
the loss. Under B, cycling keeps only **1.4%** of its own rate — nearly all of
that harm becomes driving's. So the convention drives the result, and I say so
rather than letting you find it.

**And the two versions check against two different published numbers.** Cui &
Levinson split safety cost into internal (borne by occupants) and external
(inflicted on non-motorists) for exactly this reason:

| | this project | Cui & Levinson | ratio |
|---|---:|---:|---:|
| version A | $0.1591/veh-mi | internal $0.0966 | 1.65x |
| version B | $0.2363/veh-mi | full $0.1521 | 1.55x |

Both near Florida's ~2x fatality rate over Minnesota's, both lower bounds
(we price K and A only; they price every severity). Two conventions agreeing
with two independent components is a stronger check than either alone.

**If pressed on where 93% came from:** it traces to a retired script,
`12_full_run.py`, where 0.927 was typed in by hand with a comment saying it was
counted from the crash file. No code that produces it survives, and it cannot be
reproduced. It is now measured at 99.0% by step 35, which is in the pipeline.

---

# Part 3 — questions about the data

---

## Q11. "Your traffic counts are one year. Your crashes are seven."

**This used to be a promise. It is now a measurement.** Step 34.

> "You are right, and 2020 is inside that window. So I went and got the actual
> yearly numbers — federal highway statistics, Table VM-2, one file per year,
> nothing typed in by hand.
>
> Florida drove 8% fewer miles in 2020 and did not get back to 2019 until 2022.
> That means the 2025 count I divide by is *larger* than the real traffic in
> most of my period. A larger denominator makes my rates look smaller. **Every
> crash rate in this project is 8 to 12 percent too low, not too high.**
>
> I left it uncorrected, and I will say why: fixing it makes my own finding
> bigger, and I would rather hand you a number I have understated than argue
> about one I have inflated. The correction is also smaller than the walk and
> bike exposure uncertainty it would sit inside, so it would be false precision."

**The arithmetic, if they want it:** the casualty numerator is identical either
way, so it cancels, and the whole comparison reduces to
`r_true / r_now = (V_2025 · YEARS) / Σ_y V_y`. No modelling, no casualty split
by year — which is fortunate, because the pipeline does not produce one.

**And the 2020 severity break, which needs no traffic data at all:**

> "Deaths per thousand crashes — exposure cancels out of that ratio completely.
> In our own five counties, 2020 had **21% fewer crashes than 2019 and 5% more
> deaths**. Severity jumped a third. That is the emptier-roads-faster-driving
> pattern everyone documented nationally, and it is in this region's own
> records rather than borrowed from a paper. It did not revert in 2021 either;
> it has been decaying since."

**The one assumption, stated:** VM-2 is statewide. I take the year-to-year
*shape* from Florida and keep the *level* from FDOT's five-county count. Before
doing that I checked the two sources are commensurable — the five counties are
14.9% of Florida's vehicle-miles against about 16% of its population.

---

## Q12. "You compare deaths-and-injuries for driving against deaths-only for buses."

> "I did, in a draft, and it nearly doubled the gap. The national transit
> database records no bus serious injuries at all — serious injury there is a
> rail concept under 49 CFR 674 — so the transit rate can only be fatality-only.
>
> Like-for-like, both fatality-only, it is 11.7% of driving's cost term against
> 0.12% of transit's, about 95 to 1. Not the 188 to 1 the draft said."

---

## Q13. "Can you rerun it?"

> "Yes. One command, 21 steps in dependency order, about half an hour. It diffs
> the headline figures before and after and fails if any moved.
>
> That check found a real defect. FDOT's road layer is live, and it gave me 2,429
> segments one day and 2,427 the next, which moved the result. Every data source
> is now saved to a file, so nothing is fetched at run time."

---

## Q14. "How do I know any of this is right?"

> "Four independent checks, each against something I did not produce.
>
> The casualty counts were re-derived from the raw 527 MB crash file by a
> separate reviewer and matched exactly. My driving crash cost reconciles to Cui
> and Levinson's Twin Cities figure at 1.65 times once units and dollar year are
> matched, and Florida's death rate per mile is about twice Minnesota's. My trip
> frequencies reproduce FHWA's published national rate of 2.28 exactly. And my
> driving isochrones correlate 0.90 with EPA's independent accessibility surface.
>
> The Cui and Levinson check took three attempts. The first version compared
> dollars per passenger-mile against dollars per vehicle-mile and printed PASS.
> The unit error was inside the test written to catch unit errors."

---

# Part 4 — the ones you can enjoy

---

## Q15. "Why should MEP have a safety term at all?"

> "Because leaving a cost out does not stay neutral about it. It prices it at
> zero.
>
> For driving, crash cost is 22% of what MEP already charges. For walking and
> cycling it is the *only* cost MEP would charge, because their energy and money
> terms are both zero by default.
>
> So as published, MEP scores walking and cycling highest in Tampa Bay. It is
> recommending them in a region where 915 people died walking and 277 died
> cycling in under seven years."

---

## Q16. "You already have Level of Traffic Stress. Why not use it?"

> "Because they measure different things, and I think the interesting work is
> comparing them.
>
> LTS scores how a road is built — lanes, speed, whether there is a buffer. It
> works everywhere, including roads where nothing has happened yet. Crash records
> score what actually happened, and only exist where there is history.
>
> What struck me is how few validations of LTS against observed crashes exist.
> The ones that do find some correlation and ask for more work.
>
> I have crash rates on 2,429 road segments with their own traffic counts. If you
> have LTS on those same roads, that comparison is a study nobody has done. If a
> corridor scores well on LTS and kills people anyway, that is worth knowing, and
> neither measure finds it alone."

**This is the answer that turns a defence into a proposal. Use it.**

---

## Q17. "What did you get wrong?"

Have this ready. It is a real question and the honest answer is your best one.

> "Several things, and the pattern is more useful than the list.
>
> I mixed per-crash cost values with person counts, which compounded to an eight
> times error. I used made-up walking and cycling distances when the survey that
> measures them was already downloaded. I published a cycling figure that
> contradicted my own script by 3.5 times, and the checker said PASS because it
> could not tell 24% from 124%.
>
> Every one of those produced a plausible number and raised nothing. So the fixes
> are not 'be more careful' — they are mechanical. Every figure in the report is
> now recomputed from the data files and matched at digit boundaries. Every check
> carries a meta-test fed a case it must fail. Nothing that the pipeline can
> compute is allowed to exist as a literal in a second file."

---

# The one-page version

If you have sixty seconds:

- MEP scores how much of a region you can reach and charges each travel mode for
  energy, time and money. **It never charges for the people it kills.**
- In Tampa Bay 3,471 people died in under seven years. Priced at federal values
  that is **$10.7 billion a year** the metric treats as free.
- I built MEP from scratch for 2,170 neighbourhoods — my own routing on
  OpenStreetMap, live bus timetables, federal jobs and travel-survey data — and
  added crash cost to the money term. **No new equation, no new weight.**
- **Pricing crash harm removes 16.2% of the region's score** - 23.0% if bikes may use any road, as standard MEP assumes.
- **Cycling supplies 79% of that**, because MEP prices cycling as free and here
  it costs about $10 a mile in crash harm.
- **It passes NREL's own published validation scenarios**, plus two I added.
- The block-group map, with driving danger routed, carries 8.9% local crash risk - nearly seven times the 1.3% of the old proximity method - of the
  variance. **It is not a crash-risk map and I do not present it as one.**
