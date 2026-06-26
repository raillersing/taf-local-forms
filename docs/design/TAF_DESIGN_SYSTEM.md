# TAF Design System

## Source

Cette base de design system est extraite progressivement depuis
`docs/design/prototypes/Prototype_6.html`.

Prototype 6 reste une reference UX. Il n'est pas copie tel quel dans
l'application Django.

## Objectif

F035 pose une fondation CSS locale, reutilisable et progressive pour les
interfaces etudiant et formateur, sans modifier le backend ni la structure des
routes.

## Fichier CSS

Le design system est integre dans le fichier central existant :

- `static/css/app.css`

Ce choix suit Ponytail :

- reutiliser la feuille deja chargee par `templates/base.html` ;
- eviter une deuxieme feuille globale concurrente ;
- ne pas multiplier les points de chargement CSS.

## Composants disponibles

Les primitives suivantes sont disponibles ou formalisees dans `app.css` :

- buttons : `.taf-button`, `.taf-button-primary`, `.taf-button-secondary`,
  `.taf-button-ghost`, `.taf-button-block`, `.taf-button-lg`
- cards : `.taf-card`
- panels : `.taf-panel`, `.taf-panel-title`, `.taf-section-head`
- badges / pills : `.taf-badge`, `.taf-badge-success`,
  `.taf-badge-warning`, `.taf-badge-danger`, `.taf-badge-info`, `.taf-pill`
- forms : `.taf-label`, `.taf-input`, `.taf-select`, `.taf-textarea`
- alerts : `.taf-alert`, `.taf-alert-success`, `.taf-alert-warning`,
  `.taf-alert-danger`, `.taf-alert-info`
- tables : `.taf-table-wrap`, `.taf-table`
- layout / grid : `.taf-container`, `.taf-grid`, `.taf-grid-2`,
  `.taf-grid-3`, `.taf-grid-4`
- breadcrumbs / topbar base : `.taf-breadcrumbs`, `.taf-topbar`,
  `.taf-topbar-actions`, `.taf-nav-tabs`, `.taf-nav-tab`
- accessibility / mobile : `.taf-visually-hidden` et comportement mobile-first
  des boutons, grilles et topbars

## Regles

- pas de CDN ;
- pas de build frontend ;
- CSS local uniquement ;
- accessibilite preservee ;
- mobile-first pour les eleves ;
- interface formateur lisible et stable ;
- diagnostics techniques a garder dans des zones secondaires ou repliables ;
- aucun lien admin dans les parcours etudiants.

## Integration

`templates/base.html` charge deja `static/css/app.css` via `{% static %}`.

Aucune modification du template de base n'etait necessaire pour F035.

## Contraintes de F035

- aucun changement backend ;
- aucune migration ;
- aucun changement de modele, vue, URL, formulaire, export, dashboard ou
  logique anti-doublon ;
- aucune dependance runtime ajoutee.

## Prochaines etapes

- F036 : navigation etudiant / formateur
- F037 : cockpit / QR local
- F038 : mediatheque
