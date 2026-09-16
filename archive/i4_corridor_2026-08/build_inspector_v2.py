"""
Crash inspection map, second version.

Built around one rule: the map must not claim more precision than the data has.
Roughly half the coordinates are milepost lookups rather than measured positions,
and two of them are dumping grounds holding 20 and 11 crashes, so a plain dot per
row would be a lie told convincingly.

What this adds over version one:
  - marker size scales with how many crashes share the point
  - points holding many crashes are drawn hollow: position not trustworthy
  - a milepost segment layer, which is the resolution the data actually has
  - 250 ft rings on the four at-grade ramp terminals only
  - a layer for the 226 crashes the gore trim removes
  - Non-Traffic Fatality recoded to Fatality, matching the report figures
  - measuring tape in feet

Reads sources read-only. Writes here.

Run:
    python build_inspector_v2.py
"""

import json
import math
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\Yusra\I4 Safety Ana;ysis\I4_BranchForbes_Crashes_Clean.xlsx"
DROPPED = os.path.join(HERE, "I4_DroppedCrashes.xlsx")
TERMINALS = os.path.join(HERE, "ramp_terminals.json")
OUT = os.path.join(HERE, "I4_Crash_Inspector_v2.html")

CENTERLINE_LAT = 28.0270
BOX_WEST, BOX_EAST = -82.2446584799336, -82.18669748126841
BOX_LAT_MIN, BOX_LAT_MAX = 28.0225, 28.0295
GORE_WEST, GORE_EAST = -82.23912020511585, -82.19359219348705

SEG_MI = 0.1              # milepost bin, 528 ft
STACK_WARN = 10           # at or above this, the coordinate is a dumping ground

POPUP_FIELDS = [
    ("Date_Time", "Date / time"), ("Day_of_Week", "Day"),
    ("On_Street", "On street"), ("From_Intersection", "From"),
    ("LRS_ID", "LRS route"), ("Milepost", "Milepost"),
    ("Location", "Zone"), ("Direction", "Direction"),
    ("Severity_Detail", "Severity"), ("Crash_Type", "Crash type"),
    ("First_Harmful_Event", "First harmful event"), ("Impact_Type", "Impact"),
    ("Junction", "Junction"), ("Posted_Speed", "Posted speed"),
    ("Light_Condition", "Light"), ("Weather", "Weather"),
    ("Road_Surface", "Surface"), ("Num_Vehicles", "Vehicles"),
    ("Total_Injuries", "Injuries"), ("Fatalities", "Fatalities"),
    ("V1_Body_Type", "Vehicle 1"), ("V2_Body_Type", "Vehicle 2"),
]

FLAG_FIELDS = [
    ("CMV_Involved", "Commercial vehicle"), ("Speeding", "Speeding"),
    ("Lane_Departure", "Lane departure"), ("Aggressive_Driving", "Aggressive driving"),
    ("Distracted", "Distracted"), ("Alcohol_Related", "Alcohol"),
    ("Hit_and_Run", "Hit and run"), ("Work_Zone", "Work zone"),
]


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return str(v)


def load_records(path, dropped=False):
    df = pd.read_excel(path, engine="openpyxl")
    lat = "LATITUDE" if "LATITUDE" in df.columns else "Latitude"
    lon = "LONGITUDE" if "LONGITUDE" in df.columns else "Longitude"
    df = df.dropna(subset=[lat, lon])

    # The statistics notebook recodes this and the Excel never learns about it,
    # so the map would otherwise show 4 fatalities where the report shows 5.
    if "Severity_Detail" in df.columns and "Severity" in df.columns:
        nt = df["Severity_Detail"].astype(str).eq("Non-Traffic Fatality")
        df.loc[nt, "Severity"] = "Fatality"

    recs = []
    for _, row in df.iterrows():
        r = {
            "id": clean(row.get("REPORT_NUMBER")),
            "lat": float(row[lat]), "lon": float(row[lon]),
            "year": clean(row.get("Year") or row.get("CRASH_YEAR")),
            "sev": clean(row.get("Severity") or row.get("S4_CRASH_SEVERITY")) or "Unknown",
            "zone": clean(row.get("Location")) or ("Trimmed away" if dropped else "Unknown"),
            "dir": clean(row.get("Direction")) or "Unknown",
            "mp": float(row["Milepost"]) if "Milepost" in df.columns
                  and pd.notna(row.get("Milepost")) else None,
            "props": {}, "flags": {}, "dropped": dropped,
        }
        for col, label in POPUP_FIELDS:
            if col in df.columns:
                r["props"][label] = clean(row.get(col))
        for col, label in FLAG_FIELDS:
            if col in df.columns:
                r["flags"][label] = (clean(row.get(col)) or "").upper().startswith("Y")
        recs.append(r)
    return recs


def add_stacks(recs):
    counts = {}
    for r in recs:
        k = (round(r["lat"], 6), round(r["lon"], 6))
        counts[k] = counts.get(k, 0) + 1
    for r in recs:
        r["stack"] = counts[(round(r["lat"], 6), round(r["lon"], 6))]
    return recs


def main():
    kept = add_stacks(load_records(SRC))
    print(f"Kept crashes:    {len(kept)}")

    dropped = []
    if os.path.exists(DROPPED):
        dropped = add_stacks(load_records(DROPPED, dropped=True))
        print(f"Trimmed crashes: {len(dropped)}")

    terminals = []
    if os.path.exists(TERMINALS):
        with open(TERMINALS, encoding="utf-8") as fh:
            terminals = json.load(fh)
    print(f"Ramp terminals:  {len(terminals)}")

    # Milepost segments, built from the kept crashes only. This is the honest
    # spatial summary: coarser than the geocoding error, so the error washes out.
    segs = {}
    for r in kept:
        if r["mp"] is None or r["mp"] < 1:      # guards the Milepost-as-zero rows
            continue
        s = round(round(r["mp"] / SEG_MI) * SEG_MI, 2)
        d = segs.setdefault(s, {"mp": s, "n": 0, "lat": 0.0, "lon": 0.0, "sev": {}})
        d["n"] += 1
        d["lat"] += r["lat"]
        d["lon"] += r["lon"]
        d["sev"][r["sev"]] = d["sev"].get(r["sev"], 0) + 1
    for d in segs.values():
        d["lat"] /= d["n"]
        d["lon"] /= d["n"]
    segments = sorted(segs.values(), key=lambda d: d["mp"])
    print(f"Milepost segments: {len(segments)}  "
          f"(busiest {max(s['n'] for s in segments)} crashes)")

    no_mp = sum(1 for r in kept if r["mp"] is None or r["mp"] < 1)
    print(f"Excluded from segments (Milepost missing/zero): {no_mp}")

    cfg = {
        "centerlineLat": CENTERLINE_LAT,
        "boxWest": BOX_WEST, "boxEast": BOX_EAST,
        "boxLatMin": BOX_LAT_MIN, "boxLatMax": BOX_LAT_MAX,
        "goreWest": GORE_WEST, "goreEast": GORE_EAST,
        "terminals": terminals, "segments": segments,
        "segMi": SEG_MI, "stackWarn": STACK_WARN,
        "flagLabels": [l for _, l in FLAG_FIELDS],
        "years": sorted({r["year"] for r in kept if r["year"]}),
        "zones": sorted({r["zone"] for r in kept}),
        "dirs": sorted({r["dir"] for r in kept}),
        "nDropped": len(dropped),
    }

    html = (TEMPLATE
            .replace("/*__DATA__*/", json.dumps(kept))
            .replace("/*__DROPPED__*/", json.dumps(dropped))
            .replace("/*__CONFIG__*/", json.dumps(cfg)))

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"\nWrote {OUT}")


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>I-4 Crash Inspector v2 - McIntosh Rd to Branch Forbes Rd</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html,body{margin:0;padding:0;height:100%;font-family:"Segoe UI",Arial,sans-serif}
  #map{position:absolute;inset:0 330px 0 0}
  #panel{position:absolute;top:0;right:0;bottom:0;width:330px;background:#fbfbfa;
         border-left:1px solid #d6d3cd;overflow-y:auto;font-size:12px;color:#22201d}
  #panel h1{font-size:13px;margin:0;padding:12px 14px;background:#2c2a26;color:#fff;font-weight:600}
  .sec{border-bottom:1px solid #e5e2dc;padding:10px 14px}
  .sec h2{font-size:10.5px;text-transform:uppercase;letter-spacing:.07em;color:#6b665e;
          margin:0 0 7px;font-weight:600}
  label.ck{display:flex;align-items:center;gap:6px;padding:2px 0;cursor:pointer}
  label.ck input{margin:0}
  .sw{width:11px;height:11px;border-radius:50%;border:1px solid rgba(0,0,0,.45);flex:none}
  .row{display:flex;gap:6px;align-items:center;margin:5px 0}
  .row input[type=number]{width:70px;padding:3px 5px;border:1px solid #c9c5be;border-radius:3px}
  button{font-size:11px;padding:4px 9px;border:1px solid #c9c5be;background:#fff;
         border-radius:3px;cursor:pointer}
  button:hover{background:#f0eee9}
  button.on{background:#2c2a26;color:#fff;border-color:#2c2a26}
  table.rt{width:100%;border-collapse:collapse;font-size:11px}
  table.rt td{padding:2px 0}
  table.rt td:last-child{text-align:right;font-variant-numeric:tabular-nums}
  .hint{color:#7a746b;font-size:11px;line-height:1.5}
  .warn{background:#fff6e0;border-left:3px solid #e8a33d;padding:7px 9px;
        font-size:11px;line-height:1.5;margin-top:7px}
  #counts b{font-size:16px}
  .leaflet-popup-content{font-size:12px;max-height:340px;overflow-y:auto}
  .leaflet-popup-content td{padding:1px 6px 1px 0;vertical-align:top}
  .leaflet-popup-content td.k{color:#6b665e;white-space:nowrap}
  .pid{font-weight:700;font-size:13px;margin-bottom:4px}
  #readout{position:absolute;bottom:0;left:0;z-index:900;background:rgba(255,255,255,.92);
           padding:3px 8px;font-size:11px;font-variant-numeric:tabular-nums}
  @media(max-width:720px){#map{inset:0 0 45% 0}#panel{top:55%;width:auto;left:0;border-left:none}}
</style>
</head>
<body>
<div id="map"></div>
<div id="readout">move cursor</div>
<div id="panel">
  <h1>I-4 Crash Inspector <span style="opacity:.6">v2</span></h1>

  <div class="sec"><h2>Visible</h2><div id="counts"></div></div>

  <div class="sec">
    <h2>Position honesty</h2>
    <label class="ck"><input type="checkbox" id="sizeByStack" checked>
      Size marker by crashes on the point</label>
    <label class="ck"><input type="checkbox" id="markUnsafe" checked>
      Draw unreliable positions hollow</label>
    <label class="ck"><input type="checkbox" id="jitter">
      Spread identical coordinates</label>
    <div class="warn" id="stackWarn"></div>
  </div>

  <div class="sec">
    <h2>Milepost segments</h2>
    <label class="ck"><input type="checkbox" id="showSegs"> Show segment bars</label>
    <div class="hint">The data's true resolution is about 528 ft. Segment counts are
      trustworthy; individual dot positions often are not.</div>
    <div id="segTop" style="margin-top:6px"></div>
  </div>

  <div class="sec">
    <h2>Ramp terminal rings</h2>
    <div class="row"><input type="number" id="radius" value="250" min="10" step="10"><span>feet</span></div>
    <div id="ringOut"></div>
    <div class="hint" style="margin-top:5px">Rings sit on the four at-grade ramp
      terminals. Drag a pin to place it exactly.</div>
  </div>

  <div class="sec">
    <h2>Measure</h2>
    <div class="row">
      <button id="btnMeasure">Measure distance</button>
      <button id="btnClearM">Clear</button>
    </div>
    <div id="measureOut" class="hint">Click two points on the map.</div>
  </div>

  <div class="sec"><h2>Severity</h2><div id="fSev"></div></div>
  <div class="sec"><h2>Zone</h2><div id="fZone"></div></div>
  <div class="sec"><h2>Direction</h2><div id="fDir"></div></div>
  <div class="sec"><h2>Year</h2><div id="fYear"></div></div>
  <div class="sec"><h2>Only show crashes with</h2><div id="fFlags"></div></div>
  <div class="sec"><h2>Reference geometry</h2><div id="fGeom"></div></div>
</div>

<script>
const DATA    = /*__DATA__*/;
const DROPPED = /*__DROPPED__*/;
const CFG     = /*__CONFIG__*/;
const FT = 0.3048;

const SEV_COLOR = {"Fatality":"#c1121f","Serious Injury":"#e8590c",
                   "Injury":"#e3b505","No Injury":"#4a7fb5","Unknown":"#8d8d8d"};
const SEV_ORDER = ["Fatality","Serious Injury","Injury","No Injury","Unknown"];

const map = L.map("map",{zoomControl:true}).setView([CFG.centerlineLat,(CFG.boxWest+CFG.boxEast)/2],14);

const sat = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  {maxZoom:21,maxNativeZoom:19,attribution:"Imagery: Esri"}).addTo(map);
const labels = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
  {maxZoom:21,maxNativeZoom:19,opacity:.9}).addTo(map);
const osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
  {maxZoom:19,attribution:"&copy; OpenStreetMap"});
L.control.layers({"Satellite":sat,"Street map":osm},{"Road labels":labels},{collapsed:true}).addTo(map);
L.control.scale({imperial:true,metric:true}).addTo(map);

// ---- reference geometry ----
const geom = {};
geom["Step 4 bounding box"] = L.rectangle([[CFG.boxLatMin,CFG.boxWest],[CFG.boxLatMax,CFG.boxEast]],
  {color:"#ff2d2d",weight:2,fill:false,dashArray:"6,4"}).bindTooltip("Step 4 bounding box");
geom["Centerline (direction split)"] = L.polyline(
  [[CFG.centerlineLat,CFG.boxWest],[CFG.centerlineLat,CFG.boxEast]],
  {color:"#a020f0",weight:2,dashArray:"5,5"}).bindTooltip("North = WB / South = EB");
geom["Gore-to-gore mainline"] = L.rectangle([[CFG.boxLatMin,CFG.goreWest],[CFG.boxLatMax,CFG.goreEast]],
  {color:"#00c2a8",weight:2,fill:false}).bindTooltip("Mainline kept after gore trim");
const ringGroup = L.layerGroup(); geom["Ramp terminal rings"] = ringGroup;
const segGroup  = L.layerGroup();
const dropGroup = L.layerGroup();
if (DROPPED.length) geom["Crashes removed by gore trim ("+CFG.nDropped+")"] = dropGroup;

Object.entries(geom).forEach(([n,l])=>{ if(!n.startsWith("Crashes removed")) l.addTo(map); });

// ---- state ----
const state = {sev:new Set(SEV_ORDER),zone:new Set(CFG.zones),dir:new Set(CFG.dirs),
               year:new Set(CFG.years),flags:new Set()};

function checks(host,vals,key,colorFn){
  host.innerHTML="";
  vals.forEach(v=>{
    const l=document.createElement("label");l.className="ck";
    const cb=document.createElement("input");cb.type="checkbox";cb.checked=true;
    cb.onchange=()=>{cb.checked?state[key].add(v):state[key].delete(v);render();};
    l.appendChild(cb);
    if(colorFn){const s=document.createElement("span");s.className="sw";s.style.background=colorFn(v);l.appendChild(s);}
    const t=document.createElement("span");t.textContent=v;l.appendChild(t);
    host.appendChild(l);
  });
}
checks(document.getElementById("fSev"),SEV_ORDER.filter(s=>DATA.some(d=>d.sev===s)),"sev",v=>SEV_COLOR[v]);
checks(document.getElementById("fZone"),CFG.zones,"zone");
checks(document.getElementById("fDir"),CFG.dirs,"dir");
checks(document.getElementById("fYear"),CFG.years,"year");

CFG.flagLabels.forEach(lab=>{
  const l=document.createElement("label");l.className="ck";
  const cb=document.createElement("input");cb.type="checkbox";
  cb.onchange=()=>{cb.checked?state.flags.add(lab):state.flags.delete(lab);render();};
  l.appendChild(cb);
  const t=document.createElement("span");t.textContent=lab;l.appendChild(t);
  document.getElementById("fFlags").appendChild(l);
});

Object.entries(geom).forEach(([name,layer])=>{
  const l=document.createElement("label");l.className="ck";
  const cb=document.createElement("input");cb.type="checkbox";
  cb.checked=!name.startsWith("Crashes removed");
  cb.onchange=()=>{cb.checked?layer.addTo(map):map.removeLayer(layer);};
  l.appendChild(cb);
  const t=document.createElement("span");t.textContent=name;l.appendChild(t);
  document.getElementById("fGeom").appendChild(l);
});

["sizeByStack","markUnsafe","jitter"].forEach(id=>{
  document.getElementById(id).onchange=render;
});
document.getElementById("showSegs").onchange=e=>{
  e.target.checked?segGroup.addTo(map):map.removeLayer(segGroup);
};

// ---- markers ----
const markerLayer=L.layerGroup().addTo(map);
let visible=[];

function passes(d){
  if(!state.sev.has(d.sev))return false;
  if(!state.zone.has(d.zone))return false;
  if(!state.dir.has(d.dir))return false;
  if(d.year&&!state.year.has(d.year))return false;
  for(const f of state.flags){if(!d.flags[f])return false;}
  return true;
}

function hashOffset(id,i){
  let h=0;const s=(id||"")+"#"+i;
  for(let k=0;k<s.length;k++)h=(h*31+s.charCodeAt(k))|0;
  const a=(h%360)*Math.PI/180,r=6+((h>>9)&7);
  return [Math.cos(a)*r*1e-6,Math.sin(a)*r*1e-6];
}

function popupHtml(d){
  let h='<div class="pid">Report '+(d.id||"-")+'</div>';
  if(d.dropped) h+='<div style="color:#c1121f;font-size:11px;margin-bottom:4px">'+
                   'Removed by the gore trim</div>';
  if(d.stack>=CFG.stackWarn)
    h+='<div style="background:#fff6e0;padding:4px 6px;font-size:11px;margin-bottom:4px">'+
       '<b>Position unreliable.</b> '+d.stack+' crashes share this exact coordinate, '+
       'so it is a milepost lookup rather than a measured location.</div>';
  else if(d.stack>1)
    h+='<div style="font-size:11px;color:#7a746b;margin-bottom:4px">'+d.stack+
       ' crashes share this coordinate</div>';
  h+="<table>";
  for(const [k,v] of Object.entries(d.props)){
    if(v===null||v===""||v==="nan")continue;
    h+='<tr><td class="k">'+k+'</td><td>'+v+'</td></tr>';
  }
  const on=Object.entries(d.flags).filter(([,v])=>v).map(([k])=>k);
  if(on.length)h+='<tr><td class="k">Flags</td><td>'+on.join(", ")+'</td></tr>';
  return h+"</table>";
}

function drawPoints(list,layer,opts){
  const sizeBy=document.getElementById("sizeByStack").checked;
  const hollow=document.getElementById("markUnsafe").checked;
  const jit=document.getElementById("jitter").checked;
  list.forEach((d,i)=>{
    let lat=d.lat,lon=d.lon;
    if(jit&&d.stack>1){const o=hashOffset(d.id,i);lat+=o[0];lon+=o[1];}
    const base=d.sev==="Fatality"?7:d.sev==="Serious Injury"?6:4.5;
    const r=sizeBy?Math.max(base,3.5+2.4*Math.sqrt(d.stack)):base;
    const unsafe=hollow&&d.stack>=CFG.stackWarn;
    L.circleMarker([lat,lon],{
      radius:r,
      color:unsafe?"#c1121f":(opts&&opts.dropped?"#6b665e":"#1a1a1a"),
      weight:unsafe?2:1,
      dashArray:unsafe?"3,3":null,
      fillColor:SEV_COLOR[d.sev]||"#888",
      fillOpacity:unsafe?0:(opts&&opts.dropped?0.35:0.85)
    }).bindPopup(popupHtml(d),{maxWidth:340}).addTo(layer);
  });
}

function render(){
  markerLayer.clearLayers();
  visible=DATA.filter(passes);
  drawPoints(visible,markerLayer);
  dropGroup.clearLayers();
  if(DROPPED.length) drawPoints(DROPPED,dropGroup,{dropped:true});
  updateCounts();
}

// ---- milepost segments ----
(function drawSegments(){
  const max=Math.max(...CFG.segments.map(s=>s.n));
  CFG.segments.forEach(s=>{
    const f=s.n/max;
    L.circleMarker([s.lat,s.lon],{
      radius:6+16*f, color:"#1b3a5c", weight:1.5,
      fillColor:"#2e6da4", fillOpacity:.30
    }).bindTooltip("MP "+s.mp.toFixed(1)+" &middot; <b>"+s.n+"</b> crashes",
                   {sticky:true}).addTo(segGroup);
  });
  const top=[...CFG.segments].sort((a,b)=>b.n-a.n).slice(0,5);
  document.getElementById("segTop").innerHTML =
    '<table class="rt">'+top.map(s=>'<tr><td>MP '+s.mp.toFixed(1)+
    '</td><td>'+s.n+'</td></tr>').join("")+'</table>';
})();

// ---- ramp terminal rings ----
let rings=[];
(function buildRings(){
  const rFt=parseFloat(document.getElementById("radius").value)||250;
  (CFG.terminals||[]).forEach(t=>{
    const c=L.latLng(t.lat,t.lon);
    const circle=L.circle(c,{radius:rFt*FT,color:"#ffd400",weight:2,fillOpacity:.06}).addTo(ringGroup);
    const pin=L.marker(c,{draggable:true,title:"Drag onto the exact intersection"})
               .bindTooltip(t.name).addTo(ringGroup);
    const e={name:t.name,center:c,radius:rFt*FT,circle,pin};
    pin.on("drag",ev=>{e.center=ev.latlng;circle.setLatLng(ev.latlng);updateCounts();});
    rings.push(e);
  });
})();

document.getElementById("radius").onchange=()=>{
  const rFt=parseFloat(document.getElementById("radius").value)||250;
  rings.forEach(r=>{r.radius=rFt*FT;r.circle.setRadius(rFt*FT);});
  updateCounts();
};

function countIn(c,rad,list){return list.filter(d=>c.distanceTo(L.latLng(d.lat,d.lon))<=rad);}
function sevBreak(list){
  const c={};list.forEach(d=>c[d.sev]=(c[d.sev]||0)+1);
  return SEV_ORDER.filter(s=>c[s]).map(s=>
    '<tr><td><span class="sw" style="display:inline-block;background:'+SEV_COLOR[s]+
    '"></span> '+s+'</td><td>'+c[s]+'</td></tr>').join("");
}

function updateCounts(){
  document.getElementById("counts").innerHTML =
    '<b>'+visible.length+'</b> of '+DATA.length+' crashes<table class="rt">'+
    sevBreak(visible)+'</table>';

  const rFt=parseFloat(document.getElementById("radius").value)||250;
  document.getElementById("ringOut").innerHTML='<table class="rt">'+
    rings.map(r=>'<tr><td>'+r.name.replace(" terminal","")+'</td><td>'+
      countIn(r.center,r.radius,visible).length+'</td></tr>').join("")+'</table>';

  const stacked=visible.filter(d=>d.stack>1).length;
  const bad=visible.filter(d=>d.stack>=CFG.stackWarn).length;
  document.getElementById("stackWarn").innerHTML =
    '<b>'+stacked+'</b> of '+visible.length+' visible crashes share a coordinate '+
    'with another crash.<br><b>'+bad+'</b> sit on a point holding '+CFG.stackWarn+
    '+ crashes &mdash; those are milepost lookups, not measured positions.';
}

// ---- measuring tape ----
let mPts=[],mLine=null,mArmed=false;
const btnM=document.getElementById("btnMeasure");
btnM.onclick=()=>{mArmed=!mArmed;btnM.classList.toggle("on",mArmed);
  btnM.textContent=mArmed?"Click two points...":"Measure distance";mPts=[];};
document.getElementById("btnClearM").onclick=()=>{
  if(mLine){map.removeLayer(mLine);mLine=null;}
  mPts=[];document.getElementById("measureOut").textContent="Click two points on the map.";};

map.on("click",e=>{
  if(!mArmed)return;
  mPts.push(e.latlng);
  if(mPts.length===2){
    if(mLine)map.removeLayer(mLine);
    mLine=L.polyline(mPts,{color:"#00d4ff",weight:3,dashArray:"6,4"}).addTo(map);
    const m=mPts[0].distanceTo(mPts[1]);
    document.getElementById("measureOut").innerHTML =
      '<b>'+Math.round(m/FT)+' ft</b> &nbsp;('+m.toFixed(1)+' m)';
    mArmed=false;btnM.classList.remove("on");btnM.textContent="Measure distance";mPts=[];
  } else {
    document.getElementById("measureOut").textContent="Now click the second point.";
  }
});

map.on("mousemove",e=>{
  document.getElementById("readout").textContent =
    e.latlng.lat.toFixed(6)+", "+e.latlng.lng.toFixed(6)+"   |   zoom "+map.getZoom();
});

render();
map.fitBounds(L.latLngBounds(DATA.map(d=>[d.lat,d.lon])).pad(0.08));
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
