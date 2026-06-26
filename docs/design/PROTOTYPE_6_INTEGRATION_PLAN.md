# Prototype 6 — Plan d’intégration TAf Local Forms

## 1. Objectif

Prototype 6 sert de cible UX pour les prochaines phases. Il ne doit pas être
copié-collé tel quel dans l’application Django. L’intégration doit être
progressive, compatible avec les routes existantes, et alignée sur les
contraintes terrain du projet TAfHSSiM.

## 2. Sources archivées

- `docs/design/prototypes/Prototype_6.html`
- `docs/specs/TAf_Local_Forms_Cahier_Charges_Technique_v0_1.pdf`
- `docs/specs/TAf_Local_Forms_Cahier_Charges_Metier_Non_Technique_v0_1.pdf`
- `docs/specs/TAf_Local_Forms_Guide_Developpement_v0_1.pdf`
- `docs/ai-agents/tooling/graphify-ponytail.md`
- `docs/ai-agents/tooling/taf-agent-skills.md`

## 3. Principes non négociables

- aucun changement fonctionnel dans F034A ;
- routes existantes conservées ;
- pas de migration ;
- pas de données supprimées ;
- pas de CDN en séance locale ;
- CSS local ;
- JS minimal ;
- dashboard/export/réseau protégés ;
- étudiant isolé des liens admin ;
- backup avant migrations futures ;
- médias hors Git ;
- Graphify/Ponytail utilisés comme aide, pas comme remplacement de revue.

## 4. Lecture du Prototype 6

Les zones UX repérées dans Prototype 6 couvrent :

- accueil étudiant ;
- liste modules ;
- questionnaire ;
- confirmation ;
- doublon ;
- médiathèque ;
- détail support ;
- vidéo locale ;
- ressources scolaires futures ;
- login formateur ;
- cockpit ;
- projection / QR ;
- gestion modules ;
- dashboard module ;
- exports ;
- réseau LAN ;
- gestion supports ;
- upload support ;
- configuration ;
- sauvegarde ;
- admin avancé.

## 5. Design system à extraire

Les éléments à extraire progressivement sont :

- variables CSS ;
- boutons ;
- cartes ;
- badges ;
- pills ;
- panels ;
- tables ;
- breadcrumbs ;
- topbar ;
- navigation ;
- forms ;
- alerts ;
- grids ;
- mode projection.

## 6. Découpage recommandé

- `F035` — design system CSS local sans backend.
- `F036` — navigation étudiant/formateur et breadcrumbs.
- `F037` — cockpit formateur + QR local + mode projection.
- `F038` — médiathèque documents avec migrations dédiées.
- `F039` — lecture vidéo locale.
- `F040` — matières scolaires futures.
- `F041` — backup PostgreSQL + médias.
- `F042` — packaging/terrain si nécessaire.

## 7. Protection données

- sauvegarde PostgreSQL avant toute migration ;
- volume média séparé avant upload ;
- jamais `down -v`, jamais `system prune --volumes`, jamais `flush` ;
- dumps non committés ;
- tests anti-doublon après changement de formulaire/session ;
- exports CSV protégés ;
- rollback code via Git, rollback données via backup vérifié.

## 8. Matrice prototype vers tâches

| Zone Prototype 6 | Tâche cible | Risque données | Priorité |
|---|---|---|---|
| accueil / modules | F036 | faible | P0 |
| design system | F035 | faible | P0 |
| cockpit | F037 | faible/moyen | P1 |
| QR/projection | F037 | faible | P1 |
| supports catalogue | F038 | moyen | P1 |
| upload | F038 | moyen/élevé | P1 |
| vidéo | F039 | élevé | P2 |
| matières | F040 | moyen | P3 |
| backup | F041 | élevé mais protecteur | P0/P1 |

## 9. Critères d’acceptation F034A

- Prototype archivé.
- PDF archivés.
- Plan rédigé.
- Backup créé ou statut backup documenté.
- `taf-skills-status` exécutable si corrigé.
- Aucun changement fonctionnel Django.
- Aucune migration.
- Aucun secret/runtime/dump/backup committé.
- `manage.py check`, migration dry-run et `docker compose config` OK.
