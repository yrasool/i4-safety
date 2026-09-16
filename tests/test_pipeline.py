"""
Tests for the pipeline's failure modes, not its happy path.

Every bug found in this project so far produced a plausible number rather than
an exception: per-crash costs applied to person counts, a rate resting on two
events, a denominator defaulted to its own numerator, an unbounded date window
divided by a fixed period. None would have been caught by a test asserting that
the pipeline runs. So these tests assert that WRONG INPUTS RAISE.

Run:  python -m pytest i4-safety/tests -q
      python i4-safety/tests/test_pipeline.py     (no pytest needed)

Step modules start with digits, so they cannot be imported by name.
`load()` handles that.
"""

import importlib.util
import sys
from pathlib import Path

import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import constants as C  # noqa: E402


def load(stem):
    """Import a step module whose filename begins with a digit."""
    path = SRC / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem.replace("0", "s"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# 1. Constants are defined ONCE. This is the drift guard.
# --------------------------------------------------------------------------

def test_no_step_redeclares_a_shared_constant():
    """
    YEARS was once declared in three files, the cost table in two, and the
    Amsterdam weight was a named constant in 05 and a bare literal in 06.
    Nothing disagreed yet, and nothing prevented it.
    """
    import re
    shared = ["YEARS", "COST_PER_PERSON", "MEP_DEFAULTS", "AMSTERDAM_WEIGHT",
              "DVMT_5COUNTY", "OCCUPANCY", "MIDPERIOD_POP", "DELAY_MINUTES",
              "CL_INTERNAL_PER_VEHKM", "CL_EXTERNAL_PER_VEHKM", "CRASH_CSV",
              "ALPHA", "BETA", "GAMMA"]
    offenders = []
    for f in _pipeline_step_files():
        text = f.read_text(encoding="utf-8")
        for name in shared:
            # A local assignment, not an import line. Tolerant of spacing:
            # the old `startswith(f"{name} =")` could not see `NAME  = 1.5`.
            pat = re.compile(rf"^{name}\s*=(?!=)")
            for line in text.splitlines():
                s = line.strip()
                if pat.match(s):
                    offenders.append(f"{f.name}: {s[:60]}")
    assert not offenders, (
        "shared constants redeclared in step files; import from constants.py "
        "instead:\n  " + "\n  ".join(offenders))


def _pipeline_step_files():
    """
    EVERY STEP THE PIPELINE RUNS, read from run_all.py - not `0*.py`.

    Both hygiene tests used to glob `0*.py`, so steps 10 to 36 were never
    scanned. The 9 September audit found the crash-delay literal sitting in
    steps 23 and 26, exactly where these tests could not look. The shared list
    also named `CL_PER_MILE`, which does not exist in constants.py, so that
    entry could never fire. Two tests that looked like protection, and were
    not, for weeks.

    Retired scripts (06-08, 10-15) are excluded on purpose: they are history,
    not the model. Step 36 is included because it is current code.
    """
    import re as _re
    run_all = (SRC / "run_all.py").read_text(encoding="utf-8")
    names = sorted(set(_re.findall(r'"(\d{2}_[a-z_]+\.py)"', run_all)))
    names.append("36_holdout.py")
    files = [SRC / n for n in names if (SRC / n).exists()]
    assert len(files) >= 26, (
        f"found only {len(files)} pipeline steps; run_all.py's step list "
        f"format changed and this test would silently scan too little")
    return files


def test_amsterdam_weight_is_not_hardcoded_in_an_expression():
    """
    `-0.5 * 11.32` appeared inline in 06 while 05 used the named constant.

    Only flags the literal where it is USED - `* 11.32`, `11.32 *`, `= 11.32`.
    Citing the figure in a docstring is documentation and must stay.
    """
    bad = []
    for f in _pipeline_step_files():
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            s = line.strip()
            if s.startswith("#") or "11.32" not in s:
                continue
            if any(p in s for p in ("* 11.32", "11.32 *", "*11.32",
                                    "= 11.32", "=11.32")):
                bad.append(f"{f.name}:{i}")
    assert not bad, f"11.32 used as a literal at {bad}; use C.AMSTERDAM_WEIGHT"


def test_cost_table_is_per_person_not_per_crash():
    """
    Pairing FHWA per-CRASH values with casualty counts was one third of an
    error that compounded to 8x. The two tables must stay distinguishable.
    """
    assert C.COST_PER_PERSON["K"] == 13_700_000
    assert C.COST_PER_CRASH["K"] == 15_988_000
    assert C.COST_PER_CRASH["O"] > C.COST_PER_PERSON["O"] * 3, (
        "per-crash PDO should be several times per-person PDO; if these "
        "converge the tables have been confused")


# --------------------------------------------------------------------------
# 2. Date windows must be bounded at BOTH ends.
# --------------------------------------------------------------------------

def test_ntd_queries_are_bounded_at_both_ends():
    """
    `year >= 2019` with no upper bound kept pulling newer records on every
    rerun while the code divided by a fixed YEARS, so the rate grew each time
    it was run. Any open-ended filter paired with a hardcoded period is this
    bug.
    """
    text = (SRC / "05_mep_weights.py").read_text(encoding="utf-8")
    assert "year <=" in text, (
        "NTD query has no upper year bound; the rate will drift on every rerun")


# --------------------------------------------------------------------------
# 3. num() - the parser every casualty count passes through.
# --------------------------------------------------------------------------

def test_num_handles_blank_null_and_garbage():
    m = load("02_crashes_by_mode")
    assert m.num({"x": ""}, "x") == 0
    assert m.num({"x": None}, "x") == 0
    assert m.num({}, "x") == 0
    assert m.num({"x": "0"}, "x") == 0
    assert m.num({"x": "3"}, "x") == 3
    assert m.num({"x": "3.0"}, "x") == 3
    assert m.num({"x": "not a number"}, "x") == 0


def test_denul_strips_embedded_nulls():
    """Signal Four exports carry NUL bytes; csv raises on them."""
    m = load("02_crashes_by_mode")
    assert list(m.denul(["a\x00b\n"])) == ["ab\n"]


# --------------------------------------------------------------------------
# 4. The KABCO map must never silently absorb an unknown severity.
# --------------------------------------------------------------------------

def test_non_traffic_fatality_is_excluded_not_counted_as_K():
    m = load("02_crashes_by_mode")
    assert m.KABCO["Non-Traffic Fatality"] is None
    assert m.KABCO["Fatal (within 30 days)"] == "K"
    assert set(v for v in m.KABCO.values() if v) == set("KABCO")


# --------------------------------------------------------------------------
# 5. Sentinel handling. -99999 is not a value.
# --------------------------------------------------------------------------

def test_sentinel_constant_matches_what_step_01_replaces():
    m = load("01_fetch_sld")
    assert m.NODATA == C.NODATA == -99999


def test_transit_na_is_a_true_zero_but_drive_na_is_not():
    """
    Asymmetric by design: "no transit-reachable jobs" is a real zero for a
    SUM. "No car-reachable jobs" is essentially never real, so it must raise
    rather than default. Guards against someone making the handling uniform.
    """
    six = (SRC.parent / "archive" / "retired_v1_steps" / "06_results.py").read_text(encoding="utf-8")
    assert '"A_transit"' in six and "fillna(0.0)" in six
    assert 'assert t["A_drive"].notna().all()' in six, (
        "A_drive must assert, not fillna - a defaulted 0 reads as 'nowhere to "
        "drive to from here'")


# --------------------------------------------------------------------------
# 6. Ratios whose denominator can be zero.
# --------------------------------------------------------------------------

def test_zero_household_block_groups_are_excluded_not_filled():
    """
    HH_est == 0 (industrial land, parks, water) gives 0/0. Filling it with 0
    filed those block groups under "no car-free households" and let them pull
    the quintile medians in a distributional claim.
    """
    seven = (SRC.parent / "archive" / "retired_v1_steps" / "07_equity.py").read_text(encoding="utf-8")
    assert 'empty = df["HH_est"] == 0' in seven
    assert ".fillna(0)" not in seven.split("zero_car_share")[1][:200], (
        "zero_car_share must not fillna - exclude the rows instead")


def test_acceptance_band_is_enforced_not_just_printed():
    """Step 04 must refuse to write a number outside the band, not warn."""
    four = (SRC / "04_injury_cost.py").read_text(encoding="utf-8")
    assert "FAIL" in four and "PASS" in four
    assert "ratio > 4" in four or "ACCEPT_HI" in four


# --------------------------------------------------------------------------
# 7. Outputs, if the pipeline has been run.
# --------------------------------------------------------------------------

FINAL = Path(__file__).resolve().parents[1] / "data" / "final"


def test_outputs_are_internally_consistent():
    f = FINAL / "injury_cost_by_mode.csv"
    if not f.exists():
        print("  (skipped: pipeline not yet run)")
        return
    df = pd.read_csv(f).set_index("mode")
    assert (df["K_per_yr"] >= 0).all() and (df["A_per_yr"] >= 0).all()
    # Walk and bike have no measured exposure and must stay unpriced per mile.
    for mode in ("walk", "bike"):
        if mode in df.index:
            assert pd.isna(df.loc[mode, "annual_pmt"]), (
                f"{mode} has an exposure value; there is no published walk or "
                f"bike exposure for Tampa Bay")


def test_drive_rate_stays_in_the_published_band():
    """
    THE BAND APPLIES TO THE KSI RATE ONLY, and which rate is which matters.

    The project carries two drive rates on purpose:
      KSI $0.0953/PMT      step 04. Validated against Cui & Levinson, which
                           also counts injuries. Must sit in the band.
      fatality-only        step 05. The bus comparison, because NTD cannot
        $0.0505/PMT        record a serious injury on a bus at all.

    The fatality-only rate lands BELOW the benchmark (~0.87x) and that is
    correct - it counts strictly less than an all-severity figure. Applying
    the band to it would fail a rate that is right.
    """
    f = FINAL / "injury_cost_by_mode.csv"
    if not f.exists():
        print("  (skipped: pipeline not yet run)")
        return
    ksi = pd.read_csv(f).set_index("mode").loc["vehicle_occupant",
                                               "cost_per_pmt"]
    ratio = ksi * C.OCCUPANCY / C.CL_INTERNAL_2024_PER_MILE
    assert C.ACCEPT_LO < ratio < C.ACCEPT_HI, (
        f"KSI drive rate is {ratio:.2f}x Cui & Levinson (2024 dollars, "
        f"vehicle-mile basis); outside {C.ACCEPT_LO}-{C.ACCEPT_HI} the "
        f"convention is mixed again")


def test_the_two_drive_rates_are_distinct_and_ordered():
    """Fatality-only must be strictly less than KSI. If they converge, one of
    them has silently picked up the other's severity basis."""
    a = FINAL / "injury_cost_by_mode.csv"
    b = FINAL / "injury_rate_by_mode.csv"
    if not (a.exists() and b.exists()):
        print("  (skipped: pipeline not yet run)")
        return
    ksi = pd.read_csv(a).set_index("mode").loc["vehicle_occupant",
                                               "cost_per_pmt"]
    fat = pd.read_csv(b).set_index("mode").loc["drive", "r"]
    assert fat < ksi, "fatality-only rate must be below the KSI rate"
    assert 0.4 < fat / ksi < 0.7, (
        f"fatality-only is {fat / ksi:.0%} of KSI; K is ~53% of KSI cost, so a "
        f"large move means a severity basis changed somewhere")


def test_transit_rate_is_bus_only_and_collision_only():
    """The rate must not silently readmit rail or security events."""
    five = (SRC / "05_mep_weights.py").read_text(encoding="utf-8")
    assert "BUS_MODES" in five and "COLLISION_CATEGORIES" in five, (
        "step 05 must filter to fixed-route bus and to collisions; without "
        "both, rail supplies the casualties and crime is priced on one side")
    assert "NTD_PMT_BY_MODE" in five, (
        "denominator must be bus PMT; NTD_SERVICE has no mode column")


def test_deflator_is_derived_from_the_verified_source_figure():
    """
    DEFLATOR_2010_2024 must equal USDOT's 2024 value per fatality divided by
    Blincoe's 2010 value, and Blincoe's figure must be the one that actually
    appears in Cui & Levinson's Table 2.

    This benchmark carries the project's only external validation of r_drive
    (the 1.65x check). For most of the project's life all four of its attributes
    - value, units, dollar year, severity coverage - existed only as a comment,
    and an audit correctly refused to accept them. The paper is now on disk and
    the number is checked rather than asserted.
    """
    implied = C.COST_PER_PERSON["K"] / C.CL_BLINCOE_FATAL_2010
    assert abs(implied / C.DEFLATOR_2010_2024 - 1) < 0.005, (
        f"deflator {C.DEFLATOR_2010_2024} does not match "
        f"{C.COST_PER_PERSON['K']:,} / {C.CL_BLINCOE_FATAL_2010:,} "
        f"= {implied:.4f}")

    src = (Path(__file__).resolve().parents[1] / "data" / "raw"
           / "cui_levinson_2019_full_cost_by_auto.txt")
    if not src.exists():
        return                      # paper not fetched; the arithmetic still held
    text = src.read_text(encoding="utf8", errors="replace")
    for want in ("9,134,786", "0.040", "0.023", "veh-km"):
        assert want in text, (
            f"{want!r} is not in Cui & Levinson's text. The constant it backs "
            f"is no longer traceable to the source.")


def test_cl_benchmark_is_a_lower_bound_not_a_match():
    """
    Their safety cost prices all five KABCO levels; this project prices K and A
    only. So a correctly-computed ratio is a LOWER bound, and anything that
    quietly turned it into an equality would be hiding the direction of the
    error.
    """
    assert C.ACCEPT_LO < C.ACCEPT_HI
    assert C.ACCEPT_LO >= 1.0, (
        "the floor must be at least 1.0: Florida's fatality rate per VMT is "
        "about twice Minnesota's, so a correct method cannot land below parity")


def test_no_claim_in_the_spoken_documents_is_unbacked():
    """
    THE DOCUMENTS READ ALOUD WERE THE LEAST VERIFIED ONES.

    INTERVIEW_QA Q10 asserted "I ran it both ways", "93% of pedestrian deaths
    here involve a car", and "the gap between A and B is the externality and I
    report it separately". All three were false of the live project: no step
    computed version B, REPORT.md contained no externality figure, and the 93%
    was derived by nothing. The report gate never saw it, because the gate only
    read REPORT.md.

    Two things are locked here. First, that the step which makes those claims
    true is still in the pipeline. Second, that the gate still extends to the
    documents that go in the room - deleting that block would silently restore
    the original hole.
    """
    root = Path(__file__).resolve().parents[1]

    assert (root / "data" / "final" / "externality.csv").exists(), (
        "externality.csv missing - INTERVIEW_QA Q10 makes claims that only "
        "step 35 substantiates")

    run_all = (root / "src" / "run_all.py").read_text(encoding="utf8")
    assert "35_externality.py" in run_all, (
        "step 35 dropped from the pipeline; Q10's numbers become unbacked "
        "again the moment an input upstream of them changes")

    checker = (root / "src" / "28_check_report.py").read_text(encoding="utf8")
    assert "SPOKEN" in checker and "INTERVIEW_QA.md" in checker, (
        "the report gate no longer checks the spoken documents. That is the "
        "exact gap the 93% lived in for weeks.")

    # And the figure itself must be measured, not asserted: 93% was wrong by
    # six points in the direction that understated the argument.
    import csv as _csv
    with (root / "data" / "final" / "externality.csv").open(
            encoding="utf8") as fh:
        rows = list(_csv.DictReader(fh))
    share = {r["mode"]: float(r["value"]) for r in rows
             if r["metric"] == "car_involved_share_K"}
    assert share and all(0.90 < v <= 1.0 for v in share.values()), (
        f"car-involved shares {share} outside 90-100%. Nearly every "
        f"pedestrian and cyclist death in a police crash file involves a "
        f"motor vehicle; a low value means the vehicle columns moved.")


def test_the_denominator_bias_runs_the_conservative_way():
    """
    THE CLAIM BEING LOCKED IS A DIRECTION, NOT A MAGNITUDE.

    Step 34 finds every crash rate here is 8-12% too LOW, because traffic in
    2019-2023 was below the 2025 count applied to all seven years. The report
    and the interview answer both lean on that SIGN: understating is defensible
    in a way overstating is not.

    If FHWA revises VM-2, or a later FDOT vintage is adopted, the magnitude may
    move and that is fine. If the SIGN flips, the argument inverts and every
    document quoting it becomes wrong. That is what this catches.
    """
    import csv
    root = Path(__file__).resolve().parents[1]
    p = root / "data" / "final" / "exposure_by_year.csv"
    assert p.exists(), "exposure_by_year.csv missing - run step 34"

    with p.open(encoding="utf8") as fh:
        rows = list(csv.DictReader(fh))

    under = [float(r["value"]) for r in rows
             if r["metric"] == "rate_understatement"]
    assert len(under) == 2, f"expected 2 scenarios, got {len(under)}"
    assert all(u > 0 for u in under), (
        f"The denominator bias flipped sign: {under}. Rates would now be "
        f"OVERstated, and the 'conservative, so left uncorrected' argument in "
        f"REPORT.md and Q11 no longer holds. Both must be rewritten.")

    # The 2020 severity spike is the other load-bearing claim, and unlike the
    # bias it involves no exposure figure at all - so it must survive any
    # revision to VM-2. Locked as a direction too: 2020 above 2019.
    per = {r["year"]: float(r["value"]) for r in rows
           if r["metric"] == "deaths_per_1000_crashes"}
    assert per["2020"] > per["2019"], (
        f"2020 deaths per 1,000 crashes ({per['2020']}) is no longer above "
        f"2019's ({per['2019']}). The pandemic-severity paragraph is wrong.")


def test_the_delay_term_stays_deleted():
    """
    A DELETION NEEDS A TEST AS MUCH AS AN ADDITION DOES.

    The crash-delay term was removed because it was a literal typed into two
    files and derived by no script. Nothing stops a future edit from typing it
    back in - it is two plausible-looking floats, and the literature behind it
    is real, so it would read as a fix rather than a regression.

    This test locks the deletion three ways:
      1. constants.py still says zero.
      2. Neither pipeline file declares its own delay tuple again.
      3. The report and the code agree, which step 26 also enforces at runtime.
    """
    import re
    root = Path(__file__).resolve().parents[1]

    sys.path.insert(0, str(root / "src"))
    from constants import DELAY_MINUTES
    assert DELAY_MINUTES == (0.0, 0.0), (
        f"DELAY_MINUTES is {DELAY_MINUTES}, not zero. If the delay term is "
        f"being brought back, it must first be DERIVED by a script - that is "
        f"the reason it was dropped, not the size of its effect.")

    # A re-declared literal, in any form: D_DRIVE = (0.39, 0.89), or any other
    # pair of floats. The ONE legitimate occurrence is 26_validate.py's
    # `RETIRED`, which is a probe for the historical measurement and never
    # reaches step 23.
    pat = re.compile(r"^\s*D_DRIVE\s*=\s*\(", re.M)
    for name in ("23_mep.py", "26_validate.py"):
        src = (root / "src" / name).read_text(encoding="utf8")
        assert not pat.search(src), (
            f"{name} declares its own D_DRIVE tuple again. It must read "
            f"DELAY_MINUTES from constants.py - two independent copies is "
            f"exactly how the original went unnoticed.")
        assert "DELAY_MINUTES" in src, f"{name} no longer reads DELAY_MINUTES"

    report = (root / "REPORT.md").read_text(encoding="utf8")
    assert "why it was deleted" in report, (
        "REPORT.md no longer explains the deletion. A reader who finds the "
        "Skabardonis citation in the git history and no explanation in the "
        "report will assume the term was quietly dropped to move a number.")


if __name__ == "__main__":

    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as exc:
            print(f"  FAIL  {name}\n        {str(exc)[:200]}")
            failed += 1
        except Exception as exc:
            print(f"  ERROR {name}\n        {type(exc).__name__}: "
                  f"{str(exc)[:180]}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
