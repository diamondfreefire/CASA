# ============================================================
# MOTEUR DE CALCUL D'ITINÉRAIRE
# ============================================================

from math import radians, sin, cos, sqrt, atan2
from collections import deque
from data_reseau import STATIONS, LINES, CORRESPONDANCES, get_correspondances, get_lines_for_station

# ============================================================
# DISTANCE HAVERSINE
# ============================================================

def distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    # (correction : l'ancienne version convertissait lat1/lat2 en radians AVANT de
    #  calculer dlat avec radians(lat2 - lat1) -> distances nord-sud sous-estimées ~57x)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    lat1, lat2 = radians(lat1), radians(lat2)
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# ============================================================
# TEMPS DE TRAJET
# ============================================================

STOP_TIME = 0.5  # minutes par arrêt

def calculate_travel_time(distance_m, speed_kmh):
    return (distance_m / 1000) / speed_kmh * 60

# ============================================================
# RECHERCHE DE STATION (avec PRIORITÉ aux matchs exacts)
# ============================================================

def find_stations_by_name(name):
    """
    Trouve les stations correspondant au nom.
    PRIORITÉ 1 : match exact (nom identique)
    PRIORITÉ 2 : nom commence par la recherche
    PRIORITÉ 3 : la recherche est contenue dans le nom
    PRIORITÉ 4 : nom contenu dans la recherche
    """
    name_lower = name.lower().strip()
    
    exact = []
    starts_with = []
    contains = []
    contained = []
    
    for station_id, station in STATIONS.items():
        station_name = station["name"].lower().strip()
        lines = get_lines_for_station(station_id)
        
        result = {
            "station_id": station_id,
            "name": station["name"],
            "lat": station["lat"],
            "lon": station["lon"],
            "lines": lines
        }
        
        if station_name == name_lower:
            # Match exact
            exact.append(result)
        elif station_name.startswith(name_lower):
            # Commence par
            starts_with.append(result)
        elif name_lower in station_name:
            # Contient
            contains.append(result)
        elif station_name in name_lower:
            # Est contenu dans la recherche
            contained.append(result)
    
    # Retourner dans l'ordre de priorité
    return exact + starts_with + contains + contained

# ============================================================
# STATION LA PLUS PROCHE
# ============================================================

def find_nearest_station(lat, lon, max_distance=2000):
    nearest = None
    min_distance = float('inf')
    
    for station_id, station in STATIONS.items():
        dist = distance_meters(lat, lon, station["lat"], station["lon"])
        if dist < min_distance:
            min_distance = dist
            nearest = {
                "station_id": station_id,
                "name": station["name"],
                "lat": station["lat"],
                "lon": station["lon"],
                "lines": get_lines_for_station(station_id),
                "distance_m": dist
            }
    
    if nearest and min_distance <= max_distance:
        return nearest
    return None

# ============================================================
# CALCUL D'ITINÉRAIRE SUR UNE LIGNE
# ============================================================

def calculate_route_on_line(line_id, start_station_id, end_station_id):
    line_data = LINES[line_id]
    stations_on_line = line_data["stations"]
    
    if start_station_id not in stations_on_line:
        return None
    if end_station_id not in stations_on_line:
        return None
    
    start_idx = stations_on_line.index(start_station_id)
    end_idx = stations_on_line.index(end_station_id)
    
    if start_idx <= end_idx:
        route_ids = stations_on_line[start_idx:end_idx + 1]
    else:
        route_ids = stations_on_line[end_idx:start_idx + 1][::-1]
    
    route_stations = []
    for sid in route_ids:
        s = STATIONS[sid]
        route_stations.append({
            "id": sid,
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"]
        })
    
    total_distance = 0
    for i in range(len(route_stations) - 1):
        s1 = route_stations[i]
        s2 = route_stations[i + 1]
        total_distance += distance_meters(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
    
    travel_time = calculate_travel_time(total_distance, line_data["speed"])
    stop_time = len(route_stations) * STOP_TIME
    
    return {
        "line": line_id,
        "line_name": line_data["name"],
        "line_color": line_data["color"],
        "type": line_data["type"],
        "from": route_stations[0]["name"],
        "to": route_stations[-1]["name"],
        "stations": route_stations,
        "num_stations": len(route_stations),
        "distance_m": total_distance,
        "distance_km": total_distance / 1000,
        "travel_time_min": travel_time + stop_time
    }

# ============================================================
# RECHERCHE BFS MULTI-CORRESPONDANCES (jusqu'à 4)
# ============================================================

def find_route_bfs(start_station_id, end_station_id, max_transfers=3):
    """
    Recherche l'itinéraire optimal avec BFS
    Supporte jusqu'à max_transfers correspondances (3 par défaut)
    """
    queue = deque()
    visited = {}  # (station_id, line_id) → temps minimum
    
    # Initialisation : partir de chaque ligne passant par le départ
    start_lines = get_lines_for_station(start_station_id)
    for line_id in start_lines:
        state = {
            "station_id": start_station_id,
            "line": line_id,
            "transfers": 0,
            "time": 0,
            "distance": 0,
            "path": [{
                "type": "start",
                "line": line_id,
                "station_id": start_station_id
            }]
        }
        queue.append(state)
        visited[(start_station_id, line_id)] = 0
    
    best = None
    best_time = float('inf')
    iterations = 0
    max_iter = 500000  # sécurité
    
    while queue and iterations < max_iter:
        iterations += 1
        state = queue.popleft()
        
        curr_id = state["station_id"]
        curr_line = state["line"]
        transfers = state["transfers"]
        total_time = state["time"]
        total_dist = state["distance"]
        
        # ✅ Arrivée trouvée
        if curr_id == end_station_id:
            if total_time < best_time:
                best_time = total_time
                best = state
            continue
        
        if transfers > max_transfers:
            continue
        
        # ================================================
        # 1. Continuer sur la même ligne (station voisine)
        # ================================================
        line_data = LINES[curr_line]
        stations_on_line = line_data["stations"]
        
        if curr_id in stations_on_line:
            idx = stations_on_line.index(curr_id)
            
            for next_idx in [idx - 1, idx + 1]:
                if 0 <= next_idx < len(stations_on_line):
                    next_id = stations_on_line[next_idx]
                    
                    curr_st = STATIONS[curr_id]
                    next_st = STATIONS[next_id]
                    dist = distance_meters(
                        curr_st["lat"], curr_st["lon"],
                        next_st["lat"], next_st["lon"]
                    )
                    time = calculate_travel_time(dist, line_data["speed"]) + STOP_TIME
                    
                    new_time = total_time + time
                    key = (next_id, curr_line)
                    
                    if key not in visited or visited[key] > new_time:
                        visited[key] = new_time
                        queue.append({
                            "station_id": next_id,
                            "line": curr_line,
                            "transfers": transfers,
                            "time": new_time,
                            "distance": total_dist + dist,
                            "path": state["path"] + [{
                                "type": "continue",
                                "line": curr_line,
                                "station_id": next_id
                            }]
                        })
        
        # ================================================
        # 2. Prendre une correspondance
        # ================================================
        if transfers < max_transfers:
            corrs = get_correspondances(curr_id)
            
            for corr in corrs:
                next_id = corr["to_station"]
                next_line = corr["to_line"]
                walk = corr["walk_time"]
                
                new_time = total_time + walk
                key = (next_id, next_line)
                
                if key not in visited or visited[key] > new_time:
                    visited[key] = new_time
                    queue.append({
                        "station_id": next_id,
                        "line": next_line,
                        "transfers": transfers + 1,
                        "time": new_time,
                        "distance": total_dist,
                        "path": state["path"] + [{
                            "type": "transfer",
                            "from_station": curr_id,
                            "to_station": next_id,
                            "to_line": next_line,
                            "walk_time": walk
                        }, {
                            "type": "start",
                            "line": next_line,
                            "station_id": next_id
                        }]
                    })
    
    return best

# ============================================================
# RECONSTRUIRE LES ÉTAPES DEPUIS LE PATH BFS
# ============================================================

def build_steps_from_path(path):
    steps = []
    current_ride = None
    
    for step in path:
        if step["type"] == "start":
            if current_ride is not None:
                steps.append(current_ride)
            
            line_id = step["line"]
            station = STATIONS[step["station_id"]]
            current_ride = {
                "type": "ride",
                "line": line_id,
                "line_name": LINES[line_id]["name"],
                "line_color": LINES[line_id]["color"],
                "from": station["name"],
                "to": station["name"],
                "stations": [{
                    "id": step["station_id"],
                    "name": station["name"],
                    "lat": station["lat"],
                    "lon": station["lon"]
                }]
            }
        
        elif step["type"] == "continue":
            if current_ride and step["line"] == current_ride["line"]:
                station = STATIONS[step["station_id"]]
                current_ride["stations"].append({
                    "id": step["station_id"],
                    "name": station["name"],
                    "lat": station["lat"],
                    "lon": station["lon"]
                })
                current_ride["to"] = station["name"]
        
        elif step["type"] == "transfer":
            if current_ride is not None:
                steps.append(current_ride)
                current_ride = None
            
            from_st = STATIONS[step["from_station"]]
            to_st = STATIONS[step["to_station"]]
            steps.append({
                "type": "transfer",
                "from_station": from_st["name"],
                "to_station": to_st["name"],
                "walk_time": step["walk_time"]
            })
    
    if current_ride is not None:
        steps.append(current_ride)
    
    return steps

# ============================================================
# CALCUL DES STATS DES ÉTAPES
# ============================================================

def compute_steps_stats(steps):
    for s in steps:
        if s["type"] == "ride":
            coords = [(st["lat"], st["lon"]) for st in s["stations"]]
            total_dist = 0
            for i in range(len(coords) - 1):
                total_dist += distance_meters(
                    coords[i][0], coords[i][1],
                    coords[i+1][0], coords[i+1][1]
                )
            
            speed = LINES[s["line"]]["speed"]
            travel_time = calculate_travel_time(total_dist, speed)
            stop_time = len(s["stations"]) * STOP_TIME
            
            s["num_stations"] = len(s["stations"])
            s["distance_km"] = total_dist / 1000
            s["travel_time_min"] = travel_time + stop_time
    
    return steps

# ============================================================
# RECHERCHE PRINCIPALE (multi-correspondances)
# ============================================================

def find_route(start_name, end_name, max_transfers=3):
    """
    Trouve l'itinéraire optimal entre deux stations.
    Supporte jusqu'à max_transfers correspondances (3 par défaut).
    Priorise les matchs exacts de nom de station.
    """
    start_stations = find_stations_by_name(start_name)
    end_stations = find_stations_by_name(end_name)
    
    if not start_stations:
        return {"error": f"Station de départ '{start_name}' non trouvée"}
    if not end_stations:
        return {"error": f"Station d'arrivée '{end_name}' non trouvée"}
    
    # ✅ PRIORISER LES MATCHS EXACTS
    name_lower_start = start_name.lower().strip()
    name_lower_end = end_name.lower().strip()
    
    # Si un match exact existe, ne garder QUE celui-là
    exact_start = [s for s in start_stations if s["name"].lower().strip() == name_lower_start]
    if exact_start:
        start_stations = exact_start
    
    exact_end = [s for s in end_stations if s["name"].lower().strip() == name_lower_end]
    if exact_end:
        end_stations = exact_end
    
    # ================================================
    # Test 1 : Itinéraire direct (même ligne)
    # ================================================
    for start in start_stations:
        for end in end_stations:
            common = set(start["lines"]) & set(end["lines"])
            for line_id in common:
                route = calculate_route_on_line(line_id, start["station_id"], end["station_id"])
                if route:
                    return {
                        "type": "direct",
                        "steps": [route],
                        "total_time": route["travel_time_min"],
                        "total_distance_km": route["distance_km"],
                        "num_lines": 1,
                        "num_transfers": 0,
                        "total_stations": route["num_stations"]
                    }
    
    # ================================================
    # Test 2 : Multi-correspondances (BFS)
    # ================================================
    best_route = None
    best_time = float('inf')
    
    for start in start_stations:
        for end in end_stations:
            result = find_route_bfs(
                start["station_id"],
                end["station_id"],
                max_transfers=max_transfers
            )
            
            if result and result["time"] < best_time:
                best_time = result["time"]
                best_route = result
    
    if best_route:
        steps = build_steps_from_path(best_route["path"])
        steps = compute_steps_stats(steps)
        
        num_rides = len([s for s in steps if s["type"] == "ride"])
        num_transfers = num_rides - 1
        
        total_stations = sum(s.get("num_stations", 0) for s in steps if s["type"] == "ride")
        total_distance = sum(s.get("distance_km", 0) for s in steps if s["type"] == "ride")
        
        return {
            "type": "direct" if num_rides == 1 else "with_transfer",
            "steps": steps,
            "total_time": best_route["time"],
            "total_distance_km": total_distance,
            "num_lines": num_rides,
            "num_transfers": num_transfers,
            "total_stations": total_stations
        }
    
    return {
        "error": f"Aucun itinéraire trouvé avec {max_transfers} correspondances max",
        "start_options": start_stations,
        "end_options": end_stations
    }

# ============================================================
# AFFICHAGE DE L'ITINÉRAIRE
# ============================================================

def print_route(route):
    if "error" in route:
        print(f"\n❌ {route['error']}")
        if "start_options" in route:
            print("\n🚏 Stations de départ possibles:")
            for s in route["start_options"]:
                lines_str = " / ".join(s["lines"])
                print(f"   - {s['name']} [{lines_str}]")
        if "end_options" in route:
            print("\n🚏 Stations d'arrivée possibles:")
            for s in route["end_options"]:
                lines_str = " / ".join(s["lines"])
                print(f"   - {s['name']} [{lines_str}]")
        return
    
    print("\n" + "=" * 70)
    print("🗺️  ITINÉRAIRE")
    print("=" * 70)
    
    if route["type"] == "direct":
        step = route["steps"][0]
        print(f"\n🚊 Ligne {step['line']} ({step['type'].upper()})")
        print(f"   {step['from']} → {step['to']}")
        print(f"   📊 {step['num_stations']} stations | 📏 {step['distance_km']:.2f} km | ⏱️ {step['travel_time_min']:.0f} min")
        
        print(f"\n📋 Stations:")
        for i, s in enumerate(step["stations"], 1):
            marker = "🟢" if i == 1 else "🔴" if i == len(step["stations"]) else "⚪"
            print(f"   {marker} {i:2}. {s['name']}")
    
    elif route["type"] == "with_transfer":
        num_transfers = route.get("num_transfers", route["num_lines"] - 1)
        print(f"\n🔀 Itinéraire avec {num_transfers} correspondance(s)")
        print(f"⏱️  Temps total: {route['total_time']:.0f} min")
        print(f"📏 Distance totale: {route['total_distance_km']:.2f} km")
        print(f"📊 Stations totales: {route['total_stations']}")
        
        step_num = 1
        for step in route["steps"]:
            if step["type"] == "ride":
                print(f"\n{'─' * 70}")
                print(f"🚊 ÉTAPE {step_num}: Ligne {step['line']} ({step['line_name']})")
                print(f"{'─' * 70}")
                print(f"   De: {step['from']}")
                print(f"   À:  {step['to']}")
                print(f"   📊 {step['num_stations']} stations | ⏱️ {step['travel_time_min']:.0f} min")
                print(f"\n   Stations:")
                for j, s in enumerate(step["stations"], 1):
                    marker = "🟢" if j == 1 else "🔴" if j == len(step["stations"]) else "⚪"
                    print(f"      {marker} {j:2}. {s['name']}")
                step_num += 1
            
            elif step["type"] == "transfer":
                print(f"\n{'=' * 70}")
                print(f"🚶 CORRESPONDANCE - Marche: {step['walk_time']} min")
                print(f"   Descendre à: {step['from_station']}")
                print(f"   Prendre à:   {step['to_station']}")
                print(f"{'=' * 70}")