---
name: taf-data-safety-backup
description: Use this skill when a task could affect database state, backups, Docker volumes, migrations, or future media storage in TAf Local Forms.
---

# TAf Data Safety And Backup

## When to use

Use before migration, backup, storage, Docker, or data-sensitive work.

## Inputs to read

- `AGENTS.md`
- backup and cleanup scripts in `scripts/dev/`
- relevant model, migration, export, or storage files when in scope

## Rules

- Take or confirm a backup before risky migration work.
- Preserve data volumes.
- Never run `docker compose down -v`.
- Never run `docker system prune --volumes`.
- Never run `python manage.py flush`.
- Never commit dumps, local databases, or runtime media.
- Prefer non-destructive migrations.
- Re-check anti-duplicate behavior after any data-flow change.

## Safe workflow

1. Confirm the data risk of the task.
2. Identify which storage layer is affected.
3. Use safe scripts and documented backup paths only.
4. Validate that no data artifact is added to git.

## Stop conditions

- destructive migration risk
- uncertain rollback path
- data loss possibility
- runtime volume cleanup requested implicitly

## Acceptance checklist

- Backup expectation is explicit.
- No destructive volume command is used.
- No dump or media artifact is committed.
- Data integrity and anti-duplicate rules remain covered.
