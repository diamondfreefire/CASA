# ============================================================
# T1 : Garder UNE SEULE direction (Sidi Moumen → Lissasfa)
# ============================================================

import json
from pathlib import Path

SOURCE = Path(r"C:\Users\ATLAS PRO ELECTRO\Desktop\tramextract\Casablanca_Tramway_T1.geojson")
TARGET = Path(r"C:\Users\ATLAS PRO ELECTRO\Downloads\app_tramway_web\lines_geometry.json")

with open(SOURCE, 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data.get("features", [])

# Extraire tous les segments
segments = []
for feat in features:
    geom = feat.get("geometry", {})
    if geom.get("type") == "LineString":
        coords = geom.get("coordinates", [])
        if coords:
            seg = [[c[1], c[0]] for c in coords if len(c) >= 2]
            segments.append(seg)

def distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5

# Point de départ: Sidi Moumen
start_point = [33.5879, -7.4997]

# Trouver le segment qui commence à Sidi Moumen
remaining = segments.copy()
merged = []
start_idx = 0
for i, seg in enumerate(remaining):
    if distance(seg[0], start_point) < 0.001:
        start_idx = i
        break

current = remaining.pop(start_idx)
merged.extend(current)

# Point d'arrivée: Lissasfa
end_point = [33.5340, -7.6704]

# Assembler jusqu'à atteindre Lissasfa
while remaining:
    last_point = merged[-1]
    
    # Si on est proche de Lissasfa, s'arrêter
    if distance(last_point, end_point) < 0.005:
        print(f"✅ Arrivé à Lissasfa !")
        break
    
    # Trouver le prochain segment
    best_idx = None
    best_dist = float('inf')
    reverse = False
    
    for i, seg in enumerate(remaining):
        d1 = distance(last_point, seg[0])
        if d1 < best_dist:
            best_dist = d1
            best_idx = i
            reverse = False
        d2 = distance(last_point, seg[-1])
        if d2 < best_dist:
            best_dist = d2
            best_idx = i
            reverse = True
    
    if best_idx is None or best_dist > 0.01:
        print(f"⚠️ Arrêt: distance trop grande ({best_dist:.4f})")
        break
    
    next_seg = remaining.pop(best_idx)
    if reverse:
        next_seg = next_seg[::-1]
    
    merged.extend(next_seg)
    print(f"   + Segment {len(next_seg)} pts (dist={best_dist:.4f})")

print(f"\n✅ T1: {len(merged)} points")
print(f"   Premier: [{merged[0][0]:.4f}, {merged[0][1]:.4f}]")
print(f"   Dernier: [{merged[-1][0]:.4f}, {merged[-1][1]:.4f}]")

# Sauvegarder
with open(TARGET, 'r', encoding='utf-8') as f:
    lines_geometry = json.load(f)

lines_geometry["T1"] = merged

with open(TARGET, 'w', encoding='utf-8') as f:
    json.dump(lines_geometry, f, indent=2)

print(f"\n✅ lines_geometry.json mis à jour !")