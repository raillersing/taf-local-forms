# Local TAf Agent Skills

## 1. Objectif des skills locaux TAf

Les skills locaux TAf servent a guider Codex, OpenCode et les agents
compatibles sur ce projet sans ajouter de dependances runtime ni de logique
applicative. Ils encadrent le scope, la securite, la protection des donnees,
la lecture des specs, l'usage du Prototype 6 et la qualite avant PR.

## 2. Pourquoi ne pas installer tous les skills publics

- Les skills publics ne sont pas automatiquement audites pour ce depot.
- Ils peuvent pousser des workflows trop generiques ou trop lourds.
- Certains supposent un contexte cloud, des APIs externes, ou des hooks
  globaux non adaptes a une application de salle de classe locale.
- Le projet a deja des contraintes strictes sur les donnees, Docker, le LAN,
  l'accessibilite mobile et l'absence de CDN pendant la seance.
- La politique par defaut est de preferer des skills locaux adaptes au projet.

## 3. Politique de securite des skills

- Les skills tiers non audites ne sont jamais installes automatiquement.
- Toute installation externe demande une revue humaine avant execution.
- `npx skills add --all` est interdit sur ce projet.
- Aucun skill ne doit lire, exposer ou demander des secrets.
- Aucun skill ne doit modifier une configuration globale sans accord humain.
- Aucun skill ne doit contourner `AGENTS.md`, les validations ou les hard stops.

## 4. Emplacement

- Les skills projet vivent dans `.agents/skills/`.
- Ils sont documentes pour etre reutilisables dans l'ecosysteme Agent Skills.
- Ils restent compatibles avec Codex et OpenCode dans une logique de skills
  locaux lus depuis le depot.

## 5. Skills locaux crees

- `taf-project-governance`
- `taf-django-local-app`
- `taf-data-safety-backup`
- `taf-ui-ux-prototype-6`
- `taf-lan-field-operations`
- `taf-media-library`
- `taf-testing-release-quality`
- `taf-docs-spec-traceability`
- `taf-agent-orchestration-graphify-ponytail`
- `taf-accessibility-mobile-classroom`

## 6. Quand utiliser chaque skill

- `taf-project-governance` : avant toute tache significative, pour cadrer la
  branche, la PR, le scope et les hard stops.
- `taf-django-local-app` : pour les vues, URLs, templates, formulaires, tests
  et le rendu serveur Django.
- `taf-data-safety-backup` : avant toute operation qui touche migrations,
  stockage, Docker, backup, supports ou donnees eleves.
- `taf-ui-ux-prototype-6` : pour traduire Prototype 6 vers le design system,
  les templates et l'experience eleve/formateur.
- `taf-lan-field-operations` : pour reseau local, dashboard reseau, QR local,
  projection et procedure de seance.
- `taf-media-library` : pour les futures phases mediatheque, documents, videos
  et stockage media persistant.
- `taf-testing-release-quality` : avant PR, release, tag ou validation
  runtime.
- `taf-docs-spec-traceability` : pour aligner roadmap, cahiers des charges,
  docs terrain et etat reel du code.
- `taf-agent-orchestration-graphify-ponytail` : avant grosse tache, audit ou
  refonte pour reduire le scope et mieux cartographier le depot.
- `taf-accessibility-mobile-classroom` : pour tout ce qui est visible cote
  eleve sur telephone en salle.

## 7. Ordre recommande avant une tache

1. Lire `AGENTS.md`.
2. Lire le skill pertinent dans `.agents/skills/`.
3. Lire `graphify-out/GRAPH_REPORT.md` seulement s'il existe et a ete valide.
4. Appliquer Ponytail pour reduire le scope.
5. Identifier les fichiers vraiment necessaires.
6. Garder la PR petite et ciblee.

## 8. Correspondance avec les prochaines phases

- `F034A` : `taf-project-governance`, `taf-docs-spec-traceability`,
  `taf-agent-orchestration-graphify-ponytail`, `taf-data-safety-backup`
- `F035` : `taf-project-governance`, `taf-ui-ux-prototype-6`,
  `taf-django-local-app`, `taf-accessibility-mobile-classroom`
- `F036` : `taf-project-governance`, `taf-ui-ux-prototype-6`,
  `taf-django-local-app`, `taf-lan-field-operations`
- `F037` : `taf-project-governance`, `taf-ui-ux-prototype-6`,
  `taf-lan-field-operations`, `taf-accessibility-mobile-classroom`
- `F038` : `taf-project-governance`, `taf-data-safety-backup`,
  `taf-media-library`, `taf-testing-release-quality`
- `F039` : `taf-project-governance`, `taf-media-library`,
  `taf-accessibility-mobile-classroom`, `taf-testing-release-quality`
- `F040` : `taf-project-governance`, `taf-django-local-app`,
  `taf-docs-spec-traceability`, `taf-accessibility-mobile-classroom`

## 9. Skills publics candidats a evaluer plus tard

Ces skills sont des candidats documentaires uniquement. Ils doivent etre
revus avant installation, car les skills tiers ne sont pas automatiquement
audites :

- `vercel-labs/agent-skills --skill web-design-guidelines`
- `anthropics/skills --skill frontend-design`
- `mattpocock/skills --skill tdd`
- `mattpocock/skills --skill improve-codebase-architecture`
- `obra/superpowers --skill systematic-debugging`
- `obra/superpowers --skill writing-plans`
- `obra/superpowers --skill executing-plans`
- `obra/superpowers --skill verification-before-completion`
- `anthropics/skills --skill pdf`
- `anthropics/skills --skill docx`
- `anthropics/skills --skill xlsx`
