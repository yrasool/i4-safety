"""
What is actually inside the folium maps already in the folder?

Looks for the layers, markers and geometry each one carries, so anything useful
they contain (labels, drawn features, zone boundaries) can be carried into the
new map rather than rebuilt from scratch.

Read-only.
"""

import glob
import os
import re
from collections import Counter

FOLDER = r"D:\Yusra\I4 Safety Ana;ysis"

PATTERNS = {
    "circle_marker": r"L\.circleMarker\(",
    "marker": r"L\.marker\(",
    "circle": r"L\.circle\(",
    "polyline": r"L\.polyline\(",
    "rectangle": r"L\.rectangle\(",
    "polygon": r"L\.polygon\(",
    "tile_layer": r"L\.tileLayer\(",
    "layer_control": r"L\.control\.layers\(",
    "marker_cluster": r"markerClusterGroup|MarkerCluster",
    "heat_layer": r"L\.heatLayer|HeatMap",
    "popup": r"\.bindPopup\(",
    "tooltip": r"\.bindTooltip\(",
    "feature_group": r"L\.featureGroup\(",
}

for path in sorted(glob.glob(os.path.join(FOLDER, "*.html"))):
    name = os.path.basename(path)
    with open(path, encoding="utf-8", errors="replace") as fh:
        html = fh.read()

    print("=" * 72)
    print(f"{name}   ({len(html) / 1024:.0f} KB)")
    print("=" * 72)

    counts = {k: len(re.findall(p, html)) for k, p in PATTERNS.items()}
    for k, v in counts.items():
        if v:
            print(f"   {k:16s} {v}")

    tiles = set(re.findall(r'"(https?://[^"]*\{z\}[^"]*)"', html))
    if tiles:
        print("\n   basemaps:")
        for t in sorted(tiles):
            host = t.split("/")[2]
            print(f"     {host}")

    # Legends and captions carry the author's own labelling.
    legend = re.findall(r"(?:legend|Legend)[^<]{0,60}", html)
    if legend:
        print(f"\n   legend mentions: {len(legend)}")

    # Colours in use hint at what is being encoded.
    cols = Counter(re.findall(r'"(#[0-9a-fA-F]{6})"', html))
    if cols:
        print("\n   top colours: " +
              ", ".join(f"{c}({n})" for c, n in cols.most_common(8)))

    # Any text labels baked into markers.
    labels = set(re.findall(r"(?:Ramp|Mainline|McIntosh|Branch Forbes|Gore|MP\s?\d+)"
                            r"[A-Za-z0-9 ,.\-]{0,40}", html))
    if labels:
        keep = sorted(l.strip() for l in labels if len(l.strip()) > 4)[:14]
        print("\n   labels found:")
        for l in keep:
            print(f"     {l}")
    print()
