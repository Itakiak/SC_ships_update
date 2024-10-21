import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm
import json
import sys
import time

with open("credentials.json", "r", encoding='utf-8') as f:
    credentials = json.load(f)

base_url = "https://api.star-citizen.wiki/api/v3/vehicles?page="

# Récupérer les noms de vaisseaux
all_data = []
page = 1

while True:
    response = requests.get(f"{base_url}{page}")
    
    if response.status_code != 200:
        break
    
    page_data = response.json().get("data", [])
    
    if not page_data:
        break  # Arrêter si aucune donnée n'est renvoyée

    names = [item.get("name") for item in page_data]
    all_data.extend(names)
    
    # Afficher le nombre de pages chargées sur une seule ligne
    sys.stdout.write(f"\rPages chargées : {page}")
    sys.stdout.flush()
    
    page += 1
    time.sleep(0.1)  # Petit délai pour simuler un chargement plus visible

# Effacer la ligne de progression
sys.stdout.write("\r" + " " * 30 + "\r")
sys.stdout.flush()

# Afficher uniquement le total des pages chargées
print(f"Pages chargées : {page - 1}")

# Convertir en DataFrame
ships = pd.DataFrame(all_data, columns=["name"])

def get_vehicle_characteristics(name):
    url = f"https://api.star-citizen.wiki/api/v3/vehicles/{name}?include=components,shops"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

vehicle_names = ships['name'].tolist()
vehicle_data = []

# Récupérer les caractéristiques des vaisseaux
for name in tqdm(vehicle_names, desc="Loading ships specs", unit="vaisseau(x)"):
    if name in ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]:
        continue
    
    characteristics = get_vehicle_characteristics(name)
    if characteristics and "data" in characteristics:
        data = characteristics["data"]
        vehicle_info = {
            "Nom du vaisseau": f'=HYPERLINK("{data.get("pledge_url", "")}", "{data.get("name")}")' if data.get("pledge_url") else data.get("name"),
            "Constructeur": data.get("manufacturer", {}).get("name"),
            "HP vaisseau": data.get("health"),
            "HP bouclier": data.get("shield_hp"),
            "Cargo": data.get("cargo_capacity"),
            "Capa. quantum": data.get("quantum", {}).get("quantum_fuel_capacity"),
            "Crew": str(data.get("crew", {}).get("max", data.get("crew", {}).get("min", "/"))) if data.get("crew", {}).get("max") else str(data.get("crew", {}).get("min", "/")),
            "Type": data.get("type", {}).get("en_EN"),
            "Classe": data.get("production_status", {}).get("en_EN"),
            "Size class": data.get("size_class"),
            "Vitesse SCM": data.get("speed", {}).get("scm"),
            "Vitesse NAV": data.get("speed", {}).get("max"),
            "Où acheter ?": [],
            "Prix (aUEC)": 0,
            "Prix ($)": data.get("msrp"),
        }

        # Parcourir les shops
        for shop in data.get("shops", []):
            shop_name = shop.get("name_raw", "")
            for item in shop.get("items", []):
                base_price = item.get("base_price", 0)
                if vehicle_info["Prix (aUEC)"] == 0:  # Ne garder que le premier prix trouvé
                    vehicle_info["Prix (aUEC)"] = base_price
                vehicle_info["Où acheter ?"].append(shop_name)

        # Combiner les valeurs des magasins en chaîne séparée par " / "
        vehicle_info["Où acheter ?"] = ' / '.join(vehicle_info["Où acheter ?"])

        vehicle_data.append(vehicle_info)

df = pd.DataFrame(vehicle_data)

# Dictionnaire de remplacement des noms des constructeurs
constructeurs_abreviation = {
    "Roberts Space Industries": "RSI",
    "Musashi Industrial and Starflight Concern": "MISC",
    "Anvil Aerospace": "Anvil",
    "Aegis Dynamics": "Aegis",
    "Drake Interplanetary": "Drake",
    "Origin Jumpworks": "Origin"
}

# Remplacer les noms des constructeurs par leurs abréviations
df['Constructeur'] = df['Constructeur'].replace(constructeurs_abreviation)

# Configuration pour Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
client = gspread.authorize(creds)

spreadsheet = client.open("Star citizen - ships")
worksheet = spreadsheet.get_worksheet(0)

df = df.astype(object)  # Convertir tout le DataFrame en type 'object' pour empêcher de futures erreurs
df.fillna("/", inplace=True)

data_to_insert = [df.columns.values.tolist()] + df.values.tolist()
worksheet.clear()
worksheet.update(range_name='A1', values=data_to_insert, value_input_option='USER_ENTERED')