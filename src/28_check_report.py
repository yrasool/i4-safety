"""
Step 28 - verify REPORT.md against the pipeline's own outputs.

WHY THIS EXISTS. The first draft of the report claimed the crash term was
"10.5% of what MEP already charges driving", an asymmetry of "90 to 1". Both
numbers were real, both had been printed by a script, and both were wrong for
this report: they came from step 05, which computes a FATALITY-ONLY rate, while
the report uses the KSI rate from step 04. On the KSI rate the figures are 22.1%
and 188 to 1.

Nothing detected it. The sentence read fluently, the numbers were plausible, and
they were even internally consistent with each other. It was caught only by
recomputing them by hand.

This project has made that error at least five times, in both directions: prose
that said "does not flip" when the number flipped, "26% on foot" against a
number that said otherwise, "within 1% of each other" when the gap was 9.9%.
The pattern is always the same. A figure is correct when written and then an
input changes upstream, or a figure is lifted from the wrong step.

So every load-bearing number in the report is recomputed here from the CSVs the
pipeline wrote, and checked to be PRESENT IN THE TEXT as written. A number that
has drifted fails the run.

Exit code 1 on any mismatch, so this can gate a commit.
"""

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import (GAMMA, MEP_DEFAULTS, MIDPERIOD_POP,  # noqa: E402
                       COST_PER_PERSON, YEARS)

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"
REPORT = ROOT / "REPORT.md"


def rows(p):
    with p.open(encoding="utf8") as fh:
        return list(csv.DictReader(fh))


def main():
    if not REPORT.exists():
        sys.exit(f"FAIL: {REPORT} does not exist.")
    text = REPORT.read_text(encoding="utf8")

    cas = {r["mode"]: r for r in rows(INTERIM / "casualties_by_mode.csv")}
    inj = {r["mode"]: r for r in rows(FINAL / "injury_cost_by_mode.csv")}
    val = rows(FINAL / "validation.csv")
    occ = {r["geography"]: r for r in rows(INTERIM / "occupancy.csv")}
    eq = rows(FINAL / "equity_2020.csv")

    K = sum(int(v["K"]) for v in cas.values())
    A = sum(int(v["A"]) for v in cas.values())
    cost = sum((int(v["K"]) * COST_PER_PERSON["K"]
                + int(v["A"]) * COST_PER_PERSON["A"]) / YEARS
               for v in cas.values())
    r_drive = float(inj["vehicle_occupant"]["cost_per_pmt"])
    r_drive_fatal = float(inj["vehicle_occupant"]["cost_per_pmt_fatal_only"])
    # READ, not declared. A hardcoded 0.0010 here disagreed with step 05's
    # computed 0.0010477 by 4.6%.
    with (FINAL / "injury_rate_by_mode.csv").open(encoding="utf8") as fh:
        r_transit = next(float(r["r"]) for r in csv.DictReader(fh)
                         if r["mode"] == "transit")

    # TWO SHARES, ON DIFFERENT BASES, AND THEY MUST NOT BE MIXED.
    # r_drive is KSI; r_transit is structurally fatality-only. A draft compared
    # 22.1% against 0.12% and reported an asymmetry of 188 to 1. Like-for-like
    # it is 11.7% against 0.12%, about 95 to 1 - serious injuries are 47% of
    # the drive rate, so the mismatch nearly doubled the headline.
    share_d = abs(GAMMA * r_drive / (GAMMA * MEP_DEFAULTS["drive"]["c"]))
    share_d_fatal = abs(GAMMA * r_drive_fatal
                        / (GAMMA * MEP_DEFAULTS["drive"]["c"]))
    share_t = abs(GAMMA * r_transit / (GAMMA * MEP_DEFAULTS["transit"]["c"]))
    nonmotor = (int(cas["walk"]["K"]) + int(cas["bike"]["K"])) / K

    def v(test, case):
        for r in val:
            if r["test"] == test and r["case"] == case:
                return r
        sys.exit(f"FAIL: validation.csv has no row {test}/{case}. Rerun step 26.")

    losses = [float(r["loss_fraction"]) for r in eq if r["loss_fraction"]]

    # Step 34's output. Loaded separately because it is keyed metric/year
    # rather than test/case, and because a missing file here must be a loud
    # failure: the report quotes these as a defence of the denominator.
    exy_path = FINAL / "exposure_by_year.csv"
    if not exy_path.exists():
        sys.exit("FAIL: exposure_by_year.csv missing. Run step 34.")
    exy = rows(exy_path)

    def vy(metric, year):
        for r in exy:
            if r["metric"] == metric and r["year"] == str(year):
                return float(r["value"])
        sys.exit(f"FAIL: exposure_by_year.csv has no {metric}/{year}. "
                 f"Rerun step 34.")

    # Held outside the f-string below: the scenario label contains an
    # apostrophe, and nesting it inside an f-string expression is a syntax
    # error on this interpreter.
    under_flat = vy("rate_understatement", "2025 held at 2024's level")

    # Step 35's output. Q10 quoted a 93% that no script produced; these four
    # figures are the reason that cannot recur.
    exx_path = FINAL / "externality.csv"
    if not exx_path.exists():
        sys.exit("FAIL: externality.csv missing. Run step 35.")
    exx = rows(exx_path)

    def vx(metric, mode):
        for r in exx:
            if r["metric"] == metric and r["mode"] == mode:
                return float(r["value"])
        sys.exit(f"FAIL: externality.csv has no {metric}/{mode}. Rerun 35.")

    checks = [
        ("total deaths", f"{K:,}", r"deaths|total"),
        ("total serious injuries", f"{A:,}", r"serious|total"),
        ("annual cost", f"${cost / 1e9:.2f}B", r"per year|billion|\$10"),
        ("cost per resident", f"${cost / MIDPERIOD_POP:,.0f}", r"per resident"),
        ("ped and cyclist share of deaths", f"{nonmotor:.1%}",
         r"pedestrian|cyclist"),
        ("r_drive", f"${r_drive:.4f}", r"r_drive|passenger-mile"),
        ("crash term vs driving cost, KSI", f"{share_d:.1%}",
         r"charges driving|share of what MEP"),
        ("crash term vs transit cost", f"{share_t:.2%}",
         r"charges transit|of transit's|transit cost term"),
        ("crash term vs driving, FATALITY-ONLY", f"{share_d_fatal:.1%}",
         r"like-for-like|fatality-only|fatality only"),
        ("like-for-like asymmetry",
         f"{share_d_fatal / share_t:.0f} to 1", r"asymmetr|to 1"),
        ("occupancy, regional",
         f"{float(occ['South Atlantic 2022']['occupancy']):.3f}",
         r"occupancy"),
        ("occupancy, national", f"{float(occ['US 2022']['occupancy']):.3f}",
         r"occupancy|US figure"),
        ("bike share of the drop",
         f"{float(v('attribution', 'bike')['value']):.1%}", r"^\| bike|bike"),
        ("drive share of the drop",
         f"{float(v('attribution', 'drive')['value']):.1%}",
         r"^\| drive|drive"),
        ("walk share of the drop",
         f"{float(v('attribution', 'walk')['value']):.1%}", r"^\| walk|walk"),
        ("injury-only change",
         f"{abs(float(v('delay', 'injury only')['value'])):.1%}",
         r"injury only"),
        # These were "both (lo)/(hi)" - injury AND delay - until the delay
        # term was retired. They are now the SHIPPED rows, and the checker was
        # updated with the model rather than left pointing at labels step 26
        # no longer writes. It failed loudly when they vanished, which is the
        # behaviour wanted: a checker that silently skips a missing row is
        # worse than no checker.
        ("shipped, low",
         f"{abs(float(v('delay', 'shipped (lo)')['value'])):.1%}",
         r"with crash harm, low"),
        ("shipped, high",
         f"{abs(float(v('delay', 'shipped (hi)')['value'])):.1%}",
         r"with crash harm, high"),
        ("drive vs D5AR",
         f"{float(v('external', 'drive vs D5AR')['spearman']):.4f}",
         r"D5AR"),
        ("transit vs D5BR",
         f"{float(v('external', 'transit vs D5BR')['spearman']):.4f}",
         r"D5BR"),
        ("mean loss per block group", f"{sum(losses) / len(losses):.1%}",
         r"per block group"),
        # Step 34. The 2020 severity spike and the denominator bias are both
        # quoted in the report as arguments, which is exactly the kind of
        # figure that goes stale first: nobody rechecks a number inside a
        # paragraph that reads as settled.
        ("2020 deaths per 1,000 crashes",
         f"{float(vy('deaths_per_1000_crashes', '2020')):.2f}", r"^\| 2020"),
        ("2019 deaths per 1,000 crashes",
         f"{float(vy('deaths_per_1000_crashes', '2019')):.2f}", r"^\| 2019"),
        ("rate understatement, 2025 flat",
         f"{under_flat:.1%}",
         r"2024's level|8% to 12%"),
        ("pedestrian deaths involving a car",
         f"{vx('car_involved_share_K', 'walk'):.1%}", r"pedestrian deaths"),
        ("cyclist deaths involving a car",
         f"{vx('car_involved_share_K', 'bike'):.1%}", r"cyclist deaths"),
        ("driving, version B",
         f"${vx('r_drive_version_b', 'drive'):.4f}", r"version B|cause"),
        ("the externality",
         f"${vx('externality_per_pmt', 'drive'):.4f}", r"externality"),
        ("rate understatement, 2025 grown",
         f"{vy('rate_understatement', '2025 grown at the 2023->2024 rate'):.1%}",
         r"2023.2024 rate|8% to 12%"),
    ]

    # ANCHORED MATCHING. The previous version tested `want in text`, which is
    # presence anywhere in the file. It printed
    #     ok    mean loss per block group    20.3%
    # while "20.3%" appeared only twice in the report, both times as the NHTS
    # WORK TRIP SHARE, and the report never stated a mean loss at all. A gate
    # that matches an unrelated number in an unrelated table and reports PASS
    # is worse than no gate, because it retires the suspicion that would
    # otherwise have made someone check by hand.
    #
    # Each figure now carries an ANCHOR: a phrase that must appear on the same
    # line, or in the same table row, as the value.
    print(f"checking {len(checks)} load-bearing figures against REPORT.md")
    print(f"matching is ANCHORED - the value must appear on a line that also "
          f"mentions its subject\n")
    # A ONE-LINE WINDOW, because prose wraps. Markdown hard-wraps sentences, so
    # a figure and the phrase naming it routinely land on adjacent lines. A
    # same-line-only rule rejected two correct figures for that reason alone.
    # The window stays deliberately tight: wide enough for a wrapped sentence,
    # too narrow to reach an unrelated table.
    # NORMALISE TYPOGRAPHIC DASHES BEFORE MATCHING.
    # Markdown written by hand contains four different dash characters:
    # HYPHEN-MINUS, MINUS SIGN, EN DASH and EM DASH. A value formatted by Python
    # as "-30.1%" will never match a report that renders it as "−30.1%", and the
    # failure looks exactly like a stale figure. Verified on PRESENTATION.md,
    # where a correct -30.1% reported as MISSING purely on the minus character.
    DASHES = {"−": "-", "–": "-", "—": "-", "×": "x"}

    def norm(s):
        for a, b in DASHES.items():
            s = s.replace(a, b)
        return s

    WINDOW = 1
    lines = [norm(ln) for ln in text.split("\n")]

    def present(want, line):
        """
        Digit-boundary match. Bare `want in line` is blind to exactly the error
        class this project keeps making:

            "24.0%"  in  "-124.0%"   ->  True
            "1.65x"  in  "11.65x"    ->  True

        Demonstrated on a copy of this report: changing 24.5% to 124.5% and
        -24.0% to -124.0% left the gate printing PASS on both. An 8x, a 36.6x
        and a 3.5x error are all in this project's history, and none of them
        would have been caught. A preceding digit or decimal point disqualifies
        the match.
        """
        return re.search(rf"(?<![\d.]){re.escape(want)}", line) is not None

    bad = []
    for label, want, anchor in checks:
        pat = re.compile(anchor, re.I)
        idx = [i for i, ln in enumerate(lines) if pat.search(ln)]
        ok = any(present(want, lines[j])
                 for i in idx
                 for j in range(max(0, i - WINDOW),
                                min(len(lines), i + WINDOW + 1)))
        where = (f"{len(idx)} anchored line(s) +/-{WINDOW}" if idx
                 else "ANCHOR NOT FOUND")
        print(f"  {'ok  ' if ok else 'MISS'}  {label:<40}{want:<12}{where}")
        if not ok:
            bad.append((label, want, anchor, [lines[i] for i in idx[:2]]))

    # ---------------------------------------------------------------------
    # THE DOCUMENTS THAT GO IN THE ROOM.
    #
    # Until now this gate checked REPORT.md and nothing else. But the author
    # speaks from INTERVIEW_QA.md and PRESENTATION.md, and catches up from
    # WHAT_I_DID.md. Those three were entirely unverified - the least-checked
    # documents were the ones being read out loud.
    #
    # It cost exactly what you would expect. INTERVIEW_QA Q10 stated "93% of
    # pedestrian deaths here involve a car". Nothing computed it, the real
    # figure is 99.0%, and REPORT.md never mentioned the subject at all so
    # this gate had nothing to compare against.
    #
    # DIFFERENT RULE HERE, and the difference matters. REPORT.md must contain
    # every figure. These documents need not - a slide deck is allowed to omit
    # things. So the test is CONDITIONAL: if a document raises a subject, the
    # number beside it must be right. Silence is fine; being wrong is not.
    # A SEPARATE, TIGHTER LIST - and the reason is itself a lesson.
    #
    # Reusing all 29 anchors here produced a screenful of false alarms:
    # /deaths|total/ matched "reaches too little to move the total", and
    # /pedestrian|cyclist/ matched a bullet about exposure. Those anchors are
    # fine in REPORT.md, where the surrounding context is tight, and useless
    # in prose written to be read aloud.
    #
    # A gate that cries wolf is worse than no gate, because people learn to
    # scroll past it - the same reasoning that made the anchors necessary in
    # the first place. So this list is short and every anchor is a phrase that
    # can only mean one thing.
    SPOKEN_CHECKS = [
        ("pedestrian deaths involving a car",
         f"{vx('car_involved_share_K', 'walk'):.1%}",
         r"pedestrian deaths here involve|of pedestrian deaths"),
        ("cyclist deaths involving a car",
         f"{vx('car_involved_share_K', 'bike'):.1%}", r"cyclist deaths"),
        ("driving, version B",
         f"${vx('r_drive_version_b', 'drive'):.4f}", r"[Vv]ersion B gives"),
        ("the externality",
         f"${vx('externality_per_pmt', 'drive'):.4f}",
         r"gap is the externality|the externality:"),
        ("r_drive", f"${r_drive:.4f}", r"[Vv]ersion A gives"),
        ("mean loss per block group", f"{sum(losses) / len(losses):.1%}",
         r"per block group"),
    ]
    SPOKEN = ["INTERVIEW_QA.md", "PRESENTATION.md", "WHAT_I_DID.md",
              # Added 2026-09-14: the four explainer files. Same rule - if a
              # file raises a subject, its number must match the data.
              "MATH.md", "DATA.md", "ASSUMPTIONS_AND_CHOICES.md",
              "HOW_IT_RUNS_VS_STANDARD_MEP.md", "MEP.md", "CORRECTIONS.md", "LEARN.md", "STUDY_PLAN.md"]
    print(f"\n  the documents that go in the room "
          f"(conditional: anchor present => value must match)")
    for name in SPOKEN:
        path = ROOT / name
        if not path.exists():
            print(f"    -- {name} not found, skipped")
            continue
        dlines = [norm(ln) for ln in path.read_text(encoding="utf8").split("\n")]
        checked = wrong = 0
        for label, want, anchor in SPOKEN_CHECKS:
            pat = re.compile(anchor, re.I)
            idx = [i for i, ln in enumerate(dlines) if pat.search(ln)]
            if not idx:
                continue          # the document does not raise it. Allowed.
            checked += 1
            if not any(present(want, dlines[j]) for i in idx
                       for j in range(max(0, i - WINDOW),
                                      min(len(dlines), i + WINDOW + 1))):
                wrong += 1
                bad.append((f"{name}: {label}", want, anchor,
                            [dlines[i] for i in idx[:2]]))
        flag = "ok  " if not wrong else "MISS"
        print(f"    {flag}  {name:<22}{checked:>3} subject(s) raised, "
              f"{wrong} with a figure that does not match")

    # META-TESTS. The previous version of this block was a tautology: it
    # searched for "$999.99" with a bare `in` and never invoked the matcher at
    # all, so it was always True. It was the same failure this file exists to
    # catch, living inside the file. These call `present()` on cases whose
    # answers are known.
    print(f"\n  meta-tests on the matcher itself:")
    cases = [
        ("exact value present", "24.0%", "| injury only | -24.0% |", True),
        ("value absent", "$999.99", "r_drive is $0.1059 per mile", False),
        ("ORDER OF MAGNITUDE WRONG", "24.0%", "| injury only | -124.0% |",
         False),
        ("decimal shifted", "1.65x", "the ratio is 11.65x", False),
        ("negative sign is fine", "26.3%", "with crash harm, low -26.3%", True),
    ]
    meta_ok = True
    for name, want, line, expect in cases:
        got = present(want, line)
        good = got == expect
        meta_ok &= good
        print(f"    {'ok  ' if good else 'FAIL'}  {name:<26}"
              f"want {want:<9} in {line[:34]!r} -> {got}")
    if not meta_ok:
        sys.exit("FAIL: the matcher does not behave as specified. Its verdicts "
                 "above are meaningless.")

    if bad:
        print(f"\nFAIL: {len(bad)} figure(s) in REPORT.md do not match the "
              f"pipeline output:")
        for label, want, anchor, hits in bad:
            print(f"\n    {label}")
            print(f"      the data says   {want}")
            print(f"      anchor          /{anchor}/")
            for h in hits:
                # ASCII-fold before printing. The failure printer itself
                # crashed on a U+2192 arrow under the Windows cp1252 console -
                # a gate that dies while reporting a failure reports nothing.
                safe = h.strip()[:90].encode("ascii", "replace").decode("ascii")
                print(f"      report line     {safe}")
        print("\nEither the report is stale or a step was rerun with different "
              "inputs.\nDo not publish until every line above reads ok.")
        sys.exit(1)

    print(f"\nPASS - every checked figure in REPORT.md matches the CSV the "
          f"pipeline wrote.")


if __name__ == "__main__":
    main()
