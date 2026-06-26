---
name: taf-docs-spec-traceability
description: Use this skill when a task needs alignment between code, documentation, design references, and TAf specification documents.
---

# TAf Docs Spec Traceability

## When to use

Use for audits, planning, docs updates, integration notes, and roadmap work.

## Inputs to read

- `AGENTS.md`
- `README.md`
- `docs/specs/`
- `docs/design/`
- relevant docs in `docs/ai-agents/`

## Rules

- Read the available spec and design references before making claims.
- Trace requirements to current features, tests, or future work.
- Distinguish clearly between existing, declared, recommended, and future
  states.
- Never invent an implementation status that was not verified.
- Write clearly for trainer, maintainer, and AI-agent audiences.

## Safe workflow

1. Identify the requirement source.
2. Map it to code, docs, or backlog status.
3. Mark gaps without overstating certainty.
4. Keep future phases separated from current implementation.

## Stop conditions

- requirement source is missing
- status cannot be verified
- docs would misrepresent current behavior

## Acceptance checklist

- Source references are explicit.
- Current and future states are separated.
- No unsupported status claim is introduced.
- Documentation stays readable and operational.
