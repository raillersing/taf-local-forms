# Release Checklist — TAf Local Forms

Run this checklist before every release. If any step fails, stop and fix before tagging.

## Pre-release

- [ ] Branch is `main` or the approved release branch
- [ ] Working directory is clean (`git status --short` is empty)
- [ ] All intended commits are present (`git log --oneline --max-count=10`)

## Validation gates

- [ ] `git diff --check` — no whitespace errors
- [ ] `.venv-wsl/bin/python manage.py check` — system check OK
- [ ] `.venv-wsl/bin/python manage.py test surveys.tests` — all tests pass
- [ ] `.venv-wsl/bin/python manage.py makemigrations --check --dry-run` — no pending migrations
- [ ] `docker compose config` — valid compose file
- [ ] No `.env`, `*.sqlite3`, `*.log`, `__pycache__`, or secrets in the diff

## Runtime checks (if Docker is running)

- [ ] `curl -I http://127.0.0.1:8010/module-2/` — returns 200
- [ ] `/dashboard/network/` — accessible after login
- [ ] `/dashboard/module-2/` — renders for authenticated user
- [ ] `/dashboard/export/module-2.csv` — downloads CSV for authenticated user

## Release preparation

- [ ] Release version determined (follow semver)
- [ ] Release notes written in French
- [ ] Phone test documented in notes
- [ ] Known limitations listed

## After release

- [ ] Git tag created
- [ ] Tag pushed to remote
- [ ] Release published on GitHub (if applicable)
