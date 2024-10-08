# Star Citizen Ships Data Collector

Ce projet permet de récupérer des données sur les vaisseaux du jeu **Star Citizen** via l'API publique et de les stocker dans une feuille Google Sheets. 

## Prérequis

Avant d'exécuter ce script, assurez-vous d'avoir les éléments suivants installés :

- Python 3.x
- Les bibliothèques suivantes :
  - `pandas`
  - `requests`
  - `gspread`
  - `oauth2client`
  - `tqdm`
  
Vous pouvez les installer avec pip :

```bash
pip install pandas requests gspread oauth2client tqdm
```

## Configuration

1. **Créez un projet Google Cloud :**
   - Accédez à la [console Google Cloud](https://console.cloud.google.com/).
   - Créez un nouveau projet.
   - Activez l'API Google Sheets pour ce projet.

2. **Créez des identifiants :**
   - Dans la section "Identifiants", créez une clé de service (Service Account).
   - Téléchargez le fichier JSON contenant vos identifiants et renommez-le en `credentials.json`. Placez-le dans le même répertoire que le script.

3. **Partagez votre feuille Google Sheets :**
   - Créez une nouvelle feuille Google Sheets.
   - Partagez-la avec l'adresse e-mail du compte de service (présente dans le fichier JSON des identifiants).

## Exécution

Pour exécuter le script d'exécution, utilisez la commande suivante :

```bash
python execute_PJS.py
```

### Description du script d'exécution (`execute_PJS.py`)

Ce script facilite le téléchargement des fichiers nécessaires et l'exécution du script principal.

#### Fonctionnalités :

1. **Téléchargement des credentials :**
   - Le script récupère le fichier `credentials.json` depuis Google Drive en utilisant son ID de fichier.

2. **Récupération du script principal :**
   - Il télécharge le fichier Python principal, `Project_Star_Citizen.py`, depuis un dépôt GitHub. Remplacez les valeurs `[Your GitHub username]`, `[your_repo]`, et `[your_file].py` par vos informations respectives.

3. **Exécution du script principal :**
   - Une fois le fichier téléchargé, il est exécuté automatiquement via la commande système `os.system("python Project_Star_Citizen.py")`.

4. **Nettoyage :**
   - Le script supprime les fichiers temporaires après leur utilisation.

### Description du script principal (`Project_Star_Citizen.py`)

- **Récupération des vaisseaux :**
  - Le script interroge l'API de Star Citizen pour récupérer les noms des vaisseaux disponibles.
  - Il utilise une boucle `while` pour continuer à récupérer des pages tant que le statut de la réponse est 200.

- **Affichage de la progression :**
  - Pendant le chargement, le nombre de pages chargées est affiché en temps réel dans la console.
  - À la fin du chargement, le nombre total de pages chargées est affiché.

- **Récupération des caractéristiques des vaisseaux :**
  - Pour chaque vaisseau, le script récupère ses caractéristiques (comme les points de vie, la capacité de cargaison, la vitesse, etc.) et les stocke dans un DataFrame Pandas.

- **Envoi des données à Google Sheets :**
  - Les données sont ensuite formatées et envoyées à une feuille Google Sheets pour être consultées facilement.

## Avertissements

- Si vous rencontrez des erreurs de type lors de l'utilisation de Pandas, le script convertit tous les types de données en `object` pour éviter des conflits de type.

## Contribuer

Les contributions sont les bienvenues ! N'hésitez pas à soumettre un problème ou une demande de tirage.