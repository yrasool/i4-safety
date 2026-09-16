# Rules — what this project must always do

These are **hard rules**. Anyone working on the project — you, Claude, or another agent — must
follow them. Each has the reason and where it came from.

---

## 1. Data and privacy

| rule | why | from |
|---|---|---|
| **Never share or publish the Signal Four crash records**, or anything built from individual crash records | Licensed to agencies and consultants for specific projects; not yours to publish | 6 Aug, 15 Aug |
| **The project stays private.** Mention it on the resume only — **no website** | Licence | you, 15 Aug |
| **Never read or output vehicle ID numbers (VINs) or driver ages** | Personally identifying | built in from the start |
| **Keep the crash file outside the project folder** (`C:\Users\yusra\claude\traffic-data\`) | So it can't be uploaded by accident | 14 Sep |
| **GitHub repo: private, code and documents only**, allow-list `.gitignore` | Licence and size | you, 14 Sep |
| **Don't edit anything in the `F:\Yusra` / `D:\Yusra` project folders** — read only | They belong to the original project | you, 5 Aug |

## 2. Numbers

| rule | why | from |
|---|---|---|
| **Every number must be calculated by a step, or typed once in `src/constants.py` with its source** | Numbers typed in several places drifted apart; the delay term and the 93% couldn't be rebuilt | 8–10 Sep |
| **If you can't rebuild a number, you can't defend it** — delete it | The delay term | 10 Sep |
| **Every step that reads a file must come after the step that writes it** in `run_all.py` | Steps 05, 33 and 01 were missing; old files were used silently | 9–10 Sep |
| **Run `python src/28_check_report.py` and `python -m pytest tests -q` before quoting anything** | Catches numbers that don't match the data | 8 Sep onward |
| **Compare percentages and rankings only**, never raw MEP scores with other cities | The raw score depends on how places are counted | 9 Sep |
| **Never call the neighbourhood map a crash-danger map** | Only 8.9% comes from local danger (1.3% before routing) | 9 Sep, updated 16 Sep |
| **Say a result's weak point before anyone else does** | Interviewers trust honesty about limits | throughout |
| **Measure locally where data exists** — don't use a national average when a Florida figure is available | You: "you have so much data" | 7 Sep |

## 3. How to explain things

| rule | why | from |
|---|---|---|
| **Always use simple language**, assume no prior knowledge | You need to understand and defend every part | you, 8 Sep and 14 Sep ("whenever you respond to me at all") |
| **Explain why, not just what** | So you can answer follow-up questions | you, repeatedly |
| **Use small worked examples with real numbers** | Easier to follow than formulas | 14 Sep |
| **Don't repeat the same explanation in several places** | Redundancy made documents long and confusing | you, 14 Sep |

## 4. Writing for applications

| rule | why | from |
|---|---|---|
| **No AI-sounding writing**: no em dashes, no filler, sounds human | Academic and lab readers | you, 17 Aug |
| **Don't overclaim tools**: you've used ArcGIS but aren't an expert | Honesty | you, 17 Aug |
| **The telecom/infrastructure internship was Sanguine Info Tech**, never "Jio" | Factual accuracy | your resume notes |
| **Resume bullets: short, result-first**, not overly technical — but name MEP | Readers skim | you, 16 Aug |

## 5. Git and credit

| rule | why | from |
|---|---|---|
| **Commits are credited only to you (yrasool)**, no Claude co-author | Your choice | you, 14 Sep |
| **Don't push, open pull requests or make repos public without your OK** | Outward-facing actions | standing rule |
