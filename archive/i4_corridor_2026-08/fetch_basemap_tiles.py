"""
Fetch and stitch real basemap imagery for the corridor.

Ten invented colour schemes were all wrong. The map should look like a map -
satellite or streets - with the crash data on top, so the ground is photography
rather than a palette I chose.

Two bases, both free and keyless:
    satellite  Esri World Imagery
    streets    Esri World Street Map  (the Google-Maps register)

Standard XYZ web-mercator tiles, stitched into one image per base and saved with
the exact geographic bounds of the stitched area, so three.js can lay it on the
ground plane in the right place rather than being nudged by eye.
"""

import json
import math
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "basemap")

# The corridor, with margin — matches fetch_corridor_osm.py
S, W, N, E = 28.0100, -82.2650, 28.0420, -82.1700
ZOOM = 16                      # ~2.4 m/px once stitched; z17 exceeds texture caps

BASES = {
    "satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/"
                 "World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "streets":   "https://server.arcgisonline.com/ArcGIS/rest/services/"
                 "World_Street_Map/MapServer/tile/{z}/{y}/{x}",
}


def lon2x(lon, z):
    return (lon + 180.0) / 360.0 * (1 << z)


def lat2y(lat, z):
    r = math.radians(lat)
    return (1.0 - math.log(math.tan(r) + 1.0/math.cos(r)) / math.pi) / 2.0 * (1 << z)


def x2lon(x, z):
    return x / (1 << z) * 360.0 - 180.0


def y2lat(y, z):
    n = math.pi - 2.0 * math.pi * y / (1 << z)
    return math.degrees(math.atan(0.5 * (math.exp(n) - math.exp(-n))))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow is required: this environment has it via anaconda")

    x0, x1 = int(math.floor(lon2x(W, ZOOM))), int(math.floor(lon2x(E, ZOOM)))
    y0, y1 = int(math.floor(lat2y(N, ZOOM))), int(math.floor(lat2y(S, ZOOM)))
    cols, rows = x1 - x0 + 1, y1 - y0 + 1
    print(f"zoom {ZOOM}: {cols} x {rows} = {cols*rows} tiles per base")

    # The stitched image covers whole tiles, so its true bounds are the tile
    # edges, not the requested box. Carrying these exactly is what keeps the
    # imagery aligned with the road geometry.
    bounds = {
        "west": x2lon(x0, ZOOM), "east": x2lon(x1 + 1, ZOOM),
        "north": y2lat(y0, ZOOM), "south": y2lat(y1 + 1, ZOOM),
        "zoom": ZOOM, "cols": cols, "rows": rows,
    }

    for name, tmpl in BASES.items():
        path = os.path.join(OUT_DIR, f"{name}.jpg")
        if os.path.exists(path) and os.path.getsize(path) > 200_000:
            print(f"  {name}: cached")
            continue

        canvas = Image.new("RGB", (cols * 256, rows * 256))
        got = fail = 0
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                url = tmpl.format(z=ZOOM, x=cx, y=cy)
                try:
                    req = urllib.request.Request(
                        url, headers={"User-Agent": "i4-corridor/1.0"})
                    with urllib.request.urlopen(req, timeout=30) as r:
                        from io import BytesIO
                        img = Image.open(BytesIO(r.read())).convert("RGB")
                    canvas.paste(img, ((cx - x0) * 256, (cy - y0) * 256))
                    got += 1
                except Exception:
                    fail += 1
                time.sleep(0.02)
            print(f"  {name}: column {cx-x0+1}/{cols}  ok {got} fail {fail}",
                  end="\r", flush=True)

        # Cap the long edge so it stays inside common GPU texture limits.
        if canvas.width > 4096:
            h = round(canvas.height * 4096 / canvas.width)
            canvas = canvas.resize((4096, h), Image.LANCZOS)
        canvas.save(path, "JPEG", quality=86, optimize=True)
        print(f"\n  {name}: {canvas.width}x{canvas.height}, "
              f"{os.path.getsize(path)/1e6:.1f} MB, {got} tiles, {fail} failed")

    with open(os.path.join(OUT_DIR, "bounds.json"), "w", encoding="utf-8") as fh:
        json.dump(bounds, fh, indent=1)
    print(f"\nbounds: {bounds['west']:.5f}..{bounds['east']:.5f} lon, "
          f"{bounds['south']:.5f}..{bounds['north']:.5f} lat")


if __name__ == "__main__":
    main()
