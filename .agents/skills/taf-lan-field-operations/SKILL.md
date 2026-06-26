---
name: taf-lan-field-operations
description: Use this skill when a task involves LAN access, QR distribution, field deployment steps, or trainer network operations in TAf Local Forms.
---

# TAf LAN Field Operations

## When to use

Use for network pages, LAN helper flows, QR distribution, projection, or
classroom operation docs.

## Inputs to read

- `AGENTS.md`
- `README.md`
- trainer docs and relevant files in `surveys/network.py`, `templates/`, and
  `scripts/dev/`

## Rules

- Be explicit about laptop LAN IP, trainer port, and student port.
- Respect env-driven `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.
- Keep diagnostics hidden behind `details` or secondary UI.
- Require a real phone test for field confidence.
- Prefer local QR generation or server-side safe approaches.
- No Internet dependency during classroom runtime.

## Safe workflow

1. Confirm which page or document serves the trainer.
2. Separate core student URL guidance from technical diagnostics.
3. Check before, during, and after session steps.
4. Preserve the rule that `localhost` is not for students.

## Stop conditions

- docs imply guaranteed phone connectivity
- unsafe firewall or proxy guidance appears without warning
- Internet becomes a runtime requirement

## Acceptance checklist

- LAN URL guidance is clear.
- Diagnostic content is secondary.
- Phone-test step is documented.
- QR guidance remains local-only.
- Before/during/after session checklist is covered.
