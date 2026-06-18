# TAf Local Forms – Agent Instructions

## Project purpose

This repository is a standalone local web application for the TAfHSSiM project.

TAfHSSiM means Technology Access for High School Students in Madagascar.

The application must run on a trainer's laptop and allow students connected to the same Wi-Fi or hotspot to open a questionnaire through the laptop local IP address, for example:

http://192.168.x.x:8000/

## Operating model

Codex must work as the parent Agent Orchestrator for this repository.

The parent agent must:
1. inspect the current project state before editing;
2. create or update a short execution plan;
3. split work into small coherent implementation slices;
4. use subagents when useful for architecture review, implementation review, documentation review, test coverage review, Docker review, or security/privacy review;
5. validate after each major step;
6. stop and ask for human review on ambiguity, security concern, Docker failure, migration issue, data-loss risk, or scope drift.

## Scope boundaries

Allowed scope:
- files inside this repository only;
- Django backend;
- Django templates;
- local static assets;
- Docker and Docker Compose;
- tests;
- README and local trainer documentation.

Forbidden:
- modifying unrelated repositories;
- creating or reading real secrets;
- requiring Internet during classroom runtime;
- relying on CDN assets at runtime;
- adding unnecessary external services;
- exposing the app publicly without clear production-hardening warnings.

## Technical baseline

Use:
- Python 3.12 or newer;
- Django >=5.2,<5.3;
- SQLite for MVP local storage;
- Django templates;
- local compiled CSS/static assets;
- Docker + Docker Compose;
- Gunicorn in Docker;
- WhiteNoise or equivalent simple static serving;
- Django built-in tests unless pytest has a clear benefit.

Database persistence:
- store SQLite data at /app/data/db.sqlite3 in Docker;
- mount /app/data as a persistent Docker volume or local directory;
- do not rely on container writable layer for classroom data.

Runtime network:
- bind Gunicorn to 0.0.0.0:8000 inside Docker;
- expose port 8000;
- document laptop LAN IP access for students.

Security and privacy:
- public student form only for local network classroom use;
- dashboard and admin require login;
- keep CSRF protection enabled;
- collect only required student data;
- DEBUG, SECRET_KEY, ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS must come from environment variables with safe local defaults documented in .env.example;
- never hardcode production secrets.

## UX rules

Student-facing text must be simple, clear French.

Design must be:
- premium;
- readable;
- mobile-friendly;
- navy / white / light blue;
- uncluttered;
- accessible enough for public high school students.

Use the Internet Society Madagascar Chapter logo path:

static/brand/isoc_madagascar_logo.png

If the file is absent, show the text fallback:

Internet Society – Chapitre Madagascar

## Quality gates

Before saying a task is complete, Codex must run relevant checks, normally:

python manage.py test

and, when Docker files exist:

docker compose config
docker compose up --build

If a long-running Docker command cannot be completed safely in the current session, state exactly what was not verified.

## Done means

The MVP is done only when:
- /module-2/ displays the branded student form;
- valid submission creates Student and Submission;
- invalid 2-digit school ID is rejected;
- duplicate school ID for same session is blocked;
- dashboard requires login;
- CSV export requires login;
- seed command creates Module 2 data;
- Docker Compose can start the app;
- README explains local and Wi-Fi classroom usage.
