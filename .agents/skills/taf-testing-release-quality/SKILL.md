---
name: taf-testing-release-quality
description: Use this skill when a task needs validation, release checks, runtime verification, or final quality review for TAf Local Forms.
---

# TAf Testing Release Quality

## When to use

Use before PR, release, tagging, or field-readiness confirmation.

## Inputs to read

- `AGENTS.md`
- release notes or release checklist docs
- the exact files changed by the task

## Rules

- Always run `git diff --check`.
- Always run `manage.py check`.
- Run relevant tests, and `surveys.tests` when behavior changes.
- Always run migration dry-run.
- Always run `docker compose config`.
- Run Docker runtime checks only when requested or when runtime changed.
- Keep public routes and authenticated trainer routes explicitly verified.
- Keep CSV injection and anti-duplicate coverage visible.
- Record release-note implications.

## Safe workflow

1. Match validation depth to actual risk.
2. Prefer narrow checks for docs-only work.
3. Report what was not run.
4. Do not claim runtime verification if it was skipped.

## Stop conditions

- failed validation
- migration surprise
- release note claim not backed by checks

## Acceptance checklist

- Required checks are reported.
- Skipped checks are disclosed.
- CSV injection and anti-duplicate coverage stay visible.
- Release readiness is stated honestly.
