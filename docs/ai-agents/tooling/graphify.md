# Graphify / Graphviz — TAf Local Forms

## Purpose

This document defines how Graphviz DOT diagrams and optional Graphify
integration are used in the TAf Local Forms repository.

## Current status

- **Graphviz `dot` CLI:** Not installed locally.
- **Graphify installation:** Not installed. No `graphify install` command has been run.
- **Diagram output:** DOT source files exist in `docs/architecture/graphs/`.
  No generated SVG/PNG is committed.

## Generating diagrams

Install Graphviz on WSL/Ubuntu:

```sh
sudo apt-get update && sudo apt-get install -y graphviz
```

Then generate SVG output:

```sh
cd docs/architecture/graphs
mkdir -p out
for f in *.gv; do
  dot -Tsvg "$f" -o "out/${f%.gv}.svg"
done
```

Output goes to `docs/architecture/graphs/out/`. This directory is in `.gitignore`.

## Diagram sources

| File | Description |
|------|-------------|
| `app-overview.gv` | Top-level deployment topology |
| `request-flow-module2.gv` | Student form submission flow |
| `trainer-dashboard-flow.gv` | Trainer dashboard and CSV export |
| `network-dashboard-flow.gv` | Network diagnostics page flow |

## Agent usage

- Agents may read `.gv` files for architecture orientation.
- Agents may read generated SVG/PNG only if present in `out/`.
- Agents must never modify `.gv` files without explicit task scope.
- Agents must never run `graphify install` or auto-mutation commands.

## Safety rules

- No runtime dependency: diagrams are documentation only.
- No source code is sent to external APIs.
- No `.env` or secret content is included in diagrams.
- No application code is modified.
