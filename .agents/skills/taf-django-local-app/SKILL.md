---
name: taf-django-local-app
description: Use this skill when a task touches Django views, URLs, templates, forms, tests, or local frontend behavior in TAf Local Forms.
---

# TAf Django Local App

## When to use

Use for Django implementation, review, or refactor work inside the local app.

## Inputs to read

- `AGENTS.md`
- `README.md`
- relevant files in `surveys/`, `templates/`, and `static/`

## Rules

- Prefer Django server-side rendering.
- Keep CSS local and JavaScript minimal and local.
- No CDN during classroom runtime.
- Preserve existing routes unless the task explicitly changes routing.
- Keep auth protection on dashboard, export, and network pages.
- Do not add React, Vue, or SPA architecture without explicit approval.

## Safe workflow

1. Inspect the existing route, view, form, template, and tests.
2. Reuse existing patterns before creating new abstractions.
3. Keep student and trainer contexts separate.
4. Validate with `manage.py check`, relevant tests, and migration dry-run.

## Stop conditions

- unexpected migration
- auth guard regression risk
- duplicate-submission rule becomes unclear
- runtime dependency or CDN would be introduced

## Acceptance checklist

- Existing routes remain coherent.
- Local-only frontend constraint is respected.
- Dashboard/export/network auth is preserved.
- `manage.py check` passes.
- `surveys.tests` runs when behavior changes.
- Migration dry-run stays clean.
