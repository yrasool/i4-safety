"""
Report exhibit: crash concentration within the mainline segment.

The crash-rate table treats the mainline as two segments, 3.043 mi eastbound and
3.080 mi westbound, each reported as a single averaged rate. That cannot show
where inside three miles the crashes actually sit. This figure does.

It is deliberately NOT called a segment analysis. "Segment" already means the
whole directional length in the report, and a competing definition next to that
table would confuse a reviewer.

Honesty requirement: raw milepost counts are about a third contributed by
coordinates shared between many crashes. MP 21.8 in particular is 91.5% one
point - raw, it would publish as the third-worst location on the corridor while
being nearly empty. So each bar is split into confirmed and uncertain, and the
reader can see both.

Fonts and dual png/svg export match the existing exhibits so this drops in
alongside them.

Reads the source read-only. Writes here.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"
STEM = os.path.join(HERE, "I4_Crash_Concentration_by_Milepost")

# Matching the statistics notebook so the figure sits beside the others.
TITLE_FS, LABEL_FS, TICK_FS, ANNOT_FS, LEGEND_FS = 25, 20, 18, 18, 18

BIN = 0.1          # miles, 528 ft
STACK_WARN = 10    # crashes on one coordinate at or above this = not a position

C_CONF = "#2471a3"   # confirmed position
C_UNC = "#c9d6e0"    # position uncertain
C_MARK = "#c0392b"   # annotation


def main():
    df = pd.read_excel(SRC, engine="openpyxl").dropna(subset=["LATITUDE", "LONGITUDE"])

    # The statistics notebook recodes this; carry it so severity totals agree.
    nt = df["Severity_Detail"].astype(str).eq("Non-Traffic Fatality")
    df.loc[nt, "Severity"] = "Fatality"

    key = (df["LATITUDE"].round(6).astype(str) + "," +
           df["LONGITUDE"].round(6).astype(str))
    df["stack"] = key.map(key.value_counts())
    df["uncertain"] = df["stack"] >= STACK_WARN

    usable = df[df["Milepost"].notna() & (df["Milepost"] > 1)].copy()
    dropped_mp = len(df) - len(usable)
    usable["mp"] = (usable["Milepost"] / BIN).round() * BIN

    grp = usable.groupby("mp").agg(
        total=("REPORT_NUMBER", "size"),
        uncertain=("uncertain", "sum"),
    )
    grp["confirmed"] = grp["total"] - grp["uncertain"]
    grp = grp.sort_index()

    # Interchange positions, taken from where the tagged ramp crashes sit.
    ramps = usable[usable["Location"].astype(str).str.startswith("Ramp")]
    marks = []
    for zone, label in [("Ramp - McIntosh Rd", "McIntosh Rd\ninterchange"),
                        ("Ramp - Branch Forbes Rd", "Branch Forbes Rd\ninterchange")]:
        sub = ramps[ramps["Location"] == zone]
        if len(sub):
            marks.append((sub["Milepost"].median(), label))

    fig, ax = plt.subplots(figsize=(18, 8))
    fig.patch.set_facecolor("white")

    x = grp.index.values
    ax.bar(x, grp["confirmed"], width=BIN * 0.82, color=C_CONF,
           label="Confirmed position", zorder=3)
    ax.bar(x, grp["uncertain"], width=BIN * 0.82, bottom=grp["confirmed"],
           color=C_UNC, edgecolor="#8fa3b3", hatch="///", linewidth=.8,
           label="Position uncertain (shared coordinate)", zorder=3)

    ymax = grp["total"].max() * 1.34
    ax.set_ylim(0, ymax)

    # Interchange markers. Labels run vertically alongside each line, nudged to
    # whichever side has clear space, so nothing sits on top of a bar or a callout.
    for i, (mp, label) in enumerate(marks):
        ax.axvline(mp, color="#7f8c8d", linestyle=":", linewidth=2, zorder=2)
        dx = -0.07 if i == 0 else 0.07
        # Kept low on the axes: the callouts sit high, so the two never meet.
        ax.text(mp + dx, ymax * 0.26, label.replace("\n", " "),
                ha="center", va="center", rotation=90,
                fontsize=12, color="#5d6d7e", zorder=4,
                bbox=dict(boxstyle="round,pad=0.28", fc="white", ec="#d5dbdb"))

    # Call out the two concentrations that survive cleaning. Text is offset
    # sideways so the arrows never run under the legend.
    top = grp.sort_values("confirmed", ascending=False).head(2)
    for i, (mp, r) in enumerate(top.iterrows()):
        dx = -0.42 if i == 0 else 0.42
        ax.annotate(f"{int(r['confirmed'])} confirmed\nof {int(r['total'])} "
                    f"at MP {mp:.1f}",
                    xy=(mp, r["confirmed"]),
                    xytext=(mp + dx, r["total"] * 0.86),
                    ha="center", va="center", fontsize=ANNOT_FS - 4,
                    color=C_MARK, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.35", fc="white",
                              ec=C_MARK, alpha=.92),
                    arrowprops=dict(arrowstyle="->", color=C_MARK, lw=1.8))

    ax.set_xlabel("Milepost along I-4 (SR 400)", fontsize=LABEL_FS, fontweight="bold")
    ax.set_ylabel("Number of Crashes", fontsize=LABEL_FS, fontweight="bold")
    ax.set_title("Crash Concentration within the I-4 Mainline Segment "
                 f"({int(usable['Year'].min())}\u2013{int(usable['Year'].max())})",
                 fontsize=TITLE_FS, fontweight="bold", pad=18)
    ax.tick_params(axis="both", labelsize=TICK_FS)
    ax.set_xticks([round(v, 1) for v in x][::2])
    ax.set_xlim(x.min() - BIN, x.max() + BIN)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(fontsize=LEGEND_FS - 2, frameon=True, loc="upper left",
              framealpha=.95)

    # The method note belongs under the figure, the way a report caption reads.
    caption = (
        f"Bars are {BIN:.1f}-mile bins ({BIN * 5280:.0f} ft). Crashes sharing a "
        f"coordinate with {STACK_WARN} or more others are shown separately: those are "
        f"milepost lookups rather than\nmeasured positions, so their bin is "
        f"approximate. The mainline is reported in the crash-rate table as a single "
        f"3.04 mi (EB) / 3.08 mi (WB) segment; this figure\nshows the distribution "
        f"within it.")
    if dropped_mp:
        caption += (f" {dropped_mp} of {len(df)} crashes are omitted for having no "
                    f"valid milepost.")
    fig.text(0.5, -0.02, caption, ha="center", va="top",
             fontsize=13, color="#5d6d7e", linespacing=1.5)

    plt.tight_layout()
    plt.savefig(STEM + ".png", dpi=600, bbox_inches="tight", facecolor="white")
    plt.savefig(STEM + ".svg", format="svg", bbox_inches="tight", facecolor="white")
    plt.close()

    print(f"Wrote {STEM}.png / .svg")
    print(f"\n  Bins: {len(grp)}   crashes plotted: {int(grp['total'].sum())}"
          f"   omitted (no milepost): {dropped_mp}")
    print(f"  Confirmed: {int(grp['confirmed'].sum())}   "
          f"uncertain: {int(grp['uncertain'].sum())}")
    print("\n  Top 5 by confirmed count:")
    for mp, r in grp.sort_values("confirmed", ascending=False).head(5).iterrows():
        print(f"    MP {mp:5.1f}   {int(r['confirmed']):3d} confirmed "
              f"of {int(r['total']):3d} total")
    print("\n  Interchange markers:")
    for mp, label in marks:
        print(f"    MP {mp:5.2f}  {label.replace(chr(10), ' ')}")

    grp.to_excel(STEM + "_data.xlsx", engine="openpyxl")
    print(f"\n  Underlying data: {STEM}_data.xlsx")


if __name__ == "__main__":
    main()
