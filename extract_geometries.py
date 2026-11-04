# ============================================================
# EXTRAIRE LES GÉOMÉTRIES DES LIGNES DEPUIS LES GEOJSON
# ============================================================

import json
from pathlib import Path

# ============================================================
# CHEMINS CORRIGÉS
# ============================================================

# Dossier source avec tes GeoJSON (sur le Desktop)
SOURCE_DIR = Path(r"C:\Users\ATLAS PRO ELECTRO\Desktop\tramextract")

# Dossier de l'app web (dans Downloads)
TARGET_DIR = Path(r"C:\Users\ATLAS PRO ELECTRO\Downloads\app_tramway_web")

print("=" * 70)
print("EXTRACTION DES GÉOMÉTRIES DES LIGNES")
print("=" * 70)
print(f"\n📂 Source: {SOURCE_DIR}")
print(f"📂 Cible:  {TARGET_DIR}")

# Vérifier que les dossiers existent
if not SOURCE_DIR.exists():
    print(f"\n❌ ERREUR: Dossier source introuvable: {SOURCE_DIR}")
    exit()

if not TARGET_DIR.exists():
    print(f"\n❌ ERREUR: Dossier cible introuvable: {TARGET_DIR}")
    exit()

# ============================================================
# FICHIERS À TRAITER
# ============================================================

GEOJSON_FILES = {
    "T1": SOURCE_DIR / "Casablanca_Tramway_T1.geojson",
    "T2": SOURCE_DIR / "Casablanca_Tramway_T2.geojson",
    "T3": SOURCE_DIR / "Casablanca_Tramway_T3.geojson",
    "T4": SOURCE_DIR / "Casablanca_Tramway_T4.geojson",
}

# ============================================================
# TRAITER CHAQUE FICHIER
# ============================================================

lines_geometry = {}

for line_id, geojson_file in GEOJSON_FILES.items():
    print(f"\n📂 {line_id}: {geojson_file.name}")
    
    if not geojson_file.exists():
        print(f"   ⚠️ Fichier non trouvé")
        continue
    
    with open(geojson_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get("features", [])
    print(f"   Features: {len(features)}")
    
    # Compter les types de géométrie
    types = {}
    all_coords = []
    
    for feature in features:
        geom = feature.get("geometry", {})
        geom_type = geom.get("type", "unknown")
        types[geom_type] = types.get(geom_type, 0) + 1
        
        # Extraire les coordonnées (GeoJSON: [lon, lat] → Leaflet: [lat, lon])
        if geom_type == "LineString":
            coords = geom.get("coordinates", [])
            for c in coords:
                if len(c) >= 2:
                    all_coords.append([c[1], c[0]])
        
        elif geom_type == "MultiLineString":
            for line in geom.get("coordinates", []):
                for c in line:
                    if len(c) >= 2:
                        all_coords.append([c[1], c[0]])
        
        elif geom_type == "Point":
            coords = geom.get("coordinates", [])
            if len(coords) >= 2:
                all_coords.append([coords[1], coords[0]])
    
    print(f"   Types: {types}")
    print(f"   Points totaux: {len(all_coords)}")
    
    if all_coords:
        lines_geometry[line_id] = all_coords
        print(f"   ✅ {len(all_coords)} coordonnées extraites")

# ============================================================
# SAUVEGARDER LE RÉSULTAT
# ============================================================

output_file = TARGET_DIR / "lines_geometry.json"

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(lines_geometry, f, indent=2)

print("\n" + "=" * 70)
print("RÉSULTAT")
print("=" * 70)
print(f"\n✅ Fichier créé: {output_file}")

for line_id, coords in lines_geometry.items():
    print(f"   {line_id}: {len(coords)} points")

print("\n✅ Terminé !")
print("\n💡 Maintenant lance:")
print("   python app_web.py")