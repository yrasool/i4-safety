"""
Step 08 - does the term change any decision?

The question the project could not answer. Measuring that the omitted term is
10.5% of driving's cost is not the same as showing it matters. If adding it
reorders nothing, the honest finding is that the omission is real but not
decision-relevant, and that is a result rather than a failure.

Method: rank all block groups by weighted job access with and without the
injury term, then count how many change position. Ranking is what an agency
actually does with an accessibility surface - it decides where to invest first.

Note what this CANNOT show. Step 06 proved loss_pct is an exact affine function
of the transit share, so the reordering is driven entirely by how modal
composition varies across places. That is the honest mechanism, and it is worth
measuring rather than asserting.

Writes: data/final/decision_test.csv
"""

import sys
from math import exp
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from constants import ALPHA, GAMMA, MEP_DEFAULTS as MEP, SCENARIOS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INTERIM, FINAL = ROOT / "data" / "interim", ROOT / "data" / "final"


def main():
    sld = pd.read_parquet(INTERIM / "sld.parquet")
    rates = pd.read_csv(FINAL / "injury_rate_by_mode.csv").set_index("mode")["r"]
    r = {"drive": float(rates["drive"]), "transit": float(rates["transit"])}

    df = sld[["GEOID20", "county", "TotPop", "D5AR", "D5BR"]].copy()
    df["A_d"] = pd.to_numeric(df["D5AR"], errors="coerce")
    df["A_t"] = pd.to_numeric(df["D5BR"], errors="coerce").fillna(0.0)

    w0 = {m: exp(ALPHA * MEP[m]["e"] + GAMMA * MEP[m]["c"]) for m in MEP}
    df["W_before"] = df["A_d"] * w0["drive"] + df["A_t"] * w0["transit"]
    df["rank_before"] = df["W_before"].rank(ascending=False, method="first")

    print(f"{len(df):,} block groups ranked by weighted job access\n")
    out = []
    for name, delta in SCENARIOS.items():
        w1 = {m: exp(ALPHA * MEP[m]["e"] + GAMMA * MEP[m]["c"] + delta * r[m])
              for m in MEP}
        col = f"W_{name}"
        df[col] = df["A_d"] * w1["drive"] + df["A_t"] * w1["transit"]
        rk = df[col].rank(ascending=False, method="first")
        moved = (rk != df["rank_before"])
        shift = (rk - df["rank_before"]).abs()

        # Does it change WHO you would fund first? An equity programme targets
        # the WORST-served, which is the LOWEST weighted access, not the
        # smallest rank number. Getting this backwards measures the wrong end.
        worst_b = set(df.nsmallest(100, "W_before")["GEOID20"])
        worst_a = set(df.assign(_w=df[col]).nsmallest(100, "_w")["GEOID20"])
        churn = len(worst_b - worst_a)

        print(f"{name}   delta = {delta:.3f}")
        print(f"  block groups changing rank      {moved.sum():>6,} "
              f"({moved.mean():.1%})")
        print(f"  median move among those         {shift[moved].median():>6.0f} places")
        print(f"  largest move                    {shift.max():>6.0f} places")
        print(f"  spearman before vs after        {df['rank_before'].corr(rk, method='spearman'):>6.4f}")
        print(f"  churn in the worst-served 100   {churn:>6} of 100\n")
        out.append({"scenario": name, "delta": delta,
                    "pct_moved": moved.mean(),
                    "median_move": shift[moved].median(),
                    "max_move": shift.max(),
                    "spearman": df["rank_before"].corr(rk, method="spearman"),
                    "top100_churn": churn})

    pd.DataFrame(out).to_csv(FINAL / "decision_test.csv", index=False)
    print(f"wrote {FINAL / 'decision_test.csv'}")


if __name__ == "__main__":
    main()
