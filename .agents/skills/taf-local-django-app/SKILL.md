---
name: taf-local-django-app
description: Use this skill for building, reviewing, testing, or documenting the taf-local-forms Django local classroom questionnaire app for TAfHSSiM.
---

# TAf Local Django App Skill

Use this skill whenever the task involves taf-local-forms.

## Required workflow

1. Inspect existing files first.
2. Restate the next small implementation slice.
3. Implement only that slice.
4. Add or update tests when behavior changes.
5. Run the narrowest meaningful validation.
6. Report changed files, validation results, and limitations.
7. Stop for human review on ambiguity, migration failure, Docker failure, security/privacy issue, or scope drift.

## Product constraints

- Standalone project.
- Local classroom use.
- No Internet required during runtime.
- No CDN assets at runtime.
- Public student form, protected trainer dashboard/admin.
- SQLite local storage.
- Docker-deployable.
- Premium simple French UI.

## Data integrity constraints

- The student school ID must keep leading zeroes.
- It must be exactly 2 digits.
- Duplicate submission prevention must apply to the same TrainingSession plus school ID.
- Prefer a school_id_number_snapshot on Submission plus a database-level unique constraint when practical.

## Validation checklist

Minimum tests:
- Module 2 form GET.
- Valid submission creates Student and Submission.
- Invalid school ID rejected.
- Duplicate school ID rejected for same active session.
- Dashboard requires login.
- CSV export requires login.
- Seed command creates Module 2 session.

Docker checks:
- docker compose config
- docker compose up --build
- static files load in Docker
- app listens on 0.0.0.0:8000 inside container
