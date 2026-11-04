# ============================================================
# CORRIGER T1 : Recoller les segments dans le bon ordre
# ============================================================

import json
from pathlib import Path

# Chemins
SOURCE = Path(r"C:\Users\ATLAS PRO ELECTRO\Desktop\tramextract\Casablanca_Tramway_T1.geojson")
TARGET = Path(r"C:\Users\ATLAS PRO ELECTRO\Downloads\app_tramway_web\lines_geometry.json")

print("=" * 70)
print("CORRECTION T1")
print("=" * 70)

# Charger le GeoJSON T1
with open(SOURCE, 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data.get("features", [])
print(f"\n📂 {len(features)} features trouvées")

# Extraire tous les segments
segments = []
for i, feat in enumerate(features):
    geom = feat.get("geometry", {})
    if geom.get("type") == "LineString":
        coords = geom.get("coordinates", [])
        if coords:
            # Convertir [lon, lat] → [lat, lon]
            seg = [[c[1], c[0]] for c in coords if len(c) >= 2]
            segments.append(seg)
            print(f"  Segment {i+1}: {len(seg)} points")
            print(f"     Début: [{seg[0][0]:.4f}, {seg[0][1]:.4f}]")
            print(f"     Fin:   [{seg[-1][0]:.4f}, {seg[-1][1]:.4f}]")

# ============================================================
# ALGORITHME : Recoller les segments dans le bon ordre
# ============================================================

def distance(p1, p2):
    """Distance simple entre 2 points [lat, lon]"""
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5

# Commencer par le segment qui contient le point le plus au nord-est
# (Sidi Moumen: lat=33.587, lon=-7.500)
start_point = [33.5879, -7.4997]

# Trouver le segment de départ
remaining = segments.copy()
merged = []

# Trouver le segment qui contient le point de départ
start_seg_idx = None
for i, seg in enumerate(remaining):
    for p in seg:
        if distance(p, start_point) < 0.001:
            start_seg_idx = i
            break
    if start_seg_idx is not None:
        break

if start_seg_idx is None:
    # Fallback: prendre le premier
    start_seg_idx = 0

# Ajouter le segment de départ
current = remaining.pop(start_seg_idx)
merged.extend(current)
print(f"\n🚀 Segment de départ: {len(current)} points")

# Recoller les autres segments bout à bout
while remaining:
    last_point = merged[-1]
    
    # Trouver le segment le plus proche
    best_idx = None
    best_dist = float('inf')
    reverse = False
    
    for i, seg in enumerate(remaining):
        # Essayer début du segment
        d1 = distance(last_point, seg[0])
        if d1 < best_dist:
            best_dist = d1
            best_idx = i
            reverse = False
        
        # Essayer fin du segment (inversé)
        d2 = distance(last_point, seg[-1])
        if d2 < best_dist:
            best_dist = d2
            best_idx = i
            reverse = True
    
    if best_idx is None:
        break
    
    next_seg = remaining.pop(best_idx)
    if reverse:
        next_seg = next_seg[::-1]
    
    merged.extend(next_seg)
    print(f"   + Segment ({len(next_seg)} pts, dist={best_dist:.4f})")

print(f"\n✅ T1 fusionné: {len(merged)} points")
print(f"   Premier: [{merged[0][0]:.4f}, {merged[0][1]:.4f}]")
print(f"   Dernier: [{merged[-1][0]:.4f}, {merged[-1][1]:.4f}]")

# ============================================================
# SAUVEGARDER
# ============================================================

# Charger le lines_geometry.json existant
with open(TARGET, 'r', encoding='utf-8') as f:
    lines_geometry = json.load(f)

# Remplacer T1
lines_geometry["T1"] = merged

# Sauvegarder
with open(TARGET, 'w', encoding='utf-8') as f:
    json.dump(lines_geometry, f, indent=2)

print(f"\n✅ lines_geometry.json mis à jour !")
print(f"   T1: {len(merged)} points")
print(f"\n💡 Redémarre le serveur:")
print(f"   python app_web.py")