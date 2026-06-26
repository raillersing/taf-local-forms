---
name: taf-ui-ux-prototype-6
description: Use this skill when a task translates Prototype 6 into Django templates, local CSS, or trainer/student UI patterns for TAf Local Forms.
---

# TAf UI UX Prototype 6

## When to use

Use for F035, F036, F037, design system work, and template/UI planning.

## Inputs to read

- `AGENTS.md`
- `README.md`
- `docs/design/Prototype 6.html` or local `Prototype 6.html` if present
- relevant files in `templates/` and `static/css/`

## Rules

- Prototype 6 is a UX target, not a final single-page app to paste verbatim.
- Extract reusable design tokens, cards, buttons, badges, breadcrumbs,
  panels, and tables.
- Preserve existing routes and Django page structure.
- Keep a mobile-first student experience.
- Keep a clear trainer cockpit.
- Fold technical diagnostics into `details` or secondary panels.
- Never expose admin links in student navigation.
- Do not rely on CDN QR libraries for production implementation.
- Preserve accessibility through labels, contrast, headings, and large buttons.

## Safe workflow

1. Identify reusable UI primitives from the prototype.
2. Map those primitives onto existing templates and CSS.
3. Keep student and trainer flows distinct.
4. Validate mobile readability and action clarity.

## Stop conditions

- prototype copy-paste would break routing or auth
- CDN dependency would leak into runtime
- trainer/admin context would appear on student pages

## Acceptance checklist

- Prototype 6 is treated as a reference, not a direct final build.
- Existing routes remain intact.
- Student mobile flow stays simple.
- Trainer cockpit remains operational and readable.
- Accessibility constraints are still explicit.
