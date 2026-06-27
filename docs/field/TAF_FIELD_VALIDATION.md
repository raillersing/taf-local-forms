# Validation terrain TAf Local Forms

Cette note décrit une validation terrain courte, non destructive, pour confirmer
que le runtime Docker reste stable après F040M.

Le but n'est pas de créer des données de démonstration ni de modifier la base.
On vérifie uniquement :

- la configuration Docker ;
- l'exposition locale `8010` et, si présent, le relais LAN `8011` ;
- les routes publiques ;
- les redirections des routes protégées ;
- les pages formateur après connexion ;
- la médiathèque publique ;
- le flux vidéo MP4 local ;
- la projection et son bloc QR.

## Périmètre et règles de sécurité

- Lecture seule uniquement.
- Aucune migration.
- Aucune modification de modèle.
- Aucun backup, dump, média runtime, log sensible ou `graphify-out/` ne doit
  être committé.
- Ne jamais utiliser `docker compose down -v` ni un prune destructif.
- Ne pas supposer qu'un support publié ou une vidéo publiée existe déjà.

## Pré-requis

- Docker Desktop démarré.
- Stack locale disponible via `docker compose up -d`.
- Variables projet déjà configurées via `.env` ou l'interface réseau.
- Facultatif mais recommandé pour les routes protégées :
  un compte formateur déjà existant.

## Script principal

Le script dédié est :

```bash
scripts/dev/taf-field-smoke-check
```

Exemple minimal :

```bash
scripts/dev/taf-field-smoke-check
```

Exemple avec validation formateur et médiathèque existante :

```bash
TAF_SMOKE_USERNAME=formateur \
TAF_SMOKE_PASSWORD='mot-de-passe-existant' \
TAF_SMOKE_SUPPORT_SLUG=fiche-module-2 \
TAF_SMOKE_VIDEO_SLUG=video-module-2 \
scripts/dev/taf-field-smoke-check
```

Exemple avec URL LAN explicite :

```bash
TAF_SMOKE_LAN_URL=http://192.168.1.42:8011 \
scripts/dev/taf-field-smoke-check
```

## Ce que vérifie le script

### Toujours vérifié

- `docker compose config`
- page d'accueil publique `/`
- catalogue modules `/modules/`
- catalogue supports `/supports/`
- login admin `/admin/login/`
- formulaire public `/module-2/`
- protections dashboard :
  - `/dashboard/`
  - `/dashboard/network/`
  - `/dashboard/projection/`
  - `/dashboard/supports/`
  - `/dashboard/supports/upload/`

### Vérifié si identifiants fournis

- accès 200 au cockpit formateur ;
- page réseau en 200 ;
- page projection en 200 ;
- page supports dashboard en 200 ;
- page upload support en 200 ;
- présence du bloc QR/projection dans la page projection.

### Vérifié si des slugs existants sont fournis

- détail public d'un support publié ;
- téléchargement public d'un support publié ;
- lecture `/watch/` d'une vidéo publiée ;
- téléchargement MP4 de cette vidéo ;
- présence du lecteur HTML5 `<video>`.

## Codes attendus

- `200` : route disponible et lisible.
- `302` : route protégée qui redirige vers `/admin/login/` sans session.
- `503` sur `/module-2/` : acceptable si aucune session active n'est ouverte.
- `000` sur l'URL LAN : acceptable si le relais Windows `8011` n'est pas en
  place depuis WSL ; cela demande alors une vérification réseau séparée.

## Validation manuelle terrain recommandée

Après le script, confirmer manuellement :

1. Ouvrir `/dashboard/network/` avec un compte formateur.
2. Vérifier que l'URL élève recommandée pointe vers l'IP LAN du laptop.
3. Ouvrir `/dashboard/projection/` et confirmer l'affichage plein écran.
4. Scanner le QR avec un téléphone sur le même Wi-Fi/hotspot.
5. Ouvrir un support publié.
6. Tester un téléchargement document.
7. Tester la lecture d'une vidéo MP4 locale sur téléphone si un fichier publié
   existe.

## Commandes projet à garder dans la checklist

En plus du smoke terrain, conserver les validations projet :

```bash
scripts/dev/taf-skills-status
scripts/dev/taf-graphify-status
scripts/dev/taf-ponytail-check
.venv-wsl/bin/python manage.py check
.venv-wsl/bin/python manage.py makemigrations --check --dry-run
.venv-wsl/bin/python manage.py test surveys.tests
docker compose config
.venv-wsl/bin/python manage.py collectstatic --dry-run --no-input
```

## Limites connues

- Le script ne crée aucun compte formateur.
- Le script ne publie aucun support.
- Le script ne pousse aucun média de test.
- Le script ne remplace pas un test réel depuis un téléphone élève.

## Dépannage rapide

Si le script trouve des `404` sur des routes déjà présentes dans le code courant,
par exemple `/supports/`, `/dashboard/projection/` ou `/dashboard/supports/`,
le premier suspect est un conteneur web démarré sur une image trop ancienne.

Recharger alors le runtime sans commande destructive :

```bash
docker compose up -d --build
```

Puis relancer :

```bash
scripts/dev/taf-field-smoke-check
```
