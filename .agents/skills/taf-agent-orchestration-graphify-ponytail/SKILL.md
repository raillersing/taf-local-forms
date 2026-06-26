---
name: taf-agent-orchestration-graphify-ponytail
description: Use this skill when a task needs agent orchestration, Graphify awareness, or Ponytail scope control for TAf Local Forms.
---

# TAf Agent Orchestration Graphify Ponytail

## When to use

Use before large tasks, audits, refactors, architecture mapping, or prototype
integration planning.

## Inputs to read

- `AGENTS.md`
- `docs/ai-agents/tooling/graphify-ponytail.md`
- validated `graphify-out/GRAPH_REPORT.md` only if it exists and was reviewed

## Rules

- Graphify helps understand the repository; it does not make decisions.
- Do not run Graphify extraction without explicit approval.
- Do not scan secrets, backups, dumps, local databases, media, or sensitive
  runtime files.
- Use Ponytail to reduce scope before inventing new structure.
- Never reduce security, data protection, tests, or accessibility.
- Search for an existing project solution before creating a new one.

## Safe workflow

1. Read the task brief and AGENTS rules first.
2. Consult validated architecture aids only when available.
3. Prefer targeted repository reading and minimal changes.
4. Keep the PR small and justified.

## Stop conditions

- Graphify run requested implicitly without approval
- sensitive files would be scanned
- Ponytail simplification would weaken safeguards

## Acceptance checklist

- Graphify use is documented or intentionally skipped.
- Ponytail constraints are applied.
- Existing solutions were checked first.
- Security, data, tests, and accessibility remain protected.
