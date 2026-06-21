# Workflow — TAf Local Forms

## Task lifecycle

Every task follows a strict cycle:

```
inspect → plan → branch → slice → validate → review → commit → push → tag
```

### 1. Inspect

Before any change, capture the current state:

```sh
pwd
git branch --show-current
git status --short
git log --oneline --max-count=10
```

If Docker is running:

```sh
docker compose ps
curl -I http://127.0.0.1:8010/module-2/
```

### 2. Plan

Write a short execution plan (2–5 slices). Each slice must be the smallest
coherent change that can be validated independently.

### 3. Branch

Work on `finalize/orchestrator-field-ready` or create a dedicated feature branch.

### 4. Slice

Implement one slice at a time. Stay within allowed scope (see AGENTS.md).
Do not change models, migrations, scoring, or anti-duplicate logic unless
explicitly requested.

### 5. Validate

Run all quality gates (see AGENTS.md). Every slice must pass before commit.

### 6. Review

Stop for human review when:
- scope drift is detected;
- a migration would be created;
- security or privacy is at risk;
- Docker fails;
- the change affects the classroom workflow;
- ambiguity cannot be resolved from existing docs.

### 7. Commit

One commit per slice. Use a clear conventional-commit prefix:
`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`.

### 8. Push

Only after human approval.

### 9. Cleanup

After a PR is merged, run the safe cleanup script to remove residual artifacts:

```sh
scripts/dev/taf-clean-after-merge
```

This script:
- prunes stale remote tracking references;
- deletes local branches that are already merged into `main`;
- prunes orphaned worktree references;
- stops Docker containers without deleting volumes.

### 10. Tag

Only after field test verification.

## Agent roles

Refer to AGENTS.md for the agent roster. Orchestrator always starts.
Review agents are read-only and report findings without modifying files.
