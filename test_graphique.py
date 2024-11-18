import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tqdm import tqdm
import json
import os
import sys
import time

# Fonction pour ouvrir le fichier Google Sheets
def open_file():
    file_path = filedialog.askopenfilename(title="Ouvrir un fichier", filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")))
    if file_path:
        print(f"Fichier ouvert : {file_path}")

# Fonction de mise à jour des vaisseaux
def update_ships():
    with open("credentials.json", "r", encoding='utf-8') as f:
        credentials = json.load(f)

    base_url = "https://api.star-citizen.wiki/api/v3/vehicles?page="
    all_data = []
    page = 1

    # Initialisation des barres de progression
    global progress_bar_1, progress_bar_2
    progress_bar_1["value"] = 0
    progress_bar_2["value"] = 0
    root.update_idletasks()

    while True:
        response = requests.get(f"{base_url}{page}")
        
        if response.status_code != 200:
            break
        
        page_data = response.json().get("data", [])
        
        if not page_data:
            break
        
        names = [item.get("name") for item in page_data]
        all_data.extend(names)
        
        # Mise à jour de la barre de progression générale
        progress_bar_1["value"] = (page / 50) * 100  # Supposons 50 pages max
        progress_bar_1.update()

        page += 1
        time.sleep(0.1)  # Petit délai pour simuler un chargement plus visible

    print(f"Loaded pages: {page - 1}")

    # Conversion des vaisseaux en DataFrame
    ships = pd.DataFrame(all_data, columns=["name"])

    vehicle_names = ships['name'].tolist()
    vehicle_data = []

    # Mise à jour des caractéristiques des vaisseaux
    for name in tqdm(vehicle_names, desc="Mise à jour des vaisseaux", unit="vaisseaux"):
        if name in ["Carrack Expedition w/C8X", "Carrack w/C8X", "C8 Pisces"]:
            continue
        
        characteristics = get_vehicle_characteristics(name)
        if characteristics and "data" in characteristics:
            data = characteristics["data"]
            vehicle_info = {
                "Nom du vaisseau": f'=HYPERLINK("{data.get("pledge_url")}"; "{data.get("name")}")',
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
                "Prix (aUEC)": 0,
                "Prix ($)": data.get("msrp"),
                "Où acheter ?": [],
            }

            # Parcourir les shops
            for shop in data.get("shops", []):
                shop_name = shop.get("name_raw", "")
                for item in shop.get("items", []):
                    base_price = item.get("base_price", 0)
                    if vehicle_info["Prix (aUEC)"] == 0:  # Ne garder que le premier prix trouvé
                        vehicle_info["Prix (aUEC)"] = base_price
                    vehicle_info["Où acheter ?"].append(shop_name)

            vehicle_info["Où acheter ?"] = ' / '.join(vehicle_info["Où acheter ?"])

            vehicle_data.append(vehicle_info)

        # Mise à jour de la barre de progression des vaisseaux
        progress_bar_2["value"] = (vehicle_names.index(name) / len(vehicle_names)) * 100
        progress_bar_2.update()

    # Mise à jour des données dans Google Sheets
    df = pd.DataFrame(vehicle_data)
    df['Constructeur'] = df['Constructeur'].replace({
        "Roberts Space Industries": "RSI",
        "Musashi Industrial and Starflight Concern": "MISC",
        "Anvil Aerospace": "Anvil",
        "Aegis Dynamics": "Aegis",
        "Drake Interplanetary": "Drake",
        "Origin Jumpworks": "Origin"
    })

    df.fillna("/", inplace=True)

    # Google Sheets config
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Star citizen - ships")
    worksheet = spreadsheet.get_worksheet(0)

    data_to_insert = [df.columns.values.tolist()] + df.values.tolist()
    worksheet.clear()
    worksheet.update(range_name='A1', values=data_to_insert, value_input_option='USER_ENTERED')

# Fonction pour récupérer les caractéristiques des vaisseaux
def get_vehicle_characteristics(name):
    url = f"https://api.star-citizen.wiki/api/v3/vehicles/{name}?include=components,shops"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

# Création de la fenêtre principale
root = tk.Tk()
root.title("Mise à jour des vaisseaux Star Citizen")
root.geometry("500x400")

# Création des barres de progression
progress_bar_1 = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar_1.grid(row=0, column=0, padx=10, pady=10)

progress_bar_2 = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar_2.grid(row=1, column=0, padx=10, pady=10)

# Ajouter un bouton pour ouvrir le fichier
open_button = tk.Button(root, text="Ouvrir fichier", command=open_file)
open_button.grid(row=2, column=0, pady=10)

# Ajouter un bouton pour lancer la mise à jour
update_button = tk.Button(root, text="Mettre à jour les vaisseaux", command=update_ships)
update_button.grid(row=3, column=0, pady=10)

# Démarrer l'interface graphique
root.mainloop()

if os.path.exists('temp_script.py'):
    os.remove('temp_script.py')