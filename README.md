# 🚊 Tramway Casablanca – version GitHub Pages

Calculateur d'itinéraire **T1–T4 + BW1–BW2** avec carte interactive.
Site **100 % statique** (HTML + JS) : aucun serveur Flask, aucune base de données, gratuit sur GitHub Pages.

## ✨ Ce qui a changé par rapport au projet Flask

| Avant | Maintenant |
|---|---|
| Serveur Flask + gunicorn (impossible sur GitHub Pages) | Tout tourne dans le navigateur (`assets/js/router.js`) |
| Itinéraire dessiné en lignes droites entre stations, ligne entière visible | **Seul le tronçon A → B est coloré**, le long du **vrai tracé** de la ligne ; le reste du réseau est atténué |
| Pas de repère de sens | Flux animé dans le sens du trajet, pastilles **A / B**, trajets à pied en pointillés 🚶 |
| Carte du PDF générée côté serveur (PIL) | Carte du PDF dessinée dans le navigateur (canvas), même rendu sur tous les fonds |
| Distances / temps faux (bug dans `distance_meters` : déplacements nord-sud sous-estimés ~57×) | Distances calculées **sur le tracé réel** ; temps cohérents |
| Recherche sensible aux accents | « ain diab » trouve « Aïn Diab » ; navigation clavier ↑ ↓ Entrée |
| — | Bouton ⇅ inverser, clic sur une station → *Départ / Arrivée*, 🔍 zoom sur chaque étape, lien partageable `?from=…&to=…`, légende cliquable (masquer une ligne) |
| Interface desktop uniquement | **Responsive mobile** (panneau en bas, repliable) |
| Fond « Stamen/Stadia » (clé API requise) | Remplacé par Carto clair / sombre (gratuit) |
| Moins de correspondances inutiles | Le calcul préfère moins de correspondances (pénalité d'attente de 3 min, non affichée) |

## 🚀 Déployer sur GitHub Pages

1. Créez un dépôt sur GitHub (ex. `tramway-casablanca`) et poussez le projet :
   ```bash
   git init -b main
   git add .
   git commit -m "Tramway Casablanca"
   git remote add origin https://github.com/<votre-utilisateur>/tramway-casablanca.git
   git push -u origin main
   ```
2. Sur GitHub : **Settings → Pages → Build and deploy → Source : GitHub Actions**.
3. Chaque `push` sur `main` lance `.github/workflows/deploy.yml` (onglet *Actions*) et publie le site sur
   `https://<votre-utilisateur>.github.io/tramway-casablanca/`.

Le workflow ne publie que `index.html`, `404.html`, `favicon.svg`, `assets/` et `data/` : `backend_python/` reste sur GitHub mais n'est pas servi en ligne.
Tous les chemins du site sont relatifs, il fonctionne donc aussi bien sous `/<depot>/` que sur un domaine personnalisé.

## 🧪 Tester en local

```bash
python3 -m http.server 8000      # puis ouvrir http://localhost:8000
```
(Ne pas ouvrir `index.html` en double-clic : le navigateur bloque le chargement de `data/network.json`.)

## 🗂️ Structure

```
index.html            page principale
.github/workflows/deploy.yml  déploiement automatique GitHub Pages
404.html              page d'erreur
assets/js/router.js   moteur d'itinéraire (Dijkstra) + découpe du tracé réel
assets/js/app.js      carte Leaflet, interface, dessin du tronçon
assets/js/staticmap.js  carte statique pour le PDF
assets/js/pdf.js      génération du PDF (jsPDF)
assets/vendor/leaflet/  Leaflet 1.9.4 (hébergé localement)
data/network.json     stations, lignes, tracés réels, correspondances
backend_python/       ancien projet Flask (conservé) + tools/build_network.py
```

## 🔁 Mettre à jour les données du réseau

Modifiez `backend_python/data_reseau.py` (stations, correspondances) ou `backend_python/lines_geometry.json` (tracés), puis :

```bash
python3 backend_python/tools/build_network.py
```
Le script régénère `data/network.json` et recale chaque station sur le tracé réel.

## ⚠️ Remarques

* **BW1 / BW2** : pas de tracé réel dans les données → segments droits entre stations (T1–T4 suivent le vrai tracé).
* Le PDF utilise jsPDF et QRCode chargés depuis cdnjs, et les tuiles du fond de carte choisi : une connexion Internet est nécessaire. Si un fond bloque l'export, choisissez « OpenStreetMap ».
* `backend_python/` n'est pas publié en ligne (exclu par le workflow). `requirements.txt` y a été converti en UTF-8 (il était en UTF-16, pip ne pouvait pas le lire) et le bug de distance y a aussi été corrigé.
