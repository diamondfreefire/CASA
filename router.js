/* ============================================================
   MOTEUR D'ITINÉRAIRE - TRAMWAY CASABLANCA (100 % côté navigateur)
   Portage de route_calculator.py + tronçons sur le tracé réel.
   Fonctionne dans le navigateur (window.TramRouter) et dans Node (tests).
   ============================================================ */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.TramRouter = factory();
})(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    const STOP_TIME = 0.5;               // minutes par arrêt
    const TRANSFER_PENALTY = 3;          // min d'attente moyenne : sert uniquement à préférer moins de correspondances
    const M_LAT = 111320;                // mètres par degré de latitude

    function haversine(lat1, lon1, lat2, lon2) {
        const R = 6371000, rad = Math.PI / 180;
        const dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
        const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
        return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    // minuscules + sans accents ("Aïn Diab" == "ain diab")
    function norm(s) {
        return String(s || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
            .toLowerCase().replace(/\s+/g, ' ').trim();
    }

    class MinHeap {
        constructor() { this.a = []; }
        get size() { return this.a.length; }
        push(x) {
            const a = this.a; a.push(x);
            let i = a.length - 1;
            while (i > 0) {
                const p = (i - 1) >> 1;
                if (a[p].t <= a[i].t) break;
                [a[p], a[i]] = [a[i], a[p]]; i = p;
            }
        }
        pop() {
            const a = this.a, top = a[0], last = a.pop();
            if (a.length) {
                a[0] = last;
                let i = 0;
                for (;;) {
                    const l = 2 * i + 1, r = l + 1; let m = i;
                    if (l < a.length && a[l].t < a[m].t) m = l;
                    if (r < a.length && a[r].t < a[m].t) m = r;
                    if (m === i) break;
                    [a[m], a[i]] = [a[i], a[m]]; i = m;
                }
            }
            return top;
        }
    }

    function create(net) {
        const stations = net.stations;                 // id -> {n, lat, lon}
        const lines = net.lines;                       // id -> {...}
        const lineIds = Object.keys(lines);

        // ---------- index ----------
        const stationLines = {};                       // station -> [lignes]
        const posInLine = {};                          // ligne -> station -> index
        lineIds.forEach(lid => {
            posInLine[lid] = {};
            lines[lid].stations.forEach((sid, i) => {
                posInLine[lid][sid] = i;
                (stationLines[sid] = stationLines[sid] || []).push(lid);
            });
        });

        const corrOf = {};                             // station -> [{to_station,to_line,walk_time}]
        (net.correspondances || []).forEach(c => {
            const l1 = stationLines[c.s1] || [], l2 = stationLines[c.s2] || [];
            (corrOf[c.s1] = corrOf[c.s1] || []).push({ to_station: c.s2, to_line: l2[0], walk_time: c.walk });
            (corrOf[c.s2] = corrOf[c.s2] || []).push({ to_station: c.s1, to_line: l1[0], walk_time: c.walk });
        });

        // ---------- géométrie réelle ----------
        const cumGeom = {};                            // ligne -> distances cumulées (m) le long du tracé
        function geomCum(lid) {
            if (cumGeom[lid]) return cumGeom[lid];
            const g = lines[lid].geometry, cum = [0];
            for (let i = 0; i < g.length - 1; i++) {
                const k = M_LAT * Math.cos(g[i][0] * Math.PI / 180);
                cum.push(cum[i] + Math.hypot((g[i + 1][1] - g[i][1]) * k, (g[i + 1][0] - g[i][0]) * M_LAT));
            }
            return (cumGeom[lid] = cum);
        }
        function hasGeometry(lid) {
            const l = lines[lid];
            return !!(l.geometry && l.geometry.length > 1 && l.idx && Object.keys(l.idx).length);
        }
        function pointAt(g, pos) {
            const i = Math.min(Math.floor(pos), g.length - 2), t = pos - i;
            return [g[i][0] + t * (g[i + 1][0] - g[i][0]), g[i][1] + t * (g[i + 1][1] - g[i][1])];
        }
        function alongM(lid, pos) {
            const cum = geomCum(lid), i = Math.min(Math.floor(pos), cum.length - 2);
            return cum[i] + (pos - i) * (cum[i + 1] - cum[i]);
        }

        // Tronçon du tracé réel entre deux stations d'une ligne  ->  [[lat,lon], ...]
        function sliceBetween(lid, fromId, toId) {
            const l = lines[lid];
            if (!hasGeometry(lid) || l.idx[fromId] == null || l.idx[toId] == null) {
                return [fromId, toId].map(s => [stations[s].lat, stations[s].lon]);
            }
            const g = l.geometry, a = l.idx[fromId], b = l.idx[toId];
            const lo = Math.min(a, b), hi = Math.max(a, b);
            const pts = [pointAt(g, lo)];
            for (let j = Math.floor(lo) + 1; j <= Math.floor(hi); j++) if (j > lo && j < hi) pts.push(g[j]);
            pts.push(pointAt(g, hi));
            return a <= b ? pts : pts.reverse();
        }

        // Tracé complet d'un trajet sur une ligne (suite de stations consécutives)
        function ridePath(lid, stationIds) {
            const first = stationIds[0], last = stationIds[stationIds.length - 1];
            if (stationIds.length < 2 || !hasGeometry(lid) || lines[lid].idx[first] == null || lines[lid].idx[last] == null) {
                // pas de tracé réel (busway BW1/BW2) : on relie les stations dans l'ordre
                return stationIds.map(s => [stations[s].lat, stations[s].lon]);
            }
            return sliceBetween(lid, first, last);
        }

        // distance (m) entre deux stations consécutives d'une ligne
        const edgeCache = {};
        function edgeDist(lid, i, j) {
            const key = lid + ':' + Math.min(i, j) + ':' + Math.max(i, j);
            if (edgeCache[key] != null) return edgeCache[key];
            const ids = lines[lid].stations, a = ids[i], b = ids[j];
            let d;
            if (hasGeometry(lid) && lines[lid].idx[a] != null && lines[lid].idx[b] != null) {
                d = Math.abs(alongM(lid, lines[lid].idx[a]) - alongM(lid, lines[lid].idx[b]));
            } else {
                d = haversine(stations[a].lat, stations[a].lon, stations[b].lat, stations[b].lon);
            }
            return (edgeCache[key] = d);
        }
        const edgeTime = (lid, i, j) => edgeDist(lid, i, j) / 1000 / lines[lid].speed * 60 + STOP_TIME;

        // ---------- recherche de stations ----------
        function stationInfo(sid) {
            const s = stations[sid];
            return { station_id: sid, name: s.n, lat: s.lat, lon: s.lon, lines: stationLines[sid] || [] };
        }

        function searchStations(query) {
            const q = norm(query);
            if (!q) return [];
            const exact = [], starts = [], contains = [], contained = [];
            Object.keys(stations).forEach(sid => {
                const n = norm(stations[sid].n), info = stationInfo(sid);
                if (n === q) exact.push(info);
                else if (n.startsWith(q)) starts.push(info);
                else if (n.includes(q)) contains.push(info);
                else if (q.includes(n)) contained.push(info);
            });
            return exact.concat(starts, contains, contained);
        }

        function nearestStation(lat, lon, maxDist) {
            maxDist = maxDist == null ? 2000 : maxDist;
            let best = null, bd = Infinity;
            Object.keys(stations).forEach(sid => {
                const s = stations[sid], d = haversine(lat, lon, s.lat, s.lon);
                if (d < bd) { bd = d; best = sid; }
            });
            return best && bd <= maxDist ? Object.assign(stationInfo(best), { distance_m: bd }) : null;
        }

        // ---------- ride / étape ----------
        function buildRide(lid, ids) {
            const l = lines[lid];
            const sts = ids.map(id => ({ id, name: stations[id].n, lat: stations[id].lat, lon: stations[id].lon }));
            let dist = 0;
            for (let k = 0; k < ids.length - 1; k++) dist += edgeDist(lid, posInLine[lid][ids[k]], posInLine[lid][ids[k + 1]]);
            const time = dist / 1000 / l.speed * 60 + (ids.length - 1) * STOP_TIME;
            return {
                type: 'ride', line: lid, line_name: l.name, line_color: l.color, line_type: l.type,
                from: sts[0].name, to: sts[sts.length - 1].name,
                stations: sts, num_stations: sts.length,
                distance_km: dist / 1000, travel_time_min: time,
                path: ridePath(lid, ids),
            };
        }

        function directRide(lid, a, b) {
            const i = posInLine[lid][a], j = posInLine[lid][b];
            if (i == null || j == null) return null;
            const ids = i <= j ? lines[lid].stations.slice(i, j + 1) : lines[lid].stations.slice(j, i + 1).reverse();
            return buildRide(lid, ids);
        }

        // ---------- Dijkstra multi-correspondances ----------
        function search(startId, endId, maxTransfers) {
            const heap = new MinHeap(), best = new Map();
            const push = n => {
                const k = n.id + '|' + n.line + '|' + n.tr;
                if (best.has(k) && best.get(k) <= n.t) return;
                best.set(k, n.t); heap.push(n);
            };
            (stationLines[startId] || []).forEach(line => push({ t: 0, id: startId, line, tr: 0, prev: null, kind: 'start' }));
            const done = new Set();
            while (heap.size) {
                const cur = heap.pop(), key = cur.id + '|' + cur.line + '|' + cur.tr;
                if (done.has(key)) continue;
                done.add(key);
                if (cur.id === endId) return cur;
                const idx = posInLine[cur.line][cur.id], ids = lines[cur.line].stations;
                [idx - 1, idx + 1].forEach(ni => {
                    if (ni < 0 || ni >= ids.length) return;
                    push({ t: cur.t + edgeTime(cur.line, idx, ni), id: ids[ni], line: cur.line, tr: cur.tr, prev: cur, kind: 'move' });
                });
                if (cur.tr < maxTransfers) {
                    (corrOf[cur.id] || []).forEach(c => push({
                        t: cur.t + c.walk_time + TRANSFER_PENALTY, id: c.to_station, line: c.to_line, tr: cur.tr + 1,
                        prev: cur, kind: 'transfer', walk: c.walk_time, from_station: cur.id,
                    }));
                }
            }
            return null;
        }

        function stepsFromNode(node) {
            const chain = [];
            for (let n = node; n; n = n.prev) chain.push(n);
            chain.reverse();
            const steps = [];
            let cur = null;
            // un « trajet » d'une seule station (on arrive à pied, ou on repart à pied) n'est pas un trajet
            const flush = () => { if (cur && cur.ids.length > 1) steps.push(buildRide(cur.line, cur.ids)); cur = null; };
            chain.forEach(n => {
                if (n.kind === 'start') { cur = { line: n.line, ids: [n.id] }; }
                else if (n.kind === 'move') { cur.ids.push(n.id); }
                else if (n.kind === 'transfer') {
                    flush();
                    steps.push({
                        type: 'transfer',
                        from_id: n.from_station, to_id: n.id,
                        from_station: stations[n.from_station].n, to_station: stations[n.id].n,
                        from_line: n.prev.line, to_line: n.line, walk_time: n.walk,
                        path: [[stations[n.from_station].lat, stations[n.from_station].lon],
                               [stations[n.id].lat, stations[n.id].lon]],
                    });
                    cur = { line: n.line, ids: [n.id] };
                }
            });
            flush();
            return steps;
        }

        function summarize(steps, totalTime) {
            const rides = steps.filter(s => s.type === 'ride');
            const transfers = steps.filter(s => s.type === 'transfer');
            const first = steps[0], last = steps[steps.length - 1];
            const st = id => ({ id, name: stations[id].n, lat: stations[id].lat, lon: stations[id].lon });
            return {
                type: rides.length === 1 && !transfers.length ? 'direct' : 'with_transfer',
                steps,
                start: first.type === 'ride' ? first.stations[0] : st(first.from_id),
                end: last.type === 'ride' ? last.stations[last.stations.length - 1] : st(last.to_id),
                total_time: totalTime,
                total_distance_km: rides.reduce((a, s) => a + s.distance_km, 0),
                num_lines: rides.length,
                num_transfers: transfers.length,
                total_stations: rides.reduce((a, s) => a + s.num_stations, 0),
            };
        }

        // ---------- recherche principale ----------
        function findRoute(startName, endName, maxTransfers) {
            maxTransfers = maxTransfers == null ? 3 : maxTransfers;
            let starts = searchStations(startName), ends = searchStations(endName);
            if (!starts.length) return { error: `Station de départ « ${startName} » introuvable` };
            if (!ends.length) return { error: `Station d'arrivée « ${endName} » introuvable` };

            const ns = norm(startName), ne = norm(endName);
            const es = starts.filter(s => norm(s.name) === ns); if (es.length) starts = es;
            const ee = ends.filter(s => norm(s.name) === ne); if (ee.length) ends = ee;

            if (starts.some(s => ends.some(e => e.station_id === s.station_id))) {
                return { error: 'Le départ et l\'arrivée sont la même station.' };
            }

            // 1) même ligne -> trajet direct (le plus court si plusieurs lignes communes)
            let direct = null;
            starts.forEach(s => ends.forEach(e => {
                s.lines.filter(l => e.lines.includes(l)).forEach(lid => {
                    const r = directRide(lid, s.station_id, e.station_id);
                    if (r && (!direct || r.travel_time_min < direct.travel_time_min)) direct = r;
                });
            }));
            if (direct) return summarize([direct], direct.travel_time_min);

            // 2) correspondances
            let bestNode = null;
            starts.forEach(s => ends.forEach(e => {
                const n = search(s.station_id, e.station_id, maxTransfers);
                if (n && (!bestNode || n.t < bestNode.t)) bestNode = n;
            }));
            if (bestNode) {
                const steps = stepsFromNode(bestNode);
                const walk = steps.filter(s => s.type === 'transfer').reduce((a, s) => a + s.walk_time, 0);
                const ride = steps.filter(s => s.type === 'ride').reduce((a, s) => a + s.travel_time_min, 0);
                return summarize(steps, ride + walk);
            }
            return { error: `Aucun itinéraire trouvé (maximum ${maxTransfers} correspondances)` };
        }

        return {
            stations, lines, lineIds, stationLines, corrOf, posInLine,
            searchStations, nearestStation, findRoute, sliceBetween, hasGeometry, norm,
        };
    }

    return { create, haversine, norm, STOP_TIME, TRANSFER_PENALTY };
});
