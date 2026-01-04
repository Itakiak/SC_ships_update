import pandas as pd
import requests
import gspread
import json
import sys
import concurrent.futures
from tqdm import tqdm

# --- CONFIGURATION ---
CREDENTIALS_FILE = "credentials.json"
SHEET_NAME = "Star citizen - ships"
API_BASE_URL = "https://api.star-citizen.wiki/api/v3/vehicles"
# Vaisseaux à ignorer explicitement
BLACKLIST_SHIPS = ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]

# Dictionnaire de remplacement des noms des constructeurs
CONSTRUCTEURS_ABREVIATION = {
    "Roberts Space Industries": "RSI",
    "Musashi Industrial and Starflight Concern": "MISC",
    "Anvil Aerospace": "Anvil",
    "Aegis Dynamics": "Aegis",
    "Drake Interplanetary": "Drake",
    "Origin Jumpworks": "Origin"
}

def get_all_ship_names():
    """Récupère la liste complète des noms de vaisseaux via pagination."""
    all_names = []
    page = 1
    
    with requests.Session() as session:
        print("Récupération de la liste des vaisseaux...")
        while True:
            try:
                response = session.get(f"{API_BASE_URL}?page={page}", timeout=10)
                if response.status_code != 200:
                    break
                
                data = response.json().get("data", [])
                if not data:
                    break

                names = [item.get("name") for item in data]
                all_names.extend(names)
                
                # Feedback visuel propre
                sys.stdout.write(f"\rPages chargées : {page}")
                sys.stdout.flush()
                page += 1
            except requests.RequestException as e:
                print(f"\nErreur lors de la récupération de la page {page}: {e}")
                break
                
    print(f"\nTotal vaisseaux trouvés : {len(all_names)}")
    return all_names

def fetch_ship_details(session, name):
    """Récupère les détails d'un vaisseau spécifique."""
    if name in BLACKLIST_SHIPS:
        return None

    url = f"{API_BASE_URL}/{name}?include=components,shops"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("data")
    except requests.RequestException:
        return None
    return None

def parse_ship_data(data):
    """Extrait et formate les données d'un vaisseau."""
    if not data:
        return None

    # Logique Crew (Max > Min > /)
    crew_info = data.get("crew", {})
    crew_val = crew_info.get("max") or crew_info.get("min") or "/"

    # Logique Prix et Shops
    price_auec = 0
    shops_list = []
    
    for shop in data.get("shops", []):
        shop_name = shop.get("name_raw", "")
        for item in shop.get("items", []):
            base_price = item.get("base_price", 0)
            # On prend le premier prix trouvé si c'est encore 0
            if price_auec == 0 and base_price > 0:
                price_auec = base_price
            if shop_name not in shops_list:
                shops_list.append(shop_name)

    # Gestion sécurisée du lien hypertexte (échappement des guillemets doubles)
    ship_name = data.get("name", "Unknown")
    pledge_url = data.get("pledge_url", "")
    
    # Formule Google Sheets
    if pledge_url:
        # On remplace les guillemets doubles par des simples dans le nom pour éviter de casser la formule Excel
        safe_name = ship_name.replace('"', "'")
        nom_vaisseau = f'=HYPERLINK("{pledge_url}"; "{safe_name}")'
    else:
        nom_vaisseau = ship_name

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
    # 1. Chargement des credentials
    try:
        # gspread gère maintenant auth directement avec le dict ou le fichier
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
    except Exception as e:
        print(f"Erreur d'authentification GSpread : {e}")
        return

    # 2. Récupération des noms
    vehicle_names = get_all_ship_names()
    
    # 3. Récupération des détails en PARALLÈLE (Multithreading)
    vehicle_data = []
    
    # On utilise une Session pour réutiliser les connexions TCP (beaucoup plus rapide)
    with requests.Session() as session:
        # max_workers=20 signifie 20 requêtes simultanées
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # On prépare les futures
            future_to_ship = {executor.submit(fetch_ship_details, session, name): name for name in vehicle_names}
            
            for future in tqdm(concurrent.futures.as_completed(future_to_ship), total=len(vehicle_names), desc="Mise à jour des vaisseaux", unit="ship"):
                try:
                    data = future.result()
                    parsed = parse_ship_data(data)
                    if parsed:
                        vehicle_data.append(parsed)
                except Exception as e:
                    print(f"Erreur de traitement: {e}")

    # 4. Création DataFrame
    df = pd.DataFrame(vehicle_data)
    
    # Nettoyage et Remplacements
    df['Constructeur'] = df['Constructeur'].replace(CONSTRUCTEURS_ABREVIATION)
    df.fillna("/", inplace=True) # Remplace les NaN par /
    
    # Tri par nom pour être propre
    df.sort_values(by="Nom du vaisseau", inplace=True)

    # 5. Envoi vers Google Sheets
    print("Envoi vers Google Sheets...")
    try:
        sh = gc.open(SHEET_NAME)
        worksheet = sh.get_worksheet(0)
        
        # Préparation des données (Header + Values)
        # Convertir en liste de listes
        data_to_insert = [df.columns.values.tolist()] + df.values.tolist()
        
        # Mise à jour en une seule fois (clear + update)
        worksheet.clear()
        worksheet.update(values=data_to_insert, range_name='A1', value_input_option='USER_ENTERED')
        print("Mise à jour terminée avec succès !")
        
    except gspread.SpreadsheetNotFound:
        print(f"Erreur : Le fichier '{SHEET_NAME}' est introuvable sur Google Drive.")
    except Exception as e:
        print(f"Erreur lors de l'écriture Google Sheets : {e}")

if __name__ == "__main__":
    main()