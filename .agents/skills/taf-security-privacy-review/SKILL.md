---
name: taf-security-privacy-review
description: Auth, secret handling, CSV injection prevention, and data minimisation review for TAfHSSiM.
---

# TAf Security/Privacy Review Skill

Use this skill when the task touches authentication, data collection, CSV export,
environment configuration, or any security-sensitive code.

## What I do

Audit the application for common security and privacy issues relevant to a
local classroom questionnaire app.

## Checklist

- [ ] Dashboard and admin require login (login_required)
- [ ] Student form does not expose dashboard/admin links
- [ ] CSRF protection is enabled on the student form
- [ ] `.env`, `.env.*`, `*.sqlite3`, `*.log` are in `.gitignore`
- [ ] No secrets are hardcoded in Python or templates
- [ ] `DEBUG=false` for classroom use
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are configurable via env
- [ ] CSV export sanitises formula-like cells (=, +, -, @)
- [ ] Only required student data is collected
- [ ] No Internet access required at runtime (no CDN, no external API)
- [ ] No student data is exposed without authentication
- [ ] The app does not expose internal IPs or hostnames to unauthenticated users

## When to use me

Load during implementation review and before release.

## Hard stops

- Any secret or credential visible in diff, log, or response
- Student data accessible without authentication
- CSV injection possible
- CSRF disabled on student form

## Expected output

- Findings by severity
- Verdict: APPROVE / REQUEST_CHANGES / BLOCK
