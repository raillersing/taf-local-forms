# UX Navigation Tree

## Principe directeur

La navigation cible doit rester strictement séparée entre :

- espace étudiant public ;
- espace formateur protégé ;
- actions staff renforcées ;
- parcours admin avancé séparé.

## Arbre réel actuel

```text
/
|- Espace étudiant -> /modules/
|  |- Module 2 detail -> /modules/module-2/
|  |  |- Questionnaire -> /module-2/
|  |  `- Confirmation -> /module-2/success/<id>/
|  |- Module 3 detail -> /modules/module-3/
|  |  |- Questionnaire -> /module-3/
|  |  `- Confirmation -> /module-3/success/<id>/
|  |- Module 4 detail -> /modules/module-4/
|  |  |- Questionnaire -> /module-4/
|  |  `- Confirmation -> /module-4/success/<id>/
|  |- Module 5 detail -> /modules/module-5/
|  |  |- Questionnaire -> /module-5/
|  |  `- Confirmation -> /module-5/success/<id>/
|  |- Module 6 detail -> /modules/module-6/
|  |  |- Questionnaire -> /module-6/
|  |  `- Confirmation -> /module-6/success/<id>/
|  |- Module 7 detail -> /modules/module-7/
|  |  |- Questionnaire -> /module-7/
|  |  `- Confirmation -> /module-7/success/<id>/
|  |- Module 8 detail -> /modules/module-8/
|  |  |- Questionnaire -> /module-8/
|  |  `- Confirmation -> /module-8/success/<id>/
|  `- Supports publics -> /supports/
|     |- Detail support -> /supports/<slug>/
|     |- Watch video -> /supports/<slug>/watch/
|     `- Download -> /supports/<slug>/download/
`- Espace formateur -> /dashboard/
   |- Cockpit
   |  |- Accès élèves
   |  |- Modules
   |  |- Présence
   |  |- Exports
   |  `- Outils
   |- Dashboards modules -> /dashboard/module-2/ ... /dashboard/module-8/
   |- Exports CSV -> /dashboard/export/module-2.csv ... /dashboard/export/module-8.csv
   |- Réseau -> /dashboard/network/
   |- Contrôle LAN -> /dashboard/network-control/
   |- Projection -> /dashboard/projection/
   |- Supports dashboard -> /dashboard/supports/
   |- Upload support -> /dashboard/supports/upload/
   |- Configuration réseau -> /dashboard/settings/
   |- Utiliser adresse actuelle -> POST /dashboard/settings/use-current-address/
   |- Backup -> /dashboard/backup/
   |- Présence JSON -> /dashboard/presence.json
   |- Toggle réponses -> POST /dashboard/modules/<module_code>/toggle-responses/
   `- Admin avancé -> /admin/
```

## Navigation étudiante cible recommandée

```text
Accueil
|- Modules
|  |- Detail module
|  |  `- Questionnaire ou consultation
|  `- Confirmation
|- Supports
|  |- Detail support
|  |- Lecture video
|  `- Téléchargement
`- Aide formateur
```

Règles :

- pas de route de gestion visible ;
- pas de termes techniques réseau ;
- pas d'admin ;
- les états fermés doivent rester consultables, pas seulement bloquants.

## Navigation formateur cible recommandée

```text
Cockpit
|- Vue d'ensemble
|- Accès élèves
|- Modules
|  |- Dashboard module
|  `- Export CSV
|- Présence
|- Réseau
|  |- Diagnostic réseau
|  |- Contrôle LAN
|  |- Projection
|  `- Configuration réseau
|- Supports
|  |- Liste formateur
|  `- Upload support
|- Sauvegarde
`- Admin avancé
```

Règles :

- cockpit = hub ;
- “Réseau” = lecture et diagnostic ;
- “Contrôle LAN” = action et orchestration ;
- “Configuration” = paramètres ;
- “Supports” = contenus pédagogiques ;
- “Admin avancé” = zone à part, jamais confondue avec le cockpit.

## Breadcrumbs attendus

### Étudiant

- `Accueil > Modules`
- `Accueil > Modules > Module X`
- `Accueil > Modules > Module X > Questionnaire`
- `Accueil > Modules > Confirmation`
- `Accueil > Supports`
- `Accueil > Supports > Support`
- `Accueil > Supports > Support > Regarder`

### Formateur

- `Accueil > Cockpit`
- `Cockpit > Module X`
- `Cockpit > Accès réseau`
- `Cockpit > Contrôle réseau local`
- `Cockpit > Configuration réseau`
- `Cockpit > Sauvegarde`
- `Cockpit > Supports`
- `Cockpit > Projection`

## Zones à garder hors navigation étudiante

- `/dashboard/*`
- `/admin/*`
- `/dashboard/export/*`
- `/dashboard/network-control/`
- `/dashboard/settings/`
- `/dashboard/backup/`

## Écarts de navigation notables

- Prototype 6 imagine des hubs et vues plus nombreux que l'existant ;
- l'application réelle garde une navigation compacte, mais certains liens
  restent concentrés dans le cockpit ;
- le réseau est déjà réparti sur trois pages distinctes, ce qui demande une
  documentation explicite pour éviter la confusion.
