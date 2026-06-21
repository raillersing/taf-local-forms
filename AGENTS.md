# TAf Local Forms — Agent Instructions

## Project purpose

This repository is a standalone local web application for the TAfHSSiM project.
TAfHSSiM = Technology Access for High School Students in Madagascar.

The application runs on a trainer's laptop during class. Students connected to
the same Wi-Fi or hotspot open the questionnaire through the laptop's local IP.

Example: `http://192.168.x.x:8010/module-2/`

## Operating model

Every task follows the same cycle:

1. **Inspect** — state, branch, log, existing files.
2. **Plan** — short execution plan (2–5 slices max).
3. **Branch** — work on `finalize/orchestrator-field-ready` or a dedicated feature branch.
4. **Slice** — implement the smallest coherent change.
5. **Validate** — run project quality gates after each slice.
6. **Review** — stop for human review on ambiguity, drift, security, migration, Docker failure.
7. **Commit** — single clear commit per slice.
8. **Push** — only after human approval.
9. **Tag** — only after field test.

## Scope boundaries

Allowed:
- files inside this repository only;
- Django backend (models, views, forms, tests, urls);
- Django templates, templatetags;
- local static assets (CSS, images);
- Docker and Docker Compose;
- tests;
- README, docs, agent workflow files.

Forbidden:
- modifying unrelated repositories;
- reading, creating, or committing `.env`, SQLite databases, logs, `__pycache__`, runtime files, or secrets;
- requiring Internet during classroom runtime;
- relying on CDN assets at runtime;
- adding unnecessary external services;
- exposing the app publicly without production-hardening warnings.

## Technical baseline

- Python 3.12+
- Django >=5.2,<5.3
- SQLite
- Django templates
- Local CSS (no build step)
- Docker + Docker Compose + Gunicorn
- WhiteNoise for static files
- Django built-in tests

## Python commands

Use `.venv-wsl/bin/python` in WSL. Fallback: `python3`. Never use the `.venv/` (Windows) path.

```sh
.venv-wsl/bin/python manage.py check
.venv-wsl/bin/python manage.py test surveys.tests
.venv-wsl/bin/python manage.py makemigrations --check --dry-run
```

## Quality gates

Every commit must pass all of the following:

```sh
git diff --check
.venv-wsl/bin/python manage.py check
.venv-wsl/bin/python manage.py test surveys.tests
.venv-wsl/bin/python manage.py makemigrations --check --dry-run
docker compose config
```

If Docker is running:

```sh
curl -I http://127.0.0.1:8010/module-2/
curl -I http://127.0.0.1:8010/dashboard/network/  # 200 after login
```

## Security and privacy rules

- Public student form for local classroom use only.
- Dashboard and admin require login.
- CSRF protection always enabled.
- Collect only required student data.
- `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` come from environment.
- Never hardcode production secrets.
- `.env`, `.env.*`, `*.sqlite3`, `*.log` must never be read or committed.
- CSV export sanitises cells starting with `=`, `+`, `-`, `@`.

## UX rules

- Student-facing text: simple, clear French for lycée students.
- Design: premium, readable, mobile-friendly, navy/white/light-blue palette.
- Logo: `static/brand/isoc_madagascar_logo.png`. Fallback text if absent.

## Agents

| Agent | Role |
|-------|------|
| **Orchestrator** | Plan, delegate, validate, stop on hard conditions. Always starts. |
| **Django Implementation Agent** | Write/refactor Django backend, templates, tests. |
| **Field Operations Doc Agent** | Update README, guide formateur, network/field deployment docs. |
| **UI/UX Review Agent** | Review layout, responsiveness, French text clarity. Read-only. |
| **Security/Privacy Review Agent** | Audit auth, secret handling, CSV safety. Read-only. |
| **Release Manager Agent** | Run release checklist, prepare notes, tag. |

## Skills (`.agents/skills/`)

- `taf-local-django-app` — building/reviewing/testing the Django app.
- `taf-field-ops` — classroom field operations, network access, WSL/Docker caveats.
- `taf-ui-ux-review` — UI quality, responsiveness, French readability for lycée.
- `taf-security-privacy-review` — auth, secret safety, CSV injection, data minimisation.

## Task queue

| ID | Description | Status |
|----|-------------|--------|
| F001 | MVP implementation | done |
| F002 | Codex orchestrator bootstrap | done |
| F003 | v0.1.0 release | done |
| F004 | Field polish, guide formateur | done |
| F005 | UX corrections (logo, alignment, network dashboard) | done |
| F006 | Agent workflow and skills framework | done |
| F007 | Release candidate review | pending |
| F008 | Push / PR / merge workflow | pending |
| F009 | Tag v0.1.1 | pending |
| F010 | Logo integration (official file) | pending |
| F011 | Dashboard UX polish after field feedback | pending |
| F012 | Module 3 preparation | pending |

## Prompt contracts

Full contracts in `docs/ai-agents/prompt-contracts.md`.

### Audit task

> Inspect {component} for {concern}. Report findings with severity. Do not modify files.

### Implementation task

> Implement {slice}. Follow AGENTS.md. Validate with project quality gates. Commit only when passing.

### Review task

> Review {change} against {checklist}. Read-only. Verdict: APPROVE / REQUEST_CHANGES / BLOCK.

### Release task

> Run release checklist from docs/ai-agents/release-checklist.md. Prepare notes. Tag.

### Emergency / debug task

> Reproduce {issue}. Isolate root cause. Propose fix without committing. Stop for human approval.

## Release checklist

- [ ] `manage.py check` passes
- [ ] `manage.py test surveys.tests` passes
- [ ] `manage.py makemigrations --check --dry-run` clean
- [ ] No `.env`, secrets, or runtime files in diff
- [ ] `docker compose config` valid
- [ ] `curl -I http://127.0.0.1:8010/module-2/` returns 200
- [ ] `/dashboard/network/` accessible after login
- [ ] Phone test documented in release notes
- [ ] Release notes written

## Hard stops

Stop and ask for human review when any of the following occurs:
- ambiguity that changes data model or classroom workflow;
- security or privacy risk;
- Docker failure;
- unexpected migration;
- scope drift outside approved files;
- action outside this repository;
- `.env` or secret detected in read or diff.

## References

- `docs/ai-agents/README.md` — agent documentation index
- `docs/ai-agents/workflow.md` — detailed workflow
- `docs/ai-agents/task-queue.md` — task queue management
- `docs/ai-agents/prompt-contracts.md` — reusable prompt templates
- `docs/ai-agents/release-checklist.md` — release procedure
