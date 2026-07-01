# UX Accessibility Mobile Checklist

## But

Checklist minimale à passer avant validation d'une PR UI.

## 1. Labels

- chaque champ a un label visible ;
- le placeholder ne porte pas seul l’information ;
- les filtres ont un intitulé compréhensible.

## 2. Contrastes

- texte principal lisible sur fond clair ;
- badges warning, success et error lisibles sans dépendre seulement de la couleur ;
- liens et CTA suffisamment visibles.

## 3. Boutons et zones tactiles

- les boutons critiques sont assez grands pour un téléphone ;
- les actions proches ne provoquent pas de clic accidentel ;
- `Copier l'URL`, `Plein écran` et autres actions JS non submit gardent `type="button"`.

## 4. Focus clavier

- la navigation clavier reste visible ;
- skip-link conservé ;
- aucun piège de focus dans les pages formateur.

## 5. Messages d’erreur textuels

- une erreur n’est jamais signalée seulement par couleur ;
- le message explique quoi corriger ;
- les erreurs formulaire sont proches du champ.

## 6. Titres hiérarchisés

- un titre principal par page ;
- sous-sections lisibles ;
- la hiérarchie ne saute pas arbitrairement.

## 7. Lisibilité téléphone

- aucun écran étudiant ne demande de scroll horizontal ;
- les cartes et formulaires restent lisibles sur petit écran ;
- les listes et badges ne saturent pas la largeur.

## 8. Parcours étudiant protégé de la technique

- aucun lien admin, helper, Docker, WSL, réseau ou diagnostic n’apparaît côté étudiant ;
- heartbeat et télémétrie restent invisibles côté élève ;
- les brouillons supports restent hors surface publique.

## 9. Réseau / projection

- l’URL élèves reste lisible même sans QR ;
- la projection reste compréhensible à distance ;
- les états LAN non prêt et IP obsolète restent textuels.

## 10. Cockpit et dashboards

- les tableaux et cartes formateur gardent une lecture suffisante sur écran portable ;
- les empty states sont explicites ;
- les messages helper techniques ne masquent pas l’action principale.

## 11. Média et vidéo

- les liens `watch` et `download` sont différenciés ;
- la lecture vidéo locale reste compréhensible même sur réseau lent ;
- les métadonnées longues ne cassent pas la mise en page mobile.

## 12. Critère de sortie

Une PR UI n’est pas acceptée si un seul de ces points devient faux sur un parcours critique :

- accueil étudiant ;
- formulaire module ;
- cockpit ;
- réseau/projection ;
- supports publics.
