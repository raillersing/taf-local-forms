# taf-local-forms

Application locale pour le projet TAfHSSiM.

Cette application sert pendant la séance, sur le réseau local du formateur. Ne la publiez pas sur Internet sans configuration de sécurité adaptée.

## À quoi sert l'application

Le formateur lance l'application sur son ordinateur.

Les élèves connectés au même Wi-Fi ou au même partage de connexion ouvrent le questionnaire Module 2 avec l'adresse IP locale de l'ordinateur, par exemple :

`http://192.168.1.23:8000/module-2/`

Module 2 : `Comprendre Internet`

## Démarrage rapide

1. Ouvrez Docker Desktop.
2. Configurez le fichier `.env`.
3. Lancez l'application.
4. Créez le compte admin.
5. Chargez les données Module 2.
6. Donnez l'adresse aux élèves.

Guide pas à pas pour la séance :

- [Guide Formateur Terrain](docs/GUIDE_FORMATEUR_TERRAIN.md)

## Avant de commencer

- Installez et lancez Docker Desktop.
- Connectez les élèves au même Wi-Fi ou au même partage de connexion que l'ordinateur du formateur.
- Remplacez `<LAPTOP_LAN_IP>` par l'adresse IPv4 réelle de l'ordinateur.
- Ne donnez jamais `localhost` aux élèves. `localhost` fonctionne seulement sur l'ordinateur du formateur.

## Configuration locale

1. Copiez `.env.example` vers `.env`.
2. Modifiez au minimum ces valeurs :

```env
DEBUG=false
SECRET_KEY=change-me-for-real-use
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],<LAPTOP_LAN_IP>
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://<LAPTOP_LAN_IP>:8000
DATABASE_PATH=/app/data/db.sqlite3
TIME_ZONE=Indian/Antananarivo
```

Exemple :

```env
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.1.23
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://192.168.1.23:8000
```

Important :

- remplacez `SECRET_KEY=change-me-for-real-use` par une valeur propre à votre ordinateur avant une vraie séance ;
- gardez `DEBUG=false` pour l'usage terrain.

## Lancer avec Docker

Dans le dossier du projet :

```powershell
docker compose up --build
```

L'application sera accessible sur l'ordinateur ici :

- `http://127.0.0.1:8000/module-2/`
- `http://localhost:8000/module-2/`

## Première préparation

Créer le superuser :

```powershell
docker compose exec web python manage.py createsuperuser
```

Charger les données Module 2 :

```powershell
docker compose exec web python manage.py seed_module2
```

## Adresse à donner aux élèves

Donnez aux élèves l'URL avec l'IP de l'ordinateur, par exemple :

`http://192.168.1.23:8000/module-2/`

Rappel : ne donnez pas `localhost`.

## Accès formateur

- Admin Django : `http://192.168.1.23:8000/admin/`
- Dashboard Module 2 : `http://192.168.1.23:8000/dashboard/module-2/`
- Export CSV : `http://192.168.1.23:8000/dashboard/export/module-2.csv`

Le dashboard et l'admin demandent une connexion.

## Export CSV

Depuis le dashboard, utilisez le lien `Exporter le CSV`.

Ou ouvrez directement :

`/dashboard/export/module-2.csv`

## Sauvegarde des données

Copiez la base SQLite pour faire une sauvegarde.

Base SQLite :

- en Docker : `/app/data/db.sqlite3`
- hors Docker : `data/db.sqlite3`

Avec `docker compose`, la base est stockée dans le volume `taf_local_forms_data`.

Pour une sauvegarde simple :

1. arrêtez l'application si possible ;
2. copiez le fichier SQLite ou le volume Docker ;
3. gardez une copie sur un support externe si nécessaire.

## Trouver l'adresse IP de l'ordinateur sur Windows

Dans PowerShell :

```powershell
ipconfig
```

Cherchez l'`IPv4 Address` de la carte Wi-Fi ou du partage de connexion actif.

N'utilisez pas :

- une interface déconnectée ;
- une adresse WSL ;
- une adresse virtuelle Docker si elle n'est pas celle du réseau partagé avec les élèves.

## Accès réseau — Diagnostic formateur

Le dashboard formateur inclut une page d'aide au diagnostic réseau :

`/dashboard/network/`

Cette page affiche :

- l'adresse recommandée pour les élèves ;
- les adresses du dashboard, export CSV et admin ;
- les IP candidates détectées automatiquement ;
- des avertissements si l'adresse actuelle est locale uniquement.

Elle respecte la variable d'environnement `TAF_LAN_HOST` :

```env
TAF_LAN_HOST=192.168.1.23
```

Si cette variable est définie, l'adresse recommandée utilise cette IP.
Si elle est absente, la page utilise l'IP détectée dans la requête ou la première IP candidate trouvée.

## Pare-feu Windows

Si les élèves n'arrivent pas à ouvrir la page :

1. vérifiez que Docker Desktop est lancé ;
2. vérifiez l'adresse IP de l'ordinateur ;
3. autorisez le port `8000` dans le pare-feu Windows si besoin ;
4. vérifiez que les appareils sont bien sur le même réseau ;
5. vérifiez qu'il n'y a pas d'isolation client / AP isolation sur le Wi-Fi.

## Test rapide avant la séance

1. ouvrez `http://127.0.0.1:8000/` sur l'ordinateur ;
2. vérifiez que les modules actifs s'affichent ;
3. vérifiez que l'IP locale de l'ordinateur est correcte ;
4. testez l'URL élève sur un téléphone connecté au même réseau ;
5. connectez-vous à l'admin ou au dashboard.

## Checklist avant la séance avec Docker

- Docker Desktop est lancé ;
- `.env` est prêt ;
- `SECRET_KEY` n'est plus la valeur d'exemple ;
- l'IP locale de l'ordinateur est connue ;
- l'accueil élèves `/` s'ouvre sur l'ordinateur ;
- un téléphone sur le même réseau ouvre bien `/module-2/` et `/module-3/` ;
- le cockpit formateur `/dashboard/` est accessible.

Si vous utilisez le mode sans Docker, adaptez cette checklist à votre commande de lancement locale.

## Lancer sans Docker

Si vous utilisez l'environnement Python local du projet :

```powershell
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py seed_module2
.\.venv\Scripts\python manage.py runserver 0.0.0.0:8000
```

Si vous utilisez WSL/Linux, adaptez les commandes à votre environnement.

## Tests

```powershell
.\.venv\Scripts\python manage.py test surveys.tests
```

## URLs utiles

- Accueil élèves (liste des modules) : `/`
- Formulaire Module 2 : `/module-2/`
- Formulaire Module 3 : `/module-3/`
- Page de confirmation : `/module-2/success/<id>/`
- Page de confirmation Module 3 : `/module-3/success/<id>/`
- Cockpit formateur (centralisé) : `/dashboard/`
- Dashboard Module 2 : `/dashboard/module-2/`
- Dashboard Module 3 : `/dashboard/module-3/`
- Accès réseau (diagnostic) : `/dashboard/network/`
- CSV Module 2 : `/dashboard/export/module-2.csv`
- CSV Module 3 : `/dashboard/export/module-3.csv`
- Admin : `/admin/`

Le cockpit formateur `/dashboard/` regroupe tous les outils formateur :
liens vers chaque dashboard, export CSV, diagnostic réseau, et admin Django.

## Dépannage

### Les élèves ne voient pas la page

- vérifiez qu'ils utilisent l'IP de l'ordinateur et non `localhost` ;
- vérifiez que l'ordinateur et les téléphones sont sur le même Wi-Fi ou partage de connexion ;
- vérifiez le pare-feu Windows ;
- relancez `docker compose up --build`.

### Mauvaise IP

- relancez `ipconfig` ;
- utilisez l'adresse IPv4 de la carte active ;
- mettez à jour `.env` si l'IP a changé.

### Le navigateur affiche une erreur CSRF ou host

- vérifiez `ALLOWED_HOSTS` ;
- vérifiez `CSRF_TRUSTED_ORIGINS` ;
- ajoutez l'IP exacte de l'ordinateur, par exemple `192.168.1.23`.

### Les élèves sont connectés mais rien ne charge

- testez depuis l'ordinateur avec `http://127.0.0.1:8000/module-2/` ;
- si cela marche seulement sur l'ordinateur, cherchez un blocage réseau ou pare-feu ;
- vérifiez l'absence d'AP isolation.

### Le formulaire affiche “Le formulaire n'est pas disponible maintenant.”

- lancez d'abord `docker compose exec web python manage.py seed_module2` si c'est la première préparation ;
- si le message reste affiché, connectez-vous à l'admin ;
- vérifiez qu'une session Module 2 existe et qu'elle est active ;
- si une ancienne session existe déjà mais n'est plus active, réactivez-la dans l'admin.

## Logo

Le logo attendu est :

`static/brand/isoc_madagascar_logo.png`

S'il n'est pas présent, l'application affiche automatiquement le texte :

`Internet Society – Chapitre Madagascar`

## Checklist après la séance avec Docker

- exportez le CSV si nécessaire ;
- faites une sauvegarde des données ;
- arrêtez l'application avec `docker compose down`.

Si vous utilisez le mode sans Docker, arrêtez le serveur Python local à la place.
