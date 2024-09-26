import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm

# URL de base de l'API
base_url = "https://api.star-citizen.wiki/api/v3/vehicles?page="

# Récupérer les données de toutes les pages, mais seulement les noms
all_data = [
    [item.get("name") for item in requests.get(f"{base_url}{page}").json().get("data", [])]
    for page in range(1, 16)
    if requests.get(f"{base_url}{page}").status_code == 200
]

# Aplatir la liste des listes
all_data = [name for sublist in all_data for name in sublist]

# Créer une DataFrame Pandas avec toutes les données
ships = pd.DataFrame(all_data, columns=["name"])

def get_vehicle_characteristics(name):
    url = f"https://api.star-citizen.wiki/api/v3/vehicles/{name}?include=components,shops"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Retourne les données sous forme de dictionnaire
    else:
        print(f"Erreur lors de la récupération des données pour {name}: {response.status_code}")
        return None

# Liste pour stocker les données des caractéristiques des vaisseaux
vehicle_names = ships['name'].tolist()  # Assure-toi que 'ships' est un DataFrame

vehicle_data = []

# Utiliser tqdm pour afficher la barre de progression
for name in tqdm(vehicle_names, desc="Récupération des caractéristiques", unit="vaisseau"):
    # Gérer les exceptions pour les vaisseaux spécifiques
    if name in ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]:
        print(f"Skipping {name} due to known issue.")
        continue
    
    characteristics = get_vehicle_characteristics(name)
    if characteristics and "data" in characteristics:
        # Extraire les données de la clé "data"
        data = characteristics["data"]
        
        # Vérifier si les champs nécessaires existent dans les données
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
            "Prix de vente": data.get("msrp"),  # Prix
            "lien du pledge": data.get("pledge_url")
        }
        vehicle_data.append(vehicle_info)
    else:
        print(f"Pas de caractéristiques valides pour {name}")

# Créer un nouveau DataFrame avec les données collectées
df = pd.DataFrame(vehicle_data)

# Charger les informations d'identification
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('star-citizen-ships-d2b0ff5a2ca4.json', scope)
client = gspread.authorize(creds)

# Ouvrir le Google Sheet
spreadsheet = client.open("Star citizen - ships")  # Remplace par le nom de ton fichier Google Sheet
worksheet = spreadsheet.get_worksheet(0)  # Utilise la première feuille

# Remplissage des NaN
df.fillna("/", inplace=True)
print("Remplissage des NaN")

# Convertir le DataFrame en liste de listes
data_to_insert = [df.columns.values.tolist()] + df.values.tolist()  # Ajouter les noms de colonnes

# Insérer les données dans la feuille Google Sheet
worksheet.clear()  # Efface les données existantes si tu veux partir de zéro
worksheet.update('A1', data_to_insert)  # Insère les données à partir de la cellule A1