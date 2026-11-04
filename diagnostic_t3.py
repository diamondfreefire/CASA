# ============================================================
# DIAGNOSTIC T3 - VOIR L'ORDRE DES SEGMENTS
# ============================================================

import json
from pathlib import Path

SOURCE = Path(r"C:\Users\ATLAS PRO ELECTRO\Desktop\tramextract\Casablanca_Tramway_T3.geojson")

with open(SOURCE, 'r', encoding='utf-8') as f:
    data = json.load(f)

features = data.get("features", [])

print("=" * 70)
print("DIAGNOSTIC T3 - ORDRE DES SEGMENTS")
print("=" * 70)

for i, feat in enumerate(features):
    geom = feat.get("geometry", {})
    coords = geom.get("coordinates", [])
    
    if not coords:
        continue
    
    # Premier et dernier point en [lat, lon]
    first = [coords[0][1], coords[0][0]]
    last = [coords[-1][1], coords[-1][0]]
    
    print(f"\n📌 Feature {i} : {len(coords)} points")
    print(f"   DÉBUT : [{first[0]:.5f}, {first[1]:.5f}]")
    print(f"   FIN   : [{last[0]:.5f}, {last[1]:.5f}]")

print("\n" + "=" * 70)
print("STATIONS T3 DE RÉFÉRENCE")
print("=" * 70)
print(f"  Gare Casa-Port  : [33.59828, -7.61195]  ← DOIT ÊTRE LE DÉBUT")
print(f"  Hay Al Wahda    : [33.54470, -7.54889]  ← DOIT ÊTRE LA FIN")