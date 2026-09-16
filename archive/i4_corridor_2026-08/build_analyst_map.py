"""
The analyst map: every crash, every field, cross-filtered, on real imagery.

What separates this from a crash map is that it can be interrogated. A traffic
analyst does not want to look at 648 dots - they want to ask "night-time,
wet-road, lane-departure crashes involving a truck, westbound" and see instantly
where those are and what hour they happen.

So every field in the extract is a filter, all filters compose, and three things
update together on every change: the map, a live count, and a 24-hour profile of
whatever is currently selected. The hour histogram is the part that makes it an
instrument rather than a picture - it answers WHEN, which a map alone cannot.

Colour is switchable, because what you want it to encode changes with the
question: severity, crash type, light, carriageway, or a contributing factor.

Ground is Esri imagery, placed by computation from the projection origin.
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DETAIL = os.path.join(HERE, "i4_full_detail.json")
SCENE = os.path.join(HERE, "corridor_scene.json")
BOUNDS = os.path.join(HERE, "basemap", "bounds.json")
OUT = os.path.join(HERE, "i4_analyst_map.html")


def main():
    with open(DETAIL, encoding="utf-8") as fh:
        crashes = json.load(fh)
    with open(SCENE, encoding="utf-8") as fh:
        scene = json.load(fh)
    with open(BOUNDS, encoding="utf-8") as fh:
        bounds = json.load(fh)

    payload = {
        "crashes": crashes,
        "origin": scene["origin"],
        "roads": [r for r in scene["roads"] if r["k"] in ("mainline", "ramp")],
        "bbox": scene["bbox"],
    }

    html = (TEMPLATE
            .replace("/*__DATA__*/", json.dumps(payload, separators=(",", ":")))
            .replace("/*__BOUNDS__*/", json.dumps(bounds)))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)

    print(f"{len(crashes)} crashes, {len(payload['roads'])} road highlights")
    print(f"Wrote {OUT}  ({os.path.getsize(OUT)/1e6:.2f} MB)")


TEMPLATE = r"""<meta charset="utf-8">
<title>I-4 corridor — crash analysis</title>
<style>
  /* Streets is the default base, so the chrome is light. `data-base="satellite"`
     on the root flips every token for the dark photograph. */
  :root{
    --mono: ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
    --sans: system-ui,-apple-system,"Segoe UI",sans-serif;
    --ink:#1b1f24; --dim:rgba(27,31,36,.6); --line:rgba(27,31,36,.16);
    --panel:rgba(252,251,248,.93); --hot:#c85a00; --page:#efe9dd;
    --shadow:0 2px 14px rgba(40,35,25,.14);
  }
  :root[data-base="satellite"]{
    --ink:#f3f6f9; --dim:rgba(243,246,249,.55); --line:rgba(243,246,249,.15);
    --panel:rgba(11,14,19,.88); --hot:#ff9500; --page:#0b0e13;
    --shadow:0 2px 14px rgba(0,0,0,.5);
  }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;background:var(--page);color:var(--ink);
            font-family:var(--sans);overflow:hidden;transition:background .35s}
  canvas{display:block}
  .ui{position:fixed;z-index:10;font-family:var(--mono);font-size:11px}

  #head{top:0;left:0;right:0;padding:11px 18px 16px;pointer-events:none;
        display:flex;align-items:baseline;gap:14px}
  #head .cap{background:var(--panel);border:1px solid var(--line);border-radius:4px;
             padding:8px 13px;box-shadow:var(--shadow);pointer-events:auto}
  #head h1{font-family:var(--sans);font-size:17px;font-weight:500;margin:0 0 1px}
  #head .s{color:var(--dim);font-size:9.5px}
  #baseSel{display:flex;gap:2px;background:var(--panel);border:1px solid var(--line);
           border-radius:4px;padding:4px;box-shadow:var(--shadow);pointer-events:auto}
  #baseSel button{background:transparent;border:0;color:var(--dim);font:inherit;
    font-family:var(--mono);font-size:9px;padding:4px 10px;cursor:pointer;
    border-radius:3px;transition:.13s}
  #baseSel button:hover{color:var(--ink)}
  #baseSel button.on{background:var(--ink);color:var(--page)}

  #panel{left:16px;top:84px;bottom:132px;width:262px;overflow-y:auto;
         display:flex;flex-direction:column;gap:7px;padding-right:4px}
  #panel::-webkit-scrollbar{width:5px}
  #panel::-webkit-scrollbar-thumb{background:rgba(255,255,255,.16);border-radius:3px}
  .g{background:var(--panel);border:1px solid var(--line);border-radius:4px;
     padding:8px 10px;backdrop-filter:blur(8px);box-shadow:var(--shadow)}
  .g>b{display:block;font-size:8px;letter-spacing:.16em;text-transform:uppercase;
       color:var(--dim);font-weight:400;margin-bottom:6px}
  .chips{display:flex;flex-wrap:wrap;gap:3px}
  .chip{background:rgba(255,255,255,.05);border:1px solid var(--line);
    color:var(--dim);font:inherit;font-size:9px;padding:3px 7px;cursor:pointer;
    border-radius:10px;transition:.13s;white-space:nowrap}
  .chip:hover{color:var(--ink);background:rgba(255,255,255,.13)}
  .chip.on{background:var(--hot);color:#0b0e13;border-color:var(--hot);font-weight:600}
  .chip .n{opacity:.6;margin-left:4px}
  .chip.on .n{opacity:.8}
  .g .btns{display:flex;gap:2px;flex-wrap:wrap}
  .g .btns button{background:rgba(255,255,255,.05);border:1px solid var(--line);
    color:var(--dim);font:inherit;font-size:9px;padding:4px 8px;cursor:pointer;
    border-radius:3px;transition:.13s}
  .g .btns button:hover{color:var(--ink)}
  .g .btns button.on{background:#f3f6f9;color:#0b0e13;border-color:#f3f6f9}

  #count{right:16px;top:84px;text-align:right;background:var(--panel);
    border:1px solid var(--line);border-radius:4px;padding:11px 14px;
    backdrop-filter:blur(8px);min-width:180px;box-shadow:var(--shadow)}
  #count .big{font-family:var(--sans);font-size:30px;font-weight:500;line-height:1;
              margin-bottom:3px}
  #count .of{color:var(--dim);font-size:10px}
  #count table{width:100%;margin-top:9px;border-collapse:collapse;font-size:10px}
  #count td{padding:1px 0}
  #count td:first-child{color:var(--dim);text-align:left}
  #count td:last-child{text-align:right;font-variant-numeric:tabular-nums}
  #reset{margin-top:9px;width:100%;background:rgba(255,149,0,.16);
    border:1px solid var(--hot);color:var(--hot);font:inherit;font-size:9px;
    padding:5px;cursor:pointer;border-radius:3px;letter-spacing:.08em}
  #reset:hover{background:rgba(255,149,0,.3)}

  #clock{left:16px;right:16px;bottom:16px;height:104px;background:var(--panel);
    border:1px solid var(--line);border-radius:4px;padding:9px 13px;
    backdrop-filter:blur(8px);display:flex;flex-direction:column;
    box-shadow:var(--shadow)}
  #clock b{font-size:8px;letter-spacing:.16em;text-transform:uppercase;
           color:var(--dim);font-weight:400;margin-bottom:6px}
  #bars{flex:1;display:flex;align-items:flex-end;gap:2px}
  #bars div{flex:1;background:var(--hot);border-radius:1px 1px 0 0;min-height:1px;
            position:relative;transition:height .18s;cursor:pointer;opacity:.85}
  #bars div:hover{opacity:1}
  #bars div.mut{background:rgba(255,255,255,.2)}
  #hrlab{display:flex;gap:2px;margin-top:3px;font-size:8px;color:var(--dim)}
  #hrlab span{flex:1;text-align:center}

  #detail{right:16px;bottom:132px;width:280px;background:var(--panel);
    border:1px solid var(--line);border-radius:4px;padding:12px 14px;
    opacity:0;transition:.18s;pointer-events:none;backdrop-filter:blur(8px);
    box-shadow:var(--shadow)}
  #detail.on{opacity:1}
  #detail .rp{font-family:var(--sans);font-size:14px;margin-bottom:2px}
  #detail .sv{font-size:8.5px;letter-spacing:.13em;text-transform:uppercase;
              margin-bottom:8px}
  #detail table{width:100%;border-collapse:collapse;font-size:9.5px}
  #detail td{padding:1.5px 0;vertical-align:top}
  #detail td:first-child{color:var(--dim);width:84px}
  #detail .fl{margin-top:7px;display:flex;flex-wrap:wrap;gap:3px}
  #detail .fl span{background:rgba(255,149,0,.2);color:#ffcb7a;font-size:8.5px;
                   padding:2px 6px;border-radius:8px}
  #detail .warn{margin-top:8px;padding:6px 8px;background:rgba(255,176,60,.16);
    border-left:2px solid #ffb03c;font-size:8.5px;line-height:1.5;color:#ffdca8}
</style>

<div id="head" class="ui">
  <div class="cap">
    <h1>I-4 corridor &mdash; crash analysis</h1>
    <div class="s">McIntosh Rd to Branch Forbes Rd &middot; 2021&ndash;2025 &middot;
      648 crashes, every field filterable</div>
  </div>
  <div id="baseSel">
    <button data-b="streets" class="on">streets</button>
    <button data-b="satellite">satellite</button>
  </div>
</div>

<div id="panel" class="ui"></div>

<div id="count" class="ui">
  <div class="big" id="cN">648</div>
  <div class="of">of 648 crashes</div>
  <table id="cT"></table>
  <button id="reset">clear all filters</button>
</div>

<div id="clock" class="ui">
  <b id="clockLab">when they happen &mdash; by hour</b>
  <div id="bars"></div>
  <div id="hrlab"></div>
</div>

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

const DATA = /*__DATA__*/;
const BOUNDS = /*__BOUNDS__*/;
const C = DATA.crashes, origin = DATA.origin;

/* Saturated enough to hold against a pale labelled basemap - the bright neons
   that worked on black wash out on paper. Size carries severity as well as hue,
   so it survives being printed in grey. */
const SEV = { "Fatality":{c:0xd0021b,s:2.7}, "Serious Injury":{c:0xf07800,s:2.0},
              "Injury":{c:0xe0a800,s:1.4}, "No Injury":{c:0x2f7fc4,s:0.95} };
const ZONE_LABEL = { mainline:"on the mainline", ramp_bf:"Branch Forbes ramp",
                     ramp_mc:"McIntosh ramp", intersection:"at a junction" };
const FLOOR_H = 2.6, SPREAD = 2.4;

/* ---------- scene ---------- */
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xefe9dd);
const camera = new THREE.PerspectiveCamera(50, innerWidth/innerHeight, 0.3, 9000);
const renderer = new THREE.WebGLRenderer({ antialias:true });
renderer.setPixelRatio(Math.min(2, devicePixelRatio));
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = .08;
controls.maxPolarAngle = Math.PI*.492; controls.zoomToCursor = true;
controls.zoomSpeed = .75; controls.minDistance = 5; controls.maxDistance = 1800;
scene.add(new THREE.AmbientLight(0xffffff, 1.3));

const { lat0, lon0, mLat, mLon, unit } = origin;
const toX = lon => (lon-lon0)*mLon*unit, toZ = lat => -(lat-lat0)*mLat*unit;
for (const c of C){ c.x = toX(c.lon); c.z = toZ(c.lat); }

const gx0=toX(BOUNDS.west), gx1=toX(BOUNDS.east);
const gz0=toZ(BOUNDS.north), gz1=toZ(BOUNDS.south);
const groundMat = new THREE.MeshBasicMaterial({ color:0xe4ddcd });
const ground = new THREE.Mesh(new THREE.PlaneGeometry(gx1-gx0, gz1-gz0), groundMat);
ground.rotation.x = -Math.PI/2;
ground.position.set((gx0+gx1)/2, 0, (gz0+gz1)/2);
scene.add(ground);

/* Streets is the default: the labelled base reads as a map people know, and it
   is the one that makes road names legible while you filter. */
const loader = new THREE.TextureLoader(), TEX = {};
let base = "streets";
function setBase(name){
  base = name;
  document.documentElement.dataset.base = name;
  scene.background.set(name === "satellite" ? 0x0b0e13 : 0xefe9dd);
  const done = t => {
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    TEX[name] = t; groundMat.map = t; groundMat.color.set(0xffffff);
    groundMat.needsUpdate = true;
  };
  TEX[name] ? done(TEX[name]) : loader.load(`basemap/${name}.jpg`, done);
  restyleMarkers();
}

/* corridor axis, for the carriageway split */
const AXIS = (()=>{ let ax=0,az=0;
  for (const r of DATA.roads){ if(r.k!=="mainline")continue;
    let dx=r.p[r.p.length-1][0]-r.p[0][0], dz=r.p[r.p.length-1][1]-r.p[0][1];
    if(dx<0){dx=-dx;dz=-dz;} ax+=dx; az+=dz; }
  const L=Math.hypot(ax,az)||1; return {x:ax/L,z:az/L}; })();
const PERP = { x:-AXIS.z, z:AXIS.x };
const sign = c => c.dir==="Eastbound"?1 : c.dir==="Westbound"?-1 : 0;

/* road highlights */
(function hi(){
  for (const [kind,col,w] of [["mainline",0x39c5ff,2.2],["ramp",0xffb03c,1.5]]){
    const list = DATA.roads.filter(r=>r.k===kind); if(!list.length) continue;
    const geos = list.map(r=>{
      const v=[],idx=[],hw=r.w*w/2;
      for(let i=0;i<r.p.length;i++){
        const p=r.p[i],a=r.p[Math.max(0,i-1)],b=r.p[Math.min(r.p.length-1,i+1)];
        let dx=b[0]-a[0],dz=b[1]-a[1]; const L=Math.hypot(dx,dz)||1; dx/=L;dz/=L;
        v.push(p[0]-dz*hw,.22,p[1]+dx*hw, p[0]+dz*hw,.22,p[1]-dx*hw);
      }
      for(let i=0;i<r.p.length-1;i++){const a=i*2;idx.push(a,a+2,a+1,a+1,a+2,a+3);}
      const g=new THREE.BufferGeometry();
      g.setAttribute("position",new THREE.Float32BufferAttribute(v,3));
      g.setIndex(idx);
      const n=new Float32Array(v.length); for(let i=1;i<n.length;i+=3)n[i]=1;
      g.setAttribute("normal",new THREE.BufferAttribute(n,3));
      return g;
    });
    scene.add(new THREE.Mesh(BufferGeometryUtils.mergeGeometries(geos,false),
      new THREE.MeshBasicMaterial({color:col,transparent:true,opacity:.28,
        side:THREE.DoubleSide,depthWrite:false})));
  }
})();

/* ---------- markers ---------- */
const ballGeo = new THREE.SphereGeometry(1,18,14);
const haloGeo = new THREE.SphereGeometry(1,12,10);
const markers = [];
for (const c of C){
  const spec = SEV[c.sev] || SEV["No Injury"];
  const off = sign(c)*SPREAD, y = c.f*FLOOR_H + 1.5;
  // A halo separates the marker from whatever is under it. On the pale streets
  // base it has to be white; on the photograph, black. Without it a dot
  // disappears into a rooftop or a road casing.
  const halo = new THREE.Mesh(haloGeo, new THREE.MeshBasicMaterial({
    color:0xffffff, transparent:true, opacity:.8, depthWrite:false }));
  halo.position.set(c.x+PERP.x*off, y, c.z+PERP.z*off);
  // Just enough to read as an outline. At 1.6x the halo swamped the coloured
  // core once the camera pulled back and every crash went white.
  halo.scale.setScalar(spec.s*1.28);
  scene.add(halo);
  const m = new THREE.Mesh(ballGeo, new THREE.MeshBasicMaterial({color:spec.c}));
  m.position.copy(halo.position); m.scale.setScalar(spec.s);
  m.userData = { c, s:spec.s, halo };
  scene.add(m); markers.push(m);
}

function restyleMarkers(){
  const dark = base === "satellite";
  for (const m of markers){
    m.userData.halo.material.color.set(dark ? 0x000000 : 0xffffff);
    m.userData.halo.material.opacity = dark ? 0.5 : 0.8;
  }
}

/* ---------- filters ---------- */
const F = {};                 // field -> Set of active values
const uniq = (f, sort) => {
  const c = {};
  for (const x of C){
    const v = x[f]; if (v === null || v === undefined) continue;
    c[v] = (c[v]||0)+1;
  }
  let e = Object.entries(c);
  e.sort(sort || ((a,b)=>b[1]-a[1]));
  return e;
};
const flagCounts = (()=>{ const c={};
  for (const x of C) for (const f of x.fl) c[f]=(c[f]||0)+1;
  return Object.entries(c).sort((a,b)=>b[1]-a[1]); })();

function matches(c){
  for (const f in F){
    const set = F[f];
    if (!set.size) continue;
    if (f === "fl"){ if (![...set].every(v => c.fl.includes(v))) return false; }
    else if (!set.has(String(c[f]))) return false;
  }
  return true;
}

const GROUPS = [
  { f:"sev",  label:"severity",
    order:(a,b)=>["Fatality","Serious Injury","Injury","No Injury"].indexOf(a[0])
               - ["Fatality","Serious Injury","Injury","No Injury"].indexOf(b[0]) },
  { f:"dir",  label:"carriageway" },
  { f:"k",    label:"where", fmt:v=>ZONE_LABEL[v]||v },
  { f:"typs", label:"crash type" },
  { f:"lgt",  label:"light" },
  { f:"surf", label:"road surface" },
  { f:"wea",  label:"weather" },
  { f:"dow",  label:"day of week",
    order:(a,b)=>["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
      .indexOf(a[0]) - ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"].indexOf(b[0]) },
  { f:"yr",   label:"year", order:(a,b)=>a[0]-b[0] },
  { f:"v1",   label:"first vehicle", fmt:v=>v.replace(/\s*\(.*?\)\s*/g," ").slice(0,26) },
  { f:"hrm",  label:"first harmful event", fmt:v=>v.slice(0,28) },
];

const panel = document.getElementById("panel");
function buildPanel(){
  panel.innerHTML = "";
  // colour-by first: what the map encodes should be the first decision
  const cb = document.createElement("div"); cb.className = "g";
  cb.innerHTML = `<b>colour by</b><div class="btns" id="cby">`+
    ["severity","crash type","light","carriageway"].map((l,i)=>
      `<button data-cb="${["sev","typs","lgt","dir"][i]}"${i?"":" class='on'"}>${l}</button>`
    ).join("")+`</div>`;
  panel.appendChild(cb);

  for (const g of GROUPS){
    const d = document.createElement("div"); d.className = "g";
    const vals = uniq(g.f, g.order);
    d.innerHTML = `<b>${g.label}</b>`;
    const wrap = document.createElement("div"); wrap.className = "chips";
    for (const [v,n] of vals){
      const b = document.createElement("button");
      b.className = "chip" + (F[g.f]?.has(String(v)) ? " on" : "");
      b.innerHTML = `${g.fmt?g.fmt(v):v}<span class="n">${n}</span>`;
      b.onclick = () => {
        F[g.f] = F[g.f] || new Set();
        const k = String(v);
        F[g.f].has(k) ? F[g.f].delete(k) : F[g.f].add(k);
        apply(); buildPanel();
      };
      wrap.appendChild(b);
    }
    d.appendChild(wrap); panel.appendChild(d);
  }

  const fd = document.createElement("div"); fd.className = "g";
  fd.innerHTML = `<b>contributing factors &mdash; all selected must apply</b>`;
  const fw = document.createElement("div"); fw.className = "chips";
  for (const [v,n] of flagCounts){
    const b = document.createElement("button");
    b.className = "chip" + (F.fl?.has(v) ? " on" : "");
    b.innerHTML = `${v}<span class="n">${n}</span>`;
    b.onclick = () => {
      F.fl = F.fl || new Set();
      F.fl.has(v) ? F.fl.delete(v) : F.fl.add(v);
      apply(); buildPanel();
    };
    fw.appendChild(b);
  }
  fd.appendChild(fw); panel.appendChild(fd);

  document.getElementById("cby").onclick = e => {
    const b = e.target.closest("button"); if(!b) return;
    colourBy = b.dataset.cb;
    [...b.parentNode.children].forEach(x=>x.classList.toggle("on",x===b));
    recolour();
  };
}

/* ---------- colour ---------- */
let colourBy = "sev";
const PALETTE = ["#d0021b","#f07800","#e0a800","#2f7fc4","#7b4bd0","#00926b",
                 "#c2185b","#0288a8","#8a6d00","#4a7c1f"];
function recolour(){
  let table = {};
  if (colourBy === "sev"){
    table = { "Fatality":"#d0021b","Serious Injury":"#f07800",
              "Injury":"#e0a800","No Injury":"#2f7fc4" };
  } else {
    uniq(colourBy).forEach(([v],i)=>{ table[v] = PALETTE[i % PALETTE.length]; });
  }
  for (const m of markers)
    m.material.color.set(table[m.userData.c[colourBy]] || "#8a8a8a");
  legendFor(table);
}
function legendFor(table){
  const el = document.getElementById("cT");
  const vis = C.filter(matches);
  el.innerHTML = Object.entries(table).slice(0,6).map(([v,col])=>{
    const n = vis.filter(c => String(c[colourBy]) === String(v)).length;
    return `<tr><td><span style="display:inline-block;width:8px;height:8px;`+
      `border-radius:50%;background:${col};margin-right:6px"></span>`+
      `${String(v).slice(0,20)}</td><td>${n}</td></tr>`;
  }).join("");
}

/* ---------- the hour profile ---------- */
const bars = document.getElementById("bars");
for (let h=0;h<24;h++) bars.appendChild(document.createElement("div"));
document.getElementById("hrlab").innerHTML =
  Array.from({length:24},(_,h)=> `<span>${h%3===0?h:""}</span>`).join("");
[...bars.children].forEach((b,h)=>{
  b.onclick = () => {
    F.hr = F.hr || new Set();
    const k = String(h);
    F.hr.has(k) ? F.hr.delete(k) : F.hr.add(k);
    apply();
  };
});

function drawClock(vis){
  const hist = new Array(24).fill(0);
  for (const c of vis) if (c.hr !== null) hist[c.hr]++;
  const max = Math.max(1, ...hist);
  [...bars.children].forEach((b,h)=>{
    b.style.height = (hist[h]/max*100) + "%";
    b.className = (F.hr && F.hr.size && !F.hr.has(String(h))) ? "mut" : "";
    b.title = `${h}:00 — ${hist[h]} crashes`;
  });
  const peak = hist.indexOf(Math.max(...hist));
  document.getElementById("clockLab").innerHTML =
    `when they happen &mdash; by hour &middot; <span style="color:var(--hot)">`+
    `peak ${peak}:00 with ${hist[peak]}</span>`;
}

/* ---------- apply ---------- */
function apply(){
  const vis = C.filter(matches);
  const keep = new Set(vis.map(c=>c.id));
  for (const m of markers){
    const v = keep.has(m.userData.c.id);
    m.visible = v; m.userData.halo.visible = v;
  }
  document.getElementById("cN").textContent = vis.length;
  drawClock(vis);
  recolour();
}
document.getElementById("reset").onclick = () => {
  for (const k in F) delete F[k];
  apply(); buildPanel();
};

/* ---------- hover ---------- */
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
const detail = document.getElementById("detail");
let hover = null;
addEventListener("pointermove", e => {
  mouse.x=(e.clientX/innerWidth)*2-1; mouse.y=-(e.clientY/innerHeight)*2+1;
  ray.setFromCamera(mouse,camera);
  const hits = ray.intersectObjects(markers.filter(m=>m.visible),false);
  const hit = hits.length?hits[0].object:null;
  if (hit===hover) return;
  if (hover) hover.scale.setScalar(hover.userData.s);
  hover = hit;
  if (!hit){ detail.classList.remove("on"); return; }
  hit.scale.setScalar(hit.userData.s*1.8);
  const c = hit.userData.c;
  const col = "#"+(SEV[c.sev]||SEV["No Injury"]).c.toString(16).padStart(6,"0");
  detail.innerHTML =
    `<div class="rp">Report ${c.id||"—"}</div>`+
    `<div class="sv" style="color:${col}">${c.sev} &middot; ${ZONE_LABEL[c.k]}</div>`+
    `<table>`+
    `<tr><td>when</td><td>${c.dt||""}</td></tr>`+
    `<tr><td>day</td><td>${c.dow||""}</td></tr>`+
    `<tr><td>carriageway</td><td><b>${c.dir}</b></td></tr>`+
    `<tr><td>crash type</td><td>${c.typ||""}</td></tr>`+
    (c.hrm?`<tr><td>first harm</td><td>${c.hrm}</td></tr>`:"")+
    (c.imp?`<tr><td>impact</td><td>${c.imp}</td></tr>`:"")+
    `<tr><td>light</td><td>${c.lgt||""}</td></tr>`+
    `<tr><td>weather</td><td>${c.wea||""} / ${c.surf||""}</td></tr>`+
    (c.mp!==null?`<tr><td>milepost</td><td>${(+c.mp).toFixed(3)}</td></tr>`:"")+
    (c.spd?`<tr><td>posted speed</td><td>${c.spd} mph</td></tr>`:"")+
    `<tr><td>vehicles</td><td>${c.veh} &middot; ${c.ppl} people</td></tr>`+
    (c.v1?`<tr><td>vehicle 1</td><td>${c.v1}</td></tr>`:"")+
    (c.v2?`<tr><td>vehicle 2</td><td>${c.v2}</td></tr>`:"")+
    (c.inj?`<tr><td>injuries</td><td>${c.inj}</td></tr>`:"")+
    `</table>`+
    (c.fl.length?`<div class="fl">`+c.fl.map(f=>`<span>${f}</span>`).join("")+`</div>`:"")+
    (c.n>1?`<div class="warn"><b>${c.n} crashes share this coordinate</b> —
      floor ${c.f+1}. The position is a milepost lookup, not a measured
      location.</div>`:"");
  detail.classList.add("on");
});

/* ---------- camera ---------- */
/* Frame on the crashes, not the whole imagery tile — and shift along the
   corridor so the subject clears the filter column on the left. */
const xs = C.map(c=>c.x), zs = C.map(c=>c.z);
const cx0=Math.min(...xs), cx1=Math.max(...xs);
const cz0=Math.min(...zs), cz1=Math.max(...zs);
const CXm=(cx0+cx1)/2, CZm=(cz0+cz1)/2;
const SPAN = Math.hypot(cx1-cx0, cz1-cz0);
const shift = SPAN*0.16;
camera.position.set(CXm + AXIS.x*shift - SPAN*0.34, SPAN*0.30,
                    CZm + AXIS.z*shift + SPAN*0.42);
controls.target.set(CXm + AXIS.x*shift, 6, CZm + AXIS.z*shift);
addEventListener("resize", ()=>{ camera.aspect=innerWidth/innerHeight;
  camera.updateProjectionMatrix(); renderer.setSize(innerWidth,innerHeight); });

document.getElementById("baseSel").onclick = e => {
  const b = e.target.closest("button"); if (!b) return;
  [...b.parentNode.children].forEach(x => x.classList.toggle("on", x === b));
  setBase(b.dataset.b);
};

window.__dbg = { scene, camera, controls, markers, F, C, apply };
setBase("streets");
buildPanel(); apply();

let t=0;
(function loop(){
  requestAnimationFrame(loop); t+=.006;
  for (const m of markers)
    if (m.userData.c.sev==="Fatality" && m.visible && m!==hover)
      m.scale.setScalar(m.userData.s*(1+Math.sin(t*2.2)*.15));
  controls.update(); renderer.render(scene,camera);
})();
</script>
"""


if __name__ == "__main__":
    main()
