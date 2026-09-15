"""
Twelve visual styles for the 3D corridor, each derived from a specific reference
in Yusra's Reference Room - and where possible from colours sampled out of that
reference's own image rather than invented.

Sampled dominants, for the record:
    A browser for city-scale maps   #000000 #111111        nocturnal near-black
    Black-field line creature       #000000 + greys        pure black field
    A court made of light           #000000-#000044 #66bbee
    Rainbow cliff                   #112255 #223366 #334477 #445588
    Potential flow around a car     #000088 #dddddd #ff9944
    Luminous pond                   #001155 #001166 #002255
    Low-light contact sheet         #111122 #ffffff #995522
    Develop the negative            #221111 #332211
    The brain as terrain            #000011 #110011 #220011
    One-file low-poly world         #bbaa55 #ddccbb
    Ulugh Beg ceiling               #665544 #887766

Each style controls ground, fog, marker geometry and material, the four class
colours, how a column is coloured, and whether grain sits over the frame.

`column` modes:
    heat    one hue per column, hotter the taller it is
    strata  every floor a different shade - the Rainbow Cliff reading, where a
            stack is a cross-section and you can count the layers
    mono    one colour throughout, the column is structure not signal
"""

STYLES = [
    {
        "id": "nocturne", "name": "Nocturne",
        "src": "a browser for city-scale maps",
        "bg": "#000000", "fogNear": 420, "fogFar": 1250,
        "grid1": "#141c24", "grid2": "#0b1116", "road": "#1e2c3a",
        "geo": "sphere", "emissive": 0.9, "dim": 0.28, "metal": 0.05, "rough": 0.5,
        "classes": {"mainline": "#5aa9ff", "intersection": "#ffd166",
                    "ramp_bf": "#3ee6a0", "ramp_mc": "#ff6b9d"},
        "column": "heat", "colA": "#1a2a3a", "colB": "#ff9944",
        "ink": "#e8edf2", "grain": 0.0,
    },
    {
        "id": "filament", "name": "Filament",
        "src": "black-field line creature",
        "bg": "#000000", "fogNear": 500, "fogFar": 1400,
        "grid1": "#0a0f14", "grid2": "#060a0e", "road": "#16222e",
        "geo": "point", "emissive": 1.5, "dim": 0.5, "metal": 0.0, "rough": 1.0,
        "classes": {"mainline": "#7fe9ff", "intersection": "#ffffff",
                    "ramp_bf": "#5affc8", "ramp_mc": "#ff8fd0"},
        "column": "mono", "colA": "#2a4a5a", "colB": "#7fe9ff",
        "ink": "#dff6fb", "grain": 0.0,
    },
    {
        "id": "strata", "name": "Strata",
        "src": "rainbow cliff — layers feel excavated",
        "bg": "#080d1a", "fogNear": 400, "fogFar": 1150,
        "grid1": "#16233d", "grid2": "#0d1526", "road": "#25355a",
        "geo": "box", "emissive": 0.55, "dim": 0.3, "metal": 0.1, "rough": 0.6,
        "classes": {"mainline": "#7fa8e8", "intersection": "#ffd166",
                    "ramp_bf": "#6ee0b8", "ramp_mc": "#ff8ab0"},
        "column": "strata", "colA": "#112255", "colB": "#88bbff",
        "ink": "#dfe8f8", "grain": 0.0,
    },
    {
        "id": "court", "name": "Court of light",
        "src": "a court made of light",
        "bg": "#000000", "fogNear": 380, "fogFar": 1100,
        "grid1": "#001a33", "grid2": "#000d1a", "road": "#0d3350",
        "geo": "sphere", "emissive": 1.15, "dim": 0.3, "metal": 0.2, "rough": 0.35,
        "classes": {"mainline": "#66bbee", "intersection": "#ffe066",
                    "ramp_bf": "#66eec4", "ramp_mc": "#ff6699"},
        "column": "heat", "colA": "#00224d", "colB": "#66bbee",
        "ink": "#dceefb", "grain": 0.0,
    },
    {
        "id": "flow", "name": "Flow field",
        "src": "potential flow around a car",
        "bg": "#070a18", "fogNear": 400, "fogFar": 1200,
        "grid1": "#131a38", "grid2": "#0a0f22", "road": "#1c2550",
        "geo": "bar", "emissive": 0.75, "dim": 0.3, "metal": 0.05, "rough": 0.5,
        "classes": {"mainline": "#dddddd", "intersection": "#ff9944",
                    "ramp_bf": "#66d9ff", "ramp_mc": "#ff5c8a"},
        "column": "heat", "colA": "#000088", "colB": "#ff9944",
        "ink": "#e6e9f5", "grain": 0.0,
    },
    {
        "id": "darkroom", "name": "Darkroom",
        "src": "develop the negative",
        "bg": "#140b08", "fogNear": 380, "fogFar": 1050,
        "grid1": "#2a1c14", "grid2": "#1a110c", "road": "#3a2418",
        "geo": "sphere", "emissive": 0.7, "dim": 0.28, "metal": 0.15, "rough": 0.55,
        "classes": {"mainline": "#e8a05c", "intersection": "#ffe0b0",
                    "ramp_bf": "#9ad4a0", "ramp_mc": "#e87f9a"},
        "column": "heat", "colA": "#3a2214", "colB": "#ffb066",
        "ink": "#f2e0cc", "grain": 0.06,
    },
    {
        "id": "contact", "name": "Contact sheet",
        "src": "low-light contact sheet",
        "bg": "#0b0e1a", "fogNear": 360, "fogFar": 1000,
        "grid1": "#1a2030", "grid2": "#10141f", "road": "#232a3d",
        "geo": "sphere", "emissive": 0.65, "dim": 0.25, "metal": 0.0, "rough": 0.7,
        "classes": {"mainline": "#c8d4e8", "intersection": "#ffb066",
                    "ramp_bf": "#8fd8bc", "ramp_mc": "#e08cae"},
        "column": "mono", "colA": "#2a3550", "colB": "#995522",
        "ink": "#e8ecf5", "grain": 0.075,
    },
    {
        "id": "pond", "name": "Jewel pond",
        "src": "luminous pond",
        "bg": "#00081c", "fogNear": 400, "fogFar": 1150,
        "grid1": "#0d1f4a", "grid2": "#061230", "road": "#123163",
        "geo": "point", "emissive": 1.35, "dim": 0.45, "metal": 0.0, "rough": 1.0,
        "classes": {"mainline": "#4fc3f7", "intersection": "#ffe27a",
                    "ramp_bf": "#69f0ae", "ramp_mc": "#ff80ab"},
        "column": "strata", "colA": "#001155", "colB": "#7fd4ff",
        "ink": "#d9ecff", "grain": 0.0,
    },
    {
        "id": "terrain", "name": "Terrain",
        "src": "the brain as terrain",
        "bg": "#05000d", "fogNear": 380, "fogFar": 1100,
        "grid1": "#1c0f2e", "grid2": "#110818", "road": "#2c1442",
        "geo": "sphere", "emissive": 1.0, "dim": 0.3, "metal": 0.25, "rough": 0.4,
        "classes": {"mainline": "#b06cff", "intersection": "#ffd166",
                    "ramp_bf": "#5ce0d0", "ramp_mc": "#ff5c9a"},
        "column": "heat", "colA": "#220033", "colB": "#ff5cc8",
        "ink": "#eee0f8", "grain": 0.0,
    },
    {
        "id": "voxel", "name": "Voxel",
        "src": "voxel city, first pass",
        "bg": "#0e1116", "fogNear": 420, "fogFar": 1200,
        "grid1": "#1e242c", "grid2": "#141920", "road": "#2c3742",
        "geo": "box", "emissive": 0.25, "dim": 0.15, "metal": 0.0, "rough": 0.95,
        "classes": {"mainline": "#6ea8d8", "intersection": "#e8c46a",
                    "ramp_bf": "#7fc99a", "ramp_mc": "#d88ba8"},
        "column": "mono", "colA": "#3a4652", "colB": "#7f95a8",
        "ink": "#dfe5ec", "grain": 0.0,
    },
    {
        "id": "haze", "name": "Daylight haze",
        "src": "one-file low-poly world",
        "bg": "#ddccbb", "fogNear": 330, "fogFar": 980,
        "grid1": "#c4b49c", "grid2": "#d2c3ad", "road": "#8a7a62",
        "geo": "sphere", "emissive": 0.0, "dim": 0.0, "metal": 0.05, "rough": 0.85,
        "classes": {"mainline": "#2f5d8c", "intersection": "#b06a12",
                    "ramp_bf": "#1f7a5a", "ramp_mc": "#a8285c"},
        "column": "heat", "colA": "#a89880", "colB": "#7a2a12",
        "ink": "#2a2318", "grain": 0.03,
    },
    {
        "id": "plate", "name": "Plate",
        "src": "print lane — one ink, no glow",
        "bg": "#f2ece1", "fogNear": 340, "fogFar": 1000,
        "grid1": "#d8d0c2", "grid2": "#e6dfd2", "road": "#9a9284",
        "geo": "sphere", "emissive": 0.0, "dim": 0.0, "metal": 0.0, "rough": 1.0,
        "classes": {"mainline": "#3a3a3a", "intersection": "#8c6a1f",
                    "ramp_bf": "#2f6b52", "ramp_mc": "#8c2f4a"},
        "column": "strata", "colA": "#c4bcae", "colB": "#5e1a10",
        "ink": "#231f1a", "grain": 0.035,
    },
]
