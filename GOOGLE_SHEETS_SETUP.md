# Guide Configuration Google Sheets

Pour que l'application puisse **aussi** sauvegarder les données sur Google Sheets (en plus du fichier local), suivez ces étapes :

## Étape 1 : Créer le Compte de Service

1. Allez sur [Google Cloud Console](https://console.cloud.google.com/).
2. Créez un **Nouveau Projet** (ex : `Veille Niger`).
3. Dans le menu de gauche, allez sur **APIs & Services > Library**.
4. Cherchez et activez ces deux APIs :
    - **Google Sheets API**
    - **Google Drive API**
5. Allez sur **APIs & Services > Credentials**.
6. Cliquez sur **Create Credentials > Service Account**.
7. Donnez un nom (ex : `scraper-bot`) et validez.
8. Une fois créé, cliquez sur l'adresse email de ce compte (ex : `scraper-bot@...`).
9. Allez dans l'onglet **Keys** > **Add Key** > **Create new key** > **JSON**.
10. Un fichier `.json` va se télécharger sur votre ordinateur.

## Étape 2 : Configurer le Projet

1. Copiez tout le contenu de ce fichier JSON téléchargé.
2. Ouvrez le fichier `credentials.json` dans votre dossier `veille_niger`.
3. Remplacez tout le contenu actuel par votre contenu copié.
4. Sauvegardez.

## Étape 3 : Partager la Feuille

1. Allez sur Google Sheets et créez une feuille vide.
2. Renommez la feuille (le fichier en haut) exactement : `Veille_Niger_Data`.
3. Cliquez sur le bouton **Partager**.
4. Collez l'adresse email de votre compte de service (celle créée à l'étape 1, qui ressemble à `scraper-bot@project-id.iam.gserviceaccount.com`).
5. Donnez les droits **Éditeur**.

## C'est fini !

L'application détectera automatiquement la connexion au prochain redémarrage. Si la connexion échoue, ne vous inquiétez pas, vos données sont toujours sauvegardées localement dans `data.csv`.
