"""
Ten schemes for the corridor map, rebuilt from what her archive actually does.

Sampling the ACCENT of each reference rather than its ground exposed the pattern
the current map was breaking:

    Midnight fellowship        #000000  accent #707070
    Cybersecurity in black     #000000  accent #f0f0f0
    A court made of light      #000000  accent #f8f8f8
    Black-field line creature  #080808  accent #d8d8d8
    Trace constellations       #080808  accent #888888
    Commute as geography       #181818  accent #a87898
    A shader artist's index    #101010  accent #68a0d0
    The brain as terrain       #000010  accent #883038
    Luminous pond              #001058  accent #485868
    Travel time, not radius    #e8e8e8  accent #88d0f8
    Four monochrome worlds     #f8f0e0  warm paper
    Ulugh Beg ceiling          #605038  accent #a89870

Near-black ground, ONE bright accent. "Stripped to black, white, one luminous
object." The map had seven competing hues - blue road, orange ramp, violet cross
street, four crash colours - so nothing read as the subject.

So in every scheme here the ROADS RECEDE. They are structure, drawn in low
contrast greys of the ground's own hue, and the crashes are the only bright
thing. Where a second colour appears it marks the worst crashes only, never a
fourth category.

`mark` is the way a crash is drawn:
    sphere · pin needle · disc flat on the road · slab stacked block · bar upright
    cross small plus · point tiny · cube matte · ring hollow · spike thin cone
`colorBy`: severity · direction · class · depth (position in the stack)
"""

STYLES = [
    {
        "id": "midnight", "name": "Midnight", "src": "midnight fellowship launch",
        "bg": "#000000", "ground": "#070809", "ink": "#e9edf2", "light": False,
        "road": {"main": "#3a4048", "ramp": "#4e545c", "cross": "#20242a"},
        "bldg": "#141719", "water": "#0c141c",
        "mark": "sphere", "colorBy": "severity", "glow": 1.6, "markScale": 1.0,
        "ramp": {"Fatality": "#ffffff", "Serious Injury": "#c8ced6",
                 "Injury": "#8b939c", "No Injury": "#4a5058"},
        "column": "#707070", "columnOpacity": 0.30,
    },
    {
        "id": "commute", "name": "Commute", "src": "commute as geography",
        "bg": "#161616", "ground": "#1c1c1c", "ink": "#efe8ec", "light": False,
        "road": {"main": "#3d3a3c", "ramp": "#4f4a4d", "cross": "#282628"},
        "bldg": "#232122", "water": "#1a1c22",
        "mark": "disc", "colorBy": "severity", "glow": 1.5, "markScale": 1.45,
        "ramp": {"Fatality": "#ffd9ec", "Serious Injury": "#d88ab4",
                 "Injury": "#a87898", "No Injury": "#5e4c58"},
        "column": "#a87898", "columnOpacity": 0.33,
    },
    {
        "id": "shader", "name": "Shader index", "src": "a shader artist's index",
        "bg": "#0d0d0d", "ground": "#131313", "ink": "#e4ecf4", "light": False,
        "road": {"main": "#33383e", "ramp": "#454b52", "cross": "#212427"},
        "bldg": "#1b1e21", "water": "#12181f",
        "mark": "point", "colorBy": "class", "glow": 2.0, "markScale": 0.95,
        "ramp": {"mainline": "#68a0d0", "ramp_bf": "#68d0c0",
                 "ramp_mc": "#d068a0", "intersection": "#d0c068"},
        "column": "#68a0d0", "columnOpacity": 0.28,
    },
    {
        "id": "filament", "name": "Filament", "src": "black-field line creature",
        "bg": "#050505", "ground": "#0a0a0a", "ink": "#e8e8e8", "light": False,
        "road": {"main": "#2c2c2c", "ramp": "#3c3c3c", "cross": "#191919"},
        "bldg": "#121212", "water": "#0d1114",
        "mark": "spike", "colorBy": "severity", "glow": 2.2, "markScale": 1.2,
        "ramp": {"Fatality": "#ffffff", "Serious Injury": "#e8e8e8",
                 "Injury": "#a8a8a8", "No Injury": "#5a5a5a"},
        "column": "#d8d8d8", "columnOpacity": 0.22,
    },
    {
        "id": "constellation", "name": "Constellations", "src": "trace constellations",
        "bg": "#060606", "ground": "#0b0b0b", "ink": "#dedede", "light": False,
        "road": {"main": "#2a2d30", "ramp": "#383c40", "cross": "#181a1c",},
        "bldg": "#131517", "water": "#0e1316",
        "mark": "point", "colorBy": "direction", "glow": 1.9, "markScale": 1.05,
        "ramp": {"Westbound": "#dcdcdc", "Eastbound": "#888888",
                 "Unknown": "#5a5a5a"},
        "column": "#888888", "columnOpacity": 0.25,
    },
    {
        "id": "terrain", "name": "Terrain", "src": "the brain as terrain",
        "bg": "#00000e", "ground": "#04041a", "ink": "#eadfe2", "light": False,
        "road": {"main": "#2e2a3c", "ramp": "#3e3648", "cross": "#1a1826"},
        "bldg": "#171528", "water": "#0d1030",
        "mark": "pin", "colorBy": "severity", "glow": 1.8, "markScale": 1.1,
        "ramp": {"Fatality": "#ffb0b8", "Serious Injury": "#d05060",
                 "Injury": "#883038", "No Injury": "#4a2c34"},
        "column": "#883038", "columnOpacity": 0.36,
    },
    {
        "id": "pond", "name": "Jewel pond", "src": "luminous pond",
        "bg": "#000c40", "ground": "#001058", "ink": "#dbe7f5", "light": False,
        "road": {"main": "#2a3a6a", "ramp": "#3a4c80", "cross": "#16214a"},
        "bldg": "#0d1a4e", "water": "#001a6a",
        "mark": "point", "colorBy": "class", "glow": 2.1, "markScale": 1.0,
        "ramp": {"mainline": "#9fd8ff", "ramp_bf": "#7fffd4",
                 "ramp_mc": "#ff9fd0", "intersection": "#ffe9a0"},
        "column": "#485868", "columnOpacity": 0.30,
    },
    {
        "id": "cliff", "name": "Strata", "src": "rainbow cliff",
        "bg": "#0a1430", "ground": "#102858", "ink": "#dfe6f5", "light": False,
        "road": {"main": "#31406c", "ramp": "#42527f", "cross": "#1c2749"},
        "bldg": "#16204a", "water": "#122a5e",
        "mark": "slab", "colorBy": "depth", "glow": 0.8, "markScale": 1.25,
        "depthRamp": ["#1a2c60", "#3a4c88", "#7880b8", "#cdd4ee"],
        "column": "#7880b8", "columnOpacity": 0.20,
    },
    {
        "id": "flow", "name": "Flow field", "src": "potential flow around a car",
        "bg": "#080d14", "ground": "#101820", "ink": "#eef0f8", "light": False,
        "road": {"main": "#2e3a48", "ramp": "#3e4c5c", "cross": "#1a222c"},
        "bldg": "#161e28", "water": "#080080",
        "mark": "bar", "colorBy": "direction", "glow": 1.5, "markScale": 1.15,
        "ramp": {"Westbound": "#f0f0f8", "Eastbound": "#5c7cff",
                 "Unknown": "#7a8494"},
        "column": "#f0f0f8", "columnOpacity": 0.26,
    },
    {
        "id": "daylight", "name": "Daylight", "src": "travel time, not radius",
        "bg": "#ececeb", "ground": "#e2e4e3", "ink": "#1d2024", "light": True,
        "road": {"main": "#9aa3ac", "ramp": "#7d8792", "cross": "#c2c7cb"},
        "bldg": "#d2d6d8", "water": "#c3dced",
        "mark": "ring", "colorBy": "severity", "glow": 0.0, "markScale": 1.4,
        "ramp": {"Fatality": "#0b2f4a", "Serious Injury": "#2f6f9e",
                 "Injury": "#88d0f8", "No Injury": "#adc4d2"},
        "column": "#5b7d93", "columnOpacity": 0.28,
    },
]

# `ramp` doubles as the colour table for whatever colorBy names; rename it on the
# way out so the scene code reads clearly and nothing collides with road.ramp.
# A depth-coloured scheme carries `depthRamp` instead and has no table.
for s in STYLES:
    s["colors"] = s.pop("ramp", {})

# Guard the hex values - a malformed colour renders as black and is easy to miss.
def _check():
    import re
    ok = re.compile(r"^#[0-9a-fA-F]{6}$")
    for s in STYLES:
        fields = [("bg", s["bg"]), ("ground", s["ground"]), ("ink", s["ink"]),
                  ("bldg", s["bldg"]), ("water", s["water"]),
                  ("column", s["column"])]
        fields += [(f"road.{k}", v) for k, v in s["road"].items()]
        fields += [(f"colors.{k}", v) for k, v in s["colors"].items()]
        fields += [(f"depthRamp[{i}]", v)
                   for i, v in enumerate(s.get("depthRamp", []))]
        for name, v in fields:
            if not ok.match(str(v)):
                raise ValueError(f"{s['id']}: bad colour {name} = {v!r}")


_check()
