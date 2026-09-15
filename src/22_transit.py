"""
Step 22 - transit isochrones.  RAPTOR over the live HART and PSTA timetables.

A transit trip is not a shortest path on a graph. It is: walk to a stop, wait
for a bus that actually runs, ride, maybe transfer, walk to the destination.
Only a schedule-based algorithm gets that right, because the wait depends on
when the next bus leaves, which depends on when you arrived at the stop.

RAPTOR (Delling, Pajor & Werneck 2015) does this in rounds. Round k holds the
best arrival time at every stop using at most k-1 transfers. Three rounds here,
so at most two transfers, which is what almost every real bus trip uses.

FOUR CHOICES THAT AFFECT THE ANSWER, ALL STATED:

  DATE     Thursday 2026-09-17, inside both feeds' service periods, with
           calendar_dates exceptions applied. A date outside the window yields
           a feed that parses perfectly and runs no buses at all.
  DEPARTURE Three departures, 07:45 / 08:00 / 08:15, averaged. A single
           departure rewards a stop for the bus that happens to leave at 08:00
           and punishes the identical stop next door whose bus left at 07:59.
  ACCESS   Walking to and from stops is computed on the REAL walk network from
           step 20, capped at 10 minutes, not by straight-line distance. A stop
           across a limited-access highway is not a stop you can reach.
  FOOTPATHS Stop-to-stop transfers within 300 m straight line, times 1.4 for
           street detour. Straight line is acceptable here and not for access,
           because a 300 m hop is short enough that detour error is seconds.

HART carries two route_type=0 services, the downtown Tampa streetcar. They are
kept, because a traveller can ride them, but note the crash term this project
adds to transit is FIXED-ROUTE BUS ONLY. The streetcar is 2 of 32 HART routes
over about 2.7 miles, so the inconsistency is small, but it is real.

Writes: data/interim/tt_transit.npy   (minutes, 2170 x 2170)
"""

import csv
import io
import sys
import zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
INTERIM = ROOT / "data" / "interim"
GTFS = ROOT / "data" / "raw" / "gtfs"

SERVICE_DATE = date(2026, 9, 17)          # a Thursday
# Thursday, not Wednesday: PSTA weekday service_id 2 runs Mon-Thu
# (1111000) while HART runs Mon-Fri, so Thursday is the only weekday
# both agencies operate their full weekday timetable. A Friday would
# silently drop every PSTA route.
DEPARTURES = [7 * 3600 + 45 * 60, 8 * 3600, 8 * 3600 + 15 * 60]
MAX_ACCESS_MIN = 10.0
MAX_ROUNDS = 3                             # up to two transfers
TRANSFER_M = 300.0
DETOUR = 1.4
WALK_MPS = 3.0 * 0.44704
BOARD_SLACK = 30.0                         # seconds to actually get on
MAX_MIN = 40


def rd(z, name):
    return csv.DictReader(io.TextIOWrapper(z.open(name), "utf-8-sig"))


def hhmmss(t):
    """GTFS times run past 24:00:00 for trips after midnight."""
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def active_services(z):
    """service_ids running on SERVICE_DATE, with calendar_dates applied."""
    day = SERVICE_DATE.weekday()           # Monday = 0
    cols = ["monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday"]
    ymd = SERVICE_DATE.strftime("%Y%m%d")
    on = set()
    for r in rd(z, "calendar.txt"):
        if r["start_date"] <= ymd <= r["end_date"] and r[cols[day]] == "1":
            on.add(r["service_id"])
    names = z.namelist()
    if "calendar_dates.txt" in names:
        for r in rd(z, "calendar_dates.txt"):
            if r["date"] != ymd:
                continue
            if r["exception_type"] == "1":
                on.add(r["service_id"])
            else:
                on.discard(r["service_id"])
    return on


def load_feeds():
    """Both agencies into one stop set and one pattern table."""
    stop_key, stop_ll = {}, []
    patterns = defaultdict(list)            # stop-id tuple -> list of trips
    for feed in ("hart", "psta"):
        z = zipfile.ZipFile(GTFS / f"{feed}.zip")
        on = active_services(z)
        local = {}
        for r in rd(z, "stops.txt"):
            try:
                la, lo = float(r["stop_lat"]), float(r["stop_lon"])
            except (ValueError, KeyError):
                continue
            gid = f"{feed}:{r['stop_id']}"
            local[r["stop_id"]] = gid
            if gid not in stop_key:
                stop_key[gid] = len(stop_ll)
                stop_ll.append((la, lo))

        keep = {r["trip_id"] for r in rd(z, "trips.txt")
                if r["service_id"] in on}
        by_trip = defaultdict(list)
        for r in rd(z, "stop_times.txt"):
            if r["trip_id"] not in keep:
                continue
            t = r.get("departure_time") or r.get("arrival_time")
            a = r.get("arrival_time") or t
            if not t or r["stop_id"] not in local:
                continue
            by_trip[r["trip_id"]].append(
                (int(r["stop_sequence"]), stop_key[local[r["stop_id"]]],
                 hhmmss(a), hhmmss(t)))

        for trip, rows in by_trip.items():
            rows.sort()
            if len(rows) < 2:
                continue
            key = tuple(x[1] for x in rows)
            patterns[key].append(([x[2] for x in rows], [x[3] for x in rows]))
        print(f"  {feed}: {len(on)} services active, {len(by_trip):,} trips")
    return stop_ll, patterns


def build_tables(patterns):
    """Each pattern -> stop array, arrival matrix, departure matrix."""
    out = []
    for stops, trips in patterns.items():
        arr = np.array([t[0] for t in trips], np.int32)
        dep = np.array([t[1] for t in trips], np.int32)
        order = np.argsort(dep[:, 0])
        out.append((np.asarray(stops, np.int32), arr[order], dep[order]))
    return out


def main():
    print(f"GTFS for {SERVICE_DATE:%A %d %B %Y}")
    stop_ll, patterns = load_feeds()
    stop_ll = np.asarray(stop_ll)
    n_s = len(stop_ll)
    tables = build_tables(patterns)
    print(f"  {n_s:,} stops   {len(tables):,} distinct stop patterns   "
          f"{sum(len(t[1]) for t in tables):,} trips")

    # which patterns touch each stop, and at which position
    at_stop = defaultdict(list)
    for pi, (stops, _, _) in enumerate(tables):
        for pos, s in enumerate(stops):
            at_stop[int(s)].append((pi, pos))

    # --- walk access from every origin to every stop ----------------------
    with (INTERIM / "centroids.csv").open(encoding="utf8") as fh:
        cent = list(csv.DictReader(fh))
    olat = np.array([float(r["lat"]) for r in cent])
    olon = np.array([float(r["lon"]) for r in cent])
    n_o = len(cent)

    z = np.load(INTERIM / "graph_walk.npz")
    W = csr_matrix((z["data"], z["indices"], z["indptr"]),
                   shape=tuple(z["shape"]))
    nodes = np.load(INTERIM / "graph_nodes.npy")
    lat0 = np.radians(olat.mean())
    to_m = lambda la, lo: np.column_stack(
        [np.radians(lo) * 6_371_000 * np.cos(lat0),
         np.radians(la) * 6_371_000])

    deg = np.diff(W.indptr) + np.bincount(W.indices, minlength=W.shape[0])
    usable = np.flatnonzero(deg > 0)
    tree = cKDTree(to_m(nodes[usable, 0], nodes[usable, 1]))
    _, o_near = tree.query(to_m(olat, olon), k=1)
    o_node = usable[o_near]
    d_stop, s_near = tree.query(to_m(stop_ll[:, 0], stop_ll[:, 1]), k=1)
    s_node = usable[s_near]
    print(f"  stops snapped to walk network: median {np.median(d_stop):.0f} m")

    print(f"  walk access, cutoff {MAX_ACCESS_MIN:.0f} min", flush=True)
    ACC = np.full((n_o, n_s), np.inf, np.float32)
    for i in range(0, n_o, 128):
        d = dijkstra(W, directed=False, indices=o_node[i:i + 128],
                     limit=MAX_ACCESS_MIN * 60)
        ACC[i:i + 128] = d[:, s_node].astype(np.float32)
    reach = np.isfinite(ACC).sum(axis=1)
    print(f"  origins with at least one stop in {MAX_ACCESS_MIN:.0f} min walk: "
          f"{(reach > 0).sum():,} of {n_o:,} ({(reach > 0).mean():.1%})")

    # --- stop-to-stop footpaths -------------------------------------------
    st = cKDTree(to_m(stop_ll[:, 0], stop_ll[:, 1]))
    fp = defaultdict(list)
    for a, b in st.query_pairs(TRANSFER_M):
        m = np.linalg.norm(to_m(stop_ll[[a, b], 0], stop_ll[[a, b], 1])[0]
                           - to_m(stop_ll[[a, b], 0], stop_ll[[a, b], 1])[1])
        t = m * DETOUR / WALK_MPS
        fp[a].append((b, t))
        fp[b].append((a, t))
    print(f"  {sum(len(v) for v in fp.values()) // 2:,} footpath transfers "
          f"under {TRANSFER_M:.0f} m")

    # --- RAPTOR ------------------------------------------------------------
    print(f"  RAPTOR, {len(DEPARTURES)} departures x {n_o:,} origins",
          flush=True)
    INF = np.float32(np.inf)
    total = np.zeros((n_o, n_o), np.float64)
    count = np.zeros((n_o, n_o), np.int16)

    for dep_t in DEPARTURES:
        for oi in range(n_o):
            acc = ACC[oi]
            src = np.flatnonzero(np.isfinite(acc))
            if src.size == 0:
                continue
            tau = np.full(n_s, INF)
            tau[src] = dep_t + acc[src]
            marked = set(int(x) for x in src)
            # Did the traveller actually BOARD a vehicle to reach this stop?
            # Access stops are reached on foot, so they start False. Without
            # this, the egress step below could pair an access stop with a
            # destination's access stop and return a "transit" trip that is
            # 10 minutes of walking followed by 10 more, no bus involved -
            # exactly the thing this project criticises EPA's D5BR for.
            boarded = np.zeros(n_s, bool)

            for _ in range(MAX_ROUNDS):
                queue = {}
                for s in marked:
                    for pi, pos in at_stop.get(s, ()):
                        if pi not in queue or pos < queue[pi]:
                            queue[pi] = pos
                prev = tau.copy()
                marked = set()
                for pi, start in queue.items():
                    stops, arr, dep = tables[pi]
                    trip = -1
                    for pos in range(start, len(stops)):
                        s = int(stops[pos])
                        if trip >= 0:
                            a = arr[trip, pos]
                            if a < tau[s]:
                                tau[s] = a
                                boarded[s] = True   # arrived by vehicle
                                marked.add(s)
                        ready = prev[s] + BOARD_SLACK
                        if np.isfinite(ready):
                            # earliest trip departing this stop at or after
                            # the traveller is standing there
                            j = int(np.searchsorted(dep[:, pos], ready))
                            if j < len(dep) and (trip < 0 or j < trip):
                                trip = j
                # footpaths. A short walk between stops does not un-board you,
                # so the flag carries across.
                for s in list(marked):
                    for t2, w in fp.get(s, ()):
                        if tau[s] + w < tau[t2]:
                            tau[t2] = tau[s] + w
                            boarded[t2] = boarded[s]
                            marked.add(t2)
                if not marked:
                    break

            # Egress: alight and walk to the destination. ONLY from stops the
            # traveller actually rode to, so every path counted here contains
            # at least one vehicle.
            best = np.full(n_o, np.inf)
            live = np.flatnonzero(np.isfinite(tau) & boarded)
            if live.size:
                cand = tau[live][None, :] + ACC[:, live]
                best = cand.min(axis=1)
            m = (best - dep_t) / 60.0
            ok = np.isfinite(m) & (m <= MAX_MIN)
            total[oi][ok] += m[ok]
            count[oi][ok] += 1
            if oi % 250 == 0:
                print(f"    dep {dep_t//3600:02d}:{dep_t%3600//60:02d}  "
                      f"{oi:>5,}/{n_o:,}", flush=True)

    tt = np.full((n_o, n_o), np.inf, np.float32)
    got = count > 0
    tt[got] = (total[got] / count[got]).astype(np.float32)

    # Intrazonal diagonal, matching step 21. A zero diagonal handed every
    # origin its own block group's whole opportunity count inside the 10-minute
    # transit band at no cost, and for the median origin that WAS the entire
    # reported transit reach - 91% of the region's 10-minute transit band was
    # origins counting themselves. Local trips inside a block group are walked,
    # so the walking speed is the right one here.
    area = np.array([float(r["arealand_m2"] or 0) for r in cent])
    radius = np.sqrt(np.maximum(area, 1.0) / np.pi)
    intra_min = (2.0 / 3.0) * radius / WALK_MPS / 60.0
    np.fill_diagonal(tt, intra_min.astype(np.float32))

    off = ~np.eye(n_o, dtype=bool)
    reach_off = (np.isfinite(tt) & off).sum(axis=1)
    print(f"\n  origins reaching somewhere OTHER than themselves: "
          f"{(reach_off > 0).sum():,} of {n_o:,} ({(reach_off > 0).mean():.1%})")
    print(f"  among those, mean {reach_off[reach_off > 0].mean():.1f} "
          f"destinations")

    np.save(INTERIM / "tt_transit.npy", tt)
    print(f"\n  reachable pairs within {MAX_MIN} min: "
          f"{np.isfinite(tt).mean():.2%}")
    for band in (10, 20, 30, 40):
        r = (tt <= band).sum(axis=1)
        print(f"    {band:>2} min   median {np.median(r):>6,.0f}   "
              f"mean {r.mean():>7,.0f} block groups reached")
    print(f"wrote {INTERIM / 'tt_transit.npy'}")


if __name__ == "__main__":
    main()
