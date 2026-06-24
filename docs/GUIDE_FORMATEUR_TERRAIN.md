# Guide Formateur Terrain

Ce guide aide le formateur à lancer l'application pendant une séance et à la partager aux élèves sur le même Wi-Fi ou le même partage de connexion.

L'application fonctionne sur le réseau local. Ne donnez jamais `localhost` aux élèves.

**Nouveau** : une [Fiche de démarrage terrain](FICHE_DEMARRAGE_TERRAIN.md) est disponible pour un pas à pas rapide et illustré.

### Page d'accueil — choix étudiant / formateur

La page d'accueil `/` propose deux entrées :
- **« Je suis étudiant »** → redirige vers l'espace modules `/modules/`
- **« Je suis formateur »** → redirige vers le cockpit `/dashboard/`

### Espace modules étudiant (`/modules/`)

Cette page liste les modules actifs avec :
- le statut (Réponses ouvertes / Consultation seulement / Indisponible)
- un bloc pédagogique contenant le contenu réel des présentations PowerPoint (résumé, objectifs, notions clés, méthode, activités, erreurs, à retenir)
- un bouton pour répondre ou consulter le questionnaire

Les blocs pédagogiques sont des templates partiels (fichiers `templates/surveys/module_X_pedagogy.html`) qui peuvent être mis à jour module par module. Les présentations PowerPoint restent la source de référence.

## Refonte UI/UX globale (F033)

L'interface a été entièrement refondue pour unifier l'expérience étudiant et formateur :

- **Design system local** (`static/css/app.css`) : variables CSS, badges, boutons, cartes, tableaux, breadcrumbs, assistant étapes, états vides, responsive et reduced-motion.
- **Layout unifié** (`templates/base.html`) : skip-link, blocs `extra_css`/`extra_js`, hero par page, navigation contextuelle.
- **Navigation** : la barre formateur affiche Accueil, Cockpit, Réseau, Contrôle LAN, Sauvegarde, Configuration, Admin avancé. L'espace étudiant n'affiche que Accueil et Modules.
- **Cockpit formateur** (`/dashboard/`) : statistiques globales, cartes Modules 2–8, présence live, réseau, exports, breadcrumbs.
- **Contrôle réseau local** (`/dashboard/network-control/`) : assistant LAN en 7 étapes, statut global, bouton « Configurer et rendre accessible ».
- **Sauvegarde / diagnostic** (`/dashboard/backup/`) : moteur de base actif, commande de backup, volumes Docker, commandes interdites documentées.
- **Accessibilité** : skip-link, labels ARIA, contrastes renforcés.
- **Pas de CDN** : tout le CSS/JS est local.

## Avant la séance

- [ ] Démarrez Docker Desktop.
- [ ] Vérifiez que l'ordinateur du formateur et les téléphones des élèves sont sur le même réseau.
- [ ] Préparez le fichier `.env` à partir de `.env.example`.
- [ ] Remplacez `SECRET_KEY=change-me-for-real-use` par une valeur propre à votre ordinateur.
- [ ] Vérifiez que `<LAPTOP_LAN_IP>` a bien été remplacé par l'adresse IPv4 réelle de l'ordinateur.

## Démarrer l'application

Dans PowerShell :

```powershell
docker compose up --build
```

Vérification rapide :

- ouvrez `http://127.0.0.1:8000/` (accueil élèves) sur l'ordinateur ;
- laissez la fenêtre ouverte pendant la séance.

## Créer le compte formateur

À faire au premier démarrage, ou si la base est nouvelle :

```powershell
docker compose exec web python manage.py createsuperuser
```

Ce compte sert pour l'admin et le dashboard.

## Préparer les données

```powershell
docker compose exec web python manage.py seed_module2
docker compose exec web python manage.py seed_module3
docker compose exec web python manage.py seed_module4
docker compose exec web python manage.py seed_module5
docker compose exec web python manage.py seed_module6
docker compose exec web python manage.py seed_module7
docker compose exec web python manage.py seed_module8
```

Résultat attendu :

- les modules `MODULE_2` à `MODULE_8` existent ;
- les sessions actives sont prêtes.

## Trouver l'adresse IP de l'ordinateur

Dans PowerShell :

```powershell
ipconfig
```

Cherchez l'`IPv4 Address` de la carte Wi-Fi ou du partage de connexion actif.

N'utilisez pas :

- une adresse WSL ;
- une adresse réseau Docker ;
- une interface déconnectée.

Exemple d'adresse à donner aux élèves :

`http://192.168.1.23:8000/` (accueil élèves)

Si l'accueil s'affiche, l'élève clique sur le module du jour pour accéder au questionnaire.

## Si les téléphones ne chargent pas la page

- vérifiez l'adresse IP de l'ordinateur ;
- vérifiez que Docker Desktop est bien lancé ;
- vérifiez le pare-feu Windows ;
- autorisez Docker Desktop ou le port `8000` si besoin ;
- vérifiez qu'il n'y a pas d'isolation client / AP isolation sur le Wi-Fi.

## Si le formulaire affiche “Le formulaire n'est pas disponible maintenant.”

Cela signifie qu'aucune session Module 2 active n'est disponible.

Essayez dans cet ordre :

1. si c'est la première préparation, lancez :

```powershell
docker compose exec web python manage.py seed_module2
```

2. si le message reste affiché, connectez-vous à l'admin Django ;
3. ouvrez la session Module 2 ;
4. vérifiez que `is_active` est bien coché pour la bonne session ;
5. enregistrez puis rechargez `http://127.0.0.1:8000/module-2/`.

Important :

- si une ancienne session Module 2 existe déjà mais n'est plus active, `seed_module2` ne la réactive pas automatiquement ;
- dans ce cas, l'activation se fait depuis l'admin.

## Test rapide avec un téléphone

1. Ouvrez `http://127.0.0.1:8000/` sur l'ordinateur — l'accueil élèves doit s'afficher.
2. Ouvrez l'URL IP sur un téléphone du même réseau.
3. Vérifiez que l'accueil et le formulaire Module 2 s'affichent.
4. Envoyez une réponse test si nécessaire.

## Utiliser le cockpit formateur

Adresse :

`http://<IP_PC>:8000/dashboard/`

Le cockpit centralise tous les outils formateur :

- liens vers chaque dashboard de module ;
- export CSV ;
- diagnostic réseau ;
- admin Django.

Connexion obligatoire.

### Navigation

La barre de navigation en haut de chaque page donne accès à :
- **Accueil** → `/`
- **Cockpit** → `/dashboard/` (formateur)
- **Réseau** → `/dashboard/network/` (formateur)
- **Contrôle LAN** → `/dashboard/network-control/` (formateur)
- **Sauvegarde** → `/dashboard/backup/` (formateur)
- **Configuration réseau** → `/dashboard/settings/` (formateur)
- **Admin avancé** → `/admin/` (formateur)

Les liens formateur n'apparaissent pas dans l'espace étudiant.

Le logo Internet Society / TAfHSSiM redirige vers le cockpit formateur.

### Sous-navigation du cockpit

Le cockpit `/dashboard/` est organisé en sections avec onglets :
- **Vue d'ensemble**, **Modules**, **Présence**, **Réseau**, **Exports**, **Admin**

Chaque section est accessible par un clic sur l'onglet correspondant.

### Adresse IP locale

Quand `TAF_LAN_HOST` est défini, l'IP réelle du laptop s'affiche dans une bannière verte du dashboard. Tous les liens réseau s'ouvrent dans un nouvel onglet (`target="_blank"`, `rel="noopener noreferrer"`). Si l'IP n'est pas configurée, un message d'alerte invite à la définir.

## Dashboard par module

Adresses :

- Module 2 : `http://<IP_PC>:8000/dashboard/module-2/`
- Module 3 : `http://<IP_PC>:8000/dashboard/module-3/`
- Module 4 : `http://<IP_PC>:8000/dashboard/module-4/`
- Module 5 : `http://<IP_PC>:8000/dashboard/module-5/`
- Module 6 : `http://<IP_PC>:8000/dashboard/module-6/`
- Module 7 : `http://<IP_PC>:8000/dashboard/module-7/`
- Module 8 : `http://<IP_PC>:8000/dashboard/module-8/`

Les dashboards permettent de :

- voir les réponses ;
- filtrer par classe ou groupe ;
- consulter le score moyen ;
- exporter le CSV.

Connexion obligatoire.

## Diagnostiquer l'accès réseau

Depuis le dashboard, un lien "Accès réseau" ouvre une page de diagnostic :

`http://<IP_PC>:8000/dashboard/network/`

Cette page affiche :

- l'adresse recommandée à donner aux élèves ;
- les adresses du dashboard, export CSV et admin ;
- les IP candidates détectées automatiquement ;
- des avertissements si l'accès depuis téléphone est problématique.

Optionnel : définir `TAF_LAN_HOST=<IP_DU_LAPTOP>` dans `.env` pour figer l'adresse recommandée.

## Configurer le réseau depuis l'interface (nouveau)

Une page de configuration sécurisée est disponible :

`http://<IP_PC>:8010/dashboard/settings/`

Cette page permet de modifier :
- le port d'écoute
- l'IP fixe du laptop
- les hôtes autorisés
- les origines CSRF
- le fuseau horaire

Les secrets ne sont jamais affichés. Un redémarrage Docker est nécessaire après modification.

## Présence temps réel des élèves (nouveau)

Le cockpit formateur `http://<IP_PC>:8010/dashboard/` affiche un compteur
en temps quasi réel du nombre d'élèves en train de remplir chaque module.

Mise à jour automatique toutes les 15 secondes.

## Exporter le CSV

Depuis le dashboard :

- cliquez sur `Exporter le CSV`

Ou utilisez directement :

`http://<IP_PC>:8000/dashboard/export/module-2.csv`

Connexion obligatoire.

## Sauvegarde et diagnostic

Une page dédiée `/dashboard/backup/` permet de :

- vérifier le moteur de base actif (PostgreSQL ou SQLite) ;
- voir la commande de sauvegarde recommandée ;
- lister les volumes Docker à préserver ;
- consulter les commandes interdites qui détruisent les données.

Script de sauvegarde automatique :

| Base | Emplacement Docker | Volume |
|------|-------------------|--------|
| PostgreSQL (recommandé) | service `db` | `taf_local_forms_pgdata` |
| SQLite (fallback) | `/app/data/db.sqlite3` | `taf_local_forms_data` |

### Script de sauvegarde automatique

```sh
bash scripts/dev/taf-db-backup
```

Ce script détecte automatiquement la base active (PostgreSQL ou SQLite) et
crée une sauvegarde horodatée dans `/tmp/taf-backups/`.

### Sauvegarde manuelle

1. arrêtez l'application si possible avec `docker compose down` (sans option de suppression de volume) ;
2. copiez la base SQLite ou le volume Docker ;
3. gardez une copie sur un support externe si nécessaire.

> **Commandes interdites** : ne jamais utiliser les options de suppression de volume avec `docker compose down` ou `docker system prune`, ni `flush` Django.

## Restauration

Procédure simple :

1. remettez la sauvegarde SQLite à la place de la base active ;
2. redémarrez l'application.

Pour une procédure détaillée de restauration Docker, une validation supplémentaire est recommandée avant documentation plus technique.

## Fin de séance

Avant d'arrêter :

- [ ] exportez le CSV si besoin ;
- [ ] faites une sauvegarde si la séance est terminée.

Pour arrêter l'application :

```powershell
docker compose down
```
