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

## Source of truth

The root `AGENTS.md` is the authoritative instruction file for all agents.
These docs provide detail and reference. When in doubt, follow `AGENTS.md`.

## Skills

Skills are in `.agents/skills/`. Load the relevant skill before starting
a domain-specific task.
