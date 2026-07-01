# UX Master Map

## But

Ce document cartographie l'UX réelle de TAf Local Forms avant toute nouvelle
intégration UI. Il sert de point de vérité pour :

- l'état courant de l'application ;
- la séparation étudiant / formateur ;
- les zones sensibles réseau, médias et exports ;
- les écarts entre l'application réelle et la cible Prototype 6 ;
- la préparation des prochaines PR UI sans dérive fonctionnelle.

## Sources de référence

Sources code vérifiées :

- `surveys/urls.py`
- `surveys/views.py`
- `surveys/forms.py`
- `surveys/network.py`
- `surveys/tests.py`
- `templates/surveys/`
- `static/css/app.css`

Sources documentaires relues :

- `README.md`
- `docs/design/TAF_NAVIGATION.md`
- `docs/design/TAF_COCKPIT_PROJECTION.md`
- `docs/design/TAF_MEDIA_LIBRARY.md`
- `docs/design/PROTOTYPE_6_INTEGRATION_PLAN.md`
- `docs/design/prototypes/Prototype_6.html`
- `docs/field/TAF_FIELD_VALIDATION.md`
- `docs/ai-agents/README.md`
- `docs/ai-agents/workflow.md`

Sources de cadrage présentes mais non text-extraites automatiquement dans cet
environnement :

- `docs/specs/TAf_Local_Forms_Cahier_Charges_Technique_v0_1.pdf`
- `docs/specs/TAf_Local_Forms_Cahier_Charges_Metier_Non_Technique_v0_1.pdf`
- `docs/specs/TAf_Local_Forms_Guide_Developpement_v0_1.pdf`

Conséquence :

- les constats de ce blueprint sont ancrés d'abord dans le code et les docs
  Markdown/HTML actuellement vérifiables ;
- les PDF restent les références de cadrage à conserver pour arbitrer les
  futures décisions UX.

## Vue d'ensemble de l'application

L'application est une plateforme locale de séance en classe avec deux parcours
distincts :

- parcours étudiant public, mobile-first, sans login ;
- parcours formateur protégé par login ;
- sous-ensemble formateur renforcé par `staff_member_required` pour certaines
  actions de configuration et de pilotage.

### Pôles UX principaux

1. Accueil et sas d'entrée
2. Parcours modules étudiant
3. Questionnaires module 2 à module 8
4. Parcours de confirmation / indisponibilité / réponses fermées
5. Cockpit formateur
6. Dashboards modules et exports CSV
7. Réseau local, projection et contrôle LAN
8. Médiathèque locale : supports, détail, téléchargement, vidéo
9. Configuration réseau et sauvegarde
10. Admin avancé Django

## Cartographie fonctionnelle par zone

### 1. Accueil public

Route :

- `/`

Rôle :

- séparer visuellement l'entrée étudiant et l'entrée formateur ;
- rappeler le contexte local/offline ;
- fournir un premier niveau de pédagogie sur la séance.

État courant :

- accueil fortement orienté Prototype 6 ;
- deux CTA principaux : étudiant et formateur ;
- anchor “Aide formateur” via `#espace-formateur`.

### 2. Espace étudiant

Routes :

- `/modules/`
- `/modules/module-2/` à `/modules/module-8/`
- `/module-2/` à `/module-8/`
- `/module-X/success/<id>/`
- `/supports/`
- `/supports/<slug>/`
- `/supports/<slug>/watch/`
- `/supports/<slug>/download/`

Règles UX :

- pas de lien admin ;
- pas de lien dashboard ;
- formulation simple ;
- consultation possible même quand les réponses sont fermées ;
- erreur d'indisponibilité explicite si aucune session n'est active.

### 3. Espace formateur

Routes :

- `/dashboard/`
- `/dashboard/module-2/` à `/dashboard/module-8/`
- `/dashboard/export/module-2.csv` à `/dashboard/export/module-8.csv`
- `/dashboard/network/`
- `/dashboard/network-control/`
- `/dashboard/projection/`
- `/dashboard/supports/`
- `/dashboard/supports/upload/`
- `/dashboard/settings/`
- `/dashboard/settings/use-current-address/`
- `/dashboard/backup/`
- `/dashboard/presence.json`
- `/dashboard/modules/<module_code>/toggle-responses/`

Règles UX :

- cockpit = hub opérationnel ;
- réseau et projection = tâches terrain critiques ;
- export = action administrative ;
- configuration et toggle réponses = actions staff ;
- upload support = brouillon/public maîtrisé.

### 4. Présence et heartbeat

Routes :

- `/presence/heartbeat/`
- `/dashboard/presence.json`

UX :

- invisible côté élève comme fonctionnalité métier autonome ;
- sert au feedback de présence dans le cockpit ;
- page cockpit dépend d'un rafraîchissement périodique.

## Modèle UX réel de permissions

### Public sans login

- accueil ;
- modules ;
- détails module ;
- questionnaires ;
- pages succès sous garde de session ;
- catalogue supports publiés ;
- détail support publié ;
- watch vidéo publiée ;
- download support publié.

### Login requis

- cockpit ;
- projection ;
- supports dashboard ;
- upload support ;
- dashboards modules ;
- exports CSV ;
- accès réseau ;
- backup ;
- présence JSON.

### Login + staff requis

- configuration réseau ;
- utilisation de l'adresse actuelle ;
- toggle ouverture/fermeture des réponses ;
- contrôle LAN.

## États UX transverses déjà présents

- `success` : pages merci, messages Django, badges réussite
- `warning` : réponses fermées, IP obsolète, configuration incomplète
- `error` : validation formulaire, helper LAN indisponible, support inexistant
- `empty` : aucun module, aucune réponse, aucun support publié
- `permission` : redirection vers `/admin/login/` ou blocage staff
- `unavailable` : questionnaire 503 si session absente
- `draft/private` : support caché du catalogue public
- `loading` : surtout visible dans `/dashboard/network-control/`

## Risques UX principaux observés

- mélange entre action “voir”, “consulter”, “répondre” selon l'état de module ;
- forte densité fonctionnelle du cockpit ;
- séparation encore imparfaitement documentée entre diagnostic réseau,
  configuration réseau et contrôle LAN ;
- médiathèque structurée mais encore éclatée en plusieurs conventions ;
- Prototype 6 plus large que l'application réellement disponible ;
- certains flux critiques dépendent du réseau local réel, donc l'UX doit
  rester prudente et non trompeuse.

## Cible UX directrice

La cible recommandée pour les prochaines PR UI est :

- étudiant :
  - entrée simple ;
  - liste modules claire ;
  - détail module pédagogique ;
  - questionnaire guidé ;
  - confirmation explicite ;
  - supports publiés faciles à filtrer.
- formateur :
  - cockpit = hub ;
  - réseau = diagnostic ;
  - contrôle LAN = orchestration active ;
  - projection = diffusion salle ;
  - supports = gestion contenus ;
  - configuration = paramètres ;
  - backup = sécurité opérationnelle.

## Documents liés

- `docs/ux/UX_NAVIGATION_TREE.md`
- `docs/ux/UX_ACTION_CATALOG.md`
- `docs/ux/UX_STUDENT_JOURNEYS.md`
- `docs/ux/UX_TRAINER_JOURNEYS.md`
- `docs/ux/UX_NETWORK_CONTROL.md`
- `docs/ux/UX_MODULES_RESPONSES_EXPORTS.md`
- `docs/ux/UX_MEDIA_LIBRARY.md`
- `docs/ux/UX_SCHOOL_RESOURCES.md`
- `docs/ux/UX_STATE_AND_ERROR_MATRIX.md`
- `docs/ux/UX_PROTOTYPE_6_GAP_ANALYSIS.md`
- `docs/ux/UX_IMPLEMENTATION_ROADMAP.md`
