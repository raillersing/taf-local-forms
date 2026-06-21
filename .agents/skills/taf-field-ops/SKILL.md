---
name: taf-field-ops
description: Classroom field operations, network access setup, WSL/Docker caveats, and trainer documentation for TAfHSSiM.
---

# TAf Field Operations Skill

Use this skill when the task involves field deployment, network access,
trainer documentation, or classroom readiness.

## What I do

Ensure the formateur can start the app, give the right URL to students,
diagnose connectivity issues, and complete the session successfully.

## Checklist

- [ ] Trainer docs explain Docker startup, seed, createsuperuser
- [ ] Trainer docs explain how to find laptop LAN IP (ipconfig)
- [ ] Trainer docs warn against localhost, WSL IP, Docker IP
- [ ] `/dashboard/network/` page is available and shows recommended URLs
- [ ] Firewall / AP isolation / WSL2 NAT caveats are documented
- [ ] CSV export procedure is documented
- [ ] Backup and restore procedure is documented
- [ ] Phone test step is documented

## When to use me

Load when the task touches README.md, docs/GUIDE_FORMATEUR_TERRAIN.md,
`surveys/network.py`, or the `/dashboard/network/` view.

## Hard stops

- Trainer docs promise auto-detection of LAN IP without caveats
- Network page claims to guarantee connectivity from phones
- Docs recommend unsafe firewall or netsh commands without warning

## Expected output

- Documentation updated
- Network page context verified
- Caveats clearly stated
