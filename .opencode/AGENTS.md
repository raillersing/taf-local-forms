# TAf Local Forms — OpenCode Agent Instructions

This file configures OpenCode for the TAf Local Forms repository.

## Source of truth

The authoritative agent instructions are in `/AGENTS.md` at the repository root.
Read that file first. This file provides OpenCode-specific overrides only.

## Skills

OpenCode skills are available at `.agents/skills/`. Load the relevant skill
when the task matches its description:

- `taf-local-django-app` — Django backend, templates, tests
- `taf-field-ops` — field deployment, network, trainer docs
- `taf-ui-ux-review` — UI quality and French readability review
- `taf-security-privacy-review` — auth, secrets, CSV safety audit

## Workflow

Every task follows the cycle defined in AGENTS.md:
inspect → plan → branch → slice → validate → review → commit → push → tag.

## Python environment

Use `.venv-wsl/bin/python` for all Python commands.

## Validation

Before commit, run all quality gates from AGENTS.md.

## Hard stops

Same as AGENTS.md: stop on ambiguity, security risk, Docker failure, migration,
scope drift, or cross-repo action.
