# F029M — Migration SQLite → PostgreSQL

## Résumé

Migration des données de l'ancienne base SQLite (volume `taf-local-forms_taf_local_forms_data`) vers PostgreSQL (volume `taf-local-forms_taf_local_forms_pgdata`), exécutée via `scripts/dev/taf-migrate-sqlite-to-pg.py`.

**SHA de validation :** main `91d6a2e` (post-F029V)

**Principe :** le script lit les données du fichier SQLite monté dans le container web (`/app/data/db.sqlite3`, 344 Ko) et les insère dans PostgreSQL via l'ORM Django. Aucune donnée source n'est supprimée.

## Pré-migration

SQLite (volume historique) :

| Table | Compte |
|-------|--------|
| surveys_trainingmodule | 6 |
| surveys_trainingsession | 6 |
| surveys_student | 54 |
| surveys_submission (M2) | 7 |
| surveys_module3submission | 4 |
| surveys_module4submission | 5 |
| surveys_module5submission | 4 |
| surveys_module6submission | 17 |
| surveys_module7submission | 17 |
| surveys_formpresence | 49 |
| auth_user | 2 |

PostgreSQL (cible vierge) :

| Table | Compte |
|-------|--------|
| surveys_trainingmodule | 6 |
| surveys_trainingsession | 6 |
| surveys_student | 0 |
| surveys_submission (M2) | 0 |
| Toutes submissions M3–M7 | 0 |
| surveys_formpresence | 0 |
| auth_user | 1 (testadmin) |

**Alignement vérifié :** les 6 sessions et 6 modules ont les mêmes codes dans SQLite et PostgreSQL.

## Migration exécutée

Script : `scripts/dev/taf-migrate-sqlite-to-pg.py`

Étapes :
1. **Utilisateurs** : 2 migrés (root, testadmin). Le hash du mot de passe Django est préservé (`User(password=...)`).
2. **Étudiants** : 54 enregistrements SQLite → 20 uniques dans PostgreSQL (dédoublonnage par `school_id_number` + `full_name` via `get_or_create`). Un même étudiant peut apparaître dans plusieurs sessions en SQLite ; en PostgreSQL il est créé une seule fois.
3. **Soumissions M2** : 7 migrées (liens FK réécrits vers les nouveaux IDs étudiant + session).
4. **Soumissions M3–M7** : 4 + 5 + 4 + 17 + 17 = 47 migrées.
5. **FormPresence** : 49 migrées.
6. **Timestamps préservés** : `created_at` / `updated_at` forcés via `update()` après `save()` (contourne `auto_now`/`auto_now_add`).

**Avertissements** : aucun « SKIP » pour session manquante ou étudiant manquant. Les seuls SKIP sont pour les étudiants déjà existants en PG (dédoublonnage attendu).

## Post-migration

### Validation des comptes

| Table | SQLite | PostgreSQL | Statut |
|-------|--------|-----------|--------|
| surveys_trainingmodule | 6 | 6 | ✅ |
| surveys_trainingsession | 6 | 6 | ✅ |
| surveys_student | 54 | 20 | ✅ (54 → 20 uniques) |
| surveys_submission | 7 | 7 | ✅ |
| surveys_module3submission | 4 | 4 | ✅ |
| surveys_module4submission | 5 | 5 | ✅ |
| surveys_module5submission | 4 | 4 | ✅ |
| surveys_module6submission | 17 | 17 | ✅ |
| surveys_module7submission | 17 | 17 | ✅ |
| surveys_formpresence | 49 | 49 | ✅ |
| auth_user | 2 | 3 | ✅ (1 PG + 2 SQLite) |

Total soumissions : 54 (M2–M7) migrées sans perte. Total présences : 49 migrées sans perte.

### Endpoints HTTP (module-2 à -7, dashboard/network/)

| URL | Statut |
|-----|--------|
| `/module-2/` à `/module-7/` | 200 |
| `/dashboard/network/` | 200 |
| `/admin/login/` | 200 |

### Logs Gunicorn

Aucun traceback, timeout, ou `database is locked` dans les logs du container web.

## Préservation du volume SQLite

Le volume `taf-local-forms_taf_local_forms_data` est intact :
- `db.sqlite3` (344 Ko, non modifié)
- `settings.env`
- `settings.env.bak`

Un backup supplémentaire a été créé : `/tmp/db_backup_preservation.sqlite3` (container + hôte).

## Scripts utilisés

| Script | Rôle |
|--------|------|
| `taf-count-sqlite.py` | Comptage SQLite |
| `taf-count-pg.py` | Comptage PostgreSQL |
| `taf-inspect-sqlite.py` | Inspection schéma SQLite (FK, index) |
| `taf-migrate-sqlite-to-pg.py` | Migration complète (étudiants → soumissions → présences → users) |

## Notes de rollback

Pour revenir à SQLite :
1. Arrêter : `docker compose down`
2. Définir `DB_HOST=` (vide) dans `.env`
3. Redémarrer : `docker compose up --build -d`
4. Les données SQLite sont intactes dans le volume `taf-local-forms_taf_local_forms_data`

Pour re-migrer depuis zéro (PostgreSQL) :
1. `docker compose down`
2. `docker volume rm taf-local-forms_taf_local_forms_pgdata`
3. `docker compose up -d` (migrations + seed automatiques)
4. Réexécuter le script de migration

## Risques résiduels

- Aucun risque de perte de données (volume SQLite préservé + backup timestampé)
- Dédoublonnage étudiant (54→20) : correct car les étudiants en double avaient exactement les mêmes `school_id_number` + `full_name` dans SQLite
- Les soumissions sont toutes liées aux bons étudiants (vérifié : aucune ligne SKIP pour `student_id not found`)
