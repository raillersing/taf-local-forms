# taf-local-forms

Application locale pour le projet TAfHSSiM.

Cette application fonctionne seulement dans la salle de formation, sur le reseau local du formateur. Ne la publiez pas sur Internet sans durcissement de securite adapte.

## But de l'application

Le formateur lance l'application sur son laptop.

Les eleves connectes au meme Wi-Fi ou au meme hotspot ouvrent le questionnaire Module 2 avec l'adresse IP locale du laptop, par exemple :

`http://192.168.1.23:8000/module-2/`

Module 2 : `Comprendre Internet`

## Avant de commencer

- Installez et lancez Docker Desktop.
- Connectez les eleves au meme Wi-Fi ou au meme partage de connexion que le laptop.
- Remplacez `<LAPTOP_LAN_IP>` par l'adresse IPv4 reelle du laptop.
- N'utilisez pas `localhost` sur les telephones des eleves. `localhost` fonctionne seulement sur le laptop lui-meme.

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

## Lancer avec Docker

Dans le dossier du projet :

```powershell
docker compose up --build
```

L'application sera accessible sur le laptop ici :

- `http://127.0.0.1:8000/module-2/`
- `http://localhost:8000/module-2/`

## Premiere preparation

Creer le superuser :

```powershell
docker compose exec web python manage.py createsuperuser
```

Creer les donnees Module 2 :

```powershell
docker compose exec web python manage.py seed_module2
```

## Adresse a donner aux eleves

Donnez aux eleves l'URL avec l'IP du laptop, par exemple :

`http://192.168.1.23:8000/module-2/`

## Acces formateur

- Admin Django : `http://192.168.1.23:8000/admin/`
- Dashboard Module 2 : `http://192.168.1.23:8000/dashboard/module-2/`
- Export CSV : `http://192.168.1.23:8000/dashboard/export/module-2.csv`

Le dashboard et l'admin demandent une connexion.

## Export CSV

Depuis le dashboard, utilisez le lien `Exporter le CSV`.

Ou ouvrez directement :

`/dashboard/export/module-2.csv`

## Sauvegarde des donnees

Base SQLite :

- en Docker : `/app/data/db.sqlite3`
- dans l'application locale hors Docker : `data/db.sqlite3`

Avec `docker compose`, la base est stockee dans le volume `taf_local_forms_data`.

Pour une sauvegarde simple :

1. arretez l'application si possible ;
2. faites une copie du fichier SQLite ou du volume Docker ;
3. gardez une copie sur un support externe si necessaire.

## Trouver l'IP locale du laptop sur Windows

Dans PowerShell :

```powershell
ipconfig
```

Cherchez l'`IPv4 Address` de la carte Wi-Fi ou du hotspot actif.

N'utilisez pas :

- une interface deconnectee ;
- une adresse WSL ;
- une adresse virtuelle Docker si elle n'est pas celle du Wi-Fi partage avec les eleves.

## Pare-feu Windows

Si les eleves n'arrivent pas a ouvrir la page :

1. verifiez que Docker Desktop est lance ;
2. verifiez l'adresse IP du laptop ;
3. autorisez le port `8000` dans le pare-feu Windows si besoin ;
4. verifiez que les appareils sont bien sur le meme reseau ;
5. verifiez qu'il n'y a pas d'isolation client / AP isolation sur le Wi-Fi.

## Lancer sans Docker

Si vous utilisez l'environnement Python local du projet :

```powershell
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py seed_module2
.\.venv\Scripts\python manage.py runserver 0.0.0.0:8000
```

## Tests

```powershell
.\.venv\Scripts\python manage.py test
```

## URLs utiles

- Student form : `/module-2/`
- Confirmation page : `/module-2/success/<id>/`
- Dashboard : `/dashboard/module-2/`
- CSV : `/dashboard/export/module-2.csv`
- Admin : `/admin/`

## Depannage

### Les eleves ne voient pas la page

- verifiez qu'ils utilisent l'IP du laptop et non `localhost` ;
- verifiez que le laptop et les telephones sont sur le meme Wi-Fi ou hotspot ;
- verifiez le pare-feu Windows ;
- relancez `docker compose up --build`.

### Mauvaise IP

- relancez `ipconfig` ;
- utilisez l'adresse IPv4 de la carte active ;
- mettez a jour `.env` si l'IP a change.

### Le navigateur affiche une erreur CSRF ou host

- verifiez `ALLOWED_HOSTS` ;
- verifiez `CSRF_TRUSTED_ORIGINS` ;
- ajoutez l'IP exacte du laptop, par exemple `192.168.1.23`.

### Les eleves sont connectes mais rien ne charge

- testez depuis le laptop avec `http://127.0.0.1:8000/module-2/` ;
- si cela marche seulement sur le laptop, cherchez un blocage reseau ou firewall ;
- verifiez l'absence d'AP isolation.

## Validation effectuee pendant le developpement

Commandes executees dans cette session :

```powershell
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py test surveys.tests
```

Note importante :

Cette session Codex tourne depuis Windows contre le chemin UNC WSL du projet. Les fichiers sont bien restes dans `\\wsl.localhost\Ubuntu\home\raillersing\projects\taf-local-forms`, mais les validations Python executees ici ont utilise `.\.venv\Scripts\python` cote Windows. Le projet recommande tout de meme l'usage WSL/Linux si votre environnement local est configure ainsi.
