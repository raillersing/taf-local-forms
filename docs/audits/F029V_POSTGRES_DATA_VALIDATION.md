# F029V — Validation PostgreSQL et préservation des données

## Résumé

Validation post-merge de F029 (PostgreSQL + 100-user LAN hardening) sur main `a308d33`.

## Base de données active

| Propriété | Valeur |
|-----------|--------|
| Moteur | `django.db.backends.postgresql` |
| Nom DB | `taf_local_forms` |
| Hôte | `db` (container PostgreSQL 16 Alpine) |
| Port | 5432 |

## Préservation des données

### Volumes Docker

| Volume | Contenu | Statut |
|--------|---------|--------|
| `taf-local-forms_taf_local_forms_data` | Ancienne base SQLite (344 Ko) + settings | ✅ Préservé |
| `taf-local-forms_taf_local_forms_pgdata` | Nouvelle base PostgreSQL (vierge) | ✅ Créé |

L'ancien volume SQLite est intact : `db.sqlite3` (344 Ko, contient les données des séances précédentes), `settings.env`, `settings.env.bak`. Aucune donnée perdue.

### Comptages après seed (PostgreSQL)

| Modèle | Compte |
|--------|--------|
| TrainingModule | 6 |
| TrainingSession | 6 |
| Student | 0 |
| Submission (Module 2) | 0 |
| Module3Submission | 0 |
| Module4Submission | 0 |
| Module5Submission | 0 |
| Module6Submission | 0 |
| Module7Submission | 0 |
| FormPresence | 0 |
| auth.User | 1 (testadmin) |

### Idempotence des seeds

Tous les seeds (Module 2 à 7) sont idempotents : la seconde exécution affiche « conserve » au lieu de « cree », et les comptages restent stables.

## Migrations

- Migration `0011` appliquée avec succès (suppression index `last_seen_at`, ajout index composites `(status, last_seen_at)` et `(client_id, module_code, training_session)`)
- `makemigrations --check --dry-run` : aucune migration en attente

## Tests runtime

### Endpoints HTTP (tous 200 OK)

| URL | Statut |
|-----|--------|
| `/` | 200 |
| `/modules/` | 200 |
| `/modules/module-2/` à `/modules/module-7/` | 200 |
| `/module-2/` à `/module-7/` | 200 |
| `/dashboard/` | 200 (page login) |

### Test de charge (load-smoke)

```
Concurrency: 5
Requetes totales : 75
Succes           : 75 (100%)
Taux de succes   : 100.00%
Duree totale     : 1474ms
Latence min      : 24ms
Latence moyenne  : 70ms
Latence max      : 181ms
Requetes/seconde : 50.8
```

Aucune erreur dans les logs Gunicorn (pas de traceback, timeout, connection reset, ou database is locked).

## Configuration Gunicorn

| Variable | Valeur effective |
|----------|-----------------|
| `WEB_CONCURRENCY` | 2 |
| `WEB_THREADS` | 4 |
| `GUNICORN_TIMEOUT` | 60 |

## Scripts LAN

Les 3 scripts Windows LAN existent et sont inchangés :
- `taf-lan-sync.ps1` ✅
- `taf-lan-show-status.ps1` ✅
- `taf-lan-install-auto-sync.ps1` ✅

Documentation des ports : formateur `localhost:8010`, élèves `<IP_WIFI>:8011`.

## Notes de rollback

Pour revenir à SQLite :
1. Arrêter : `docker compose down`
2. Définir `DB_HOST=` (vide) dans `.env`
3. Redémarrer : `docker compose up --build -d`
4. Les données SQLite sont dans le volume `taf-local-forms_taf_local_forms_data` (inchangé)

## Risques résiduels

- Aucun risque de perte de données identifié
- Le volume SQLite historique est préservé et peut être réactivé à tout moment
- La bascule PostgreSQL→SQLite est transparente (via `DB_HOST`)
- `psycopg[binary]` 3.2+ ajouté dans requirements.txt (installé dans l'image Docker)

## Qualité

| Gate | Statut |
|------|--------|
| `git diff --check` | ✅ Aucune erreur |
| `manage.py check` | ✅ 0 issues |
| `manage.py test surveys.tests` | ✅ 397/397 pass |
| `makemigrations --check --dry-run` | ✅ Aucune migration en attente |
| `docker compose config` | ✅ Valide |
| `taf-clean-status` | ✅ Propre |
