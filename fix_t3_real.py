# ============================================================
# RECOLLER LES SEGMENTS T3 - VERSION CORRIGÉE
# En ignorant les segments de RETOUR (doublons)
# ============================================================

import json
from pathlib import Path

SOURCE = Path(r"C:\Users\ATLAS PRO ELECTRO\Desktop\tramextract\Casablanca_Tramway_T3.geojson")
TARGET = Path(r"C:\Users\ATLAS PRO ELECTRO\Downloads\app_tramway_web\lines_geometry.json")

print("=" * 70)
print("RECOLLER T3 - VERSION CORRIGÉE")
print("=" * 70)

# ============================================================
# CHARGER LE GEOJSON
# ============================================================

with open(SOURCE, 'r', encoding='utf-8') as f:
    geojson = json.load(f)

features = geojson.get("features", [])
print(f"\n📊 Features : {len(features)}")

# ============================================================
# SEGMENTS À GARDER (dans le bon ordre)
# ============================================================

# Feature 5 → va de Hay Al Wahda vers Casa-Port (inversé)
# Feature 2 → va du Nord vers Hay Al Wahda
# Feature 1 → connecteur
# Feature 0 → doit exister aussi

# On va construire: Casa-Port → Nord → Sud → Hay Al Wahda

# Ordre : Feature 5 (inversé) + Feature 4 (inversé) + Feature 3 + Feature 2 (inversé) ...

# En fait, on va juste prendre tous SAUF le retour
# Le retour est Feature 3 (doublon de Feature 2)

# Ordre correct : 5(inversé) → 4(inversé) → 3(inversé?non) → 2(inversé) → 1(inversé) → 0

# Essayer : 5 inversé, puis 4, puis 2 inversé, puis 1, puis 0

segments = []
for i, feat in enumerate(features):
    geom = feat.get("geometry", {})
    coords = geom.get("coordinates", [])
    # Convertir [lon, lat] → [lat, lon]
    seg = [[c[1], c[0]] for c in coords if len(c) >= 2]
    segments.append(seg)

print(f"\n📊 Segments extraits : {len(segments)}")

for i, seg in enumerate(segments):
    if len(seg) >= 2:
        print(f"   Feature {i}: {len(seg)} pts | "
              f"{seg[0][0]:.5f},{seg[0][1]:.5f} → {seg[-1][0]:.5f},{seg[-1][1]:.5f}")

# ============================================================
# CONSTRUIRE T3 EN IGNORANT LE RETOUR (Feature 3)
# ============================================================

# Feature 5 : Casa-Port ← Nord, on l'inverse pour aller Casa-Port → Nord
seg5 = segments[5][::-1]  # Inversé

# Feature 4 : connecteur
seg4 = segments[4]  # 2 points

# Feature 3 : on l'inverse pour aller Nord → Sud (au lieu de Sud → Nord)
seg3 = segments[3][::-1]

# Feature 2 : ⚠️ C'est un doublon ! On le SAUTE (c'est le retour)

# Feature 1 : connecteur
seg1 = segments[1]

# Feature 0 : on l'inverse pour aller Nord → Sud
seg0 = segments[0][::-1]

# ⚠️ En fait, on doit mieux comprendre...
# Le T3 va de Casa-Port (Nord) à Hay Al Wahda (Sud)
# 
# Feature 5 : [33.55970, -7.59438] → [33.59844, -7.61233]  (Nord → Casa-Port)
#             On l'inverse : Casa-Port → Nord
# Feature 4 : [33.55925, -7.59429] → [33.55970, -7.59438]  (connecteur)
# Feature 3 : [33.54443, -7.54930] → [33.55925, -7.59429]  (Sud → Nord)
#             ⚠️ Ce segment va de Hay Al Wahda vers Nord. 
#             Mais on va de Casa-Port vers Hay Al Wahda, donc on l'inverse
#             → Nord → Sud
# Feature 2 : [33.55923, -7.59434] → [33.54445, -7.54933]  (Nord → Sud)
#             ⚠️ DOUBLON de Feature 3 ! On le saute.
# Feature 1 : [33.55969, -7.59442] → [33.55923, -7.59434]  (connecteur)
# Feature 0 : on l'inverse

# Construction finale : Casa-Port → Hay Al Wahda
final = []

# 1. Feature 5 inversé : Casa-Port → Nord
final.extend(segments[5][::-1])
print(f"\n✅ Feature 5 (inversé) ajouté : {len(segments[5])} pts")

# 2. Feature 0 inversé (si c'est le bon connecteur)
# Vérifions ce que contient Feature 0
print(f"   Feature 0 : {len(segments[0])} pts | "
      f"{segments[0][0][0]:.5f},{segments[0][0][1]:.5f} → "
      f"{segments[0][-1][0]:.5f},{segments[0][-1][1]:.5f}")

# Continuons avec Feature 3 inversé (Nord → Sud)
final.extend(segments[3][::-1])
print(f"✅ Feature 3 (inversé) ajouté : {len(segments[3])} pts")

# ============================================================
# VÉRIFICATION
# ============================================================

print(f"\n📊 Total : {len(final)} pts")
print(f"   Début : [{final[0][0]:.5f}, {final[0][1]:.5f}]")
print(f"   Fin   : [{final[-1][0]:.5f}, {final[-1][1]:.5f}]")
print(f"   Attendu début : [33.59828, -7.61195] (Gare Casa-Port)")
print(f"   Attendu fin   : [33.54470, -7.54889] (Hay Al Wahda)")

# ============================================================
# SAUVEGARDER
# ============================================================

with open(TARGET, 'r', encoding='utf-8') as f:
    data = json.load(f)

data['T3'] = final

with open(TARGET, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✅ T3 mis à jour : {len(final)} pts")