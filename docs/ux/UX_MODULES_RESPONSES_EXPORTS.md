# UX Modules Responses Exports

## Périmètre

Ce document couvre :

- `/modules/`
- `/modules/module-X/`
- `/module-X/`
- `/module-X/success/<id>/`
- `/dashboard/module-X/`
- `/dashboard/export/module-X.csv`
- `/dashboard/modules/<module_code>/toggle-responses/`

## Modèle UX commun aux modules

Chaque module possède quatre surfaces principales :

1. carte dans la liste modules ;
2. page détail pédagogique ;
3. questionnaire ;
4. dashboard formateur + export.

## États de séance

### 1. Session active + réponses ouvertes

Étudiant :

- badge `Réponses ouvertes`
- CTA `Commencer le questionnaire`
- formulaire envoyable

Formateur :

- badge `Réponses ouvertes`
- bouton `Fermer les réponses`
- dashboard module et export disponibles

### 2. Session active + réponses fermées

Étudiant :

- badge `Consultation seulement`
- CTA `Consulter le questionnaire`
- questions lisibles, submit désactivé

Formateur :

- badge `Réponses fermées`
- bouton `Ouvrir les réponses`

### 3. Aucune session active

Étudiant :

- badge `Indisponible`
- carte désactivée ou message d’attente
- page indisponible 503 si accès direct au questionnaire

Formateur :

- cockpit signale `Aucune session active`
- pas de toggle utile

## Parcours étudiant type

`Modules -> Detail module -> Questionnaire -> Merci`

ou

`Modules -> Detail module -> Consultation seulement`

ou

`Modules -> Indisponible`

## Parcours formateur type

`Cockpit -> Dashboard module -> Filtres -> Lecture réponses -> Export CSV`

ou

`Cockpit -> Toggle ouverture/fermeture`

## Règles UX à préserver

- le détail module doit précéder le questionnaire ;
- le statut doit être visible avant l’entrée dans le formulaire ;
- la fermeture des réponses ne doit pas supprimer la valeur pédagogique ;
- le dashboard module doit rester focalisé sur lecture et export, pas sur
  édition intrusive.

## Variantes par module

Constat :

- la structure UX est largement homogène de M2 à M8 ;
- les contenus pédagogiques et champs métier changent, mais le squelette de
  parcours reste identique.

Implication UX :

- une future refonte doit viser des composants partagés ;
- la documentation des états peut être mutualisée ;
- il faut éviter des divergences de wording inutiles entre modules.

## Exports CSV

### Rôle UX

- action formateur administrative ;
- non visible côté étudiant ;
- téléchargement direct sans étape intermédiaire.

### Contraintes

- login requis ;
- pas de page de confirmation ;
- CSV sanitize côté sécurité.

### Améliorations UX futures

- rendre les libellés d’export plus homogènes ;
- documenter plus explicitement le contenu de chaque export ;
- éviter une surcharge de liens CSV sans regroupement visuel si de nouveaux
  modules apparaissent.

## Toggle réponses

### Rôle UX

- contrôle rapide de séance ;
- ne remplace pas la gestion complète des sessions ;
- action sensible réservée au staff.

### Risques UX

- confusion entre :
  - module existant ;
  - session active ;
  - réponses ouvertes ;
- feedback de succès encore discret.

### Recommandation

- dans une future PR UI, renforcer :
  - le libellé d’état ;
  - la preuve visuelle du changement ;
  - le lien entre le toggle et le statut côté étudiant.
