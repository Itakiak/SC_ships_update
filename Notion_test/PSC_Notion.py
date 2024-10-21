import requests
import json
from tqdm import tqdm
import time
import sys
from notion_client import Client

# URL de l'API Star Citizen
base_url = "https://api.star-citizen.wiki/api/v3/vehicles?page="

# Configuration Notion
notion_token = "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"
database_id = "dc5b813d-83e6-40f2-abb7-e70634fee52f"  # Vérifie que c'est bien le bon format (UUID)
notion = Client(auth=notion_token)

# Fonction pour récupérer les caractéristiques d'un véhicule
def get_vehicle_characteristics(name):
    url = f"https://api.star-citizen.wiki/api/v3/vehicles/{name}?include=components,shops"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Récupération des noms de vaisseaux
all_data = []
page = 1

while True:
    response = requests.get(f"{base_url}{page}")
    if response.status_code != 200:
        break
    
    page_data = response.json().get("data", [])
    if not page_data:
        break

    names = [item.get("name") for item in page_data]
    all_data.extend(names)

    sys.stdout.write(f"\rPages chargées : {page}")
    sys.stdout.flush()

    page += 1
    time.sleep(0.1)

sys.stdout.write("\r" + " " * 30 + "\r")
sys.stdout.flush()
print(f"Pages chargées : {page - 1}")

# Dictionnaire de remplacement des noms des constructeurs
constructeurs_abreviation = {
    "Roberts Space Industries": "RSI",
    "Musashi Industrial and Starflight Concern": "MISC",
    "Anvil Aerospace": "Anvil",
    "Aegis Dynamics": "Aegis",
    "Drake Interplanetary": "Drake",
    "Origin Jumpworks": "Origin"
}

# Récupération des caractéristiques des vaisseaux et ajout à Notion
for name in tqdm(all_data, desc="Chargement des spécifications des vaisseaux", unit="vaisseau(x)"):
    if name in ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]:
        continue

    characteristics = get_vehicle_characteristics(name)
    if characteristics and "data" in characteristics:
        data = characteristics["data"]
        
        manufacturer = data.get("manufacturer", {}).get("name")
        manufacturer_abbr = constructeurs_abreviation.get(manufacturer, manufacturer)

        shops = data.get("shops", [])
        buy_locations = []
        price_auec = 0
        for shop in shops:
            shop_name = shop.get("name_raw", "")
            for item in shop.get("items", []):
                base_price = item.get("base_price", 0)
                if price_auec == 0:
                    price_auec = base_price
                buy_locations.append(shop_name)

        try:
            notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Nom du vaisseau": {"title": [{"text": {"content": data.get("name", "")}}]},
                    "Constructeur": {"rich_text": [{"text": {"content": manufacturer_abbr}}]},
                    "HP vaisseau": {"number": data.get("health")},
                    "HP bouclier": {"number": data.get("shield_hp")},
                    "Cargo": {"number": data.get("cargo_capacity")},
                    "Capa. quantum": {"number": data.get("quantum", {}).get("quantum_fuel_capacity")},
                    "Crew": {"rich_text": [{"text": {"content": str(data.get("crew", {}).get("max", data.get("crew", {}).get("min", "/")))}}]},
                    "Type": {"rich_text": [{"text": {"content": data.get("type", {}).get("en_EN", "")}}]},
                    "Classe": {"rich_text": [{"text": {"content": data.get("production_status", {}).get("en_EN", "")}}]},
                    "Size class": {"rich_text": [{"text": {"content": str(data.get("size_class", ""))}}]},
                    "Vitesse SCM": {"number": data.get("speed", {}).get("scm")},
                    "Vitesse NAV": {"number": data.get("speed", {}).get("max")},
                    "Prix (aUEC)": {"number": price_auec},
                    "Prix ($)": {"number": data.get("msrp")},
                    "Où acheter ?": {"rich_text": [{"text": {"content": " / ".join(buy_locations)}}]},
                    "URL": {"url": data.get("pledge_url", "")}
                }
            )
        except Exception as e:
            print(f"Erreur lors de la création de la page pour {data.get('name', '')}: {e}")

print("Mise à jour de la base de données Notion terminée.")