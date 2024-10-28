from googleapiclient.discovery import build
from google.oauth2 import service_account
from notion_client import Client
import time

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
notion = Client(auth="ton_token_notion")

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
    for row in rows:
        properties = {}
        for i, header in enumerate(headers):
            if i < len(row):  # S'assure que l'on ne dépasse pas les données disponibles
                properties[header] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": row[i]
                            }
                        }
                    ]
                }

        # Création de la page dans la base Notion
        notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties=properties
        )
        time.sleep(0.3)  # Pause pour éviter de dépasser les limites d'API

def main():
    headers, rows = fetch_data_from_google_sheets()
    update_notion_database(headers, rows)
    print("Mise à jour de Notion terminée !")

if __name__ == '__main__':
    main()
