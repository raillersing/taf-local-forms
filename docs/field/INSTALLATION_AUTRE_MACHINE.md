# Installer TAf Local Forms sur une autre machine

## Statut de ce guide

Ce guide décrit l'installation **manuelle actuelle**. Docker rend l'application
principale transférable. Les scripts LAN détectent le dépôt lorsqu'ils sont
lancés depuis `\\wsl.localhost`; sinon, renseigner `TAF_WSL_PROJECT_PATH` et,
si nécessaire, `TAF_WSL_DISTRO` avant de lancer les actions LAN.

## Machine cible recommandée

- Windows 11 64 bits avec droits administrateur ;
- Docker Desktop avec moteur WSL 2 ;
- une distribution Ubuntu WSL ;
- Git ;
- PowerShell 5.1 ou supérieur ;
- 4 coeurs, 8 Go de RAM et 10 Go libres recommandés ;
- Wi-Fi ou hotspot privé pour les élèves.

L'application reste destinée à un réseau local de classe. Ne pas ouvrir les
ports sur Internet.

## 1. Installer les prérequis

1. Activer WSL 2 et installer Ubuntu.
2. Installer Docker Desktop et activer l'intégration avec Ubuntu.
3. Installer Git.
4. Redémarrer Windows, puis vérifier dans Ubuntu :

```sh
docker version
docker compose version
git --version
```

## 2. Installer le dépôt

Dans Ubuntu WSL :

```sh
mkdir -p ~/projects
cd ~/projects
git clone <URL_DU_DEPOT> taf-local-forms
cd taf-local-forms
git checkout <TAG_DE_RELEASE_VALIDE>
```

Utiliser un tag validé, jamais une branche de développement avec des fichiers
non commités.

## 3. Préparer la configuration

```sh
cp .env.example .env
```

Modifier localement `.env` sans jamais le transmettre ni le commiter. Définir au
minimum :

- un `SECRET_KEY` aléatoire et unique ;
- un mot de passe PostgreSQL unique ;
- `DEBUG=0` ;
- l'adresse IPv4 du PC dans `ALLOWED_HOSTS` ;
- les origines locales 8010 et 8011 dans `CSRF_TRUSTED_ORIGINS` ;
- les paramètres PostgreSQL attendus par `docker-compose.yml`.

Exemple de génération d'un secret dans WSL :

```sh
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Ne pas réutiliser les valeurs `change-me-*` ou `taf-dev-only`.

## 4. Construire et démarrer

```sh
docker compose config
docker compose up -d --build
docker compose ps
```

Les services `web` et `db` doivent être actifs ; PostgreSQL doit être sain.

## 5. Créer le compte formateur

```sh
docker compose exec web python manage.py createsuperuser
```

Utiliser un mot de passe robuste et nominatif. Ne pas partager le compte admin
avec les élèves.

## 6. Initialiser les modules

```sh
docker compose exec web python manage.py seed_module_2
docker compose exec web python manage.py seed_module_3
docker compose exec web python manage.py seed_module_4
docker compose exec web python manage.py seed_module_5
docker compose exec web python manage.py seed_module_6
docker compose exec web python manage.py seed_module_7
docker compose exec web python manage.py seed_module_8
```

Les commandes doivent être idempotentes avant d'être utilisées en exploitation.

## 7. Vérifier le poste local

```sh
curl -I http://127.0.0.1:8010/
curl -I http://127.0.0.1:8010/modules/
scripts/dev/taf-field-smoke-check
```

Ouvrir ensuite `http://localhost:8010/` et vérifier la connexion formateur.

## 8. Configurer l'accès des téléphones

### Contexte WSL

Si le dépôt est ouvert depuis `\\wsl.localhost`, les scripts détectent le chemin
Linux. Pour une copie Windows ou une distribution WSL non détectée, renseigner
le contexte avant de les lancer :

```powershell
$env:TAF_WSL_PROJECT_PATH = "/home/<utilisateur>/projects/taf-local-forms"
$env:TAF_WSL_DISTRO = "Ubuntu"
```

Ouvrir ensuite PowerShell en administrateur à la racine du dépôt :

```powershell
Set-ExecutionPolicy -Scope Process Bypass
& ".\scripts\windows\taf-lan-helper-start.ps1"
& ".\scripts\windows\taf-lan-sync.ps1"
& ".\scripts\windows\taf-lan-show-status.ps1"
```

Puis :

1. ouvrir `/dashboard/network/` avec le compte formateur ;
2. confirmer l'adresse IPv4 et l'état du pare-feu ;
3. connecter un téléphone au même Wi-Fi/hotspot ;
4. désactiver temporairement les données mobiles du téléphone ;
5. ouvrir `http://<IP_DU_PC>:8011/` ;
6. soumettre un questionnaire de test et vérifier sa présence dans le cockpit.

Un statut helper vert ne remplace pas ce test physique.

## 9. Transférer des données existantes

Cloner le dépôt ne transfère ni PostgreSQL ni les médias. Pour déplacer une
installation existante :

1. arrêter les nouvelles saisies sur la machine source ;
2. produire une sauvegarde PostgreSQL et une archive des médias ;
3. vérifier leur taille et leur somme de contrôle ;
4. installer exactement la même version sur la cible ;
5. restaurer la base et les médias ;
6. exécuter les contrôles de cohérence et un parcours élève complet ;
7. conserver la source intacte jusqu'à validation humaine.

La restauration Compose est volontairement protégée par
`scripts/dev/taf-db-restore <dossier_backup> --confirm-restore`. Elle remplace
la base et les médias actuels, exige l'arrêt préalable du web et doit être
testée par un mainteneur sur une machine vierge avant tout usage terrain.

## 10. Arrêt et mises à jour

Arrêt non destructif :

```sh
docker compose down --remove-orphans
```

Ne jamais utiliser `docker compose down -v` : cette commande supprime les
volumes persistants et peut détruire la base et les médias.

Avant chaque mise à jour : sauvegarder, vérifier la sauvegarde, lire les notes de
version, utiliser un tag validé, reconstruire, puis refaire le smoke check et le
test téléphone.

## Critères d'installation réussie

- web et PostgreSQL actifs et sains ;
- contrôles Django et migrations sans anomalie ;
- suite de tests de la release entièrement verte ;
- accueil, modules et supports accessibles localement ;
- cockpit et admin inaccessibles sans authentification ;
- téléphone réel capable d'ouvrir et soumettre via le LAN ;
- sauvegarde produite et restauration testée ;
- aucune valeur secrète de démonstration conservée.






• Voici les checklists manuelles à exécuter avant de considérer l’application commercialisable.

  ### 1. Installation sur une nouvelle machine

  - Installer Windows 11, Docker Desktop, WSL2, Ubuntu et Git.
  - Cloner le dépôt dans WSL.
  - Copier .env.example vers .env.
  - Générer un SECRET_KEY unique.
  - Définir un mot de passe PostgreSQL unique.
  - Vérifier ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS et l’IP LAN.
  - Lancer :

  docker compose config
  docker compose up -d --build
  docker compose ps

  - Vérifier que web et db sont actifs et que PostgreSQL est sain.
  - Créer le compte formateur.
  - Initialiser les modules 2 à 8.
  - Vérifier l’accès à l’accueil, aux modules et aux supports.

  ### 2. Parcours élève

  Pour chaque module 2 à 8 :

  - Ouvrir la page module.
  - Vérifier le contenu pédagogique.
  - Ouvrir le questionnaire.
  - Vérifier les champs obligatoires.
  - Soumettre une réponse valide.
  - Vérifier la page de succès.
  - Soumettre une seconde fois avec le même élève et confirmer le blocage anti-doublon.
  - Tester un module fermé et vérifier la page indisponible.
  - Vérifier que l’élève ne voit aucun lien Cockpit, Admin, Réseau ou Exports.
  - Tester sur téléphone en 360 px et 390 px.

  ### 3. Parcours formateur

  - Ouvrir /dashboard/ sans connexion et vérifier la redirection.
  - Se connecter avec le compte formateur.
  - Vérifier le cockpit.
  - Vérifier les modules 2 à 8.
  - Vérifier la projection.
  - Vérifier les supports.
  - Vérifier l’upload d’un support autorisé.
  - Vérifier les exports CSV.
  - Vérifier la présence en temps réel.
  - Vérifier la sauvegarde.
  - Vérifier que /admin/ reste protégé.
  - Vérifier que /dashboard/network-control/ reste réservé au staff.

  ### 4. Réseau local Windows

  Dans PowerShell administrateur :

  Set-ExecutionPolicy -Scope Process Bypass
  & ".\scripts\windows\taf-lan-helper-start.ps1"
  & ".\scripts\windows\taf-lan-sync.ps1"
  & ".\scripts\windows\taf-lan-show-status.ps1"

  - Vérifier que le helper répond sur http://127.0.0.1:8019/status.
  - Vérifier l’IP Wi-Fi détectée.
  - Vérifier le portproxy 8011 -> 8010.
  - Vérifier la règle pare-feu TAf Local Forms - Port 8011.
  - Vérifier que Django accepte l’IP LAN.
  - Depuis un vrai téléphone connecté au même Wi-Fi, ouvrir :

  http://IP_DU_PC:8011/

  - Ouvrir /module-2/.
  - Soumettre un questionnaire depuis le téléphone.
  - Vérifier la réponse dans le cockpit.
  - Tester après redémarrage Docker.
  - Tester après changement d’adresse IP.
  - Vérifier que localhost n’est jamais communiqué aux élèves.

  ### 5. Sauvegarde

  Avant toute mise à jour :

  bash scripts/dev/taf-db-backup

  Vérifier manuellement :

  - Le dossier de sauvegarde est créé.
  - database.postgres.dump existe.
  - media.tar.gz existe.
  - MANIFEST.txt existe.
  - SHA256SUMS existe.
  - Les sommes SHA-256 sont valides.
  - Le commit indiqué correspond à la version installée.
  - Le dossier est copié hors du laptop.
  - Aucun fichier de sauvegarde n’est ajouté à Git.

  ### 6. Restauration sur machine vierge

  À effectuer uniquement sur une machine ou une pile de test :

  - Vérifier le nombre de réponses.
  - Vérifier les modules et sessions.
  - Vérifier les supports et vidéos.
  - Vérifier un export CSV.
  - Vérifier qu’aucune réponse n’a été perdue.
  - Vérifier qu’aucun doublon n’a été créé.
  - Documenter la durée de restauration et les éventuelles erreurs.

  ### 7. Validation finale

  - manage.py check passe.
  - makemigrations --check --dry-run indique aucune migration.
  - Les 578 tests passent.
  - docker compose config passe avec de vrais secrets.
  - Le conteneur est reconstruit avec docker compose up -d --build.
  - Le smoke check terrain passe.
  - Le test téléphone réel passe.
  - La restauration sur machine vierge passe.
  - Le formateur signe la recette.
  - La documentation d’installation est relue.
  - Les secrets de démonstration sont absents.
  - Aucun push n’est effectué avant validation humaine.

  Le guide complet est disponible dans docs/field/INSTALLATION_AUTRE_MACHINE.md.
