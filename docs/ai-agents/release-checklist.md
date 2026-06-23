# Release Checklist — TAf Local Forms

Run this checklist before every release. If any step fails, stop and fix before tagging.

## Pre-release

- [ ] Branch is `main` or the approved release branch
- [ ] Working directory is clean (`git status --short` is empty)
- [ ] All intended commits are present (`git log --oneline --max-count=10`)
- [ ] Field user manual (`docs/FICHE_DEMARRAGE_TERRAIN.md`) is up to date

## Validation gates

- [ ] `git diff --check` — no whitespace errors
- [ ] `.venv-wsl/bin/python manage.py check` — system check OK
- [ ] `.venv-wsl/bin/python manage.py test surveys.tests` — all tests pass
- [ ] `.venv-wsl/bin/python manage.py makemigrations --check --dry-run` — no pending migrations
- [ ] `docker compose config` — valid compose file
- [ ] No `.env`, `*.sqlite3`, `*.log`, `__pycache__`, or secrets in the diff

## Runtime checks (if Docker is running)

- [ ] `curl -I http://127.0.0.1:8010/module-2/` — returns 200
- [ ] `curl -I http://127.0.0.1:8010/module-5/` — returns 200
- [ ] `curl -I http://127.0.0.1:8010/module-6/` — returns 200
- [ ] `curl -I http://127.0.0.1:8010/module-7/` — returns 200
- [ ] `/dashboard/module-5/` — renders for authenticated user
- [ ] `/dashboard/module-6/` — renders for authenticated user
- [ ] `/dashboard/module-7/` — renders for authenticated user
- [ ] `/dashboard/export/module-5.csv` — downloads CSV for authenticated user
- [ ] `/dashboard/export/module-6.csv` — downloads CSV for authenticated user
- [ ] `/dashboard/export/module-7.csv` — downloads CSV for authenticated user
- [ ] `/dashboard/network/` — accessible after login
- [ ] `/dashboard/module-2/` — renders for authenticated user
- [ ] `/dashboard/export/module-2.csv` — downloads CSV for authenticated user
- [ ] `/dashboard/settings/` — renders for staff user, not for anonymous
- [ ] `/dashboard/presence.json` — returns JSON for authenticated user
- [ ] Presence heartbeat — `POST /presence/heartbeat/` returns `{"ok": true}`
- [ ] PostgreSQL service `db` is healthy (`docker compose ps`)
- [ ] Gunicorn workers/threads/timeout configured (`WEB_CONCURRENCY`, `WEB_THREADS`, `GUNICORN_TIMEOUT`)
- [ ] Backup script — `bash scripts/dev/taf-db-backup` runs without error
- [ ] Load smoke script — `bash scripts/dev/taf-load-smoke` runs without error (dry-run with 1 req)

## PostgreSQL health

- [ ] `docker compose exec db pg_isready -U taf_user` — returns `accepting connections`
- [ ] `docker compose exec web python manage.py dbshell` — connects to PostgreSQL
- [ ] PostgreSQL healthcheck passes (`docker inspect --format='{{json .State.Health}}' $(docker compose ps -q db)`)
- [ ] Fallback SQLite works when `DB_HOST` is unset

## Release preparation

- [ ] Release version determined (follow semver)
- [ ] Release notes written in French
- [ ] Phone test documented in notes
- [ ] Known limitations listed

## After release

- [ ] Git tag created
- [ ] Tag pushed to remote
- [ ] Release published on GitHub (if applicable)
- [ ] Run `scripts/dev/taf-clean-after-merge` to clean up merged branches and stop containers
