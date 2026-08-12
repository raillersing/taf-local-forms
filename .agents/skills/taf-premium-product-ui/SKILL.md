---
name: taf-premium-product-ui
description: Concevoir et implémenter les interfaces premium de TAf Local Forms dans Django, CSS local et JavaScript minimal, pour les parcours formateur, étudiant, Cockpit, réseau, modules et supports, en combinant hiérarchie éditoriale, identité de marque, lisibilité terrain, responsive et accessibilité.
---

# TAf Premium Product UI

Utiliser ce skill pour toute évolution de template, CSS, composant, navigation,
état ou parcours utilisateur dans TAf Local Forms. Il remplace Prototype 6
comme référence de conception active. Prototype 6 reste une archive de
traçabilité, pas une maquette à recopier.

## Workflow obligatoire

1. Examiner l’écran réel, la route Django, le rôle utilisateur et le parcours
   amont/aval avant de modifier le code.
2. Identifier une action principale et ordonner l’information autour d’elle.
3. Définir la composition, la densité, le rythme et la hiérarchie avant les
   détails décoratifs.
4. Réutiliser les routes nommées, tokens CSS, templates et composants locaux.
5. Préserver le rendu serveur Django, le fonctionnement hors ligne et la
   séparation étudiant/formateur.
6. Implémenter tous les états pertinents : normal, vide, chargement, succès,
   attention, erreur et information non confirmée.
7. Ajouter les retours d’action et les micro-interactions uniquement lorsqu’ils
   clarifient une transition. Respecter `prefers-reduced-motion`.
8. Vérifier clavier, focus, zoom 200 %, 360 px minimum, tactile et contraste.
9. Reconstruire l’application avant d’interpréter un résultat visuel runtime.

## Direction visuelle TAf

S’inspirer des interfaces éditoriales et des sites primés pour leur composition,
leur typographie, leur espace et leur identité, sans copier leurs effets
expérimentaux. Appliquer :

- marine profond comme ancrage institutionnel ;
- blanc et bleu clair pour la lecture ;
- jaune comme accent d’action ou d’attention, jamais comme décoration massive ;
- titres expressifs mais lisibles en français ;
- hiérarchie forte et espaces généreux sur les pages d’accueil ;
- densité contrôlée sur les écrans de données et de diagnostic ;
- surfaces ouvertes, séparateurs et sections éditoriales pour éviter les
  mosaïques de cartes uniformes ;
- ombres discrètes, bordures nettes et alignements optiques ;
- mouvements courts, locaux et désactivables.

Le premium signifie ici une interface distinctive, calme, rapide, lisible et
rassurante pendant une séance. Il ne signifie pas ajouter du WebGL, une
dépendance externe, un scroll détourné ou une animation qui retarde une action.

## Contraintes produit

- Ne pas créer de SPA, de nouvelle dépendance frontend ou de CDN runtime.
- Conserver les URL, protections d’authentification et formulaires existants.
- Ne jamais embellir un état non vérifié : afficher `Non confirmé` lorsqu’il
  manque une preuve.
- Ne pas mélanger les métriques élèves, soumissions, réponses et scores.
- Garder les diagnostics techniques dans des panneaux secondaires lorsque leur
  détail n’est pas nécessaire à l’action immédiate.
- Maintenir un parcours étudiant simple et exempt de liens dashboard, réseau,
  export ou administration.
- Garder une action principale claire par page.

## Références ciblées

Lire uniquement la référence nécessaire au travail :

- [product-context.md](references/product-context.md) pour le terrain, les
  rôles et les contraintes de fonctionnement ;
- [visual-direction.md](references/visual-direction.md) pour la composition,
  les tokens et la hiérarchie premium ;
- [interaction-accessibility.md](references/interaction-accessibility.md) pour
  les états, le responsive, le clavier et le mouvement.

## Validation de sortie

Avant de déclarer une interface terminée, confirmer :

- l’action principale est identifiable sans lire toute la page ;
- les données et états affichés sont issus d’une source réelle ;
- les libellés sont courts, cohérents et compréhensibles ;
- la page fonctionne à 360 px et à 200 % de zoom sans perte d’action ;
- le focus est visible et l’ordre clavier conserve le sens du parcours ;
- le mode mouvement réduit ne perd aucune information ;
- les pages protégées le restent ;
- les tests et la reconstruction runtime ont été exécutés ou explicitement
  signalés comme non exécutés.
