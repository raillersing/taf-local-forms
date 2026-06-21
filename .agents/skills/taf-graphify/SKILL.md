---
name: taf-graphify
description: Read-only architecture visualisation skill for TAf Local Forms using Graphviz DOT diagrams.
---

# TAf Graphify Skill

Use this skill when the task involves understanding or documenting the
application architecture, request flow, or deployment topology.

## What I do

Provide DOT-format architecture diagrams and Graphviz-based visualisation
for the TAf Local Forms application. No runtime dependencies.

## Diagram inventory

| Diagram | File | Covers |
|---------|------|--------|
| App overview | `docs/architecture/graphs/app-overview.gv` | Formateur → Docker → Django → SQLite |
| Module 2 flow | `docs/architecture/graphs/request-flow-module2.gv` | Élève → form → submission → confirmation |
| Dashboard | `docs/architecture/graphs/trainer-dashboard-flow.gv` | Formateur → dashboard → CSV export |
| Network page | `docs/architecture/graphs/network-dashboard-flow.gv` | Formateur → network page → diagnostic |

## Generating images

If `dot` (Graphviz) is installed:

```sh
cd docs/architecture/graphs
dot -Tsvg app-overview.gv -o out/app-overview.svg
dot -Tsvg request-flow-module2.gv -o out/request-flow-module2.svg
dot -Tsvg trainer-dashboard-flow.gv -o out/trainer-dashboard-flow.svg
dot -Tsvg network-dashboard-flow.gv -o out/network-dashboard-flow.svg
```

Output goes to `docs/architecture/graphs/out/`. This directory is gitignored.

## Reading diagrams

Open the `.gv` files in any text editor. They use standard DOT syntax.
Convert to SVG/PNG with Graphviz to visualise.

## When to use me

Load when the task involves architecture review, documentation, or
onboarding new agents.

## Hard stops

- Never run `graphify install` or any auto-mutation command
- Never send source code to an external API
- Never read `.env` or secrets
- Never modify application code

## References

- `docs/ai-agents/tooling/graphify.md` — full Graphify tooling docs
- `docs/architecture/graphs/` — diagram sources
