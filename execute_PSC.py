import requests
import os

url = "https://raw.githubusercontent.com/[Your GitHub username]/[your_repo]/refs/heads/main/[your_file].py"

# Télécharger les credentials depuis Google Drive
drive_file_id = "your_drive_file_id"  # Remplace par l'ID de ton fichier JSON
credentials_url = f"https://drive.google.com/uc?id={drive_file_id}"

response = requests.get(credentials_url)

if response.status_code == 200:
    # Sauvegarder le fichier credentials.json
    with open("credentials.json", "wb") as f:
        f.write(response.content)

    # Récupérer et exécuter Project_Star_Citizen.py
    response_main = requests.get(url_main_script)
    if response_main.status_code == 200:
        with open("temp_script.py", "w", encoding="utf-8") as file:
            file.write(response_main.text)

        # Exécuter Project_Star_Citizen.py
        os.system("python temp_script.py")
    else:
        print(f"Erreur de récupération de Project_Star_Citizen.py: {response_main.status_code}")

else:
    print(f"Erreur de récupération des credentials: {response.status_code}")

os.remove("temp_script.py")
os.remove("credentials.json")

print("Script executed successfully.")
