# ============================================================
# CORRIGER LA GÉOMÉTRIE T3 AVEC LES VRAIES STATIONS
# ============================================================

import json
from pathlib import Path
from data_reseau import STATIONS

GEOMETRY_FILE = Path(__file__).parent / "lines_geometry.json"

# Charger la géométrie existante
with open(GEOMETRY_FILE, 'r', encoding='utf-8') as f:
    LINES_GEOMETRY = json.load(f)

# ============================================================
# RECONSTRUIRE T3 À PARTIR DES STATIONS
# ============================================================

T3_STATIONS = [
    "T3_01", "T3_02", "T3_03", "T3_04", "T3_05",
    "T3_06", "T3_07", "T3_08", "T3_09", "T3_10",
    "T3_11", "T3_12", "T3_13", "T3_14", "T3_15",
    "T3_16", "T3_17", "T3_18", "T3_19", "T3_20"
]

# Construire une géométrie simple reliant les stations
new_t3_geometry = []

for station_id in T3_STATIONS:
    station = STATIONS[station_id]
    # Format : [lat, lon]
    new_t3_geometry.append([station['lat'], station['lon']])

print(f"✅ T3 reconstruit : {len(new_t3_geometry)} points")
for i, coord in enumerate(new_t3_geometry):
    sid = T3_STATIONS[i]
    print(f"   {sid} ({STATIONS[sid]['name']}): {coord}")

# ============================================================
# REMPLACER T3 DANS lines_geometry.json
# ============================================================

LINES_GEOMETRY['T3'] = new_t3_geometry

# Sauvegarder
with open(GEOMETRY_FILE, 'w', encoding='utf-8') as f:
    json.dump(LINES_GEOMETRY, f, indent=2, ensure_ascii=False)

print(f"\n✅ lines_geometry.json mis à jour")
print(f"   T3: {len(new_t3_geometry)} points (lignes droites)")