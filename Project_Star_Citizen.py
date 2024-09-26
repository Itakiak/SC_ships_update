import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm  # Importer tqdm
import json

with open("credentials.json", "r") as f:
    credentials = json.load(f)

base_url = "https://api.star-citizen.wiki/api/v3/vehicles?page="

# Récupérer les noms de vaisseaux
all_data = []
for page in tqdm(range(1, 16), desc="Récupération des vaisseaux", unit="page"):
    response = requests.get(f"{base_url}{page}")
    if response.status_code == 200:
        page_data = response.json().get("data", [])
        names = [item.get("name") for item in page_data]
        all_data.extend(names)

# Convertir en DataFrame
ships = pd.DataFrame(all_data, columns=["name"])

def get_vehicle_characteristics(name):
    url = f"https://api.star-citizen.wiki/api/v3/vehicles/{name}?include=components,shops"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

vehicle_names = ships['name'].tolist()
vehicle_data = []

# Récupérer les caractéristiques des vaisseaux
for name in tqdm(vehicle_names, desc="Récupération des caractéristiques des vaisseaux", unit="vaisseau"):
    if name in ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]:
        continue
    
    characteristics = get_vehicle_characteristics(name)
    if characteristics and "data" in characteristics:
        data = characteristics["data"]
        vehicle_info = {
            "Nom du vaisseau": data.get("name"),
            "HP vaisseau": data.get("health"),
            "HP bouclier": data.get("shield_hp"),
            "Capacité de cargo": data.get("cargo_capacity"),
            "Capacité réservoir quantum": data.get("quantum", {}).get("quantum_fuel_capacity"),
            "crew minimum": data.get("crew", {}).get("min"),
            "crew maximum": data.get("crew", {}).get("max"),
            "Type": data.get("type", {}).get("en_EN"),
            "Classe": data.get("production_status", {}).get("en_EN"),
            "Classe de taille": data.get("size_class"),
            "Vitesse SCM": data.get("speed", {}).get("scm"),
            "Vitesse max": data.get("speed", {}).get("max"),
            "Prix de vente": data.get("msrp"),
            "lien du pledge": data.get("pledge_url")
        }
        vehicle_data.append(vehicle_info)

df = pd.DataFrame(vehicle_data)

# Configuration pour Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
client = gspread.authorize(creds)

spreadsheet = client.open("Star citizen - ships")
worksheet = spreadsheet.get_worksheet(0)

df.fillna("/", inplace=True)
data_to_insert = [df.columns.values.tolist()] + df.values.tolist()
worksheet.clear()
worksheet.update('A1', data_to_insert)
