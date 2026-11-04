#!/usr/bin/env python3
"""
Génère data/network.json (utilisé par le site statique GitHub Pages) à partir de
data_reseau.py + lines_geometry.json.

Pour chaque ligne, on calcule la position EXACTE de chaque station sur le tracé
réel (projection sur les segments du tracé, pas simple sommet le plus proche).
Les tracés T2 et T4 contiennent les deux sens de circulation (boucle), donc on
choisit, par programmation dynamique, la suite de positions la plus courte et
cohérente le long du tracé.

Usage :  python3 backend_python/tools/build_network.py
"""
import importlib.util, json, math, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # racine du projet
BACKEND = ROOT / "backend_python"
OUT = ROOT / "data" / "network.json"

# --- charger data_reseau.py sans polluer le sys.path ---------------------------------
os.chdir(BACKEND)
spec = importlib.util.spec_from_file_location("data_reseau", BACKEND / "data_reseau.py")
dr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dr)

GEOM = json.loads((BACKEND / "lines_geometry.json").read_text(encoding="utf-8"))

M_LAT = 111_320.0                                    # m par degré de latitude


def m_lon(lat):                                      # m par degré de longitude
    return M_LAT * math.cos(math.radians(lat))


def project(pt, a, b):
    """Projection de pt sur le segment [a,b] (plan local). -> (t, distance_m)"""
    k = m_lon(pt[0])
    ax, ay = (a[1] - pt[1]) * k, (a[0] - pt[0]) * M_LAT
    bx, by = (b[1] - pt[1]) * k, (b[0] - pt[0]) * M_LAT
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
    px, py = ax + t * dx, ay + t * dy
    return t, math.hypot(px, py)


def candidates(geom, st, tol=25.0, kmax=10):
    """Positions candidates (index flottant k+t) : minima locaux proches du minimum global."""
    n = len(geom) - 1
    proj = [project(st, geom[i], geom[i + 1]) for i in range(n)]
    dmin = min(d for _, d in proj)
    out = []
    for i, (t, d) in enumerate(proj):
        if d > dmin + tol:
            continue
        prev_d = proj[i - 1][1] if i > 0 else 1e9
        next_d = proj[i + 1][1] if i < n - 1 else 1e9
        if d <= prev_d and d <= next_d:
            out.append((i + t, d))
    out.sort(key=lambda c: c[1])
    return out[:kmax]


def cumulative(geom):
    cum = [0.0]
    for i in range(len(geom) - 1):
        k = m_lon(geom[i][0])
        cum.append(cum[-1] + math.hypot((geom[i + 1][1] - geom[i][1]) * k,
                                        (geom[i + 1][0] - geom[i][0]) * M_LAT))
    return cum


def along(cum, pos):
    i = min(int(pos), len(cum) - 2)
    t = pos - i
    return cum[i] + t * (cum[i + 1] - cum[i])


def snap_line(line_id, station_ids, geom):
    cum = cumulative(geom)
    cands = [candidates(geom, (dr.STATIONS[s]["lat"], dr.STATIONS[s]["lon"])) for s in station_ids]
    # DP : coût = distance le long du tracé entre positions consécutives + 3 * écart station/tracé
    best = [[3 * d for _, d in cands[0]]]
    back = [[None] * len(cands[0])]
    for s in range(1, len(cands)):
        row, brow = [], []
        for pos, d in cands[s]:
            opts = [(best[s - 1][j] + abs(along(cum, pos) - along(cum, pp)) + 3 * d, j)
                    for j, (pp, _) in enumerate(cands[s - 1])]
            c, j = min(opts)
            row.append(c); brow.append(j)
        best.append(row); back.append(brow)
    j = min(range(len(best[-1])), key=lambda x: best[-1][x])
    picks = [None] * len(cands)
    for s in range(len(cands) - 1, -1, -1):
        picks[s] = cands[s][j]
        j = back[s][j]
    return picks


def main():
    stations = {sid: {"n": s["name"], "lat": s["lat"], "lon": s["lon"]} for sid, s in dr.STATIONS.items()}
    lines = {}
    for lid, ld in dr.LINES.items():
        geom = GEOM.get(lid) or []
        entry = {
            "name": ld["name"], "type": ld["type"], "color": ld["color"], "speed": ld["speed"],
            "description": ld["description"], "stations": ld["stations"],
            "geometry": [[round(p[0], 6), round(p[1], 6)] for p in geom],
            "idx": {},
        }
        if len(geom) >= 2:
            picks = snap_line(lid, ld["stations"], geom)
            worst = 0
            for sid, (pos, d) in zip(ld["stations"], picks):
                entry["idx"][sid] = round(pos, 4)
                worst = max(worst, d)
            print(f"{lid}: {len(geom)} pts, {len(picks)} stations calées, écart max station→tracé = {worst:.0f} m")
        else:
            print(f"{lid}: pas de tracé réel → segments droits entre stations")
        lines[lid] = entry
    corr = [{"s1": c["station1"], "s2": c["station2"], "walk": c["walk_time"]} for c in dr.CORRESPONDANCES]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"stations": stations, "lines": lines, "correspondances": corr},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"✅ {OUT}  ({OUT.stat().st_size/1024:.0f} Ko)")


if __name__ == "__main__":
    main()
