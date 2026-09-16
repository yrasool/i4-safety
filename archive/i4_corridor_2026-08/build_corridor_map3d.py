"""
The corridor as a place you can fly into.

The previous 3D scene drew a fake road - a tube fitted through the crash points -
seen from five kilometres up, so it read as an abstract diagram. This one draws
the actual OpenStreetMap geometry: real carriageways at real widths, the ramp
curves peeling off them, cross streets, 1,720 extruded buildings, water. Zoom in
and an interchange looks like that interchange.

The crash markers keep the behaviour that justified 3D in the first place: where
crashes share a coordinate they stack into a column, one body per crash, and the
tallest holds 41.

Two camera presets land you at the interchanges rather than making you find them.
"""

import json
import os

from styles_corridor import STYLES

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "corridor_scene.json")
OUT = os.path.join(HERE, "i4_corridor_map3d.html")


def main():
    with open(SRC, encoding="utf-8") as fh:
        scene = json.load(fh)
    html = (TEMPLATE
            .replace("/*__SCENE__*/", json.dumps(scene, separators=(",", ":")))
            .replace("/*__STYLES__*/", json.dumps(STYLES, separators=(",", ":"))))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    m = scene["meta"]
    print(f"{m['n']} crashes, tallest stack {m['tallest']}, "
          f"{len(scene['roads'])} roads, {len(scene['buildings'])} buildings")
    print(f"{len(STYLES)} styles: " + ", ".join(s["name"] for s in STYLES))
    print(f"Wrote {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)")


TEMPLATE = r"""<meta charset="utf-8">
<title>I-4 — the corridor, close up</title>
<style>
  :root{
    --mono: ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
    --sans: system-ui,-apple-system,"Segoe UI",sans-serif;
    --ink:#eaf0f6; --dim:rgba(234,240,246,.45); --line:rgba(234,240,246,.14);
    --panel:rgba(6,9,14,.86);
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:#05070b;color:var(--ink);
            font-family:var(--sans);overflow:hidden}
  canvas{display:block}
  .ui{position:fixed;z-index:10;font-family:var(--mono);font-size:11px;
      letter-spacing:.04em}
  #head{top:0;left:0;right:0;padding:17px 24px 26px;pointer-events:none;
        background:linear-gradient(#05070b 48%,transparent)}
  #head h1{font-family:var(--sans);font-size:20px;font-weight:500;margin:0 0 2px}
  #head .s{color:var(--dim);font-size:10.5px}

  #styleNav{right:24px;top:170px;display:flex;flex-direction:column;gap:1px;
    background:var(--panel);border:1px solid var(--line);border-radius:3px;
    padding:5px;backdrop-filter:blur(4px);max-height:calc(100vh - 220px);
    overflow-y:auto}
  #styleNav button{background:transparent;border:0;color:var(--dim);font:inherit;
    font-size:10px;letter-spacing:.05em;padding:6px 10px;cursor:pointer;
    text-align:right;transition:.15s;border-radius:2px;white-space:nowrap}
  #styleNav button:hover{color:var(--ink);background:rgba(128,128,128,.14)}
  #styleNav button.on{background:var(--ink);color:var(--bgc,#05070b)}
  #styleNav button i{display:block;font-style:normal;font-size:8.5px;opacity:.55;
                     margin-top:2px;letter-spacing:.02em}

  #left{left:24px;top:104px;display:flex;flex-direction:column;gap:12px;
        max-height:calc(100vh - 130px);overflow-y:auto;padding-right:4px}
  .grp{background:var(--panel);border:1px solid var(--line);border-radius:3px;
       padding:9px 11px;backdrop-filter:blur(4px)}
  .grp>b{display:block;font-size:9px;letter-spacing:.13em;text-transform:uppercase;
         color:var(--dim);font-weight:400;margin-bottom:7px}
  .grp .btns{display:flex;gap:2px;flex-wrap:wrap}
  .grp button{background:transparent;border:1px solid var(--line);color:var(--dim);
    font:inherit;font-size:10px;letter-spacing:.07em;padding:5px 10px;
    cursor:pointer;transition:.15s;border-radius:2px}
  .grp button:hover{color:var(--ink);background:rgba(255,255,255,.07)}
  .grp button.on{background:var(--ink);color:#05070b;border-color:var(--ink)}
  .grp label{display:flex;align-items:center;gap:7px;padding:3px 0;cursor:pointer;
             font-size:10.5px;color:var(--dim)}
  .grp label:hover{color:var(--ink)}
  .grp label i{width:15px;height:3px;border-radius:2px;display:block;flex:none}
  .grp label input{margin:0}

  #detail{right:24px;bottom:22px;width:288px;background:var(--panel);
    border:1px solid var(--line);border-radius:3px;padding:14px 16px;
    opacity:0;transform:translateY(6px);transition:.18s;pointer-events:none;
    backdrop-filter:blur(4px)}
  #detail.on{opacity:1;transform:none}
  #detail .rp{font-family:var(--sans);font-size:15px;margin-bottom:3px}
  #detail .sv{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;
              margin-bottom:10px}
  #detail table{width:100%;border-collapse:collapse;font-size:10.5px}
  #detail td{padding:2px 0;vertical-align:top}
  #detail td:first-child{color:var(--dim);width:90px}
  #detail .warn{margin-top:10px;padding:8px 9px;background:rgba(255,180,60,.13);
    border-left:2px solid #ffb43c;font-size:9.5px;line-height:1.55;color:#ffd79a}

  #road{position:fixed;z-index:9;pointer-events:none;font-family:var(--mono);
        font-size:10px;color:var(--ink);background:var(--panel);padding:4px 8px;
        border:1px solid var(--line);border-radius:2px;opacity:0;transition:.12s}
  #stats{right:24px;top:104px;text-align:right;color:var(--dim);line-height:1.75}
  #stats b{color:var(--ink);font-variant-numeric:tabular-nums}
</style>

<div id="head" class="ui">
  <h1>The corridor, close up</h1>
  <div class="s">I-4 (SR 400), McIntosh Rd to Branch Forbes Rd &middot; real road
    geometry &middot; 648 crashes, one body each</div>
</div>

<nav id="styleNav" class="ui"></nav>

<div id="left" class="ui">
  <div class="grp"><b>fly to</b><div class="btns" id="cam">
    <button data-c="over">whole corridor</button>
    <button data-c="bf" class="on">Branch Forbes</button>
    <button data-c="mc">McIntosh</button>
    <button data-c="stack">tallest stack</button>
  </div></div>

  <div class="grp"><b>show</b>
    <label><input type="checkbox" id="tBld" checked><i style="background:#3a4654"></i>buildings</label>
    <label><input type="checkbox" id="tSrv" checked><i style="background:#2a3340"></i>service roads</label>
    <label><input type="checkbox" id="tCol" checked><i style="background:#ff9944"></i>stack columns</label>
  </div>

  <div class="grp"><b>roads</b>
    <label><i style="background:#8ec4f5"></i>the road &mdash; I-4 carriageways</label>
    <label><i style="background:#ffb765"></i>ramps</label>
    <label><i style="background:#b49bf0"></i>intersecting roads</label>
    <div class="btns" style="margin-top:7px" id="fw">
      <button data-w="normal">normal</button>
      <button data-w="wide">wide</button>
      <button data-w="broad" class="on">broad</button>
      <button data-w="huge">huge</button>
      <button data-w="max">max</button>
    </div>
    <div style="font-size:9px;color:var(--dim);line-height:1.5;margin-top:5px;
                max-width:196px">Carriageways widen <i>and</i> separate together,
      so each crash sits on one side or the other. Spacing is drawn for reading,
      not to scale.</div>
  </div>

  <div class="grp" id="crashLegend"></div>

  <div class="grp"><b>filter by where</b>
    <label><input type="checkbox" data-k="mainline" checked>on the mainline <span style="margin-left:auto;opacity:.6" id="n-mainline"></span></label>
    <label><input type="checkbox" data-k="ramp_bf" checked>Branch Forbes ramps <span style="margin-left:auto;opacity:.6" id="n-ramp_bf"></span></label>
    <label><input type="checkbox" data-k="ramp_mc" checked>McIntosh ramps <span style="margin-left:auto;opacity:.6" id="n-ramp_mc"></span></label>
    <label><input type="checkbox" data-k="intersection" checked>at a junction <span style="margin-left:auto;opacity:.6" id="n-intersection"></span></label>
  </div>

  <div class="grp"><b>direction</b>
    <label><input type="checkbox" data-d="Westbound" checked>westbound <span style="margin-left:auto;opacity:.6" id="n-wb"></span></label>
    <label><input type="checkbox" data-d="Eastbound" checked>eastbound <span style="margin-left:auto;opacity:.6" id="n-eb"></span></label>
    <label style="margin-top:5px;padding-top:6px;border-top:1px solid var(--line)">
      <input type="checkbox" id="tDir" checked>split onto carriageways</label>
    <div style="font-size:9px;color:var(--dim);line-height:1.55;margin-top:5px;
                max-width:196px">Most mainline coordinates are snapped to the
      centreline. Split places each crash on the carriageway its own record
      names — a placement rule, not a measured position.</div>
  </div>
</div>

<div id="stats" class="ui"></div>
<div id="detail" class="ui"></div>
<div id="road"></div>

<script type="importmap">
{"imports":{
  "three":"https://unpkg.com/three@0.160.0/build/three.module.js",
  "three/addons/":"https://unpkg.com/three@0.160.0/examples/jsm/"
}}
</script>

<script type="module">
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import * as BufferGeometryUtils from "three/addons/utils/BufferGeometryUtils.js";

const SCENE = /*__SCENE__*/;
const { roads, buildings, water, land, marks, bbox, meta } = SCENE;

/* Roads carry a little emissive of their own so they stay legible against a
   dark ground at any camera angle, and so the ramp reads as a different kind of
   road from the carriageway it leaves. */
const STYLES = /*__STYLES__*/;
let S = STYLES[0];

/* Roads take their three colours from the active scheme and stay LOW CONTRAST.
   They are structure. The crashes are the only bright thing on the map - which
   is what every reference in the archive does and what the old seven-hue version
   broke. Minor roads step down from the cross-street colour rather than
   introducing a fourth hue. */
function roadPalette(){
  const r = S.road;
  const mix = (hex, t) => {
    const c = new THREE.Color(hex), g = new THREE.Color(S.ground);
    return c.lerp(g, t);
  };
  return {
    mainline:{ c:new THREE.Color(r.main),  o:1.00 },
    ramp:    { c:new THREE.Color(r.ramp),  o:1.00 },
    major:   { c:new THREE.Color(r.cross), o:1.00 },
    minor:   { c:mix(r.cross, 0.22),       o:1.00 },
    local:   { c:mix(r.cross, 0.42),       o:0.95 },
    service: { c:mix(r.cross, 0.62),       o:0.85 },
  };
}

const CLASS_OF = { mainline:"mainline", intersection:"intersection",
                   ramp_bf:"ramp_bf", ramp_mc:"ramp_mc" };
const CLASS_LABEL = { mainline:"on the mainline", ramp_bf:"Branch Forbes ramp",
                      ramp_mc:"McIntosh ramp", intersection:"at a junction" };

/* What a crash's colour means depends on the scheme: how bad it was, which
   carriageway, where it happened, or how deep it sits in a stack. */
function crashColor(m){
  const t = S.colors || {};
  if (S.colorBy === "severity")  return t[m.sev]  || t["No Injury"] || "#888888";
  if (S.colorBy === "direction") return t[m.dir]  || t.Unknown     || "#888888";
  if (S.colorBy === "class")     return t[m.cls]  || t.mainline    || "#888888";
  if (S.colorBy === "depth"){
    const ramp = S.depthRamp || ["#334477","#aaccee"];
    const k = m.n > 1 ? m.f / (m.n - 1) : 0;
    const i = Math.min(ramp.length-2, Math.floor(k*(ramp.length-1)));
    const f = k*(ramp.length-1) - i;
    return "#" + new THREE.Color(ramp[i]).lerp(new THREE.Color(ramp[i+1]), f)
                   .getHexString();
  }
  return "#888888";
}

/* Ten ways of drawing a crash, one per scheme. */
function markGeometry(){
  switch (S.mark){
    case "point": return new THREE.SphereGeometry(0.62, 10, 8);
    case "cube":  return new THREE.BoxGeometry(1.5, 1.5, 1.5);
    case "slab":  return new THREE.BoxGeometry(2.2, 0.7, 2.2);
    case "bar":   return new THREE.BoxGeometry(0.8, 3.0, 0.8);
    case "disc":  return new THREE.CylinderGeometry(1.5, 1.5, 0.28, 18);
    case "ring":  return new THREE.TorusGeometry(1.2, 0.3, 8, 20);
    case "pin":   return new THREE.ConeGeometry(0.85, 3.4, 10);
    case "spike": return new THREE.ConeGeometry(0.5, 4.4, 8);
    case "cross": return new THREE.BoxGeometry(2.6, 0.42, 0.42);
    default:      return new THREE.SphereGeometry(1, 16, 12);
  }
}
function orientMark(mesh){
  if (S.mark === "ring")  mesh.rotation.x = -Math.PI/2;   // lie flat
  if (S.mark === "pin")   mesh.rotation.x =  Math.PI;     // point down at the road
  if (S.mark === "spike") mesh.rotation.x =  Math.PI;
}

const SEV_SCALE = { "Fatality":2.4, "Serious Injury":1.8, "Injury":1.25, "No Injury":0.85 };
const FLOOR_H = 2.6;

/* I-4 runs east-west here, so the two carriageways sit north and south of the
   centreline. Most mainline coordinates are snapped to that centreline, which is
   why direction was impossible to see. Offsetting each marker onto the
   carriageway its own Direction field names puts it on the right side of the
   road - closer to the truth than leaving everything stacked on the median, and
   labelled as a placement rule rather than a measurement. */
const CARRIAGEWAY = 2.4;   // scene units, ~24 m between carriageway centres

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x05070b);
// No fog. Flying along the corridor was fading the rest of the road to black,
// which hid exactly the thing being looked for. Nothing should go dark.

const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.3, 9000);
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.maxPolarAngle = Math.PI * 0.49;
// Zoom toward the cursor rather than the orbit target, so you can push into a
// specific interchange instead of always diving at the middle of the scene.
controls.zoomToCursor = true;
controls.zoomSpeed = 0.75;
controls.minDistance = 6;
controls.maxDistance = 1600;
controls.screenSpacePanning = false;
controls.panSpeed = 0.9;
controls.keyPanSpeed = 24;

// Named, because applyStyle() rebalances them per scheme.
const amb = new THREE.AmbientLight(0xffffff, 0.95);
scene.add(amb);
const key = new THREE.DirectionalLight(0xcfe4ff, 0.6);
key.position.set(-1, 2.2, 1.4); scene.add(key);
const rim = new THREE.DirectionalLight(0xff9a5c, 0.22);
rim.position.set(1.5, 0.6, -1); scene.add(rim);

/* ---------- ground ---------- */
const W = bbox.x1 - bbox.x0, D = bbox.z1 - bbox.z0;
const CX = (bbox.x0 + bbox.x1)/2, CZ = (bbox.z0 + bbox.z1)/2;
let groundMesh = null;
(function ground(){
  groundMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(W*1.4, D*1.6),
    new THREE.MeshStandardMaterial({ color:new THREE.Color(S.ground), roughness:1 }));
  groundMesh.rotation.x = -Math.PI/2; groundMesh.position.set(CX, -0.15, CZ);
  scene.add(groundMesh);
})();

/* polygon helper: ring of [x,z] -> flat shape at height y */
function polyMesh(rings, y, color, opacity){
  const geos = [];
  for (const ring of rings){
    if (ring.length < 3) continue;
    const shape = new THREE.Shape(ring.map(p => new THREE.Vector2(p[0], p[1])));
    geos.push(new THREE.ShapeGeometry(shape));
  }
  if (!geos.length) return null;
  const merged = BufferGeometryUtils.mergeGeometries(geos, false);
  if (!merged) return null;
  const m = new THREE.Mesh(merged, new THREE.MeshStandardMaterial({
    color, roughness:1, transparent: opacity < 1, opacity }));
  m.rotation.x = -Math.PI/2; m.position.y = y;
  return m;
}

/* Landcover sits just off the ground colour so it gives texture without becoming
   a second subject. Water is the one natural feature allowed its own hue. */
const landMeshes = [];
let waterMesh = null;
(function landcover(){
  const byType = {};
  for (const l of land) (byType[l.t] = byType[l.t] || []).push(l.p);
  const shades = { forest:-0.06, grass:-0.04, meadow:-0.04,
                   farmland:0.03, industrial:0.05, retail:0.06 };
  for (const t in byType){
    const m = polyMesh(byType[t], -0.08, 0xffffff, 1);
    if (!m) continue;
    m.userData.shade = shades[t] ?? 0.02;
    scene.add(m); landMeshes.push(m);
  }
  waterMesh = polyMesh(water.map(w => w.p), -0.05, 0xffffff, 1);
  if (waterMesh) scene.add(waterMesh);
})();

function tintLandcover(){
  const g = new THREE.Color(S.ground);
  for (const m of landMeshes){
    const c = g.clone();
    const hsl = {}; c.getHSL(hsl);
    c.setHSL(hsl.h, Math.min(1, hsl.s + 0.05),
             Math.max(0, Math.min(1, hsl.l + m.userData.shade)));
    m.material.color.copy(c);
  }
  if (waterMesh) waterMesh.material.color.set(S.water);
}

/* ---------- roads as flat ribbons ---------- */
function ribbon(pts, width){
  const v = [], idx = [];
  const hw = width/2;
  for (let i = 0; i < pts.length; i++){
    const p = pts[i];
    const a = pts[Math.max(0,i-1)], b = pts[Math.min(pts.length-1,i+1)];
    let dx = b[0]-a[0], dz = b[1]-a[1];
    const L = Math.hypot(dx,dz) || 1; dx/=L; dz/=L;
    const nx = -dz*hw, nz = dx*hw;
    v.push(p[0]+nx, 0, p[1]+nz, p[0]-nx, 0, p[1]-nz);
  }
  // Wind counter-clockwise as seen from above, so the ribbon faces up. Normals
  // do not control culling - winding does - and the reversed order rendered
  // every road invisible from any camera above the ground.
  for (let i = 0; i < pts.length-1; i++){
    const a = i*2;
    idx.push(a, a+2, a+1, a+1, a+2, a+3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(v, 3));
  g.setIndex(idx);
  // Force normals up. computeVertexNormals() derives them from winding, and a
  // flat XZ strip whose winding happens to run the other way ends up lit from
  // underneath - every road renders black.
  const n = new Float32Array(v.length);
  for (let i = 1; i < n.length; i += 3) n[i] = 1;
  g.setAttribute("normal", new THREE.BufferAttribute(n, 3));
  return g;
}

/* True width is ~15 m for a four-lane carriageway, which at corridor zoom is a
   hairline. Every road map exaggerates road width for legibility; this exposes
   the factor rather than baking one in, so the carriageways can be made as
   readable as they need to be. */
const WIDTH_FACTOR = { normal:2.0, wide:4.0, broad:7.0, huge:11.0, max:16.0 };
let widthMode = "broad";

/* Widening alone is not enough. The two carriageways are only ~25 m apart, so at
   any real exaggeration they merge into one ribbon and east/west becomes
   unreadable again — the exact problem this is meant to solve. So the
   carriageways are pushed APART in step with the widening, and the crash markers
   ride the same spread, which is what lets a crash be pinpointed on one
   carriageway or the other. */
const spreadFor = f => f * 2.6;

/* The corridor runs diagonally, not along an axis, so pushing carriageways apart
   in +z/-z slides them ALONG the road as much as across it and they stay fused.
   The offset has to be perpendicular to the corridor's own heading.

   AXIS is the corridor's principal direction, built by summing every mainline
   way's heading with the westbound ones flipped so they do not cancel out.
   PERP is that turned 90 degrees. With AXIS pointing east, PERP points +z, which
   in this projection is south - the eastbound side. */
const AXIS = (() => {
  let ax = 0, az = 0;
  for (const r of roads){
    if (r.k !== "mainline") continue;
    let dx = r.p[r.p.length-1][0] - r.p[0][0];
    let dz = r.p[r.p.length-1][1] - r.p[0][1];
    if (dx < 0){ dx = -dx; dz = -dz; }        // fold onto the eastward heading
    ax += dx; az += dz;
  }
  const L = Math.hypot(ax, az) || 1;
  return { x: ax/L, z: az/L };
})();
const PERP = { x: -AXIS.z, z: AXIS.x };

/* Eastbound if the way runs with the corridor axis, westbound if against it.
   Carriageways are one-way and opposed, so their headings differ by ~180 deg
   and this separates them cleanly wherever the corridor bends. */
function sideOfWay(r){
  const dx = r.p[r.p.length-1][0] - r.p[0][0];
  const dz = r.p[r.p.length-1][1] - r.p[0][1];
  return (dx*AXIS.x + dz*AXIS.z) >= 0 ? 1 : -1;   // +1 eastbound, -1 westbound
}

const roadGroups = {};
function drawRoads(){
  for (const k in roadGroups){
    scene.remove(roadGroups[k]);
    roadGroups[k].geometry.dispose();
    roadGroups[k].material.dispose();
    delete roadGroups[k];
  }
  const f = WIDTH_FACTOR[widthMode];
  const spread = spreadFor(f);
  const PAL = roadPalette();
  const byKind = {};
  for (const r of roads) (byKind[r.k] = byKind[r.k] || []).push(r);
  for (const kind in byKind){
    // Carriageways and ramps get the full exaggeration; minor roads get less,
    // or the cross-street mesh swamps the corridor it is meant to frame.
    const local = (kind === "mainline" || kind === "ramp") ? f
                : (kind === "service") ? 1 + (f - 1) * 0.22
                : 1 + (f - 1) * 0.42;
    const geos = byKind[kind].map(r => {
      const g = ribbon(r.p, r.w * local);
      // Mainline and ramps move outward onto their own carriageway so the two
      // directions stay separate at any width. Everything else stays put.
      const s = (kind === "mainline" || kind === "ramp")
              ? sideOfWay(r) * spread : 0;
      g.translate(PERP.x * s, 0.02 + r.z * 0.012 + (r.b ? 0.25 : 0), PERP.z * s);
      return g;
    });
    const merged = BufferGeometryUtils.mergeGeometries(geos, false);
    const st = PAL[kind];
    const mesh = new THREE.Mesh(merged, new THREE.MeshStandardMaterial({
      color: st.c, roughness:0.92, metalness:0.0, side: THREE.DoubleSide,
      transparent: st.o < 1, opacity: st.o }));
    scene.add(mesh); roadGroups[kind] = mesh;
  }
  const sv = document.getElementById("tSrv");
  if (sv && roadGroups.service) roadGroups.service.visible = sv.checked;
}
drawRoads();

/* ---------- buildings ---------- */
let buildingMesh = null;
(function drawBuildings(){
  const geos = [];
  for (const b of buildings){
    if (b.p.length < 3) continue;
    const shape = new THREE.Shape(b.p.map(p => new THREE.Vector2(p[0], -p[1])));
    let g;
    try {
      g = new THREE.ExtrudeGeometry(shape, { depth: b.h, bevelEnabled:false });
    } catch(e){ continue; }
    g.rotateX(-Math.PI/2);
    geos.push(g);
  }
  if (!geos.length) return;
  const merged = BufferGeometryUtils.mergeGeometries(geos, false);
  buildingMesh = new THREE.Mesh(merged, new THREE.MeshStandardMaterial({
    color:new THREE.Color(S.bldg), roughness:0.94, metalness:0.02 }));
  scene.add(buildingMesh);
})();

/* ---------- crash markers + stack columns ---------- */
const markers = [], columns = [];
const counts = {};
let dirOffset = true;

/* Eastbound rides +PERP, matching sideOfWay, so a marker lands on the same
   carriageway the road geometry was pushed to. Returns the SIGN only; the
   distance comes from the current spread. */
function dirSign(m){
  if (m.dir === "Eastbound") return  1;
  if (m.dir === "Westbound") return -1;
  return 0;
}
const sideOf = m => dirSign(m) * spreadFor(WIDTH_FACTOR[widthMode]);

for (const m of marks){
  m.cls = CLASS_OF[m.k] || "mainline";
  counts[m.cls] = (counts[m.cls]||0)+1;
}
for (const k in counts){
  const el = document.getElementById("n-"+k);
  if (el) el.textContent = counts[k];
}

function buildMarkers(){
  for (const mesh of markers){
    scene.remove(mesh);
    mesh.geometry.dispose(); mesh.material.dispose();
  }
  markers.length = 0;
  const geo = markGeometry();
  const glow = S.glow, ms = S.markScale;
  for (const m of marks){
    const col = new THREE.Color(crashColor(m));
    const mesh = new THREE.Mesh(geo.clone(), new THREE.MeshStandardMaterial({
      color: col, emissive: col,
      emissiveIntensity: glow * (m.sev === "No Injury" ? 0.45 : 1.0),
      roughness: glow > 0 ? 0.3 : 0.85, metalness: 0.03 }));
    const y = m.f * FLOOR_H + 1.4;
    const off = sideOf(m);
    mesh.position.set(m.x + PERP.x*off, y, m.z + PERP.z*off);
    orientMark(mesh);
    const s = (SEV_SCALE[m.sev] || 0.9) * ms;
    mesh.scale.setScalar(s);
    mesh.userData = { m, s, y, x0: m.x, z0: m.z, sign: dirSign(m) };
    scene.add(mesh); markers.push(mesh);
  }
}

let tallest = null;
function drawColumns(){
  for (const c of columns){
    scene.remove(c); c.geometry.dispose(); c.material.dispose();
  }
  columns.length = 0;
  tallest = null;
  // Group by coordinate AND direction, so a shared point that holds both
  // carriageways becomes two columns on the correct sides rather than one
  // column straddling the median.
  const groups = {};
  for (const m of marks){
    const k = m.x+","+m.z+","+m.dir;
    (groups[k] = groups[k] || []).push(m);
  }
  for (const k in groups){
    const g = groups[k];
    if (g.length < 2) continue;
    const h = (g.length-1)*FLOOR_H + 2.6;
    const heat = Math.min(1, g.length / meta.tallest);
    const cyl = new THREE.Mesh(
      new THREE.CylinderGeometry(0.3, 0.3, h, 6),
      new THREE.MeshBasicMaterial({
        color: new THREE.Color(S.column),
        transparent:true,
        opacity: S.columnOpacity * (0.55 + heat*0.75) }));
    const off = sideOf(g[0]);
    const cxp = g[0].x + PERP.x*off, czp = g[0].z + PERP.z*off;
    cyl.position.set(cxp, h/2, czp);
    cyl.userData = { x0:g[0].x, z0:g[0].z, sign:dirSign(g[0]) };
    scene.add(cyl); columns.push(cyl);
    if (!tallest || g.length > tallest.n)
      tallest = { x:cxp, z:czp, x0:g[0].x, z0:g[0].z,
                  sign:dirSign(g[0]), n:g.length, h };
  }
  const tc = document.getElementById("tCol");
  if (tc) for (const c of columns) c.visible = tc.checked;
}

/* ---------- camera presets ---------- */
const bfX = Math.max(...marks.filter(m=>m.k==="ramp_bf").map(m=>m.x));
const bfZ = marks.filter(m=>m.k==="ramp_bf").reduce((a,m)=>a+m.z,0) /
            Math.max(1, marks.filter(m=>m.k==="ramp_bf").length);
const mcX = Math.min(...marks.filter(m=>m.k==="ramp_mc").map(m=>m.x));
const mcZ = marks.filter(m=>m.k==="ramp_mc").reduce((a,m)=>a+m.z,0) /
            Math.max(1, marks.filter(m=>m.k==="ramp_mc").length);

/* Interchange views sit back far enough to hold the whole junction — ramps
   included — rather than dropping the camera inside it. */
const VIEWS = {
  over:  { t:[CX, 10, CZ],   p:[CX-330, 260, CZ+420] },
  bf:    { t:[bfX, 6, bfZ],  p:[bfX-150, 118, bfZ+185] },
  mc:    { t:[mcX, 6, mcZ],  p:[mcX-145, 112, mcZ+178] },
  stack: { t:[0, 0, 0],      p:[0,0,0] },
};
function refreshStackView(){
  if (!tallest) return;
  VIEWS.stack = { t:[tallest.x, tallest.h*0.55, tallest.z],
                  p:[tallest.x-42, tallest.h*0.95+26, tallest.z+52] };
}
refreshStackView();

let anim = null;
function flyTo(name){
  const v = VIEWS[name]; if (!v) return;
  anim = { t0:performance.now(), dur:900,
           fromP:camera.position.clone(), fromT:controls.target.clone(),
           toP:new THREE.Vector3(...v.p), toT:new THREE.Vector3(...v.t) };
}
document.getElementById("cam").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  [...b.parentNode.children].forEach(c => c.classList.toggle("on", c === b));
  flyTo(b.dataset.c);
};
camera.position.set(...VIEWS.bf.p);
controls.target.set(...VIEWS.bf.t);

/* ---------- toggles ---------- */
const hidden = new Set(), hiddenDir = new Set();
document.querySelectorAll("[data-k]").forEach(cb => {
  cb.onchange = () => {
    cb.checked ? hidden.delete(cb.dataset.k) : hidden.add(cb.dataset.k);
    apply();
  };
});
document.querySelectorAll("[data-d]").forEach(cb => {
  cb.onchange = () => {
    cb.checked ? hiddenDir.delete(cb.dataset.d) : hiddenDir.add(cb.dataset.d);
    apply();
  };
});
/* Markers and columns ride whatever spread the roads are currently drawn at. */
function placeMarkers(){
  const spread = spreadFor(WIDTH_FACTOR[widthMode]);
  const put = (obj, u) => {
    const off = dirOffset ? u.sign * spread : 0;
    obj.position.x = u.x0 + PERP.x * off;
    obj.position.z = u.z0 + PERP.z * off;
  };
  for (const mesh of markers) put(mesh, mesh.userData);
  for (const c of columns)    put(c, c.userData);
  // keep the tallest-stack camera preset pointing at where that column now sits
  if (tallest){
    const off = dirOffset ? tallest.sign * spread : 0;
    tallest.x = tallest.x0 + PERP.x * off;
    tallest.z = tallest.z0 + PERP.z * off;
    refreshStackView();
  }
}
document.getElementById("tDir").onchange = e => {
  dirOffset = e.target.checked;
  placeMarkers();
};
document.getElementById("tBld").onchange = e => {
  if (buildingMesh) buildingMesh.visible = e.target.checked; };
document.getElementById("tSrv").onchange = e => {
  if (roadGroups.service) roadGroups.service.visible = e.target.checked; };
document.getElementById("fw").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  widthMode = b.dataset.w;
  [...b.parentNode.children].forEach(c => c.classList.toggle("on", c === b));
  drawRoads();
  placeMarkers();     // markers follow the carriageways outward
};
document.getElementById("tCol").onchange = e => {
  for (const c of columns) c.visible = e.target.checked; };

function apply(){
  let shown = 0, wb = 0, eb = 0;
  for (const mesh of markers){
    const m = mesh.userData.m;
    const vis = !hidden.has(m.cls) && !hiddenDir.has(m.dir);
    mesh.visible = vis; if (vis) shown++;
  }
  for (const m of marks){
    if (m.dir === "Westbound") wb++;
    else if (m.dir === "Eastbound") eb++;
  }
  document.getElementById("n-wb").textContent = wb;
  document.getElementById("n-eb").textContent = eb;
  document.getElementById("stats").innerHTML =
    `<b>${shown}</b> of ${meta.n} crashes<br>`+
    `<b>${meta.coords}</b> distinct coordinates<br>`+
    `<b>${meta.tallest}</b> on the tallest point<br>`+
    `<b>${roads.length}</b> roads &middot; <b>${buildings.length}</b> buildings`;
}

/* ---------- hover ---------- */
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
const detail = document.getElementById("detail");
const roadTip = document.getElementById("road");
let hover = null;

addEventListener("pointermove", e => {
  mouse.x = (e.clientX/innerWidth)*2-1;
  mouse.y = -(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(mouse, camera);
  const hits = ray.intersectObjects(markers.filter(m=>m.visible), false);
  const hit = hits.length ? hits[0].object : null;
  if (hit !== hover){
    if (hover) hover.scale.setScalar(hover.userData.s);
    hover = hit;
    if (hit){ hit.scale.setScalar(hit.userData.s*1.9); show(hit.userData.m); }
    else detail.classList.remove("on");
  }
  if (hit){ roadTip.style.opacity = 0; }
  else {
    roadTip.style.left = (e.clientX+14)+"px";
    roadTip.style.top = (e.clientY+14)+"px";
  }
});

function show(m){
  const col = "#"+CLASS_COLOR[m.cls].toString(16).padStart(6,"0");
  const where = CLASS_LABEL[m.cls] || "on the mainline";
  const flags = [m.cmv&&"commercial vehicle", m.spd&&"speeding",
                 m.ldp&&"lane departure"].filter(Boolean);
  detail.innerHTML =
    `<div class="rp">Report ${m.id||"—"}</div>`+
    `<div class="sv" style="color:${col}">${m.sev} &middot; ${where}</div>`+
    `<table>`+
    `<tr><td>when</td><td>${m.dt||m.yr}</td></tr>`+
    `<tr><td>carriageway</td><td><b>${m.dir||"unknown"}</b></td></tr>`+
    `<tr><td>type</td><td>${m.typ}</td></tr>`+
    (m.hrm?`<tr><td>first harm</td><td>${m.hrm}</td></tr>`:"")+
    `<tr><td>light</td><td>${m.lgt}</td></tr>`+
    `<tr><td>surface</td><td>${m.surf}</td></tr>`+
    (m.mp!==null?`<tr><td>milepost</td><td>${(+m.mp).toFixed(3)}</td></tr>`:"")+
    `<tr><td>vehicles</td><td>${m.veh}</td></tr>`+
    (m.inj?`<tr><td>injuries</td><td>${m.inj}</td></tr>`:"")+
    (flags.length?`<tr><td>flags</td><td>${flags.join(", ")}</td></tr>`:"")+
    `</table>`+
    (m.n>1?`<div class="warn"><b>${m.n} crashes share this coordinate</b> —
      floor ${m.f+1} of that column. The position is a milepost lookup, not a
      measured location.</div>`:"");
  detail.classList.add("on");
}

addEventListener("resize", () => {
  camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

// Module scope is otherwise unreachable from the console; this makes the scene
// inspectable when something renders wrong.
window.__dbg = { scene, camera, controls, renderer, roadGroups, buildingMesh,
                 markers, columns, VIEWS, THREE, STYLES, get S(){ return S; } };

/* ---------- schemes ---------- */
function applyStyle(){
  scene.background = new THREE.Color(S.bg);
  document.body.style.background = S.bg;
  const r = document.documentElement.style;
  r.setProperty("--ink", S.ink);
  r.setProperty("--dim", S.light ? "rgba(29,32,36,.55)" : "rgba(234,240,246,.45)");
  r.setProperty("--line", S.light ? "rgba(29,32,36,.18)" : "rgba(234,240,246,.14)");
  r.setProperty("--panel", S.light ? "rgba(255,255,255,.86)" : "rgba(6,9,14,.86)");
  r.setProperty("--bgc", S.bg);
  amb.intensity = S.light ? 1.15 : 0.95;
  key.intensity = S.light ? 0.5 : 0.6;

  if (groundMesh) groundMesh.material.color.set(S.ground);
  if (buildingMesh) buildingMesh.material.color.set(S.bldg);
  tintLandcover();
  drawRoads();
  buildMarkers();
  drawColumns();
  placeMarkers();
  buildCrashLegend();
  apply();
}

/* The crash legend depends on what the scheme encodes with colour. */
function buildCrashLegend(){
  const host = document.getElementById("crashLegend");
  if (!host) return;
  const by = S.colorBy;
  const rows = [];
  if (by === "severity"){
    for (const k of ["Fatality","Serious Injury","Injury","No Injury"])
      rows.push([S.colors[k], k, marks.filter(m=>m.sev===k).length]);
  } else if (by === "direction"){
    for (const k of ["Westbound","Eastbound"])
      rows.push([S.colors[k], k.toLowerCase(), marks.filter(m=>m.dir===k).length]);
  } else if (by === "class"){
    for (const k of ["mainline","ramp_bf","ramp_mc","intersection"])
      rows.push([S.colors[k], CLASS_LABEL[k], marks.filter(m=>m.cls===k).length]);
  } else {
    const ramp = S.depthRamp || [];
    rows.push([ramp[0], "bottom of a stack", ""]);
    rows.push([ramp[ramp.length-1], "top of a stack", ""]);
  }
  host.innerHTML = `<b>crashes &mdash; ${
    by === "depth" ? "position in the stack" : by}</b>` +
    rows.map(([c,l,n]) => `<label><i style="background:${c}"></i>${l}`+
      (n !== "" ? `<span style="margin-left:auto;opacity:.6">${n}</span>` : "")+
      `</label>`).join("");
}

const styleNav = document.getElementById("styleNav");
STYLES.forEach((st, i) => {
  const b = document.createElement("button");
  b.className = i === 0 ? "on" : "";
  b.innerHTML = `${st.name}<i>${st.src}</i>`;
  b.onclick = () => {
    S = st;
    [...styleNav.children].forEach((c, j) => c.classList.toggle("on", j === i));
    applyStyle();
  };
  styleNav.appendChild(b);
});

(function fromHash(){
  const h = new URLSearchParams(location.hash.slice(1));
  const i = STYLES.findIndex(x => x.id === h.get("s"));
  if (i >= 0){
    S = STYLES[i];
    [...styleNav.children].forEach((c, j) => c.classList.toggle("on", j === i));
  }
})();

applyStyle();

let t = 0;
(function loop(){
  requestAnimationFrame(loop);
  t += 0.006;
  if (anim){
    const k = Math.min(1, (performance.now()-anim.t0)/anim.dur);
    const e = k<0.5 ? 4*k*k*k : 1-Math.pow(-2*k+2,3)/2;   // easeInOutCubic
    camera.position.lerpVectors(anim.fromP, anim.toP, e);
    controls.target.lerpVectors(anim.fromT, anim.toT, e);
    if (k>=1) anim = null;
  }
  for (const m of markers){
    if (m.userData.m.sev === "Fatality" && m.visible && m !== hover)
      m.scale.setScalar(m.userData.s*(1+Math.sin(t*2.2)*0.17));
  }
  controls.update();
  renderer.render(scene, camera);
})();
</script>
"""


if __name__ == "__main__":
    main()
