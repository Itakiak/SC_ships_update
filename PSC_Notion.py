from googleapiclient.discovery import build
from google.oauth2 import service_account
from notion_client import Client
import time
from tqdm import tqdm  # Import de tqdm pour la barre de chargement

# Configuration
SPREADSHEET_ID = '1GJH3QmXWMRwRt0_VuUA6e4C-s23h7SlibBCHXAldYGc'  # ID de Google Sheets
RANGE_NAME = 'Feuille 1!A:Z'  # Récupère toutes les colonnes non-vides
NOTION_DATABASE_ID = 'dc5b813d83e640f2abb7e70634fee52f'  # ID de la base de données Notion

# Connexion à l'API Google Sheets avec les credentials téléchargés
creds = service_account.Credentials.from_service_account_file(
    "credentials.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
sheets_service = build('sheets', 'v4', credentials=creds)

# Connexion à l'API Notion
notion = Client(auth="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")

def fetch_data_from_google_sheets():
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get('values', [])
    if not values:
        return [], []
    headers = values[0]  # Première ligne : en-têtes de colonne
    rows = values[1:]    # Lignes suivantes : données
    return headers, rows

def update_notion_database(headers, rows):
    # Créer une barre de chargement avec tqdm
    with tqdm(total=len(rows), desc="Importation dans Notion", unit="page") as pbar:
        for row in rows:
            properties = {}
            for i, header in enumerate(headers):
                if i < len(row):  # Vérifie si la ligne a une valeur pour cet en-tête
                    properties[header] = {
                        "rich_text": [
                            {
                                "text": {
                                    "content": row[i]
                                }
                            }
                        ]
                    }

            if properties:  # Ne crée la page que si des propriétés sont valides
                notion.pages.create(
                    parent={"database_id": NOTION_DATABASE_ID},
                    properties=properties
                )
                pbar.update(1)  # Mettre à jour la barre de progression après chaque page créée
            time.sleep(0.3)  # Pause pour éviter de dépasser les limites d'API

def main():
    headers, rows = fetch_data_from_google_sheets()
    update_notion_database(headers, rows)
    print("Mise à jour de Notion terminée !")

if __name__ == '__main__':
    main()
