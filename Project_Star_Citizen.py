import pandas as pd
import requests
import gspread
import json
import sys
import concurrent.futures
import warnings  # <--- Ajouté pour le silence
from tqdm import tqdm

# On ignore les alertes de type FutureWarning pour le nettoyage des données
warnings.simplefilter(action='ignore', category=FutureWarning)

# --- CONFIGURATION ---
CREDENTIALS_FILE = "credentials.json"
SHEET_NAME = "Star citizen - ships"
API_BASE_URL = "https://api.star-citizen.wiki/api/v3/vehicles"

BLACKLIST_SHIPS = ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]

CONSTRUCTEURS_ABREVIATION = {
    "Roberts Space Industries": "RSI",
    "Musashi Industrial and Starflight Concern": "MISC",
    "Anvil Aerospace": "Anvil",
    "Aegis Dynamics": "Aegis",
    "Drake Interplanetary": "Drake",
    "Origin Jumpworks": "Origin",
    "Greycat Industrial": "Greycat",
    "Argo Astronautics": "Argo",
    "Tumbril Land Systems": "Tumbril",
    "Gatac Manufacture": "Gatac"
}

def get_all_ship_names():
    all_names = []
    page = 1
    with requests.Session() as session:
        print("Récupération de la liste des vaisseaux...")
        while True:
            try:
                response = session.get(f"{API_BASE_URL}?page={page}", timeout=10)
                if response.status_code != 200: break
                data = response.json().get("data", [])
                if not data: break
                names = [item.get("name") for item in data]
                all_names.extend(names)
                sys.stdout.write(f"\rPages chargées : {page}")
                sys.stdout.flush()
                page += 1
            except requests.RequestException as e:
                print(f"\nErreur page {page}: {e}")
                break
    print(f"\nTotal vaisseaux trouvés : {len(all_names)}")
    return all_names

def fetch_ship_details(session, name):
    if name in BLACKLIST_SHIPS: return None
    url = f"{API_BASE_URL}/{name}?include=components,shops"
    try:
        response = session.get(url, timeout=10)
        return response.json().get("data") if response.status_code == 200 else None
    except: return None

def parse_ship_data(data):
    if not data: return None
    crew_info = data.get("crew", {})
    crew_val = crew_info.get("max") or crew_info.get("min") or "/"
    price_auec = 0
    shops_list = []
    for shop in data.get("shops", []):
        shop_name = shop.get("name_raw", "")
        for item in shop.get("items", []):
            base_price = item.get("base_price", 0)
            if price_auec == 0 and base_price > 0: price_auec = base_price
            if shop_name not in shops_list: shops_list.append(shop_name)
    ship_name = data.get("name", "Unknown")
    pledge_url = data.get("pledge_url", "")
    nom_vaisseau = f'=HYPERLINK("{pledge_url}"; "{ship_name.replace('"', "'")}")' if pledge_url else ship_name

    return {
        "Nom du vaisseau": nom_vaisseau,
        "Constructeur": data.get("manufacturer", {}).get("name"),
        "HP vaisseau": data.get("health"),
        "HP bouclier": data.get("shield_hp"),
        "Cargo": data.get("cargo_capacity"),
        "Capa. quantum": data.get("quantum", {}).get("quantum_fuel_capacity"),
        "Crew": str(crew_val),
        "Type": data.get("type", {}).get("en_EN"),
        "Classe": data.get("production_status", {}).get("en_EN"),
        "Size class": data.get("size_class"),
        "Vitesse SCM": data.get("speed", {}).get("scm"),
        "Vitesse NAV": data.get("speed", {}).get("max"),
        "Prix (aUEC)": price_auec,
        "Prix ($)": data.get("msrp"),
        "Où acheter ?": ' / '.join(shops_list)
    }

def main():
    try:
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
    except Exception as e:
        print(f"Erreur Auth : {e}"); return

    vehicle_names = get_all_ship_names()
    vehicle_data = []
    with requests.Session() as session:
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_ship = {executor.submit(fetch_ship_details, session, name): name for name in vehicle_names}
            for future in tqdm(concurrent.futures.as_completed(future_to_ship), total=len(vehicle_names), desc="Mise à jour", unit="ship"):
                res = future.result()
                parsed = parse_ship_data(res)
                if parsed: vehicle_data.append(parsed)

    df = pd.DataFrame(vehicle_data)
    
    # Remplacement constructeurs
    if 'Constructeur' in df.columns:
        df['Constructeur'] = df['Constructeur'].replace(CONSTRUCTEURS_ABREVIATION)
    
    # MÉTHODE RADICALE : On remplace les NaN par "/" de façon globale avant tout autre traitement
    df = df.where(pd.notnull(df), "/")
    
    # Tri
    if "Nom du vaisseau" in df.columns:
        df.sort_values(by="Nom du vaisseau", inplace=True)

    print("Envoi vers Google Sheets...")
    try:
        sh = gc.open(SHEET_NAME)
        worksheet = sh.get_worksheet(0)
        data_to_insert = [df.columns.values.tolist()] + df.values.tolist()
        worksheet.clear()
        worksheet.update(values=data_to_insert, range_name='A1', value_input_option='USER_ENTERED')
        print("✅ Mise à jour terminée !")
    except Exception as e:
        print(f"❌ Erreur : {e}")

if __name__ == "__main__":
    main()