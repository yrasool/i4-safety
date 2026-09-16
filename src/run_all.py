"""
Run the whole pipeline in dependency order and prove it reproduces.

WHY THIS EXISTS. "Can you rerun it?" is the first question anyone asks about a
result, and until now the answer was a list of scripts and an ordering that
lived only in a handoff file. Numbering is not dependency: step 24 must run
BEFORE step 16, because 16 needs the block groups 24 defines.

Every step prints its own checks and exits non-zero on failure, so this stops
at the first thing that breaks rather than carrying a bad input forward.

REPRODUCIBILITY CHECK. Before running, the current headline figures are read
from data/final/. After running, they are read again and compared. If a step is
not deterministic given its inputs, this is where it shows.

    python src/run_all.py            everything
    python src/run_all.py --fast     skip the two slow routing steps
"""

import csv
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FINAL = ROOT / "data" / "final"

# (script, minutes, needs_network, slow)
STEPS = [
    # 01 WAS MISSING - the third instance of this bug, after 05 and 33. It is
    # the only step that writes sld.parquet, which 03, 04 and 26 all READ, and
    # 26's two gated external-validation figures (0.8985 vs D5AR, 0.6161 vs
    # D5BR) rested on it. It had been run by hand on 7 September and never
    # again. It now caches EPA's raw response in data/raw/ first, because the
    # source is a live service; verified that a fresh fetch reproduces the
    # 7 September file exactly, row for row, before it was added here.
    ("01_fetch_sld.py", 1, True, False),
    ("02_crashes_by_mode.py", 3, False, False),
    ("03_exposure_by_mode.py", 1, True, False),
    ("18_centroids.py", 1, True, False),
    ("24_acs.py", 2, True, False),
    ("16_opportunities.py", 1, True, False),
    ("17_activity_freq.py", 2, True, False),
    ("25_spatial_equivalency.py", 3, True, False),
    ("04_injury_cost.py", 1, False, False),
    # 05 WAS MISSING, and it is the only step that writes
    # injury_rate_by_mode.csv. Steps 23, 26 and 28 all READ that file, so the
    # pipeline was consuming an output no pipeline step produced. It survived
    # because those three read the `transit` row, while the stale `drive` row
    # sat at the superseded occupancy of 1.67 and was 11% wrong. METHOD.md and
    # mode_results.csv are still quoting figures derived from it.
    ("05_mep_weights.py", 2, True, False),
    ("19_fetch_osm.py", 1, True, False),      # cached; re-fetches only gaps
    ("20_build_graph.py", 2, False, False),
    ("21_isochrones.py", 15, False, True),
    ("22_transit.py", 10, False, True),
    ("09_segment_rates.py", 5, True, False),
    # 33 MUST PRECEDE 29, and was not in this list at all. It is the only
    # step that writes segment_facility.csv, which 29 READS to fit a separate
    # safety curve per road type. Same shape of bug as the missing 05 above:
    # the pipeline consumed an output no pipeline step produced, and survived
    # only because a stale file happened to be on disk from a manual run.
    ("33_spf_stratified.py", 3, True, False),
    ("29_spf_eb.py", 1, False, False),
    ("30_route_risk.py", 2, False, False),
    # 40 is the route assignment step 30's own docstring said it was not.
    # Shortest-time tree per origin, risk summed along the path to every
    # destination by pointer jumping. It needs the network on the first run to
    # cache FDOT polylines, and about 16 minutes. Its output is read by step 23
    # only under MEP_DRIVE_RISK=route until the switch is decided.
    ("40_route_assignment.py", 17, True, True),
    # 32 reads 29's segment_eb.csv, so it must follow it. It produces a
    # NEGATIVE result - non-motorist risk could not be made to vary by place -
    # and it is in the pipeline precisely so that negative result stays true
    # as the inputs move, rather than being a one-off claim in a document.
    ("32_nonmotor_by_place.py", 4, True, False),
    ("23_mep.py", 2, False, False),
    ("26_validate.py", 3, False, False),
    ("27_equity.py", 1, False, False),
    ("28_check_report.py", 1, False, False),
    # 31 WAS MISSING TOO. It is the only check that this build behaves like
    # MEP at all - NREL's own published validation scenarios. A pipeline that
    # never runs it can drift into not-MEP silently.
    ("31_nrel_scenarios.py", 1, False, False),
    # 34 tests the denominator every rate in the project divides by: one 2025
    # traffic count applied to 2019-2025. Runs last because it changes no
    # figure - it bounds the bias in one, and the bias runs against this
    # project's own conclusion.
    ("34_exposure_by_year.py", 1, False, False),
    # 35 computes the externality split. It is in the pipeline because
    # INTERVIEW_QA Q10 asserted "I ran it both ways" and "I report it
    # separately" while NO live step did either, and the 93% it quoted was
    # derived by nothing. A claim in a document must be produced by a step in
    # the run, or it is not a claim, it is a memory.
    ("35_externality.py", 2, False, False),
    # 36-39 are CHECKS. They compute nothing the headline depends on; they
    # exist so that a figure which has drifted fails a run rather than waiting
    # to be contradicted in a room. Each one is here because of a specific
    # question a reviewer can ask and this project could not previously answer:
    #   36  does the model predict, or only fit?      (2019-22 -> 2023-25)
    #   37  can anyone WITHOUT the licence check it?  (public dashboard)
    #   38  is this region typical of Florida?        (casualty share vs people)
    #   39  what does a bus CAUSE, not just suffer?   (step 35 had no bus side)
    # 36 was written on 14 September and left out of this list for a day, which
    # is the same omission as 01, 05 and 33 - hence the stale-file detector
    # below, which now reports any output older than the run that produced it.
    ("36_holdout.py", 2, False, False),
    ("37_s4_public_check.py", 1, False, False),
    ("38_florida_context.py", 1, False, False),
    ("39_bus_externality.py", 2, False, False),
]


def headline():
    """The figures that must not move between identical runs."""
    out = {}
    try:
        with (FINAL / "mep_by_blockgroup.csv").open(encoding="utf8") as fh:
            rows = list(csv.DictReader(fh))
        out["n_blockgroups"] = len(rows)
        out["mep_published"] = round(
            sum(float(r["mep_published"]) for r in rows) / len(rows), 4)
        out["mep_harm_lo"] = round(
            sum(float(r["mep_harm_lo"]) for r in rows) / len(rows), 4)
    except Exception:
        pass
    try:
        with (FINAL / "injury_cost_by_mode.csv").open(encoding="utf8") as fh:
            for r in csv.DictReader(fh):
                if r["mode"] == "vehicle_occupant":
                    out["r_drive"] = round(float(r["cost_per_pmt"]), 6)
    except Exception:
        pass
    return out


def main():
    fast = "--fast" in sys.argv
    steps = [s for s in STEPS if not (fast and s[3])]
    before = headline()

    print(f"{'=' * 70}")
    print(f"PIPELINE RUN  {len(steps)} steps  "
          f"~{sum(s[1] for s in steps)} minutes")
    if fast:
        print("--fast: skipping isochrones and transit, which reuse cached "
              "matrices")
    print(f"{'=' * 70}")
    if before:
        print("current headline figures, to compare against afterwards:")
        for k, v in before.items():
            print(f"  {k:<18}{v}")
    print()

    t0 = time.time()
    for i, (script, mins, net, _slow) in enumerate(steps, 1):
        label = f"[{i}/{len(steps)}] {script}"
        print(f"{label}  {'(network)' if net else ''}", flush=True)
        t = time.time()
        r = subprocess.run([sys.executable, "-u", str(SRC / script)],
                           capture_output=True, text=True)
        took = time.time() - t
        if r.returncode != 0:
            print(f"    FAILED after {took:.0f}s\n")
            tail = (r.stdout or "").strip().split("\n")[-15:]
            for ln in tail:
                print(f"    | {ln}")
            if r.stderr:
                for ln in r.stderr.strip().split("\n")[-15:]:
                    print(f"    ! {ln}")
            sys.exit(f"\nPipeline stopped at {script}. Fix it before rerunning "
                     f"the rest - later steps would run on its stale output.")
        print(f"    ok  {took:.0f}s", flush=True)

    after = headline()
    print(f"\n{'=' * 70}")
    print(f"COMPLETE in {(time.time() - t0) / 60:.1f} minutes")
    print(f"{'=' * 70}")

    # WHAT DID THIS RUN NOT REGENERATE?
    #
    # Three times this pipeline consumed a file that no step in it produced:
    # injury_rate_by_mode.csv (step 05 missing), segment_facility.csv (33
    # missing) and sld.parquet (01 missing). Each survived because a manual
    # run had left the file on disk, so every later run read it happily and
    # nothing failed.
    #
    # A static check was tried first and rejected: parsing each step's
    # "Writes:" docstring would have MISSED the segment_facility.csv case,
    # because step 33's docstring did not list it. The documentation was as
    # stale as the file. So this checks what actually happened on disk
    # instead - anything in interim/ or final/ older than this run was not
    # written by it.
    #
    # Reported, not fatal: outputs of retired scripts (06, 07, 08, 11-15)
    # legitimately sit here untouched. The point is that the list is SHORT
    # and SEEN, so a new entry on it gets noticed.
    data = SRC.parent / "data"
    stale = sorted(p.relative_to(data).as_posix()
                   for d in (data / "interim", data / "final") if d.exists()
                   for p in d.iterdir()
                   if p.is_file() and p.stat().st_mtime < t0)
    if fast:
        print("  (--fast: the skipped steps' matrices are expected to be "
              "older than this run)")
    if stale:
        print(f"\n  {len(stale)} data file(s) NOT regenerated by this run:")
        for s in stale:
            print(f"    {s}")
        print("  If any pipeline step READS one of these, it is consuming "
              "stale data -\n  that is the bug found three times here. "
              "Outputs of retired scripts\n  are expected on this list.")
    else:
        print("\n  every file in data/interim and data/final was regenerated "
              "by this run")

    if not before:
        print("no prior figures to compare against; this run is the baseline")
        return
    print(f"  {'figure':<20}{'before':>16}{'after':>16}  same?")
    drift = []
    for k in sorted(set(before) | set(after)):
        b, a = before.get(k), after.get(k)
        same = b == a
        print(f"  {k:<20}{str(b):>16}{str(a):>16}  {'yes' if same else 'NO'}")
        if not same:
            drift.append(k)
    if drift:
        print(f"\n  {len(drift)} figure(s) MOVED between runs on the same "
              f"inputs.")
        print(f"  Either an input changed underneath, or a step is not "
              f"deterministic.\n  Both matter: a result that cannot be "
              f"reproduced cannot be defended.")
        sys.exit(1)
    print(f"\n  Every headline figure reproduced exactly.")


if __name__ == "__main__":
    main()
