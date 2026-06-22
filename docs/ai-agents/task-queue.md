# Task Queue — TAf Local Forms

## Status legend

| Status | Meaning |
|--------|---------|
| done | Completed and committed |
| pending | Not yet started |
| blocked | Waiting on external dependency |
| cancelled | No longer needed |

## Current queue

| ID | Description | Status |
|----|-------------|--------|
| F001 | MVP implementation (Module 2 form, Student/Submission, anti-duplicate, scoring) | done |
| F002 | Codex orchestrator bootstrap (AGENTS.md, .codex/, .agents/) | done |
| F003 | v0.1.0 release (tag, GitHub remote, release notes) | done |
| F004 | Field polish (guide formateur, README updates, seed command improvements) | done |
| F005 | UX corrections (logo placement, form alignment, label fix) | done |
| F006 | Agent workflow and skills framework (this document, AGENTS.md, skills) | done |
| F007 | Release candidate review + Graphify integration | done |
| F008 | Push / PR / merge workflow (push branch, open PR, merge, cleanup) | done |
| F009 | Module 3 + 4 questionnaires (combined PR #5) | done |
| F009 | Tag v0.1.1 | pending |
| F010 | Safe cleanup workflow | done |
| F011 | Module 3 + 4 field deployment | done |
| F012 | Update field user manual for Modules 2, 3, 4 | done |
| F013 | Final validation + v0.2.0 release notes | done |
| F014 | Safe network config panel + live presence | done |
| F015 | Update v0.2.0 release notes after F014 | done |
| F016 | LAN diagnostics + admin Django interface refinement | done |

## Managing the queue

- Move the orchestrator cursor through the queue in order.
- Skip blocked items.
- Update status after each commit.
- Add new items as they are discovered.
