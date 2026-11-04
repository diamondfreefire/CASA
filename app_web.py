# ============================================================
# SERVEUR WEB - TRAMWAY CASABLANCA
# ============================================================

from flask import Flask, render_template, jsonify, request, send_file
from data_reseau import STATIONS, LINES, CORRESPONDANCES
from route_calculator import find_route, find_stations_by_name, find_nearest_station
from pathlib import Path
from io import BytesIO
import json
import requests as http_requests
from PIL import Image, ImageDraw, ImageFont
from math import radians, cos, pi, log, tan

app = Flask(__name__)

# ============================================================
# CHARGER LES GÉOMÉTRIES
# ============================================================

GEOMETRY_FILE = Path(__file__).parent / "lines_geometry.json"

if GEOMETRY_FILE.exists():
    with open(GEOMETRY_FILE, 'r', encoding='utf-8') as f:
        LINES_GEOMETRY = json.load(f)
    print(f"\n✅ Géométries réelles chargées:")
    for line_id, coords in LINES_GEOMETRY.items():
        print(f"   {line_id}: {len(coords)} points")
else:
    LINES_GEOMETRY = {}

# ============================================================
# COULEURS
# ============================================================

LINE_COLORS = {
    'T1': (227, 6, 19),
    'T2': (0, 150, 57),
    'T3': (247, 168, 0),
    'T4': (123, 45, 142),
    'BW1': (84, 160, 87),
    'BW2': (169, 123, 80),
}

# ============================================================
# FONDS DE CARTE
# ============================================================

BASEMAP_URLS = {
    'osm': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    'esri_satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    'esri_street': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
    'esri_topo': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
    'opentopo': 'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
    'stamen_toner': 'https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}.png',
}

# ============================================================
# ✅ INDEX DES CORRESPONDANCES (calculé une fois)
# ============================================================

def build_correspondance_index():
    """Construit un index { station_id: [info correspondances] }"""
    index = {}
    for corr in CORRESPONDANCES:
        sid1 = corr["station1"]
        sid2 = corr["station2"]
        
        if sid1 not in index:
            index[sid1] = []
        if sid2 not in index:
            index[sid2] = []
        
        index[sid1].append({
            "line": corr["line2"],
            "station": corr["name2"],
            "station_id": sid2,
            "walk_time": corr["walk_time"]
        })
        index[sid2].append({
            "line": corr["line1"],
            "station": corr["name1"],
            "station_id": sid1,
            "walk_time": corr["walk_time"]
        })
    return index

CORRESPONDANCE_INDEX = build_correspondance_index()
print(f"\n✅ Index des correspondances : {len(CORRESPONDANCE_INDEX)} stations concernées")

# ============================================================
# PAGE PRINCIPALE
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/lines')
def api_lines():
    result = []
    for line_id, line_data in LINES.items():
        if line_id in LINES_GEOMETRY and LINES_GEOMETRY[line_id]:
            coordinates = LINES_GEOMETRY[line_id]
            source = "real"
        else:
            coordinates = []
            for station_id in line_data["stations"]:
                station = STATIONS[station_id]
                coordinates.append([station["lat"], station["lon"]])
            source = "stations"
        
        result.append({
            "id": line_id,
            "name": line_data["name"],
            "description": line_data["description"],
            "type": line_data["type"],
            "color": line_data["color"],
            "coordinates": coordinates,
            "source": source,
            "num_points": len(coordinates)
        })
    return jsonify(result)

# ============================================================
# ✅ API STATIONS AVEC CORRESPONDANCES
# ============================================================

@app.route('/api/stations')
def api_stations():
    result = []
    for station_id, station in STATIONS.items():
        lines_at_station = [
            line_id for line_id, line_data in LINES.items()
            if station_id in line_data["stations"]
        ]
        
        # ✅ Récupérer les correspondances depuis l'index
        correspondances = CORRESPONDANCE_INDEX.get(station_id, [])
        is_correspondance = len(correspondances) > 0
        
        result.append({
            "id": station_id,
            "name": station["name"],
            "lat": station["lat"],
            "lon": station["lon"],
            "lines": lines_at_station,
            "is_correspondance": is_correspondance,
            "correspondances": correspondances
        })
    return jsonify(result)

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    return jsonify(find_stations_by_name(query))

@app.route('/api/route', methods=['POST'])
def api_route():
    data = request.get_json()
    start = data.get('start', '').strip()
    end = data.get('end', '').strip()
    
    if not start or not end:
        return jsonify({"error": "Départ et arrivée requis"}), 400
    
    return jsonify(find_route(start, end, max_transfers=3))

@app.route('/api/correspondances')
def api_correspondances():
    result = []
    for corr in CORRESPONDANCES:
        s1 = STATIONS[corr["station1"]]
        s2 = STATIONS[corr["station2"]]
        result.append({
            "name1": corr["name1"], "line1": corr["line1"],
            "lat1": s1["lat"], "lon1": s1["lon"],
            "name2": corr["name2"], "line2": corr["line2"],
            "lat2": s2["lat"], "lon2": s2["lon"],
            "walk_time": corr["walk_time"]
        })
    return jsonify(result)

@app.route('/api/nearest')
def api_nearest():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        return jsonify({"error": "Coordonnées invalides"}), 400
    
    nearest = find_nearest_station(lat, lon)
    if nearest:
        return jsonify(nearest)
    return jsonify({"error": "Aucune station trouvée"}), 404

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def lonlat_to_pixel(lon, lat, zoom):
    lat_rad = radians(lat)
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n * 256
    y = (1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n * 256
    return x, y

def build_tile_url(basemap, zoom, tx, ty):
    url_template = BASEMAP_URLS.get(basemap, BASEMAP_URLS['osm'])
    x = tx % (2 ** zoom)
    y = ty
    
    if 'arcgisonline' in url_template:
        return url_template.replace('{z}', str(zoom)).replace('{y}', str(y)).replace('{x}', str(x))
    else:
        return url_template.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))

def get_segment_between_stations(line_id, station_a_name, station_b_name):
    station_a = None
    station_b = None
    
    for sid, sdata in STATIONS.items():
        if sdata['name'] == station_a_name:
            station_a = sdata
        if sdata['name'] == station_b_name:
            station_b = sdata
    
    if not station_a or not station_b:
        return []
    
    return [
        [station_a['lat'], station_a['lon']],
        [station_b['lat'], station_b['lon']]
    ]

# ============================================================
# API : CARTE STATIQUE
# ============================================================

@app.route('/api/static-map', methods=['POST'])
def static_map():
    try:
        data = request.get_json()
        route = data.get('route')
        basemap = data.get('basemap', 'osm')
        
        if not route:
            return jsonify({"error": "Route requise"}), 400
        
        all_coords = []
        segments = []
        stations_list = []
        
        if route['type'] == 'direct':
            step = route['steps'][0]
            line_id = step['line']
            stations_list = step['stations']
            
            for s in stations_list:
                all_coords.append((s['lat'], s['lon']))
            
            for i in range(len(stations_list) - 1):
                name_a = stations_list[i]['name']
                name_b = stations_list[i + 1]['name']
                seg = get_segment_between_stations(line_id, name_a, name_b)
                if seg:
                    segments.append((seg, line_id))
                    all_coords.extend(seg)
        else:
            for step in route['steps']:
                if step['type'] == 'ride':
                    line_id = step['line']
                    stations = step['stations']
                    
                    for s in stations:
                        if not any(x['name'] == s['name'] for x in stations_list):
                            stations_list.append(s)
                        all_coords.append((s['lat'], s['lon']))
                    
                    for i in range(len(stations) - 1):
                        name_a = stations[i]['name']
                        name_b = stations[i + 1]['name']
                        seg = get_segment_between_stations(line_id, name_a, name_b)
                        if seg:
                            segments.append((seg, line_id))
                            all_coords.extend(seg)
        
        if not all_coords:
            return jsonify({"error": "Aucune coordonnée"}), 400
        
        lats = [c[0] for c in all_coords]
        lons = [c[1] for c in all_coords]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        lat_margin = max((max_lat - min_lat) * 0.10, 0.003)
        lon_margin = max((max_lon - min_lon) * 0.10, 0.003)
        
        min_lat -= lat_margin
        max_lat += lat_margin
        min_lon -= lon_margin
        max_lon += lon_margin
        
        TILE_SIZE = 256
        IMG_WIDTH = 1400
        IMG_HEIGHT = 900
        
        zoom = 15
        for z in range(8, 18):
            x1, y1 = lonlat_to_pixel(min_lon, max_lat, z)
            x2, y2 = lonlat_to_pixel(max_lon, min_lat, z)
            if (x2 - x1) < IMG_WIDTH and (y2 - y1) < IMG_HEIGHT:
                zoom = z
            else:
                zoom = z - 1
                break
        
        x1, y1 = lonlat_to_pixel(min_lon, max_lat, zoom)
        x2, y2 = lonlat_to_pixel(max_lon, min_lat, zoom)
        
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        img_left = center_x - IMG_WIDTH / 2
        img_top = center_y - IMG_HEIGHT / 2
        
        tile_x_min = int(img_left // TILE_SIZE)
        tile_y_min = int(img_top // TILE_SIZE)
        tile_x_max = int((img_left + IMG_WIDTH) // TILE_SIZE) + 1
        tile_y_max = int((img_top + IMG_HEIGHT) // TILE_SIZE) + 1
        
        canvas = Image.new('RGB', (IMG_WIDTH, IMG_HEIGHT), (240, 240, 240))
        
        headers = {'User-Agent': 'Mozilla/5.0 CasablancaTramwayApp/1.0'}
        tiles_loaded = 0
        
        for tx in range(tile_x_min, tile_x_max):
            for ty in range(tile_y_min, tile_y_max):
                if ty < 0 or ty >= 2 ** zoom:
                    continue
                
                px = int(tx * TILE_SIZE - img_left)
                py = int(ty * TILE_SIZE - img_top)
                
                url = build_tile_url(basemap, zoom, tx, ty)
                
                try:
                    resp = http_requests.get(url, headers=headers, timeout=10)
                    if resp.status_code == 200:
                        tile_img = Image.open(BytesIO(resp.content)).convert('RGB')
                        canvas.paste(tile_img, (px, py))
                        tiles_loaded += 1
                except Exception as e:
                    print(f"❌ Tuile: {e}")
        
        print(f"✅ {tiles_loaded} tuiles ({basemap})")
        
        draw = ImageDraw.Draw(canvas)
        
        for coords, line_id in segments:
            color = LINE_COLORS.get(line_id, (255, 0, 0))
            
            pixels = []
            for lat, lon in coords:
                px, py = lonlat_to_pixel(lon, lat, zoom)
                px -= img_left
                py -= img_top
                pixels.append((int(px), int(py)))
            
            if len(pixels) >= 2:
                draw.line(pixels, fill=(255, 255, 255), width=14)
                draw.line(pixels, fill=color, width=9)
        
        try:
            font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 12)
        except:
            font_small = ImageFont.load_default()
        
        for s in stations_list:
            px, py = lonlat_to_pixel(s['lon'], s['lat'], zoom)
            px -= img_left
            py -= img_top
            px, py = int(px), int(py)
            
            r = 7
            draw.ellipse(
                [px - r - 2, py - r - 2, px + r + 2, py + r + 2],
                fill=(255, 255, 255), outline=(50, 50, 50), width=2
            )
            
            name = s['name']
            try:
                bbox = draw.textbbox((0, 0), name, font=font_small)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except:
                text_w = len(name) * 7
                text_h = 12
            
            label_x = px + 12
            label_y = py - text_h // 2
            
            padding = 4
            draw.rectangle(
                [label_x - padding, label_y - padding,
                 label_x + text_w + padding, label_y + text_h + padding],
                fill=(255, 255, 255),
                outline=(100, 100, 100),
                width=1
            )
            
            draw.text((label_x, label_y), name, fill=(20, 20, 20), font=font_small)
        
        if all_coords:
            lat, lon = all_coords[0]
            px, py = lonlat_to_pixel(lon, lat, zoom)
            px -= img_left
            py -= img_top
            px, py = int(px), int(py)
            r = 14
            draw.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3], fill=(255, 255, 255))
            draw.ellipse([px - r, py - r, px + r, py + r], fill=(76, 175, 80))
        
        if all_coords:
            lat, lon = all_coords[-1]
            px, py = lonlat_to_pixel(lon, lat, zoom)
            px -= img_left
            py -= img_top
            px, py = int(px), int(py)
            r = 14
            draw.ellipse([px - r - 3, py - r - 3, px + r + 3, py + r + 3], fill=(255, 255, 255))
            draw.ellipse([px - r, py - r, px + r, py + r], fill=(244, 67, 54))
        
        img_bytes = BytesIO()
        canvas.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return send_file(img_bytes, mimetype='image/png')
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ============================================================
# LANCEMENT
# ============================================================

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🌐 SERVEUR WEB - TRAMWAY CASABLANCA")
    print("=" * 70)
    print("\n📍 http://localhost:5000")
    print("⛔ Ctrl+C pour arrêter")
    print("=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)