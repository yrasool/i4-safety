# 20-minute presentation

Fourteen slides. Roughly 80 seconds each, leaving 6 minutes for questions.

Every number here is checked by `python src/28_check_report.py`.

**Say the numbers out loud when you practise.** The whole case rests on four of
them: 3,471 · $10.7B · 25% · 79%.

---

## Slide 1 — Title

> **Pricing crash harm in NREL's Mobility Energy Productivity metric**
> Tampa Bay, FDOT District 7
> Yusra Rasool

**Say:** "I extended MEP with the one cost it doesn't charge, and it changes the
answer by a quarter."

Nothing else. Do not read the slide.

---

## Slide 2 — What MEP does

> MEP scores how much of a region you can reach.
>
> For each mode — drive, bus, walk, cycle — it charges:
> **energy · time · money**

**Say:** "It's an accessibility metric. Not how fast you can drive, but how many
actual destinations are within reach, discounted by what getting there costs
you."

**Do not explain MEP to the room.** They built it. This slide is scaffolding for
the next one.

---

## Slide 3 — The gap

> It never charges any mode for the people it kills.

Leave it on screen for a beat.

**Say:** "Under the published defaults, walking and cycling are given zero energy
and zero cost. In MEP's own terms they are free."

---

## Slide 4 — Why that matters here

> **Tampa Bay, 2019–2025**
>
> 3,471 killed · 20,305 seriously injured
> **915 died walking. 277 died cycling.**

**Say:** "So the metric recommends walking and cycling hardest in a region that
kills people doing both. That is the gap I wanted to close."

**Pause here.** This is the emotional centre of the talk and the only place you
should slow down.

---

## Slide 5 — What that costs

> **$10.7 billion a year**
> $3,092 per resident
>
> USDOT values: $13.7M per death, $1,302,300 per serious injury

**Say:** "Priced at the federal values every DOT uses for benefit-cost analysis.
That is what the metric currently treats as free."

**If asked why VSL:** it's not a moral claim, it's the number used to decide
whether a guardrail is worth building.

---

## Slide 6 — What I changed

> ```
> Eq 2   M = α·e + β·t + σ·c
>
> c  →  c + r      crash cost, $/passenger-mile
> ```
>
> **No new equation. No new weight.**

**Say:** "Crash harm is dollars per passenger-mile, which is the unit the cost
term already carries. Precedent: Garikapati et al. added ride-hailing by changing
three input values and no maths."

**This slide buys you credibility.** It says you extended the metric rather than
replacing it.

---

## Slide 7 — I had to build MEP first

> | what MEP needs | what I built |
> |---|---|
> | isochrones, 4 modes | OpenStreetMap, 827,133 junctions, own routing |
> | transit times | RAPTOR over live HART + PSTA timetables |
> | opportunities | LODES 2023, 1.57M jobs, six activity types |
> | trip frequencies | NHTS 2022, from the microdata |

**Say:** "Nobody hands you these. 177 MB of federal open data, all of it
reproducible."

**The line to land:** "The transit times are schedule-based routing on current
timetables, not an API call."

---

## Slide 8 — THE RESULT

> **Pricing crash harm removes 23.4%
> of Tampa Bay's accessibility score.**
>
> Population-weighted, MEP's own aggregation rule

**Say:** "Between a fifth and a quarter. MEP currently says this region is
that much better connected than it really is."

**Name the aggregation rule unprompted** — Hou et al. p.9. It shows you read
their method rather than taking an average.

---

## Slide 9 — Where the loss comes from

> | mode | share of the loss |
> |---|---:|
> | **cycling** | **79%** |
> | driving | 15% |
> | walking | 5% |
> | bus | 0% |

**Say:** "This surprised me. Cycling dominates because MEP prices it at zero on
both other terms, so crash cost is the *only* cost it would ever carry. Here
that's about $10 a mile, roughly ninety times driving."

**The mechanism, if asked:** a mode's share is its *reach* times its *rate*.
Walking has the higher rate but reaches too little to move the total.

---

## Slide 10 — Who bears it

> | zero-car households | MEP loss |
> |---|---:|
> | fewest | 22.8% |
> | ↓ | 23.4% |
> | ↓ | 25.5% |
> | most | **27.2%** |

**Say:** "The households with no car are the ones left walking, cycling and
taking the bus. Those are exactly the modes whose cost the metric was hiding."

**Say the caveat yourself:** "The bottom two quintiles are tied, so it's a
gradient not a clean ladder. And it's an association — dense places have both
more carless households and more walking."

---

## Slide 11 — Does it behave like MEP?

> **NREL's own published validation scenarios**
>
> | | required | this build |
> |---|---|---|
> | fuel economy ×3 | score ↑ | **+27.6%** |
> | driving faster | score ↑ | **↑** |
> | driving cost ×3 | score ↓ | **−30.1%** |
> | nothing changed | identical | **identical** |

**Say:** "They published the checks they used to convince themselves the
formulation works. I ran them. The bottom two are mine — a score that rises
whenever anything improves might just rise on everything, so cost has to push
the other way."

**This is your strongest slide.** It is evidence the implementation *is* MEP,
tested against their own stated criteria.

**Caveat to volunteer:** the travel-time scenario is truncated at 40 minutes, so
it's a direction check, not a magnitude.

---

## Slide 12 — What I got wrong

> - Made-up walking and cycling distances — off by 3×
> - Compared deaths-and-injuries against deaths-only — doubled a gap
> - Wrong benchmark activity — **every score 11× too large**
> - A checker that couldn't tell 24% from 124%

**Say:** "Every one of those produced a plausible number and raised nothing. So
the fixes are mechanical, not 'be more careful.'"

**Do not skip this slide.** It is the one that separates you from someone who
presents a clean result they haven't stress-tested.

---

## Slide 13 — The limit of the map

> Loss surface is **93.0% mode mix**, 7.0% local crash risk (routed).
> County explains 23% of route risk; it explained 77% before routing.
>
> **This is not a crash-risk map, and I don't present it as one.**

**Say:** "With one crash rate per mode, the loss at every neighbourhood reduces
algebraically to its mode shares. I proved that and verified it to 6e-16. Four
numbers cannot make a 2,170-row map. I built place-varying driving risk with a
safety performance function and Empirical Bayes, and it broke the identity — but
only by 7.0% of the variance. So I call it a first-order county-scale
correction."

**This slide wins the room.** Almost nobody volunteers the ceiling on their own
result.

---

## Slide 14 — What's next

> 1. **Pedestrian and cyclist exposure by place** — 84% of the loss is still
>    a regional average
> 2. **Stratify the safety curve by road type** — HSM practice
> 3. **Validate Level of Traffic Stress against observed crashes** —
>    barely done in the literature, and I have the data for it

**Say:** "The third one isn't a fix, it's a study. LTS scores how a road is
built; crash records score what happened. Almost nobody has checked whether they
agree, and if a corridor scores well on LTS and kills people anyway, that's worth
knowing."

**End on this.** It turns a defence into a proposal.

---

# Delivery notes

## Timing

| slides | minutes |
|---|---|
| 1–5, the setup | 5 |
| 6–7, the method | 3 |
| 8–10, the result | 5 |
| 11–13, the validation and the limits | 5 |
| 14, next | 2 |
| **questions** | **6** |

If you're running long, **cut slide 7** and say the data sources in one sentence
over slide 6. Never cut 11, 12 or 13.

## The four numbers to know cold

```
3,471    people killed
$10.7B   a year, treated as free
25%      of the score removed
79%      of that from cycling
```

## Three things to say unprompted

They are the difference between presenting and defending.

1. **"Population-weighted, which is MEP's own rule."** Slide 8.
2. **"The bottom two quintiles are tied."** Slide 10.
3. **"This is not a crash-risk map."** Slide 13.

Each one takes a question out of their hands.

## If they interrupt

They will. Answer briefly and return to the deck. Anything longer than two
sentences, say: *"I have a slide on that"* if you do, or *"can I come back to
that at the end"* if you don't.

Full answers to seventeen likely questions are in `INTERVIEW_QA.md`.

## What not to do

- **Do not explain MEP to them.** Slides 2 and 3 exist only to set up slide 4.
- **Do not quote an absolute MEP score.** Percentages and rankings only.
- **Do not claim the travel-time scenario magnitude.** It's truncated.
- **Do not resurrect the delay term.** It is deleted. If someone raises
  congestion, the answer is that there is no time-side term left to double
  count — see Q6. Volunteering that you cut it, and that the headline shrank
  2.4 points as a result, is a stronger move than defending it ever was.
