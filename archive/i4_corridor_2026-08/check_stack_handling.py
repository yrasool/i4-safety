"""
Do the existing notebooks do anything about crashes sharing a coordinate?

Searches both notebooks for the techniques that would address it - deduplication,
clustering, jitter, aggregation by location, segment binning - and for the ones
that would be actively harmed by it, notably HeatMap.

Read-only.
"""

import io
import json
import re

NOTEBOOKS = [
    r"D:\Yusra\I4 Safety Ana;ysis\I4_Branch_Forbes.ipynb",
    r"D:\Yusra\I4 Safety Ana;ysis\I4_Statistics_Visualization.ipynb",
]

# Things that would MITIGATE the stacking problem.
MITIGATIONS = [
    "drop_duplicates", "duplicated", "MarkerCluster", "FastMarkerCluster",
    "jitter", "random.uniform", "np.random", "offset",
    "groupby('coord", 'groupby("coord', "nunique",
    "Milepost", "LRS_MILEPOINT", "segment", "bin",
]

# Things that are actively UNSAFE on stacked points.
HAZARDS = ["HeatMap", "kdeplot", "gaussian_kde", "hexbin", "density"]

# Anything that draws a point on a map.
PLOTTING = ["CircleMarker", "folium.Marker", "Marker(", "add_to(", "scatter"]


def cells(path):
    with io.open(path, encoding="utf-8") as fh:
        nb = json.load(fh)
    return [(i, "".join(c["source"])) for i, c in enumerate(nb["cells"])]


for path in NOTEBOOKS:
    name = path.rsplit("\\", 1)[-1]
    print("=" * 70)
    print(name)
    print("=" * 70)

    src = cells(path)
    whole = "\n".join(s for _, s in src)

    print("\n-- MITIGATIONS (would help with stacked points) --")
    found_any = False
    for term in MITIGATIONS:
        hits = [i for i, s in src if term in s]
        if hits:
            found_any = True
            print(f"   FOUND  {term:22s} in cells {hits}")
    if not found_any:
        print("   none found")

    print("\n-- HAZARDS (unsafe on stacked points) --")
    haz = False
    for term in HAZARDS:
        hits = [i for i, s in src if term in s]
        if hits:
            haz = True
            print(f"   FOUND  {term:22s} in cells {hits}")
    if not haz:
        print("   none found")

    print("\n-- POINT PLOTTING --")
    for term in PLOTTING:
        hits = [i for i, s in src if term in s]
        if hits:
            print(f"   {term:22s} in cells {hits}")

    # Imports tell you what was at least considered.
    imports = re.findall(r"^\s*(?:from|import)\s+.*$", whole, re.M)
    plug = [ln.strip() for ln in imports if "folium" in ln or "plugins" in ln]
    if plug:
        print("\n-- FOLIUM IMPORTS --")
        for ln in plug:
            print("   " + ln)
    print()
