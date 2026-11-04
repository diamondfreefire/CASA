import json
import os

# ============================================================
# TABLE 1 : STATIONS (coordonnées corrigées WGS 1984)
# ============================================================

STATIONS = {
    # ----- T1 -----
    "T1_01": {"name": "Sidi Moumen", "lat": 33.5869421, "lon": -7.5014958},
    "T1_02": {"name": "Nassim", "lat": 33.5848658, "lon": -7.5047309},
    "T1_03": {"name": "Mohammed Zefzaf", "lat": 33.5823627, "lon": -7.5086783},
    "T1_04": {"name": "Centre de maintenance", "lat": 33.5795318, "lon": -7.5131257},
    "T1_05": {"name": "Hôpital Sidi Moumen", "lat": 33.5765838, "lon": -7.5177446},
    "T1_06": {"name": "Attacharouk", "lat": 33.5740556, "lon": -7.5243104},
    "T1_07": {"name": "Okba Ibnou Nafia", "lat": 33.5729113, "lon": -7.5325590},
    "T1_08": {"name": "Forces Auxiliaires", "lat": 33.5747292, "lon": -7.5394513},
    "T1_09": {"name": "Hay Raja", "lat": 33.5766816, "lon": -7.5484674},
    "T1_10": {"name": "Ibn Tachfine", "lat": 33.5807938, "lon": -7.5634191},
    "T1_11": {"name": "Hay Mohammadi", "lat": 33.5856343, "lon": -7.5667291},
    "T1_12": {"name": "Achouhada", "lat": 33.5884957, "lon": -7.5677696},
    "T1_13": {"name": "Ali Yata", "lat": 33.5914733, "lon": -7.5699572},
    "T1_14": {"name": "Grande Ceinture", "lat": 33.5904069, "lon": -7.5737654},
    "T1_15": {"name": "Anciens Abattoirs", "lat": 33.5909906, "lon": -7.5785810},
    "T1_16": {"name": "Bahmad", "lat": 33.5947641, "lon": -7.5864433},
    "T1_17": {"name": "Gare de Casa-Voyageurs", "lat": 33.5903581, "lon": -7.5919484},
    "T1_18": {"name": "Place Al Yassir", "lat": 33.5929091, "lon": -7.5969495},
    "T1_19": {"name": "La Résistance", "lat": 33.5934485, "lon": -7.6031621},
    "T1_20": {"name": "Mohammed Diouri", "lat": 33.5937216, "lon": -7.6077746},
    "T1_21": {"name": "Marché Central", "lat": 33.5946005, "lon": -7.6126113},
    "T1_22": {"name": "Place des Nations-Unies", "lat": 33.5951210, "lon": -7.6181166},
    "T1_23": {"name": "Place Mohammed V", "lat": 33.5896378, "lon": -7.6200092},
    "T1_24": {"name": "Avenue Hassan II", "lat": 33.5841157, "lon": -7.6230413},
    "T1_25": {"name": "Les Hôpitaux", "lat": 33.5800157, "lon": -7.6248387},
    "T1_26": {"name": "Faculté de Médecine", "lat": 33.5749271, "lon": -7.6258240},
    "T1_27": {"name": "Abdelmoumen", "lat": 33.5705527, "lon": -7.6259823},
    "T1_28": {"name": "Bachkou", "lat": 33.5652367, "lon": -7.6268540},
    "T1_29": {"name": "Mekka", "lat": 33.5578244, "lon": -7.6298311},
    "T1_30": {"name": "Gare de l'Oasis", "lat": 33.5541270, "lon": -7.6313118},
    "T1_31": {"name": "Panoramique", "lat": 33.5471668, "lon": -7.6318846},
    "T1_32": {"name": "Technopark", "lat": 33.5447470, "lon": -7.6380510},
    "T1_33": {"name": "Zénith", "lat": 33.5407369, "lon": -7.6428150},
    "T1_34": {"name": "Gare de Casa-Sud", "lat": 33.5419773, "lon": -7.6506450},
    "T1_35": {"name": "Facultés", "lat": 33.5458466, "lon": -7.6571703},
    "T1_36": {"name": "Al Laymoun", "lat": 33.5400945, "lon": -7.6663597},
    "T1_37": {"name": "Lissasfa", "lat": 33.5350512, "lon": -7.6700775},

    # ----- T2 -----
    "T2_01": {"name": "Aïn Diab", "lat": 33.5874318, "lon": -7.6808073},
    "T2_02": {"name": "Littoral", "lat": 33.5809428, "lon": -7.6748004},
    "T2_03": {"name": "Hay Hassani", "lat": 33.5765668, "lon": -7.6729263},
    "T2_04": {"name": "Sidi Abderrahmane", "lat": 33.5719563, "lon": -7.6693821},
    "T2_05": {"name": "Cité de l'Air", "lat": 33.5682234, "lon": -7.6641842},
    "T2_06": {"name": "Abdellah Ben Cherif", "lat": 33.5658832, "lon": -7.6602935},
    "T2_07": {"name": "Place Financière", "lat": 33.5623151, "lon": -7.6609173},
    "T2_08": {"name": "Anfa Park", "lat": 33.5597662, "lon": -7.6574725},
    "T2_09": {"name": "Anfa Clubs", "lat": 33.5612793, "lon": -7.6530017},
    "T2_10": {"name": "Beauséjour", "lat": 33.5643393, "lon": -7.6479197},
    "T2_11": {"name": "Ghandi", "lat": 33.5687753, "lon": -7.6446034},
    "T2_12": {"name": "Riviera", "lat": 33.5709439, "lon": -7.6363555},
    "T2_13": {"name": "Derb Ghalef", "lat": 33.5700369, "lon": -7.6316695},
    "T2_14": {"name": "Anoual", "lat": 33.5694206, "lon": -7.6249310},
    "T2_15": {"name": "Hermitage", "lat": 33.5691964, "lon": -7.6179068},
    "T2_16": {"name": "2 Mars", "lat": 33.5690979, "lon": -7.6127062},
    "T2_17": {"name": "El Fida", "lat": 33.5664939, "lon": -7.6072591},
    "T2_18": {"name": "Place Sraghna", "lat": 33.5696125, "lon": -7.6021427},
    "T2_19": {"name": "Derb Sultan", "lat": 33.5721247, "lon": -7.5958327},
    "T2_20": {"name": "Hay Farah", "lat": 33.5716601, "lon": -7.5863452},
    "T2_21": {"name": "Derb Milan", "lat": 33.5719662, "lon": -7.5807423},
    "T2_22": {"name": "Cimetière Achouhada", "lat": 33.5765751, "lon": -7.5744115},
    "T2_23": {"name": "Hay Adil", "lat": 33.5792387, "lon": -7.5681439},
    "T2_24": {"name": "Mdakra", "lat": 33.5811962, "lon": -7.5634043},
    "T2_25": {"name": "Kissariat Hay Mohammadi", "lat": 33.5870986, "lon": -7.5635552},
    "T2_26": {"name": "Carrières Centrales", "lat": 33.5927308, "lon": -7.5644470},
    "T2_27": {"name": "Dar Laman", "lat": 33.5937762, "lon": -7.5574550},
    "T2_28": {"name": "Wifaq", "lat": 33.5957085, "lon": -7.5378809},
    "T2_29": {"name": "Al Aman", "lat": 33.5991917, "lon": -7.5327628},
    "T2_30": {"name": "Préfecture d'Aïn Sebaâ", "lat": 33.6021198, "lon": -7.5299302},
    "T2_31": {"name": "Gare d'Aïn Sebaâ", "lat": 33.6074235, "lon": -7.5243059},
    "T2_32": {"name": "Abou Dar Al Ghifari", "lat": 33.6066082, "lon": -7.5180446},
    "T2_33": {"name": "Sidi Bernoussi", "lat": 33.6100859, "lon": -7.5098188},

    # ----- T3 -----
    "T3_01": {"name": "Gare Casa-Port", "lat": 33.5982808, "lon": -7.6119462},
    "T3_02": {"name": "Mohammed Smiha", "lat": 33.5931834, "lon": -7.6087036},
    "T3_03": {"name": "Place de la Victoire", "lat": 33.5883375, "lon": -7.6085431},
    "T3_04": {"name": "Mohammed Zerktouni", "lat": 33.5849179, "lon": -7.6059461},
    "T3_05": {"name": "Habous", "lat": 33.5789697, "lon": -7.6007293},
    "T3_06": {"name": "Garage Allal", "lat": 33.5760050, "lon": -7.5991351},
    "T3_07": {"name": "Derb Tolba", "lat": 33.5712092, "lon": -7.5968214},
    "T3_08": {"name": "Derb Chorfa", "lat": 33.5664626, "lon": -7.5956040},
    "T3_09": {"name": "Abou Chouaib Doukkali", "lat": 33.5617773, "lon": -7.5947489},
    "T3_10": {"name": "Afriquia", "lat": 33.5549753, "lon": -7.5925944},
    "T3_11": {"name": "Dar Attouzani", "lat": 33.5489272, "lon": -7.5864876},
    "T3_12": {"name": "Bd Mohammed VI", "lat": 33.5435771, "lon": -7.5808243},
    "T3_13": {"name": "6 Novembre", "lat": 33.5464155, "lon": -7.5759409},
    "T3_14": {"name": "Abdessalam Ennaciri", "lat": 33.5483742, "lon": -7.5726160},
    "T3_15": {"name": "Jardin Alesco", "lat": 33.5507114, "lon": -7.5688198},
    "T3_16": {"name": "Hay Lalla Meriem", "lat": 33.5570446, "lon": -7.5584269},
    "T3_17": {"name": "Idriss El Allam", "lat": 33.559843007184256, "lon": -7.5510242443356965},
    "T3_18": {"name": "Abdelkader Essahraoui", "lat": 33.5558468, "lon": -7.5476375},
    "T3_19": {"name": "10 Mars", "lat": 33.5518863, "lon": -7.5508633},
    "T3_20": {"name": "Hay Al Wahda", "lat": 33.5446960, "lon": -7.5488921},

    # ----- T4 -----
    "T4_01": {"name": "Parc de la Ligue Arabe", "lat": 33.5881461, "lon": -7.6220418},
    "T4_02": {"name": "Mers Sultan", "lat": 33.5878420, "lon": -7.6170665},
    "T4_03": {"name": "Jaber ibn Hayane", "lat": 33.5888244, "lon": -7.6077100},
    "T4_04": {"name": "La Gironde", "lat": 33.5877705, "lon": -7.6012121},
    "T4_05": {"name": "Ifni", "lat": 33.5847669, "lon": -7.5981333},
    "T4_06": {"name": "Aïn Borja", "lat": 33.5803669, "lon": -7.5919089},
    "T4_07": {"name": "Gare Ouled Ziane", "lat": 33.5761014, "lon": -7.5858925},
    "T4_08": {"name": "Hay Tissir", "lat": 33.5724040, "lon": -7.5805767},
    "T4_09": {"name": "Jardin Chtaiba", "lat": 33.5653058, "lon": -7.5709571},
    "T4_10": {"name": "Boulevard du Nil", "lat": 33.5665552, "lon": -7.5648230},
    "T4_11": {"name": "Hay Assalama", "lat": 33.5680572, "lon": -7.5587672},
    "T4_12": {"name": "Mohammed Bouziane", "lat": 33.5638795, "lon": -7.5545659},
    "T4_13": {"name": "Idriss El Harti", "lat": 33.56141713193964, "lon": -7.550958414375435},
    "T4_14": {"name": "Hay El Falah", "lat": 33.5632396, "lon": -7.5479507},
    "T4_15": {"name": "Faculté Ben M'Sick", "lat": 33.5660792, "lon": -7.5430075},
    "T4_16": {"name": "Mohammed Joudar", "lat": 33.5684014, "lon": -7.5362432},
    "T4_17": {"name": "Moulay Rachid", "lat": 33.5715192, "lon": -7.5312834},
    "T4_18": {"name": "Zone Industrielle", "lat": 33.5707943, "lon": -7.5241872},
    "T4_19": {"name": "Mohammed Erradi", "lat": 33.5692574, "lon": -7.5182281},

    # ----- BW1 -----
    "BW1_01": {"name": "Omar Al Khiyam", "lat": 33.540049, "lon": -7.666877},
    "BW1_02": {"name": "Sidi Maârouf", "lat": 33.532912, "lon": -7.651269},
    "BW1_03": {"name": "Moustakbal", "lat": 33.531660, "lon": -7.646741},
    "BW1_04": {"name": "CasaNearShore", "lat": 33.530253, "lon": -7.638743},
    "BW1_05": {"name": "Californie", "lat": 33.531193, "lon": -7.630616},
    "BW1_06": {"name": "Azzohour", "lat": 33.530487, "lon": -7.623485},
    "BW1_07": {"name": "Taddart", "lat": 33.532044, "lon": -7.616691},
    "BW1_08": {"name": "Hay Chrifa", "lat": 33.535032, "lon": -7.609965},
    "BW1_09": {"name": "Ouled Haddou", "lat": 33.537028, "lon": -7.605340},
    "BW1_10": {"name": "Inara", "lat": 33.539661, "lon": -7.599023},
    "BW1_11": {"name": "Taza", "lat": 33.541284, "lon": -7.593205},
    "BW1_12": {"name": "Sefrou", "lat": 33.542246, "lon": -7.588626},
    "BW1_13": {"name": "Al Qods", "lat": 33.543670, "lon": -7.581954},
    "BW1_14": {"name": "Amgala", "lat": 33.539957, "lon": -7.578898},
    "BW1_15": {"name": "Jardin Sunday", "lat": 33.539956, "lon": -7.578787},
    "BW1_16": {"name": "Lahrizi", "lat": 33.540000, "lon": -7.568560},
    "BW1_17": {"name": "Al Joulane", "lat": 33.543805, "lon": -7.562193},
    "BW1_18": {"name": "Stade Tissima", "lat": 33.540863, "lon": -7.558593},
    "BW1_19": {"name": "Sbata", "lat": 33.538419, "lon": -7.554733},
    "BW1_20": {"name": "Salmia 2", "lat": 33.537030, "lon": -7.550713},

    # ----- BW2 (coordonnées corrigées depuis Overpass) -----
    "BW2_01": {"name": "Oulmès", "lat": 33.5715969, "lon": -7.6485714},
    "BW2_02": {"name": "C.I.L.", "lat": 33.5672889, "lon": -7.6561487},
    "BW2_03": {"name": "Les Musees", "lat": 33.5650847, "lon": -7.6605555},
    "BW2_04": {"name": "Oued Oum Rabia", "lat": 33.5633309, "lon": -7.6650721},
    "BW2_05": {"name": "Oued Laou", "lat": 33.5614368, "lon": -7.6698105},
    "BW2_06": {"name": "Oued Beht", "lat": 33.5583094, "lon": -7.6793888},
    "BW2_07": {"name": "Moulouya", "lat": 33.5562728, "lon": -7.6834727},
    "BW2_08": {"name": "Haj Fateh", "lat": 33.5532501, "lon": -7.6898332},
    "BW2_09": {"name": "Essafa", "lat": 33.5509644, "lon": -7.6961115},
    "BW2_10": {"name": "Moulay Thami", "lat": 33.5484912, "lon": -7.7011037},
    "BW2_11": {"name": "Riad Al Oulfa", "lat": 33.5462995, "lon": -7.7048930},
    "BW2_12": {"name": "La Rocade", "lat": 33.5438713, "lon": -7.7091522},
    "BW2_13": {"name": "La Perception", "lat": 33.5379458, "lon": -7.7185567},
    "BW2_14": {"name": "Jardin Errahma", "lat": 33.5345712, "lon": -7.7238461},
    "BW2_15": {"name": "Arrahma", "lat": 33.5314650, "lon": -7.7287838},
    "BW2_16": {"name": "Oued Sebou", "lat": 33.5286321, "lon": -7.7336503},
    "BW2_17": {"name": "Les Ecoles", "lat": 33.5266262, "lon": -7.7397676},
    "BW2_18": {"name": "Ouled Ahmed", "lat": 33.5249049, "lon": -7.7459929},
    "BW2_19": {"name": "La Ferme", "lat": 33.5225449, "lon": -7.7511376},
    "BW2_20": {"name": "Ouled Azzouz", "lat": 33.5186039, "lon": -7.7575279},
}

# ============================================================
# CHARGEMENT DE LA GÉOMÉTRIE DEPUIS LES GEOJSON
# ============================================================

def load_line_geometry(geojson_path):
    """Charge un fichier GeoJSON de ligne et retourne les coordonnées"""
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_coords = []
    for feature in data.get("features", []):
        geom = feature.get("geometry", {})
        if geom.get("type") == "LineString":
            all_coords.extend(geom["coordinates"])
        elif geom.get("type") == "MultiLineString":
            for line in geom["coordinates"]:
                all_coords.extend(line)
    return all_coords


def build_lines_with_geometry(base_dir="."):
    """Construit la structure LINES"""
    lines = {
        "T1": {"name": "T1", "type": "tram", "color": "#E30613", "speed": 25,
               "description": "Sidi Moumen ↔ Lissasfa",
               "stations": ["T1_01","T1_02","T1_03","T1_04","T1_05","T1_06","T1_07",
                            "T1_08","T1_09","T1_10","T1_11","T1_12","T1_13","T1_14",
                            "T1_15","T1_16","T1_17","T1_18","T1_19","T1_20","T1_21",
                            "T1_22","T1_23","T1_24","T1_25","T1_26","T1_27","T1_28",
                            "T1_29","T1_30","T1_31","T1_32","T1_33","T1_34","T1_35",
                            "T1_36","T1_37"]},
        "T2": {"name": "T2", "type": "tram", "color": "#009639", "speed": 25,
               "description": "Aïn Diab ↔ Sidi Bernoussi",
               "stations": ["T2_01","T2_02","T2_03","T2_04","T2_05","T2_06","T2_07",
                            "T2_08","T2_09","T2_10","T2_11","T2_12","T2_13","T2_14",
                            "T2_15","T2_16","T2_17","T2_18","T2_19","T2_20","T2_21",
                            "T2_22","T2_23","T2_24","T2_25","T2_26","T2_27","T2_28",
                            "T2_29","T2_30","T2_31","T2_32","T2_33"]},
        "T3": {"name": "T3", "type": "tram", "color": "#F7A800", "speed": 25,
               "description": "Gare Casa-Port ↔ Hay El Wahda",
               "stations": ["T3_01","T3_02","T3_03","T3_04","T3_05","T3_06","T3_07",
                            "T3_08","T3_09","T3_10","T3_11","T3_12","T3_13","T3_14",
                            "T3_15","T3_16","T3_17","T3_18","T3_19","T3_20"]},
        "T4": {"name": "T4", "type": "tram", "color": "#7B2D8E", "speed": 25,
               "description": "Parc Ligue Arabe ↔ Mohammed Erradi",
               "stations": ["T4_01","T4_02","T4_03","T4_04","T4_05","T4_06","T4_07",
                            "T4_08","T4_09","T4_10","T4_11","T4_12","T4_13","T4_14",
                            "T4_15","T4_16","T4_17","T4_18","T4_19"]},
        "BW1": {"name": "BW1", "type": "busway", "color": "#54A057", "speed": 20,
                "description": "Omar Al Khiyam ↔ Salmia 2",
                "stations": [f"BW1_{i:02d}" for i in range(1, 21)]},
        "BW2": {"name": "BW2", "type": "busway", "color": "#A97B50", "speed": 20,
                "description": "Oulmès ↔ Oulad Azzouz",
                "stations": [f"BW2_{i:02d}" for i in range(1, 21)]},
    }

    # Charger la géométrie des lignes T1-T4
    for line_id in ["T1", "T2", "T3", "T4"]:
        path = os.path.join(base_dir, f"Casablanca_Tramway_{line_id}.geojson")
        if os.path.exists(path):
            lines[line_id]["geometry"] = load_line_geometry(path)
            print(f"[OK] Géométrie {line_id} chargée : {len(lines[line_id]['geometry'])} points")
        else:
            lines[line_id]["geometry"] = []
            print(f"[!] Fichier manquant : {path}")

    return lines


# ============================================================
# TABLE 3 : CORRESPONDANCES
# ============================================================

CORRESPONDANCES = [
    # ----- T1 ↔ BW1 -----
    {"station1": "T1_37", "line1": "T1", "name1": "Lissasfa",
     "station2": "BW1_01", "line2": "BW1", "name2": "Omar Al Khiyam",
     "walk_time": 5},

    # ----- T1 ↔ T2 -----
    {"station1": "T1_27", "line1": "T1", "name1": "Abdelmoumen",
     "station2": "T2_14", "line2": "T2", "name2": "Anoual", "walk_time": 3},
    {"station1": "T1_13", "line1": "T1", "name1": "Ali Yata",
     "station2": "T2_26", "line2": "T2", "name2": "Carrières Centrales", "walk_time": 4},
    {"station1": "T1_10", "line1": "T1", "name1": "Ibn Tachfine",
     "station2": "T2_24", "line2": "T2", "name2": "Mdakra", "walk_time": 4},

    # ----- T1 ↔ T3 -----
    {"station1": "T1_20", "line1": "T1", "name1": "Mohammed Diouri",
     "station2": "T3_02", "line2": "T3", "name2": "Mohammed Smiha", "walk_time": 3},

    # ----- T1 ↔ T4 -----
    {"station1": "T1_07", "line1": "T1", "name1": "Okba Ibnou Nafia",
     "station2": "T4_17", "line2": "T4", "name2": "Moulay Rachid", "walk_time": 4},
    {"station1": "T1_23", "line1": "T1", "name1": "Place Mohammed V",
     "station2": "T4_01", "line2": "T4", "name2": "Parc de la Ligue Arabe", "walk_time": 5},

    # ----- T2 ↔ T3 -----
    {"station1": "T2_19", "line1": "T2", "name1": "Derb Sultan",
     "station2": "T3_07", "line2": "T3", "name2": "Derb Tolba", "walk_time": 3},

    # ----- T2 ↔ T4 -----
    {"station1": "T2_21", "line1": "T2", "name1": "Derb Milan",
     "station2": "T4_08", "line2": "T4", "name2": "Hay Tissir", "walk_time": 2},

    # ----- T3 ↔ T4 -----
    {"station1": "T3_03", "line1": "T3", "name1": "Place de la Victoire",
     "station2": "T4_03", "line2": "T4", "name2": "Jaber ibn Hayane", "walk_time": 3},
    {"station1": "T3_17", "line1": "T3", "name1": "Idriss El Allam",
     "station2": "T4_13", "line2": "T4", "name2": "Idriss El Harti", "walk_time": 3},

    # ----- T3 ↔ BW1 -----
    {"station1": "T3_12", "line1": "T3", "name1": "Bd Mohammed VI",
     "station2": "BW1_13", "line2": "BW1", "name2": "Al Qods", "walk_time": 3},

    # ----- T2 ↔ BW2 (CORRIGÉE) -----
    {"station1": "T2_06", "line1": "T2", "name1": "Abdellah Ben Cherif",
     "station2": "BW2_03", "line2": "BW2", "name2": "Les Musees", "walk_time": 4},
]

# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def get_correspondances(station_id):
    results = []
    for corr in CORRESPONDANCES:
        if corr["station1"] == station_id:
            results.append({"from": corr["name1"], "to_station": corr["station2"],
                            "to_name": corr["name2"], "to_line": corr["line2"],
                            "walk_time": corr["walk_time"]})
        elif corr["station2"] == station_id:
            results.append({"from": corr["name2"], "to_station": corr["station1"],
                            "to_name": corr["name1"], "to_line": corr["line1"],
                            "walk_time": corr["walk_time"]})
    return results


def get_lines_for_station(station_id):
    lines = []
    for line_id, line_data in LINES.items():
        if station_id in line_data["stations"]:
            lines.append(line_id)
    return lines


# ============================================================
# INITIALISATION
# ============================================================

LINES = build_lines_with_geometry(base_dir=".")

if __name__ == "__main__":
    print("\n=== RÉSUMÉ DU RÉSEAU ===")
    for line_id, line in LINES.items():
        n_st = len(line["stations"])
        n_pts = len(line.get("geometry", []))
        print(f"{line_id} : {n_st} stations, {n_pts} points de géométrie")

    print(f"\n=== CORRESPONDANCES ({len(CORRESPONDANCES)}) ===")
    for corr in CORRESPONDANCES:
        print(f"  {corr['line1']} {corr['name1']} ↔ {corr['line2']} {corr['name2']} ({corr['walk_time']} min)")