"""
The corridor on real imagery.

Ten invented colour schemes were rejected, and rightly - a map should look like a
map. The ground here is photography: Esri World Imagery, or Esri World Street Map
for the Google-Maps register, stitched from 126 real tiles and laid on the ground
plane using the exact tile-edge bounds so it registers with the road geometry
rather than being nudged into place.

What changes when the ground is real:
  - the invented landuse and water polygons go; the imagery already has them
  - the road ribbons stop being the road and become HIGHLIGHTS - thin translucent
    overlays marking which carriageway is which, on top of the real asphalt
  - buildings default off over satellite, since the photograph shows them
  - crash markers get a dark halo, because a bright dot on busy mid-tone imagery
    is far harder to see than on a black field

The stacking behaviour that justified 3D is unchanged: shared coordinates rise as
columns, one body per crash, tallest holds 41.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SCENE = os.path.join(HERE, "corridor_scene.json")
BOUNDS = os.path.join(HERE, "basemap", "bounds.json")
OUT = os.path.join(HERE, "i4_satellite_map.html")


def main():
    with open(SCENE, encoding="utf-8") as fh:
        scene = json.load(fh)
    with open(BOUNDS, encoding="utf-8") as fh:
        bounds = json.load(fh)

    # Drop what the photograph already shows.
    scene.pop("land", None)
    scene.pop("water", None)

    html = (TEMPLATE
            .replace("/*__SCENE__*/", json.dumps(scene, separators=(",", ":")))
            .replace("/*__BOUNDS__*/", json.dumps(bounds)))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)

    o = scene["origin"]
    print(f"{scene['meta']['n']} crashes, {len(scene['roads'])} roads, "
          f"{len(scene['buildings'])} buildings")
    print(f"imagery {bounds['cols']}x{bounds['rows']} tiles at z{bounds['zoom']}")
    print(f"origin  {o['lat0']:.5f}, {o['lon0']:.5f}")
    print(f"Wrote {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)")


TEMPLATE = r"""<meta charset="utf-8">
<title>I-4 — 648 crashes on the ground</title>
<style>
  :root{
    --mono: ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
    --sans: system-ui,-apple-system,"Segoe UI",sans-serif;
    --ink:#f2f5f8; --dim:rgba(242,245,248,.55); --line:rgba(242,245,248,.16);
    --panel:rgba(10,13,18,.82);
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:#0b0f14;color:var(--ink);
            font-family:var(--sans);overflow:hidden}
  canvas{display:block}
  .ui{position:fixed;z-index:10;font-family:var(--mono);font-size:11px;
      letter-spacing:.03em}
  #head{top:0;left:0;right:0;padding:15px 22px 22px;pointer-events:none;
        background:linear-gradient(rgba(8,11,15,.92),transparent)}
  #head h1{font-family:var(--sans);font-size:19px;font-weight:500;margin:0 0 2px;
           text-shadow:0 1px 8px rgba(0,0,0,.7)}
  #head .s{color:var(--dim);font-size:10.5px;text-shadow:0 1px 6px rgba(0,0,0,.8)}

  #left{left:22px;top:96px;display:flex;flex-direction:column;gap:9px;
        max-height:calc(100vh - 125px);overflow-y:auto;padding-right:3px}
  .grp{background:var(--panel);border:1px solid var(--line);border-radius:4px;
       padding:9px 11px;backdrop-filter:blur(7px)}
  .grp>b{display:block;font-size:8.5px;letter-spacing:.15em;text-transform:uppercase;
         color:var(--dim);font-weight:400;margin-bottom:7px}
  .btns{display:flex;gap:2px;flex-wrap:wrap}
  .grp button{background:rgba(255,255,255,.06);border:1px solid var(--line);
    color:var(--dim);font:inherit;font-size:9.5px;letter-spacing:.07em;
    padding:5px 9px;cursor:pointer;transition:.15s;border-radius:3px}
  .grp button:hover{color:var(--ink);background:rgba(255,255,255,.14)}
  .grp button.on{background:#f2f5f8;color:#0b0f14;border-color:#f2f5f8}
  .grp label{display:flex;align-items:center;gap:7px;padding:2.5px 0;cursor:pointer;
             font-size:10px;color:var(--dim)}
  .grp label:hover{color:var(--ink)}
  .grp label i{width:11px;height:11px;border-radius:50%;display:block;flex:none;
               box-shadow:0 0 0 1.5px rgba(0,0,0,.55)}
  .grp label input{margin:0}
  .note{font-size:8.5px;color:var(--dim);line-height:1.5;margin-top:5px;
        max-width:190px}

  #detail{right:22px;bottom:20px;width:286px;background:var(--panel);
    border:1px solid var(--line);border-radius:4px;padding:13px 15px;
    opacity:0;transform:translateY(6px);transition:.18s;pointer-events:none;
    backdrop-filter:blur(7px)}
  #detail.on{opacity:1;transform:none}
  #detail .rp{font-family:var(--sans);font-size:15px;margin-bottom:2px}
  #detail .sv{font-size:9px;letter-spacing:.12em;text-transform:uppercase;
              margin-bottom:9px}
  #detail table{width:100%;border-collapse:collapse;font-size:10px}
  #detail td{padding:1.5px 0;vertical-align:top}
  #detail td:first-child{color:var(--dim);width:88px}
  #detail .warn{margin-top:9px;padding:7px 8px;background:rgba(255,176,60,.15);
    border-left:2px solid #ffb03c;font-size:9px;line-height:1.5;color:#ffdca8}
  #stats{right:22px;top:96px;text-align:right;color:var(--dim);line-height:1.7;
         text-shadow:0 1px 6px rgba(0,0,0,.85)}
  #stats b{color:var(--ink);font-variant-numeric:tabular-nums}
</style>

<div id="head" class="ui">
  <h1>648 crashes on the ground</h1>
  <div class="s">I-4 (SR 400), McIntosh Rd to Branch Forbes Rd &middot; 2021&ndash;2025
    &middot; Esri imagery &middot; drag to orbit, scroll to zoom</div>
</div>

<div id="left" class="ui">
  <div class="grp"><b>basemap</b><div class="btns" id="base">
    <button data-b="satellite" class="on">satellite</button>
    <button data-b="streets">streets</button>
  </div></div>

  <div class="grp"><b>fly to</b><div class="btns" id="cam">
    <button data-c="over">whole corridor</button>
    <button data-c="bf" class="on">Branch Forbes</button>
    <button data-c="mc">McIntosh</button>
    <button data-c="stack">tallest stack</button>
  </div></div>

  <div class="grp"><b>crashes &mdash; severity</b>
    <label><i style="background:#ff2d55"></i>fatality <span style="margin-left:auto" id="n-f"></span></label>
    <label><i style="background:#ff9500"></i>serious injury <span style="margin-left:auto" id="n-s"></span></label>
    <label><i style="background:#ffe14d"></i>injury <span style="margin-left:auto" id="n-i"></span></label>
    <label><i style="background:#4dd2ff"></i>no injury <span style="margin-left:auto" id="n-n"></span></label>
  </div>

  <div class="grp"><b>carriageway</b>
    <label><input type="checkbox" data-d="Westbound" checked>westbound <span style="margin-left:auto" id="n-wb"></span></label>
    <label><input type="checkbox" data-d="Eastbound" checked>eastbound <span style="margin-left:auto" id="n-eb"></span></label>
    <label><input type="checkbox" id="tDir" checked>split onto carriageways</label>
    <div class="note">Most mainline coordinates are snapped to the centreline.
      Split places each crash on the carriageway its record names &mdash; a
      placement rule, not a measured position.</div>
  </div>

  <div class="grp"><b>filter by where</b>
    <label><input type="checkbox" data-k="mainline" checked>on the mainline <span style="margin-left:auto" id="n-mainline"></span></label>
    <label><input type="checkbox" data-k="ramp_bf" checked>Branch Forbes ramps <span style="margin-left:auto" id="n-ramp_bf"></span></label>
    <label><input type="checkbox" data-k="ramp_mc" checked>McIntosh ramps <span style="margin-left:auto" id="n-ramp_mc"></span></label>
    <label><input type="checkbox" data-k="intersection" checked>at a junction <span style="margin-left:auto" id="n-intersection"></span></label>
  </div>

  <div class="grp"><b>overlays</b>
    <label><input type="checkbox" id="tHi" checked><i style="background:#39c5ff"></i>highlight carriageways</label>
    <label><input type="checkbox" id="tRamp" checked><i style="background:#ffb03c"></i>highlight ramps</label>
    <label><input type="checkbox" id="tCol" checked>stack columns</label>
    <label><input type="checkbox" id="tBld">buildings</label>
  </div>
</div>

<div id="stats" class="ui"></div>
<div id="detail" class="ui"></div>

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
const BOUNDS = /*__BOUNDS__*/;
const { roads, buildings, marks, bbox, meta, origin } = SCENE;

/* Severity ramp chosen to survive on photography: warm and bright for harm,
   cool and recessive for none. Every marker also gets a dark halo, because a
   bright dot on mid-tone imagery is far weaker than on a black field. */
const SEV = {
  "Fatality":       { c:0xff2d55, s:2.6 },
  "Serious Injury": { c:0xff9500, s:2.0 },
  "Injury":         { c:0xffe14d, s:1.4 },
  "No Injury":      { c:0x4dd2ff, s:0.95 },
};
const CLASS_LABEL = { mainline:"on the mainline", ramp_bf:"Branch Forbes ramp",
                      ramp_mc:"McIntosh ramp", intersection:"at a junction" };
const FLOOR_H = 2.6;
const SPREAD = 2.4;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0b0f14);
const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.3, 9000);
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.maxPolarAngle = Math.PI * 0.492;
controls.zoomToCursor = true; controls.zoomSpeed = 0.75;
controls.minDistance = 5; controls.maxDistance = 1800;

scene.add(new THREE.AmbientLight(0xffffff, 1.25));
const key = new THREE.DirectionalLight(0xffffff, 0.35);
key.position.set(-1, 2.4, 1.2); scene.add(key);

/* ---------- the imagery, placed by computation ---------- */
const { lat0, lon0, mLat, mLon, unit } = origin;
const toX = lon => (lon - lon0) * mLon * unit;
const toZ = lat => -(lat - lat0) * mLat * unit;

const gx0 = toX(BOUNDS.west),  gx1 = toX(BOUNDS.east);
const gz0 = toZ(BOUNDS.north), gz1 = toZ(BOUNDS.south);

const loader = new THREE.TextureLoader();
const groundMat = new THREE.MeshBasicMaterial({ color:0x1a1f26 });
const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(gx1 - gx0, gz1 - gz0), groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.set((gx0 + gx1)/2, 0, (gz0 + gz1)/2);
scene.add(ground);

const textures = {};
function setBase(name){
  if (textures[name]){ groundMat.map = textures[name]; groundMat.needsUpdate = true; return; }
  loader.load(`basemap/${name}.jpg`, tex => {
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
    textures[name] = tex;
    groundMat.map = tex; groundMat.color.set(0xffffff);
    groundMat.needsUpdate = true;
  });
}
// initial base is chosen after the hash is read, further down

/* ---------- carriageway / ramp highlights ---------- */
function ribbon(pts, width){
  const v = [], idx = [], hw = width/2;
  for (let i=0;i<pts.length;i++){
    const p = pts[i];
    const a = pts[Math.max(0,i-1)], b = pts[Math.min(pts.length-1,i+1)];
    let dx=b[0]-a[0], dz=b[1]-a[1];
    const L=Math.hypot(dx,dz)||1; dx/=L; dz/=L;
    v.push(p[0]-dz*hw, 0, p[1]+dx*hw, p[0]+dz*hw, 0, p[1]-dx*hw);
  }
  for (let i=0;i<pts.length-1;i++){ const a=i*2; idx.push(a,a+2,a+1,a+1,a+2,a+3); }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(v,3));
  g.setIndex(idx);
  const n = new Float32Array(v.length);
  for (let i=1;i<n.length;i+=3) n[i]=1;
  g.setAttribute("normal", new THREE.BufferAttribute(n,3));
  return g;
}

/* Which carriageway a way is on, from its heading against the corridor axis. */
const AXIS = (() => {
  let ax=0, az=0;
  for (const r of roads){
    if (r.k !== "mainline") continue;
    let dx=r.p[r.p.length-1][0]-r.p[0][0], dz=r.p[r.p.length-1][1]-r.p[0][1];
    if (dx<0){ dx=-dx; dz=-dz; }
    ax+=dx; az+=dz;
  }
  const L=Math.hypot(ax,az)||1; return {x:ax/L, z:az/L};
})();
const sideOfWay = r => {
  const dx=r.p[r.p.length-1][0]-r.p[0][0], dz=r.p[r.p.length-1][1]-r.p[0][1];
  return (dx*AXIS.x + dz*AXIS.z) >= 0 ? 1 : -1;
};

const overlays = {};
(function highlights(){
  for (const [kind, colour, w] of [["mainline", 0x39c5ff, 2.2],
                                   ["ramp", 0xffb03c, 1.5]]){
    const list = roads.filter(r => r.k === kind);
    if (!list.length) continue;
    const geos = list.map(r => {
      const g = ribbon(r.p, r.w * w);
      g.translate(0, 0.22, 0);
      return g;
    });
    const mesh = new THREE.Mesh(
      BufferGeometryUtils.mergeGeometries(geos, false),
      new THREE.MeshBasicMaterial({ color:colour, transparent:true,
        opacity:0.30, side:THREE.DoubleSide, depthWrite:false }));
    scene.add(mesh); overlays[kind] = mesh;
  }
})();

/* ---------- buildings, off by default over photography ---------- */
let buildingMesh = null;
(function bldgs(){
  const geos = [];
  for (const b of buildings){
    if (b.p.length < 3) continue;
    try {
      const shape = new THREE.Shape(b.p.map(p => new THREE.Vector2(p[0], -p[1])));
      const g = new THREE.ExtrudeGeometry(shape, { depth:b.h, bevelEnabled:false });
      g.rotateX(-Math.PI/2);
      geos.push(g);
    } catch(e){}
  }
  if (!geos.length) return;
  buildingMesh = new THREE.Mesh(
    BufferGeometryUtils.mergeGeometries(geos, false),
    new THREE.MeshStandardMaterial({ color:0x8a929c, roughness:0.95,
      transparent:true, opacity:0.55 }));
  buildingMesh.visible = false;
  scene.add(buildingMesh);
})();

/* ---------- crashes ---------- */
const markers = [], columns = [];
const dirSign = m => m.dir === "Eastbound" ? 1 : m.dir === "Westbound" ? -1 : 0;
const PERP = { x:-AXIS.z, z:AXIS.x };
let dirOffset = true;

const ballGeo = new THREE.SphereGeometry(1, 18, 14);
const haloGeo = new THREE.SphereGeometry(1, 12, 10);
const counts = { mainline:0, ramp_bf:0, ramp_mc:0, intersection:0 };
const sevCount = {};

for (const m of marks){
  m.cls = m.k;
  counts[m.cls] = (counts[m.cls]||0)+1;
  sevCount[m.sev] = (sevCount[m.sev]||0)+1;
  const spec = SEV[m.sev] || SEV["No Injury"];
  const off = dirSign(m) * SPREAD;
  const y = m.f * FLOOR_H + 1.5;

  // dark halo first, so the marker survives busy imagery
  const halo = new THREE.Mesh(haloGeo, new THREE.MeshBasicMaterial({
    color:0x000000, transparent:true, opacity:0.5, depthWrite:false }));
  halo.position.set(m.x + PERP.x*off, y, m.z + PERP.z*off);
  halo.scale.setScalar(spec.s * 1.55);
  scene.add(halo);

  const mesh = new THREE.Mesh(ballGeo, new THREE.MeshBasicMaterial({
    color: spec.c }));
  mesh.position.copy(halo.position);
  mesh.scale.setScalar(spec.s);
  mesh.userData = { m, s:spec.s, y, x0:m.x, z0:m.z, sign:dirSign(m), halo };
  scene.add(mesh); markers.push(mesh);
}

document.getElementById("n-f").textContent = sevCount["Fatality"]||0;
document.getElementById("n-s").textContent = sevCount["Serious Injury"]||0;
document.getElementById("n-i").textContent = sevCount["Injury"]||0;
document.getElementById("n-n").textContent = sevCount["No Injury"]||0;
for (const k in counts){
  const el = document.getElementById("n-"+k); if (el) el.textContent = counts[k];
}
document.getElementById("n-wb").textContent = marks.filter(m=>m.dir==="Westbound").length;
document.getElementById("n-eb").textContent = marks.filter(m=>m.dir==="Eastbound").length;

let tallest = null;
(function cols(){
  const groups = {};
  for (const m of marks){
    const k = m.x+","+m.z+","+m.dir;
    (groups[k] = groups[k]||[]).push(m);
  }
  for (const k in groups){
    const g = groups[k];
    if (g.length < 2) continue;
    const h = (g.length-1)*FLOOR_H + 2.8;
    const heat = Math.min(1, g.length/meta.tallest);
    const off = dirSign(g[0]) * SPREAD;
    const cyl = new THREE.Mesh(
      new THREE.CylinderGeometry(0.34, 0.34, h, 8),
      new THREE.MeshBasicMaterial({ color:0xffffff, transparent:true,
        opacity:0.16 + heat*0.4, depthWrite:false }));
    cyl.position.set(g[0].x + PERP.x*off, h/2, g[0].z + PERP.z*off);
    cyl.userData = { x0:g[0].x, z0:g[0].z, sign:dirSign(g[0]) };
    scene.add(cyl); columns.push(cyl);
    if (!tallest || g.length > tallest.n)
      tallest = { x:cyl.position.x, z:cyl.position.z, n:g.length, h };
  }
})();

/* ---------- camera ---------- */
const CX=(bbox.x0+bbox.x1)/2, CZ=(bbox.z0+bbox.z1)/2;
const bf = marks.filter(m=>m.k==="ramp_bf"), mc = marks.filter(m=>m.k==="ramp_mc");
const avg = (a,f)=>a.reduce((s,m)=>s+f(m),0)/Math.max(1,a.length);

/* The control column occupies roughly the left third of the window, so a target
   centred in the viewport lands underneath it. Shift each view along the
   corridor axis so the subject sits in the clear right-hand area. */
const PANEL_SHIFT = 0.30;
function view(tx, tz, dist, height){
  const sx = AXIS.x * dist * PANEL_SHIFT, sz = AXIS.z * dist * PANEL_SHIFT;
  return { t:[tx + sx, 4, tz + sz],
           p:[tx + sx - dist*0.62, height, tz + sz + dist*0.78] };
}
const VIEWS = {
  over:  view(CX, CZ, 520, 300),
  bf:    view(avg(bf,m=>m.x), avg(bf,m=>m.z), 170, 96),
  mc:    view(avg(mc,m=>m.x), avg(mc,m=>m.z), 165, 92),
  stack: { t:[0,0,0], p:[0,0,0] },
};
if (tallest) VIEWS.stack = {
  t:[tallest.x + AXIS.x*26, tallest.h*0.5, tallest.z + AXIS.z*26],
  p:[tallest.x + AXIS.x*26 - 34, tallest.h*0.9+24, tallest.z + AXIS.z*26 + 44] };
let anim = null;
function flyTo(n){
  const v = VIEWS[n]; if (!v) return;
  anim = { t0:performance.now(), dur:850,
           fromP:camera.position.clone(), fromT:controls.target.clone(),
           toP:new THREE.Vector3(...v.p), toT:new THREE.Vector3(...v.t) };
}
/* Deep link: #v=over&b=streets — so a specific view can be opened or captured. */
const HASH = new URLSearchParams(location.hash.slice(1));
const startView = VIEWS[HASH.get("v")] ? HASH.get("v") : "bf";
const startBase = HASH.get("b") === "streets" ? "streets" : "satellite";
camera.position.set(...VIEWS[startView].p);
controls.target.set(...VIEWS[startView].t);

/* ---------- controls ---------- */
const hidden = new Set(), hiddenDir = new Set();
document.getElementById("base").onclick = e => {
  const b = e.target.closest("button"); if(!b) return;
  [...b.parentNode.children].forEach(c=>c.classList.toggle("on",c===b));
  setBase(b.dataset.b);
};
document.getElementById("cam").onclick = e => {
  const b = e.target.closest("button"); if(!b) return;
  [...b.parentNode.children].forEach(c=>c.classList.toggle("on",c===b));
  flyTo(b.dataset.c);
};
document.querySelectorAll("[data-k]").forEach(cb => cb.onchange = () => {
  cb.checked ? hidden.delete(cb.dataset.k) : hidden.add(cb.dataset.k); apply(); });
document.querySelectorAll("[data-d]").forEach(cb => cb.onchange = () => {
  cb.checked ? hiddenDir.delete(cb.dataset.d) : hiddenDir.add(cb.dataset.d); apply(); });
document.getElementById("tHi").onchange = e => {
  if (overlays.mainline) overlays.mainline.visible = e.target.checked; };
document.getElementById("tRamp").onchange = e => {
  if (overlays.ramp) overlays.ramp.visible = e.target.checked; };
document.getElementById("tCol").onchange = e => {
  for (const c of columns) c.visible = e.target.checked; };
document.getElementById("tBld").onchange = e => {
  if (buildingMesh) buildingMesh.visible = e.target.checked; };
document.getElementById("tDir").onchange = e => { dirOffset = e.target.checked; place(); };

function place(){
  for (const mesh of markers){
    const u = mesh.userData, off = dirOffset ? u.sign*SPREAD : 0;
    mesh.position.x = u.x0 + PERP.x*off; mesh.position.z = u.z0 + PERP.z*off;
    u.halo.position.copy(mesh.position);
  }
  for (const c of columns){
    const u = c.userData, off = dirOffset ? u.sign*SPREAD : 0;
    c.position.x = u.x0 + PERP.x*off; c.position.z = u.z0 + PERP.z*off;
  }
}

function apply(){
  let shown = 0;
  for (const mesh of markers){
    const m = mesh.userData.m;
    const v = !hidden.has(m.cls) && !hiddenDir.has(m.dir);
    mesh.visible = v; mesh.userData.halo.visible = v;
    if (v) shown++;
  }
  document.getElementById("stats").innerHTML =
    `<b>${shown}</b> of ${meta.n} crashes<br>`+
    `<b>${meta.coords}</b> distinct coordinates<br>`+
    `<b>${meta.tallest}</b> on the tallest point`;
}

/* ---------- hover ---------- */
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
const detail = document.getElementById("detail");
let hover = null;
addEventListener("pointermove", e => {
  mouse.x = (e.clientX/innerWidth)*2-1;
  mouse.y = -(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(mouse, camera);
  const hits = ray.intersectObjects(markers.filter(m=>m.visible), false);
  const hit = hits.length ? hits[0].object : null;
  if (hit === hover) return;
  if (hover) hover.scale.setScalar(hover.userData.s);
  hover = hit;
  if (!hit){ detail.classList.remove("on"); return; }
  hit.scale.setScalar(hit.userData.s*1.8);
  const m = hit.userData.m;
  const col = "#"+(SEV[m.sev]||SEV["No Injury"]).c.toString(16).padStart(6,"0");
  const flags = [m.cmv&&"commercial vehicle", m.spd&&"speeding",
                 m.ldp&&"lane departure"].filter(Boolean);
  detail.innerHTML =
    `<div class="rp">Report ${m.id||"—"}</div>`+
    `<div class="sv" style="color:${col}">${m.sev} &middot; ${CLASS_LABEL[m.cls]}</div>`+
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
});

addEventListener("resize", () => {
  camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

setBase(startBase);
document.querySelectorAll("#base button").forEach(b =>
  b.classList.toggle("on", b.dataset.b === startBase));
document.querySelectorAll("#cam button").forEach(b =>
  b.classList.toggle("on", b.dataset.c === startView));

window.__dbg = { scene, camera, controls, renderer, markers, columns,
                 overlays, ground, VIEWS, THREE };
apply();

let t = 0;
(function loop(){
  requestAnimationFrame(loop);
  t += 0.006;
  if (anim){
    const k = Math.min(1,(performance.now()-anim.t0)/anim.dur);
    const e = k<0.5 ? 4*k*k*k : 1-Math.pow(-2*k+2,3)/2;
    camera.position.lerpVectors(anim.fromP, anim.toP, e);
    controls.target.lerpVectors(anim.fromT, anim.toT, e);
    if (k>=1) anim = null;
  }
  for (const mesh of markers){
    if (mesh.userData.m.sev === "Fatality" && mesh.visible && mesh !== hover)
      mesh.scale.setScalar(mesh.userData.s*(1+Math.sin(t*2.2)*0.15));
  }
  controls.update();
  renderer.render(scene, camera);
})();
</script>
"""


if __name__ == "__main__":
    main()
