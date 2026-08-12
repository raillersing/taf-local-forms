---
name: taf-product-ui-review
description: Auditer en lecture seule les interfaces TAf Local Forms et les parcours formateur ou étudiant avec preuves, sévérité, critères terrain, responsive, accessibilité, cohérence visuelle et exactitude des états et données.
---

# TAf Product UI Review

Utiliser ce skill avant une implémentation UI importante, après un lot visuel
ou lorsqu’un utilisateur signale qu’un écran est confus, désordonné, premium
mais peu pratique, ou incohérent avec les données réelles. Ce skill est
strictement en lecture seule : il ne modifie aucun fichier produit.

## Méthode d’audit

1. Identifier la route, le rôle, le contexte de séance et la tâche attendue.
2. Lire le template, la vue, les CSS et les tests directement concernés.
3. Vérifier le parcours depuis l’entrée jusqu’à la réussite ou l’erreur.
4. Examiner la hiérarchie : orientation, titre, état essentiel, action
   principale, détails secondaires.
5. Vérifier la cohérence des labels, des états, des métriques et des messages.
6. Évaluer ordinateur, tablette, 360 px minimum, clavier, focus et zoom 200 %.
7. Contrôler les contraintes TAf : hors ligne, LAN, auth, séparation des rôles,
   données non confirmées et protection des informations élèves.
8. Comparer au design system local et à la direction premium TAf, jamais à une
   préférence esthétique isolée.

## Domaines de contrôle

- architecture de l’information et navigation ;
- charge cognitive et repérage de la prochaine action ;
- composition éditoriale, typographie, espace et contraste ;
- répétition excessive des cartes, badges ou actions ;
- responsive et absence de défilement horizontal inutile ;
- clavier, focus, intitulés, landmarks et ordre de lecture ;
- états vide, attente, succès, erreur et `Non confirmé` ;
- cohérence entre chiffres affichés, source et définition métier ;
- messages d’erreur orientés résolution ;
- sécurité UX des imports, sauvegardes et opérations sensibles ;
- absence de CDN ou de dépendance Internet pendant la classe.

## Sévérité

- **Bloquant** : parcours impossible, auth contournable, données trompeuses,
  action destructive non maîtrisée ou problème majeur d’accessibilité.
- **Élevée** : tâche principale difficile, confusion probable en classe,
  information réseau non fiable ou rupture responsive importante.
- **Moyenne** : incohérence de hiérarchie, libellé ambigu, état incomplet ou
  défaut récurrent d’ergonomie.
- **Faible** : finition visuelle, alignement ou amélioration non bloquante.

Ne pas classer une préférence visuelle comme un défaut sans preuve d’impact.
Ne pas considérer une donnée correcte sans identifier sa source et sa définition.

## Format de restitution

Commencer par un verdict unique : `APPROVE`, `REQUEST_CHANGES` ou `BLOCK`.
Pour chaque constat, fournir :

```text
Gravité : Bloquant | Élevée | Moyenne | Faible
Preuve : fichier, route, état ou scénario observé
Impact : conséquence pour le formateur, l’élève ou le terrain
Recommandation : changement ciblé et réutilisable
Validation : test ou parcours permettant de confirmer la correction
```

Terminer par :

- les points non confirmés ;
- les éléments hors périmètre ;
- les fichiers probablement concernés par une implémentation future ;
- une recommandation de lot minimal, sans modifier le code.

## Références ciblées

- [review-checklist.md](references/review-checklist.md) pour la grille détaillée
  et les scénarios formateur/étudiant ;
- [verdict-template.md](references/verdict-template.md) pour la restitution
  homogène des audits.
