# UX Implementation Roadmap

## But

Prioriser les futures PR UI après ce blueprint, sans mélanger :

- refonte visuelle ;
- évolution fonctionnelle ;
- dette documentaire ;
- risques réseau/terrain.

## Principes

- petits lots ;
- routes existantes conservées sauf décision explicite ;
- pas de changement backend métier “caché” dans une PR UI ;
- priorité à la clarté de séance locale ;
- aucune régression d’auth, de tests, de médiathèque ou d’anti-doublon.

## Lot 0 — Documentation et cadrage

Objectif :

- consolider ce blueprint comme référence de review UX.

Contenu :

- adoption de `docs/ux/*` comme base pour les futures PR ;
- usage de `docs/ux/UX_TRACEABILITY_MATRIX.md` comme check documentaire avant toute PR UI sensible ;
- usage de `UX_FINAL_ACCEPTANCE_CRITERIA.md`, `UX_COMPONENT_CONTRACTS.md`, `UX_COPY_AND_MESSAGES_GUIDE.md` et `UX_ACCESSIBILITY_MOBILE_CHECKLIST.md` comme pack de validation avant merge UI ;
- projection et `presence/heartbeat` désormais documentés comme surfaces UX de référence ;
- ajout futur éventuel d’un index UX dans `docs/ai-agents/README.md`.

Priorité : P0

## Lot 1 — Navigation et libellés globaux

Objectif :

- harmoniser les libellés et la logique de navigation.

Contenu :

- normaliser `voir`, `consulter`, `commencer`, `ouvrir` ;
- vérifier les labels du menu étudiant ;
- vérifier les labels du menu formateur ;
- renforcer les breadcrumbs sur quelques pages critiques si nécessaire.

Risque :

- faible

Priorité : P0

## Lot 2 — États étudiant modules / questionnaires

Objectif :

- rendre les états de séance encore plus évidents.

Contenu :

- harmoniser visuellement :
  - ouvert ;
  - consultation seulement ;
  - indisponible ;
- revoir les pages “merci” et “indisponible” ;
- renforcer l’erreur doublon et le rappel 2 chiffres.

Risque :

- faible à moyen

Priorité : P0

## Lot 3 — Cockpit formateur

Objectif :

- réduire la charge cognitive du cockpit sans perdre la richesse fonctionnelle.

Contenu :

- meilleure hiérarchie overview / accès / modules / exports / outils ;
- regroupement visuel plus fort des actions réseau ;
- clarification de la section présence.

Risque :

- moyen

Priorité : P1

## Lot 4 — Réseau, configuration, contrôle LAN

Objectif :

- clarifier le triptyque réseau.

Contenu :

- `/dashboard/network/` = lecture / diagnostic ;
- `/dashboard/network-control/` = actions helper ;
- `/dashboard/settings/` = paramètres ;
- renforcer messages et transitions entre ces trois pages.

Risque :

- moyen, car page terrain sensible

Priorité : P0

## Lot 5 — Dashboards modules et exports

Objectif :

- unifier la lecture des dashboards modules.

Contenu :

- alignement des filtres, tables, cartes stats ;
- meilleure lisibilité des exports ;
- empty states plus assumés.

Risque :

- faible à moyen

Priorité : P1

## Lot 6 — Médiathèque publique

Objectif :

- rendre la consultation supports plus fluide.

Contenu :

- distinction document / vidéo plus forte ;
- gestion des empty states après filtres ;
- amélioration de la lecture des métadonnées ;
- meilleure continuité catalogue -> détail -> watch/download.

Risque :

- faible

Priorité : P1

## Lot 7 — Dashboard supports / upload

Objectif :

- améliorer le flux formateur de contenus sans créer de nouvelle logique.

Contenu :

- meilleure lisibilité brouillon/public ;
- guidage matière/chapitre ;
- messages d’erreur upload encore plus explicites ;
- éventuel lien structuré vers admin avancé pour édition.

Risque :

- faible à moyen

Priorité : P2

## Lot 8 — Ressources scolaires futures

Objectif :

- préparer un vrai parcours UX “matières / chapitres” si et seulement si la
  stratégie contenu devient stable.

Contenu :

- exploration par matière ;
- éventuelle page dédiée ;
- articulation avec médiathèque.

Risque :

- moyen à élevé si engagé trop tôt

Priorité : P3

## Ordre recommandé

1. Lot 1
2. Lot 2
3. Lot 4
4. Lot 3
5. Lot 5
6. Lot 6
7. Lot 7
8. Lot 8

## Prochaine PR UI recommandée

Lot recommandé après F047C :

- `Lot 1 — Navigation et libellés globaux`

Pourquoi :

- impact large avec faible risque ;
- prépare la cohérence des CTA étudiant/formateur ;
- s’appuie directement sur le guide de messages et les contrats composants ;
- évite de commencer par la zone la plus risquée (`network-control`).

## Stop conditions pour les futures PR UI

- si la PR modifie des modèles ou migrations sans le dire ;
- si une PR UI touche auth ou sécurité sans tests adaptés ;
- si `network-control` perd ses garde-fous localhost/helper ;
- si une PR promet une fonctionnalité UX non implémentée ;
- si le parcours étudiant devient plus complexe au lieu de devenir plus clair.
