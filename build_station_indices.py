# ============================================================
# PRÉ-CALCULER L'INDEX DE CHAQUE STATION DANS SA LIGNE
# ============================================================

import json
from pathlib import Path
from data_reseau import STATIONS, LINES

# Charger les géométries
GEOMETRY_FILE = Path(__file__).parent / "lines_geometry.json"

with open(GEOMETRY_FILE, 'r', encoding='utf-8') as f:
    LINES_GEOMETRY = json.load(f)

def find_closest_index(geometry, lat, lon):
    """Trouve l'index du point le plus proche"""
    min_dist = float('inf')
    min_idx = None
    for i, point in enumerate(geometry):
        if isinstance(point, list) and len(point) >= 2:
            plat, plon = point[0], point[1]
            dist = (plat - lat)**2 + (plon - lon)**2
            if dist < min_dist:
                min_dist = dist
                min_idx = i
    return min_idx

# ============================================================
# CALCULER LES INDEX POUR CHAQUE LIGNE
# ============================================================

STATION_INDICES = {}  # { line_id: { station_id: index } }

for line_id, line_data in LINES.items():
    line_geometry = LINES_GEOMETRY.get(line_id, [])
    
    if not line_geometry:
        print(f"⚠️ {line_id}: pas de géométrie")
        continue
    
    station_indices = {}
    
    for station_id in line_data["stations"]:
        station = STATIONS[station_id]
        idx = find_closest_index(line_geometry, station["lat"], station["lon"])
        
        if idx is not None:
            station_indices[station_id] = idx
    
    STATION_INDICES[line_id] = station_indices
    print(f"✅ {line_id}: {len(station_indices)} stations indexées")

# ============================================================
# SAUVEGARDER
# ============================================================

output_file = Path(__file__).parent / "station_indices.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(STATION_INDICES, f, indent=2, ensure_ascii=False)

print(f"\n✅ Fichier créé: {output_file}")
print(f"   Lignes: {list(STATION_INDICES.keys())}")