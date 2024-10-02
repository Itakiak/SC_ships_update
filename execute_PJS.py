import requests
import os

# URL du fichier Python sur GitHub
url = "https://raw.githubusercontent.com/[Your GitHub username]/[your_repo]/main/[your_file].py"

# Télécharger les credentials depuis Google Drive
drive_file_id = "your_drive_file_id"  # Remplace par l'ID de ton fichier JSON
credentials_url = f"https://drive.google.com/uc?id={drive_file_id}"

response = requests.get(credentials_url)

if response.status_code == 200:
    # Sauvegarder le fichier credentials.json
    with open("credentials.json", "wb") as f:
        f.write(response.content)

    # Récupérer le contenu du fichier Python
    response = requests.get(url)

    if response.status_code == 200:
        with open("temp_script.py", "w", encoding="utf-8") as file:
            file.write(response.text)

        # Exécuter le fichier temporaire
        os.system("python temp_script.py")
else:
    print(f"Erreur de récupération des credentials: {response.status_code}")

# Supprimer les fichiers temporaires après l'exécution
os.remove("temp_script.py")
os.remove("credentials.json")