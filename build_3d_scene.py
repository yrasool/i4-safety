"""
The I-4 corridor in three dimensions, in twelve styles.

Why 3D at all: 350 of 648 crashes share a coordinate, and one point carries 41.
Flat, that is a single dot hiding forty records - the worst defect in the original
analysis and invisible in every map in the source folder. Given a vertical axis it
inverts. A shared coordinate becomes a column, each crash gets its own body, and
the tallest towers mark exactly where the geolocation collapsed.

Y is NOT elevation. Y is position within the stack. Said on the page, because a
3D scene implying false terrain would be worse than the flat map it replaces.

Styles live in styles_3d.py, each derived from a named reference in Yusra's
Reference Room, with colours sampled from that reference's own image where the
image allowed it.
"""

import json
import os

from styles_3d import STYLES

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "i4_crashes_3d.json")
OUT = os.path.join(HERE, "i4_corridor_3d.html")


def main():
    with open(SRC, encoding="utf-8") as fh:
        crashes = json.load(fh)

    lats = [c["lat"] for c in crashes]
    lons = [c["lon"] for c in crashes]
    meta = {
        "n": len(crashes),
        "coords": len({(c["lat"], c["lon"]) for c in crashes}),
        "tallest": max(c["n"] for c in crashes),
        "stacked": sum(1 for c in crashes if c["n"] > 1),
        "latMin": min(lats), "latMax": max(lats),
        "lonMin": min(lons), "lonMax": max(lons),
    }
    print(f"{meta['n']} crashes, {meta['coords']} coordinates, "
          f"tallest {meta['tallest']}, stacked {meta['stacked']}")
    print(f"{len(STYLES)} styles: " + ", ".join(s['name'] for s in STYLES))

    html = (TEMPLATE
            .replace("/*__CRASHES__*/", json.dumps(crashes, separators=(",", ":")))
            .replace("/*__META__*/", json.dumps(meta))
            .replace("/*__STYLES__*/", json.dumps(STYLES, separators=(",", ":"))))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"\nWrote {OUT}  ({os.path.getsize(OUT) / 1024:.0f} KB)")


TEMPLATE = r"""<meta charset="utf-8">
<title>I-4 corridor — 648 crashes, one body each</title>
<style>
  :root{
    --mono: ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
    --sans: system-ui,-apple-system,"Segoe UI",sans-serif;
    --ink:#e8edf2; --dim:rgba(232,237,242,.45); --line:rgba(232,237,242,.14);
    --panel:rgba(4,6,10,.82);
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:#04060a;color:var(--ink);
            font-family:var(--sans);overflow:hidden;transition:background .5s}
  canvas{display:block}
  #grain{position:fixed;inset:0;z-index:5;pointer-events:none;opacity:0;
         mix-blend-mode:overlay;transition:opacity .4s}

  .ui{position:fixed;z-index:10;font-family:var(--mono);font-size:11px;
      letter-spacing:.04em;color:var(--ink)}
  #head{top:0;left:0;right:0;padding:18px 24px 30px;pointer-events:none}
  #head h1{font-family:var(--sans);font-size:20px;font-weight:500;margin:0 0 3px;
           letter-spacing:-.01em}
  #head .s{color:var(--dim);font-size:10.5px}
  #head .stats{margin-top:12px;display:flex;gap:24px;font-variant-numeric:tabular-nums}
  #head .stats b{display:block;font-size:16px;font-weight:500;margin-bottom:1px}
  #head .stats span{font-size:9px;color:var(--dim);letter-spacing:.1em;
                    text-transform:uppercase}

  #styles{left:24px;top:150px;display:flex;flex-direction:column;gap:1px;
          background:var(--panel);border:1px solid var(--line);border-radius:3px;
          padding:6px;backdrop-filter:blur(4px);max-height:calc(100vh - 300px);
          overflow-y:auto}
  #styles button{background:transparent;border:0;color:var(--dim);font:inherit;
    font-size:10px;letter-spacing:.06em;padding:6px 10px;cursor:pointer;
    text-align:left;transition:.15s;border-radius:2px;white-space:nowrap}
  #styles button:hover{color:var(--ink);background:rgba(255,255,255,.07)}
  #styles button.on{background:var(--ink);color:var(--bg,#04060a)}
  #styles button i{display:block;font-style:normal;font-size:8.5px;opacity:.55;
                   margin-top:2px;letter-spacing:.02em}

  #ctl{right:24px;top:150px;display:flex;flex-direction:column;gap:13px;
       align-items:flex-end}
  .grp{display:flex;flex-direction:column;gap:5px;align-items:flex-end}
  .grp>b{font-size:9px;letter-spacing:.13em;text-transform:uppercase;
         color:var(--dim);font-weight:400}
  .grp .btns{display:flex;gap:2px}
  .grp button{background:var(--panel);border:1px solid var(--line);
    color:var(--dim);font:inherit;font-size:10px;letter-spacing:.09em;
    text-transform:uppercase;padding:5px 10px;cursor:pointer;transition:.16s}
  .grp button:hover{color:var(--ink)}
  .grp button.on{background:var(--ink);color:var(--bg,#04060a);border-color:var(--ink)}

  #legend{left:24px;bottom:22px;display:flex;flex-direction:column;gap:6px;
          background:var(--panel);padding:12px 14px;border:1px solid var(--line);
          border-radius:3px;backdrop-filter:blur(4px)}
  #legend .row{display:flex;align-items:center;gap:9px;cursor:pointer;
               transition:opacity .2s;font-size:10.5px}
  #legend .row.off{opacity:.26}
  #legend .row i{width:9px;height:9px;border-radius:50%;display:block;flex:none}
  #legend .row span{color:var(--dim);margin-left:auto;padding-left:14px;
                    font-variant-numeric:tabular-nums}
  #legend .note{margin-top:8px;padding-top:8px;border-top:1px solid var(--line);
                color:var(--dim);font-size:9.5px;line-height:1.6;max-width:236px}

  #detail{right:24px;bottom:22px;width:290px;background:var(--panel);
    border:1px solid var(--line);border-radius:3px;padding:14px 16px;
    opacity:0;transform:translateY(6px);transition:.18s;pointer-events:none;
    backdrop-filter:blur(4px)}
  #detail.on{opacity:1;transform:none}
  #detail .rp{font-family:var(--sans);font-size:15px;margin-bottom:3px}
  #detail .sv{font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;
              margin-bottom:10px}
  #detail table{width:100%;border-collapse:collapse;font-size:10.5px}
  #detail td{padding:2px 0;vertical-align:top}
  #detail td:first-child{color:var(--dim);width:92px}
  #detail .warn{margin-top:10px;padding:8px 9px;background:rgba(255,180,60,.13);
    border-left:2px solid #ffb43c;font-size:9.5px;line-height:1.55;color:#ffd79a}
</style>

<div id="grain"></div>

<div id="head" class="ui">
  <h1>Every crash, one body each</h1>
  <div class="s">I-4 (SR 400), McIntosh Rd to Branch Forbes Rd &middot; 2021&ndash;2025
    &middot; drag to orbit, scroll to zoom</div>
  <div class="stats">
    <div><b id="s1">0</b><span>crashes</span></div>
    <div><b id="s2">0</b><span>coordinates</span></div>
    <div><b id="s3">0</b><span>tallest stack</span></div>
    <div><b id="s4">0</b><span>on a shared point</span></div>
  </div>
</div>

<nav id="styles" class="ui"></nav>

<div id="ctl" class="ui">
  <div class="grp"><b>severity</b><div class="btns" id="fsev">
    <button data-s="all" class="on">all</button>
    <button data-s="inj">injury+</button>
    <button data-s="ksi">killed / serious</button>
  </div></div>
  <div class="grp"><b>columns</b><div class="btns" id="fcol">
    <button data-c="on" class="on">stacked</button>
    <button data-c="off">flattened</button>
  </div></div>
  <div class="grp"><b>motion</b><div class="btns" id="fspin">
    <button data-r="off" class="on">still</button>
    <button data-r="on">orbit</button>
  </div></div>
</div>

<div id="legend" class="ui"></div>
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

const CRASHES = /*__CRASHES__*/;
const META = /*__META__*/;
const STYLES = /*__STYLES__*/;

const LABELS = { mainline:"mainline", intersection:"junction coded",
                 ramp_bf:"Branch Forbes ramps", ramp_mc:"McIntosh ramps" };
const SEV_SCALE = { "Fatality":2.3, "Serious Injury":1.7, "Injury":1.2, "No Injury":0.85 };

/* projection: local metres, corridor centred */
const LAT0 = (META.latMin + META.latMax) / 2;
const M_LAT = 111320, M_LON = 111320 * Math.cos(LAT0 * Math.PI / 180);
const cxDeg = (META.lonMin + META.lonMax) / 2;
const UNIT = 0.1, FLOOR_H = 2.6;
const pos = c => ({
  x: (c.lon - cxDeg) * M_LON * UNIT,
  z: -(c.lat - LAT0) * M_LAT * UNIT,
  y: c.f * FLOOR_H + 1.2,
});

let S = STYLES[0];
let sevMode = "all", stacked = true, spinning = false;
const hidden = new Set();

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(46, innerWidth/innerHeight, 0.5, 4000);
camera.position.set(-330, 235, 395);
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.06;
controls.maxPolarAngle = Math.PI * 0.495;
controls.target.set(0, 26, 0);

const amb = new THREE.AmbientLight(0xffffff, 0.75); scene.add(amb);
const key = new THREE.DirectionalLight(0xffffff, 0.55);
key.position.set(-1, 2, 1); scene.add(key);

/* groups rebuilt whenever the style changes */
let gGround = new THREE.Group(), gMarks = new THREE.Group(), gCols = new THREE.Group();
scene.add(gGround, gMarks, gCols);
let markers = [], columns = [];

function clear(g){
  while(g.children.length){
    const o = g.children.pop();
    o.geometry?.dispose?.(); o.material?.dispose?.();
  }
}

function geoFor(style){
  switch(style.geo){
    case "box":   return new THREE.BoxGeometry(1.7, 1.7, 1.7);
    case "point": return new THREE.SphereGeometry(0.62, 8, 6);
    case "bar":   return new THREE.CylinderGeometry(0.62, 0.62, 2.2, 6);
    default:      return new THREE.SphereGeometry(1, 14, 10);
  }
}

function lerpHex(a, b, t){
  const A = new THREE.Color(a), B = new THREE.Color(b);
  return A.lerp(B, t);
}

function buildGround(){
  clear(gGround);
  const span = Math.max(
    (META.lonMax - META.lonMin) * M_LON * UNIT,
    (META.latMax - META.latMin) * M_LAT * UNIT) * 1.25;
  const grid = new THREE.GridHelper(span, 46, new THREE.Color(S.grid1),
                                    new THREE.Color(S.grid2));
  gGround.add(grid);

  const main = CRASHES.filter(c => c.k === "mainline" && c.mp !== null)
                      .sort((a,b) => a.mp - b.mp);
  if (main.length > 2){
    const pts = main.map(c => { const p = pos(c);
      return new THREE.Vector3(p.x, 0.35, p.z); });
    const curve = new THREE.CatmullRomCurve3(pts, false, "catmullrom", 0.15);
    gGround.add(new THREE.Mesh(
      new THREE.TubeGeometry(curve, 320, 1.5, 8, false),
      new THREE.MeshBasicMaterial({ color:new THREE.Color(S.road),
        transparent:true, opacity:0.85 })));
  }
}

function buildMarkers(){
  clear(gMarks); markers = [];
  const geo = geoFor(S);
  for (const c of CRASHES){
    const col = new THREE.Color(S.classes[c.k] || S.classes.mainline);
    const m = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
      color: col, emissive: col,
      emissiveIntensity: c.sev === "No Injury" ? S.dim : S.emissive,
      roughness: S.rough, metalness: S.metal }));
    const p = pos(c);
    m.position.set(p.x, p.y, p.z);
    const s = SEV_SCALE[c.sev] || 0.9;
    m.scale.setScalar(s);
    m.userData = { c, base:p, s };
    gMarks.add(m); markers.push(m);
  }
}

function buildColumns(){
  clear(gCols); columns = [];
  const groups = {};
  for (const c of CRASHES){
    const k = c.lat + "," + c.lon;
    (groups[k] = groups[k] || []).push(c);
  }
  for (const k in groups){
    const g = groups[k];
    if (g.length < 2) continue;
    const p = pos(g[0]);
    const heat = Math.min(1, g.length / META.tallest);

    if (S.column === "strata"){
      // one slab per floor, shaded by depth: a stack reads as a cross-section
      for (let i = 0; i < g.length; i++){
        const t = i / Math.max(1, g.length - 1);
        const slab = new THREE.Mesh(
          new THREE.CylinderGeometry(0.9, 0.9, FLOOR_H * 0.55, 8),
          new THREE.MeshBasicMaterial({ color: lerpHex(S.colA, S.colB, t),
            transparent:true, opacity:0.55 }));
        slab.position.set(p.x, i * FLOOR_H + 1.2, p.z);
        gCols.add(slab); columns.push(slab);
      }
    } else {
      const h = (g.length - 1) * FLOOR_H + 2.4;
      const col = S.column === "heat" ? lerpHex(S.colA, S.colB, heat)
                                      : new THREE.Color(S.colB);
      const cyl = new THREE.Mesh(
        new THREE.CylinderGeometry(0.28, 0.28, h, 6),
        new THREE.MeshBasicMaterial({ color: col, transparent:true,
          opacity: S.column === "heat" ? 0.3 + heat * 0.5 : 0.34 }));
      cyl.position.set(p.x, h/2, p.z);
      gCols.add(cyl); columns.push(cyl);
    }
  }
}

/* grain overlay, generated once and re-tinted by opacity */
(function makeGrain(){
  const c = document.createElement("canvas"); c.width = c.height = 160;
  const g = c.getContext("2d");
  const img = g.createImageData(160,160);
  for (let i = 0; i < img.data.length; i += 4){
    const v = 128 + (Math.random()-0.5) * 255;
    img.data[i] = img.data[i+1] = img.data[i+2] = v; img.data[i+3] = 255;
  }
  g.putImageData(img, 0, 0);
  document.getElementById("grain").style.backgroundImage = `url(${c.toDataURL()})`;
})();

function applyStyle(){
  scene.background = new THREE.Color(S.bg);
  scene.fog = new THREE.Fog(new THREE.Color(S.bg), S.fogNear, S.fogFar);
  document.body.style.background = S.bg;
  const r = document.documentElement.style;
  r.setProperty("--ink", S.ink);
  r.setProperty("--bg", S.bg);
  const light = new THREE.Color(S.bg).getHSL({}).l > 0.5;
  r.setProperty("--dim", light ? "rgba(35,31,26,.55)" : "rgba(232,237,242,.45)");
  r.setProperty("--line", light ? "rgba(35,31,26,.18)" : "rgba(232,237,242,.14)");
  r.setProperty("--panel", light ? "rgba(255,255,255,.8)" : "rgba(4,6,10,.82)");
  amb.intensity = light ? 1.0 : 0.75;
  document.getElementById("grain").style.opacity = S.grain;
  buildGround(); buildMarkers(); buildColumns(); apply();
}

/* interaction */
const ray = new THREE.Raycaster();
const mouse = new THREE.Vector2();
const detail = document.getElementById("detail");
let hoverMesh = null;

addEventListener("pointermove", e => {
  mouse.x = (e.clientX/innerWidth)*2 - 1;
  mouse.y = -(e.clientY/innerHeight)*2 + 1;
  ray.setFromCamera(mouse, camera);
  const hits = ray.intersectObjects(markers.filter(m => m.visible), false);
  const hit = hits.length ? hits[0].object : null;
  if (hit === hoverMesh) return;
  if (hoverMesh) hoverMesh.scale.setScalar(hoverMesh.userData.s);
  hoverMesh = hit;
  if (!hit){ detail.classList.remove("on"); return; }
  hit.scale.setScalar(hit.userData.s * 1.9);
  showDetail(hit.userData.c);
});

function showDetail(c){
  const col = S.classes[c.k] || S.classes.mainline;
  const flags = [c.cmv && "commercial vehicle", c.spd && "speeding",
                 c.ldp && "lane departure"].filter(Boolean);
  detail.innerHTML =
    `<div class="rp">Report ${c.id || "—"}</div>`+
    `<div class="sv" style="color:${col}">${c.sev} &middot; ${LABELS[c.k]}</div>`+
    `<table>`+
    `<tr><td>when</td><td>${c.dt || c.yr}</td></tr>`+
    `<tr><td>direction</td><td>${c.dir}</td></tr>`+
    `<tr><td>type</td><td>${c.typ}</td></tr>`+
    (c.hrm?`<tr><td>first harm</td><td>${c.hrm}</td></tr>`:"")+
    `<tr><td>light</td><td>${c.lgt}</td></tr>`+
    `<tr><td>surface</td><td>${c.surf}</td></tr>`+
    (c.mp!==null?`<tr><td>milepost</td><td>${c.mp.toFixed(3)}</td></tr>`:"")+
    `<tr><td>vehicles</td><td>${c.veh}</td></tr>`+
    (c.inj?`<tr><td>injuries</td><td>${c.inj}</td></tr>`:"")+
    (flags.length?`<tr><td>flags</td><td>${flags.join(", ")}</td></tr>`:"")+
    `</table>`+
    (c.n > 1 ? `<div class="warn"><b>${c.n} crashes share this exact
       coordinate</b> — floor ${c.f+1} of that column. The position is a milepost
       lookup, not a measured location.</div>` : "");
  detail.classList.add("on");
}

function passes(c){
  if (hidden.has(c.k)) return false;
  if (sevMode === "inj" && c.sev === "No Injury") return false;
  if (sevMode === "ksi" && !(c.sev === "Fatality" || c.sev === "Serious Injury"))
    return false;
  return true;
}

function apply(){
  for (const m of markers){
    m.visible = passes(m.userData.c);
    m.position.y = stacked ? m.userData.base.y : 1.2;
  }
  for (const c of columns) c.visible = stacked;
  buildLegend();
}

function buildLegend(){
  const lg = document.getElementById("legend");
  lg.innerHTML = "";
  for (const k in LABELS){
    const shown = CRASHES.filter(c => c.k === k && passes(c)).length;
    const total = CRASHES.filter(c => c.k === k).length;
    if (!total) continue;
    const row = document.createElement("div");
    row.className = "row" + (hidden.has(k) ? " off" : "");
    row.innerHTML = `<i style="background:${S.classes[k]}"></i>${LABELS[k]}`+
                    `<span>${shown}</span>`;
    row.onclick = () => { hidden.has(k) ? hidden.delete(k) : hidden.add(k); apply(); };
    lg.appendChild(row);
  }
  const note = document.createElement("div");
  note.className = "note";
  note.textContent = "Height is position in the stack, not elevation. Where "+
    "crashes share a coordinate they rise as a column — the tallest holds 41.";
  lg.appendChild(note);
}

/* style switcher */
const nav = document.getElementById("styles");
STYLES.forEach((st, i) => {
  const b = document.createElement("button");
  b.className = i === 0 ? "on" : "";
  b.innerHTML = `${st.name}<i>${st.src}</i>`;
  b.onclick = () => {
    S = st;
    [...nav.children].forEach((c, j) => c.classList.toggle("on", j === i));
    applyStyle();
  };
  nav.appendChild(b);
});

document.getElementById("fsev").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  sevMode = b.dataset.s;
  [...b.parentNode.children].forEach(x => x.classList.toggle("on", x === b));
  apply();
};
document.getElementById("fcol").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  stacked = b.dataset.c === "on";
  [...b.parentNode.children].forEach(x => x.classList.toggle("on", x === b));
  apply();
};
document.getElementById("fspin").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  spinning = b.dataset.r === "on";
  [...b.parentNode.children].forEach(x => x.classList.toggle("on", x === b));
};

document.getElementById("s1").textContent = META.n;
document.getElementById("s2").textContent = META.coords;
document.getElementById("s3").textContent = META.tallest;
document.getElementById("s4").textContent = META.stacked;

addEventListener("resize", () => {
  camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

/* deep link: #s=strata */
(function fromHash(){
  const h = new URLSearchParams(location.hash.slice(1));
  const id = h.get("s");
  const i = STYLES.findIndex(x => x.id === id);
  if (i >= 0){
    S = STYLES[i];
    [...nav.children].forEach((c, j) => c.classList.toggle("on", j === i));
  }
})();

applyStyle();

let t = 0;
(function loop(){
  requestAnimationFrame(loop);
  t += 0.006;
  for (const m of markers){
    if (m.userData.c.sev === "Fatality" && m.visible && m !== hoverMesh){
      m.scale.setScalar(m.userData.s * (1 + Math.sin(t*2.2)*0.16));
    }
  }
  if (spinning) controls.autoRotate = true, controls.autoRotateSpeed = 0.5;
  else controls.autoRotate = false;
  controls.update();
  renderer.render(scene, camera);
})();
</script>
"""


if __name__ == "__main__":
    main()
