# MEP — what it is, explained from zero

This file explains **MEP itself** — NREL's score — before any of our project. If you read
nothing else about MEP, read this.

Other files: `MATH.md` (every calculation in detail), `HOW_IT_RUNS_VS_STANDARD_MEP.md`
(how our project runs it, and how that differs from NREL), `DATA.md`,
`ASSUMPTIONS_AND_CHOICES.md`.

| part | what it covers |
|---|---|
| 1 | MEP in one sentence |
| 2 | who made it, and why |
| 3 | the big idea, with an everyday example |
| 4 | what MEP needs to be calculated |
| 5 | how the score is made, in three steps |
| 6 | MEP's default settings |
| 7 | what a score means — and what the number's size doesn't mean |
| 8 | how MEP has been used |
| 9 | how NREL checked MEP works |
| 10 | what MEP leaves out |
| 11 | how our project uses MEP |
| 12 | words to know |

---

## 1. MEP in one sentence

**MEP (Mobility Energy Productivity) scores a place by how many useful destinations people
can reach from it — giving more credit when those trips are fast, cheap and use little energy.**

---

## 2. Who made it, and why

**Who:** NREL — the **National Renewable Energy Laboratory**, a US Department of Energy lab. The
method is described in **Hou et al. (2019)**, first tried on **Columbus, Ohio**.

**Why it was invented:** older ways of judging transport mostly asked **"how fast is traffic?"** or
**"how congested are the roads?"**. Those miss what people actually care about — **can I get to
work, the shops, the doctor?** — and they ignore **energy**.

NREL wanted **one score** that answers:
- **Mobility:** how much can people reach?
- **Cost:** how much time and money does it take?
- **Energy:** how much fuel or electricity does it use?

So a city that adds a good bus line, builds bike lanes, or switches to electric buses should see its
score **go up**, and MEP can show by how much.

**Where it's been applied:** Columbus (Hou et al.), and **South Florida** — Miami-Dade, Broward and
Palm Beach — by Florida International University with NREL, for the Florida Department of
Transportation (report **BDV29-977-66**, 2023). NREL also turned it into a software tool others can run.

---

## 3. The big idea, with an everyday example

Imagine two neighbourhoods:

**Neighbourhood A:** 500 shops, restaurants and workplaces within a **10-minute** drive, bus ride or
walk.

**Neighbourhood B:** the same 500 places, but they take **40 minutes** to reach, only by car.

Both can "reach 500 places". But A is clearly **better connected** — trips are shorter, and there are
cheaper, lower-energy ways to make them.

**MEP captures that difference.** It counts reachable places, but each one counts for **less** the more
time, money and energy it takes to get there:

> **a place 10 minutes away by an efficient mode counts for a lot;**
> **a place 40 minutes away by an expensive, energy-hungry mode counts for little.**

Then it adds everything up.

---

## 4. What MEP needs to be calculated

According to NREL and the South Florida report, five kinds of input:

| input | in plain words | example source |
|---|---|---|
| **isochrones** | the area you can reach within 10, 20, 30 and 40 minutes, for each mode | a road map and bus timetables |
| **land use and employment** | what places exist, and where | a list of businesses, or job counts |
| **energy and cost per mode** | how much energy and money a mile of travel takes, by car, bus, walking, bike… | MEP's default table |
| **activity frequency** | how often people go to each kind of place | the national travel survey |
| **population density** | where people live, to weight areas | the Census |

**"Isochrone"** comes from Greek: *iso* = same, *chrone* = time. It's the line joining all the places
you can reach in the same amount of time — like a ripple spreading out from your home.

---

## 5. How the score is made, in three steps

MEP is three equations. Here they are in plain words; `MATH.md` has every detail and worked example.

### Step 1 — What can you reach?

For each area, each mode, and each time band (10, 20, 30, 40 minutes), add up the places you can reach.

But not all places count the same:
- **Common kinds of places** (like all jobs) are scaled **down**, and **rare kinds** (like arts venues) are
  scaled **up**, so no one kind swamps the rest. The reference kind is **restaurants** ("meals").
- **Places people go more often** (like shops) get **more** weight than places they rarely go (like doctors).

### Step 2 — How costly is the trip?

Each mode gets a **penalty** that grows with:
- **energy used** per mile,
- **time** (the minutes of that band),
- **money** per mile.

The penalty is turned into a **"keep" share** — how much each reachable place still counts. No penalty
keeps 100%; a big penalty keeps very little.

### Step 3 — Add it all up

> **score = places reached in each band × keep share**, added up over every mode and every time band

**One important detail:** a place is counted **once**, in the **first** time band where it's reached. A
shop 5 minutes away isn't counted again in the 20-, 30- and 40-minute bands.

**Then** areas are combined into a city score, **weighted by how many people live in each**.

---

## 6. MEP's default settings

### Energy and money cost per mode
From MEP's default table (South Florida report, Table 7):

| mode | energy (kWh per passenger-mile) | money ($ per passenger-mile) |
|---|---:|---:|
| car | 0.90 | 0.48 |
| bus | 0.65 | 0.85 |
| walking | 0 | 0 |
| biking | 0 | 0 |
| Uber / Lyft (ride-hailing) | 1.80 | 1.54 |
| dial-a-ride vans (paratransit) | 4.13 | 2.25 |

**Notice:** walking and biking cost **nothing** — no energy, no money. That's why they score so well in MEP.

### The weights in the penalty

| part | weight |
|---|---:|
| energy | −0.5 per kWh per mile |
| time | −0.08 per minute |
| money | −0.5 per dollar per mile |

### Other settings

| setting | value |
|---|---|
| time bands | 10, 20, 30, 40 minutes |
| reference kind of place | restaurants ("meals") |
| scaling basis | national totals, the same for every city |
| combining areas | weighted by population |
| bike speed (South Florida basic setup) | 12 mph, on roads except limited-access highways |

**Why 40 minutes at most?** Most everyday trips are shorter; places beyond 40 minutes add little to how
connected a place feels, and cutting off there keeps the calculation manageable.

---

## 7. What a score means — and what its size doesn't mean

**A higher score = better connected**, counting time, money and energy.

**Comparisons that work:**
- **the same place, before and after a change** — for example, adding a bus route;
- **areas within the same study** — which neighbourhoods are better or worse connected;
- **percentage changes.**

**Comparisons that don't work:** the **raw number** between studies that counted places differently.

**The proof, from the South Florida report — the same region, two data setups:**

| data used | MEP score |
|---|---:|
| a paid road map + a paid list of **places** | **122.35** |
| a traffic model's road network + **job counts** | **11,983** |

Nearly **100 times** apart — for the same region. The report found the **pattern** across the map matched
well; only the size differed. The raw number depends on **how you count places**.

---

## 8. How MEP has been used

MEP is mostly used for **"what if" studies** — change something, see how the score moves.

| study | what was changed | what happened |
|---|---|---|
| Columbus (Hou et al.) | car fuel economy tripled | score went **up** |
| Columbus (Hou et al.) | driving made faster | score went **up** |
| South Florida (FDOT report) | existing bike lanes added to the bike network (18 mph on them) | bike score **up 141%** |
| South Florida (FDOT report) | planned 2045 bike improvements | bike score up only **3%** more |
| South Florida (FDOT report) | new transit routes with electric buses | tested energy efficiency of electric buses |

MEP can also produce **mode-only** scores (just biking, just buses) and **activity-only** scores (just
shopping, just work).

---

## 9. How NREL checked MEP works

Hou et al. ran **"scenario analyses"** to make sure the score reacts the way it should:

1. **Better fuel economy** (car fuel economy tripled) → the score **must go up**, because the same trips now
   use less energy.
2. **Faster driving** (a 10-minute trip becomes 3 minutes) → the score **must go up**, because more places
   are reachable sooner.

**Why these tests matter:** if a formula reacted the wrong way to such obvious changes, its results couldn't
be trusted. They're also a way for anyone who rebuilds MEP to prove their version really is MEP. (Our
project passes both, plus two more — see `HOW_IT_RUNS_VS_STANDARD_MEP.md`.)

---

## 10. What MEP leaves out

MEP is useful, but it doesn't measure everything.

| MEP does not count | why it matters |
|---|---|
| **crash deaths and injuries** | a mode that gets people killed is charged nothing for it. **This is what our project adds.** |
| **how people actually travel** | MEP counts where you **could** go by each mode, not whether anyone does. A place you **could** bike to counts, even if nobody bikes there |
| **walking and biking costs** | they're set to zero — no energy, no money, and no danger — so they look better than they may really be |
| **who can use each mode** | someone with no car can't drive, but MEP still counts driving access for their area |
| **traffic jams**, unless the travel times include them | depends on the road data used |
| **comfort, weather, safety from crime** | a 40-minute walk in Florida heat counts the same as one on a cool day |

**The first three matter most for our project**, because in Tampa Bay walking and biking are free in MEP
but very dangerous per mile.

---

## 11. How our project uses MEP

**In one sentence:** we calculated standard MEP for Tampa Bay's five counties from scratch, then added
**one** thing — **crash cost** — to MEP's money cost.

- **Same:** MEP's equations, default settings, weights, time bands, scaling reference and population
  weighting.
- **Different data:** free sources (OpenStreetMap, Census job counts, the 2022 travel survey, real bus
  timetables) instead of paid ones.
- **The one change to the formula:**
  > **money cost → money cost + crash cost per mile**
- **Result:** Tampa Bay's MEP score drops **16.2%** once crash cost is counted — mostly because biking, which
  MEP treats as free, is very dangerous per mile here.

Full details: `HOW_IT_RUNS_VS_STANDARD_MEP.md`.

---

## 12. Words to know

| word | meaning |
|---|---|
| **MEP** | Mobility Energy Productivity — NREL's access score |
| **NREL** | National Renewable Energy Laboratory, a US Department of Energy lab |
| **mode** | a way of travelling: car, bus, walking, biking, Uber/Lyft… |
| **isochrone** | the area reachable within a set time |
| **time band** | 0–10, 10–20, 20–30 or 30–40 minutes |
| **opportunity / destination** | a place people go: work, shops, restaurants, doctors, schools, fun |
| **activity frequency** | how often people go to each kind of place |
| **passenger-mile** | one person travelling one mile |
| **kWh** | kilowatt-hour, a unit of energy (petrol and electricity can both be measured in it) |
| **spatial equivalency / scaling number** | the factor that stops common kinds of places swamping rare ones |
| **scenario analysis** | changing an input to see how the score reacts |
| **population-weighted** | areas with more people count for more |
