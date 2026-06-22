# TAf Local Forms — Manuel terrain du formateur

## Présentation

L'application **TAf Local Forms** s'exécute sur le laptop du formateur pendant la séance.
Les élèves, connectés **au même Wi-Fi ou hotspot**, ouvrent le questionnaire avec l'adresse IP locale du laptop.

L'application ne nécessite **pas Internet** pendant la séance. Tout fonctionne en local.

Le formateur peut consulter les réponses en direct dans un **panel formateur** (dashboard) protégé par mot de passe.

---

## Interface utilisateur

### Page d'accueil — choix étudiant / formateur

La page d'accueil `/` affiche deux entrées :

- **« Je suis étudiant »** → redirige vers l'espace modules `/modules/`
- **« Je suis formateur »** → redirige vers le cockpit `/dashboard/`

### Espace modules étudiant (`/modules/`)

Les élèves arrivent sur cette page après avoir cliqué sur « Je suis étudiant ».
Chaque module actif est présenté avec :

- son **titre** et un **statut** (Réponses ouvertes / Consultation seulement / Indisponible)
- un **bloc pédagogique** décrivant les objectifs et le contenu de la formation
- un bouton **« Répondre au questionnaire »** (ou « Consulter le questionnaire »)

### Adresses principales
| Module 3 – Recherche efficace | `http://127.0.0.1:8010/module-3/` |
| Module 4 – Sources fiables | `http://127.0.0.1:8010/module-4/` |
| Panel formateur | `http://127.0.0.1:8010/dashboard/` |
| Accès réseau | `http://127.0.0.1:8010/dashboard/network/` |
| Configuration réseau (interface) | `http://127.0.0.1:8010/dashboard/settings/` |
| Admin Django | `http://127.0.0.1:8010/admin/` |

> **Important :** `127.0.0.1` fonctionne uniquement sur l'ordinateur du formateur.
> Les élèves ne peuvent pas utiliser cette adresse.

---

## Adresse pour les élèves

Les élèves utilisent l'**adresse IP locale du laptop** :

```
http://192.168.X.X:8010/
```

### Trouver l'IP du laptop

Dans **PowerShell**, lancez :

```powershell
ipconfig
```

Repérez l'**adresse IPv4** de votre carte Wi-Fi ou du partage de connexion.  
Exemple : `192.168.0.102`.

Ne donnez pas aux élèves :
- `127.0.0.1` — cela ne fonctionne que sur votre machine
- `localhost` — idem
- une adresse WSL ou Docker — elle n'est pas accessible depuis les téléphones

---

## Préparation avant séance

1. [ ] Ouvrez **Docker Desktop** (attendez qu'il soit prêt).
2. [ ] Ouvrez **WSL Ubuntu** (terminal Linux).
3. [ ] Allez dans le dossier du projet :

```bash
cd "$HOME/projects/taf-local-forms"
```

4. [ ] Vérifiez que vous êtes sur `main` et à jour :

```bash
git checkout main
git pull --ff-only origin main
git status --short
```

Le statut doit être vide.

---

## Configuration réseau (fichier `.env`)

Le fichier `.env` contient les réglages réseau. Créez-le à partir de l'exemple :

```bash
cp .env.example .env
```

Modifiez-le avec vos valeurs réelles. Exemple générique :

```env
TAF_HOST_PORT=8010
TAF_LAN_HOST=192.168.0.102
ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.0.102
CSRF_TRUSTED_ORIGINS=http://localhost:8010,http://127.0.0.1:8010,http://192.168.0.102:8010
```

Remplacez `192.168.0.102` par **votre véritable IP** (voir `ipconfig` ci-dessus).

> **Ne modifiez pas** `SECRET_KEY` si vous n'avez pas de valeur de remplacement — mais changez-la avant une vraie séance.

---

## Démarrage de l'application

Dans le dossier du projet, lancez :

```bash
docker compose up --build -d
```

Vérifiez que tout tourne :

```bash
docker compose ps
```

Vous devriez voir le service `web` avec l'état `Up`.

---

## Initialisation des modules

Chargez les données de chaque module. Cette opération est **idempotente** (on peut la répéter sans risque).

```bash
docker compose exec web python manage.py seed_module2
docker compose exec web python manage.py seed_module3
docker compose exec web python manage.py seed_module4
```

Chaque commande :
- crée le module s'il n'existe pas
- crée ou réutilise une session active
- n'écrase pas les réponses existantes

---

## Création du compte formateur

Au premier démarrage (ou si la base est neuve), créez un compte admin :

```bash
docker compose exec web python manage.py createsuperuser
```

Répondez :
- **Username** : par exemple `formateur`
- **Email** : laissez vide (appuyez sur Entrée)
- **Password** : choisissez un mot de passe simple pour la séance

Ce compte protège le panel formateur et l'admin Django.

---

## Vérification des pages

Testez que tout est accessible depuis le laptop :

```bash
curl -I http://127.0.0.1:8010/
curl -I http://127.0.0.1:8010/module-2/
curl -I http://127.0.0.1:8010/module-3/
curl -I http://127.0.0.1:8010/module-4/
```

Résultat attendu : **`200 OK`** pour chaque page.

Pour les dashboards (connexion obligatoire) :

```bash
curl -I http://127.0.0.1:8010/dashboard/
curl -I http://127.0.0.1:8010/dashboard/module-2/
curl -I http://127.0.0.1:8010/dashboard/module-3/
curl -I http://127.0.0.1:8010/dashboard/module-4/
```

Résultat attendu (sans connexion) : **`302 Found`** (redirection vers la page de connexion).

---

## Utilisation en classe

### Côté formateur

1. L'application tourne (voir « Démarrage »).
2. Ouvrez `http://127.0.0.1:8010/dashboard/network/` pour vérifier l'adresse à donner.
3. Donnez l'IP aux élèves (exemple : `http://192.168.0.102:8010/`).
4. Suivez les réponses dans le dashboard de chaque module.

### Côté élève

1. Connecté au même Wi-Fi / hotspot que le formateur.
2. Ouvre son navigateur.
3. Tape l'adresse donnée par le formateur (ex. `http://192.168.0.102:8010/`).
4. Sur la page d'accueil, clique sur **« Je suis étudiant »**.
5. Dans l'espace modules (`/modules/`), lit la présentation du module et clique sur **« Répondre au questionnaire »**.
6. Remplit le questionnaire et valide.
7. Voit une page de confirmation.

### Rappels

- Tous les appareils doivent être **sur le même réseau**.
- **Pas besoin d'Internet** : l'application tourne en local.
- Un élève ne peut soumettre qu'**une seule réponse** par module (anti-doublon).

---

## Dashboards et exports

### Dashboard Module 2

URL : `http://<IP_LAPTOP>:8010/dashboard/module-2/`

Affiche :
- nombre de réponses
- score moyen
- filtre par classe / groupe
- tableau des réponses
- export CSV

### Dashboard Module 3

URL : `http://<IP_LAPTOP>:8010/dashboard/module-3/`

Idem Module 2, adapté au contenu Module 3.

### Dashboard Module 4

URL : `http://<IP_LAPTOP>:8010/dashboard/module-4/`

Affiche en plus un résumé des décisions (fiable / douteuse / pas encore).

### Exports CSV

| Module | URL directe |
|--------|-------------|
| Module 2 | `/dashboard/export/module-2.csv` |
| Module 3 | `/dashboard/export/module-3.csv` |
| Module 4 | `/dashboard/export/module-4.csv` |

> **Conseil** : après la séance, exportez les CSV et sauvegardez-les dans un dossier sécurisé.
> Les données de la base SQLite sont dans un volume Docker.

---

## Configuration réseau depuis l'interface

Depuis le cockpit formateur, vous pouvez modifier certains paramètres réseau
sans éditer le fichier `.env` à la main.

**Page** : `/dashboard/settings/`

Champs modifiables :
- `TAF_HOST_PORT` — port d'écoute (1024-65535)
- `TAF_LAN_HOST` — IP fixe du laptop (ou laisser vide)
- `ALLOWED_HOSTS` — hôtes autorisés
- `CSRF_TRUSTED_ORIGINS` — origines CSRF autorisées
- `TIME_ZONE` — fuseau horaire

> **Important** : les secrets (SECRET_KEY, mots de passe) ne sont jamais affichés
> ni modifiables. Un redémarrage de l'application est nécessaire pour appliquer
> les changements réseau.

---

## Compteur temps réel des élèves en cours de saisie

Le cockpit formateur affiche en temps quasi réel le nombre d'élèves en train
de remplir chaque module (Module 2, 3, 4).

Fonctionnement :
- un petit script sur la page de chaque module envoie un signal toutes les 15 secondes
- le dashboard interroge les présences toutes les 8 secondes
- un élève qui ferme brutalement le navigateur disparaît après environ 60 secondes

> **Limite** : le compteur est indicatif. Si un élève ferme l'onglet sans prévenir,
> sa présence reste active jusqu'à 60 secondes maximum.

---

## Navigation dans l'interface

### Barre de navigation

La barre en haut de chaque page donne accès à :
- **Modules de formation** → accueil public des élèves
- **Espace formateur** → tableau de bord cockpit
- **Accès réseau** → diagnostic et adresses (visible uniquement pages formateur)
- **Configuration réseau** → paramètres IP (visible uniquement pages formateur)
- **Admin avancé** → administration Django (visible uniquement pages formateur)

Le logo Internet Society / TAfHSSiM (en haut à gauche) redirige vers le **cockpit formateur**.

### Sous-navigation du tableau de bord

Le cockpit formateur `/dashboard/` est organisé en sections avec onglets :
- **Vue d'ensemble** — statistiques globales
- **Modules** — cartes Module 2/3/4 avec statut et switch d'ouverture/fermeture des réponses
- **Présence** — compteur en direct des élèves en cours de saisie
- **Réseau** — adresses IP et liens vers chaque page (s'ouvrent dans un nouvel onglet)
- **Exports** — téléchargement CSV des résultats
- **Admin** — outils avancés et documentation

### Adresse IP locale dans le dashboard

Quand `TAF_LAN_HOST` est configuré dans `.env`, le dashboard affiche l'IP locale réelle du laptop dans une bannière verte. Tous les liens réseau utilisent cette IP et s'ouvrent dans un nouvel onglet (`target="_blank"`, `rel="noopener noreferrer"`).

Si l'IP n'est pas configurée, un message d'alerte invite à la définir dans `/dashboard/settings/`.

---

## Arrêt de l'application

**Commande sûre** (conserve les données) :

```bash
docker compose down
```

Si vous voulez aussi supprimer les conteneurs orphelins (le plus souvent inutile mais sans risque) :

```bash
docker compose down --remove-orphans
```

---

## Nettoyage après cycles agents

Deux scripts utiles dans `scripts/dev/` :

| Script | Action |
|--------|--------|
| `taf-clean-status` | Affiche l'état du projet (lecture seule) |
| `taf-clean-after-merge` | Nettoie après fusion de PR : supprime branches mergées, arrête conteneurs, nettoie les worktrees |

Ces scripts ne suppriment **pas** les volumes de données Docker.

---

## Commandes interdites

| Commande | Pourquoi c'est interdit |
|----------|------------------------|
| `docker compose down -v` | **Supprime la base SQLite** avec toutes les réponses des élèves |
| `docker system prune --volumes` | **Supprime tous les volumes Docker** de tous les projets |
| `git branch -D` (force delete) | Peut perdre du travail non mergé |

> Utilisez `docker compose down` (sans `-v`) pour arrêter l'application en toute sécurité.

---

## Mise à jour de l'application

Quand une nouvelle version est disponible :

```bash
git checkout main
git pull --ff-only origin main
docker compose up --build -d
```

Redémarrez les seeds si de nouveaux modules ont été ajoutés (cf. « Initialisation des modules »).

---

## Problèmes fréquents

| Problème | Solution |
|----------|----------|
| Le téléphone ne voit pas la page | Vérifiez l'IP, le Wi-Fi, le pare-feu ; lancez le diagnostic : `bash scripts/dev/taf-lan-diagnose` (WSL) ou `.\scripts\windows\taf-lan-show-status.ps1` (Windows) |
| Mauvaise IP | Relancez `ipconfig`, utilisez l'IPv4 de la carte active |
| Pare-feu Windows bloque | Exécutez (Admin) `.\scripts\windows\taf-lan-open-port.ps1` ou autorisez le port `8010` manuellement |
| VPN actif | Déconnectez le VPN |
| Pas le même Wi-Fi | Formateur et élèves doivent être sur le même réseau |
| Module absent (« non disponible ») | Relancez `seed_moduleX` |
| Dashboard demande connexion | Normal — connectez-vous avec le compte formateur |
| `curl` échoue juste après démarrage | Attendez 5 secondes, le temps que Gunicorn soit prêt |
| Erreur CSRF ou Host | Vérifiez `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` dans `.env` |
| Problème persistant | Consultez `docs/network/WINDOWS_WSL_LAN_TROUBLESHOOTING.md` |

---

## Checklist rapide avant séance

- [ ] Docker Desktop est ouvert
- [ ] WSL Ubuntu est ouvert
- [ ] `docker compose up --build -d` a été lancé
- [ ] `docker compose ps` montre `Up`
- [ ] Les seeds ont été lancés (Modules 2, 3, 4)
- [ ] Le compte formateur est créé
- [ ] L'IP réseau a été vérifiée (`ipconfig`)
- [ ] Un téléphone sur le même réseau ouvre la page d'accueil
- [ ] Les dashboards sont accessibles (après connexion)
- [ ] Les exports CSV sont testés

---

## Résumé ultra-court

1. **Démarrer** → `docker compose up --build -d`
2. **Seeder** → `seed_module2`, `seed_module3`, `seed_module4`
3. **Compte** → `createsuperuser`
4. **Vérifier** → `curl` les pages (dont `/` et `/modules/`)
5. **Ouvrir** → `/dashboard/network/` pour l'IP
6. **Donner l'IP** → aux élèves (ils arrivent sur la page d'accueil avec le choix étudiant / formateur)
7. **Suivre** → les réponses dans le dashboard
8. **Exporter** → les CSV après la séance
9. **Arrêter** → `docker compose down`

---

> Document maintenu par l'équipe TAfHSSiM — Dernière mise à jour : juin 2026
