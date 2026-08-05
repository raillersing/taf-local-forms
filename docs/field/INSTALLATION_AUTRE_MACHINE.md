# Installer TAf Local Forms sur une autre machine

## Statut de ce guide

Ce guide décrit l'installation **manuelle actuelle**. Docker rend l'application
principale transférable, mais l'automatisation LAN Windows n'est pas encore
portable : certains scripts supposent la distribution WSL `Ubuntu` et le chemin
`/home/raillersing/projects/taf-local-forms`. Corriger ce point est obligatoire
avant une installation commerciale en libre-service.

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

### Limite actuelle

Avant correction des scripts, rechercher dans les fichiers Windows les valeurs
`Ubuntu` et `/home/raillersing/projects/taf-local-forms`. Si la distribution ou
le chemin cible diffère, le helper ne doit pas être déclaré opérationnel sans
adaptation et test. Ne pas contourner ce problème par une exposition Internet.

Après portabilisation, ouvrir PowerShell en administrateur à la racine du dépôt :

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

La procédure de restauration Compose n'est pas encore suffisamment automatisée
pour être considérée self-service. Elle doit être exécutée par un mainteneur
jusqu'à clôture de la tranche sauvegarde de la feuille de route.

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
