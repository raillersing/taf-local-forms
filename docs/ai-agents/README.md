# AI Agents — TAf Local Forms

This directory contains the agent workflow documentation for the
TAf Local Forms project.

## Files

| File | Purpose |
|------|---------|
| `README.md` | This index |
| `workflow.md` | Detailed task lifecycle |
| `task-queue.md` | Task queue and status management |
| `prompt-contracts.md` | Reusable prompt templates for agents |
| `release-checklist.md` | Step-by-step release procedure |
| `CODEX_ORCHESTRATOR_LAUNCH.md` | Codex boot prompt (legacy, kept for reference) |

## Tooling

| File | Purpose |
|------|---------|
| `tooling/graphify.md` | Graphviz/Graphify diagram docs for architecture visualisation |

## Architecture diagrams

DOT source files: `docs/architecture/graphs/*.gv`

| Diagram | File |
|---------|------|
| App overview | `docs/architecture/graphs/app-overview.gv` |
| Module 2 request flow | `docs/architecture/graphs/request-flow-module2.gv` |
| Trainer dashboard flow | `docs/architecture/graphs/trainer-dashboard-flow.gv` |
| Network dashboard flow | `docs/architecture/graphs/network-dashboard-flow.gv` |

## Source of truth

The root `AGENTS.md` is the authoritative instruction file for all agents.
These docs provide detail and reference. When in doubt, follow `AGENTS.md`.

## Skills

Skills are in `.agents/skills/`. Load the relevant skill before starting
a domain-specific task.
