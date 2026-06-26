---
name: taf-project-governance
description: Use this skill when a task needs project governance, scope control, branch discipline, or stop conditions for TAf Local Forms.
---

# TAf Project Governance

## When to use

Use before any significant agent task in this repository.

## Inputs to read

- `AGENTS.md`
- `docs/ai-agents/tooling/graphify-ponytail.md`
- task brief, branch state, and current git status

## Rules

- One task = one branch = one PR.
- Start from a clean `main` plus known local untracked context.
- Do not simulate human merge approval.
- Do not expand scope beyond the stated slice.
- Do not run `docker compose down -v`.
- Do not run `docker system prune --volumes`.
- Do not run `python manage.py flush`.
- Do not read or expose secrets.

## Safe workflow

1. Inspect git state and recent log.
2. Create a dedicated branch for the task.
3. Restate the smallest coherent slice.
4. Change only the files needed for that slice.
5. Run the narrowest required validation.
6. Stop if risk exceeds the approved scope.

## Stop conditions

- Git conflict
- failing validation
- unexpected migration
- Docker failure
- secret exposure risk
- scope drift outside the repository or task brief

## Acceptance checklist

- Branch and PR scope are explicit.
- No forbidden command was used.
- No secret or runtime file is added.
- Validation status is reported clearly.
- Human review is preserved where required.
