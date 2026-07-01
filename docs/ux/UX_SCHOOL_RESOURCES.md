# UX School Resources

## Périmètre

Ce document couvre la couche “ressources scolaires” présente dans
l'application actuelle via :

- matières (`Subject`)
- chapitres (`Chapter`)
- classification des supports
- filtres du catalogue public

## État réel vérifié

La structure existe au niveau modèle et UX publique minimale :

- `LearningResource` peut être lié à une matière ;
- `LearningResource` peut être lié à un chapitre ;
- le catalogue public filtre par matière ;
- le catalogue public filtre par niveau ;
- le catalogue public filtre par module ;
- le détail support affiche matière et chapitre si présents.

## Ce qui est visible côté étudiant

### Catalogue public

- filtre `Matière`
- filtre `Niveau`
- badges matière sur les cartes
- métadonnées matière / chapitre dans les cartes et détails

### Ce qui n’existe pas encore

- page publique dédiée “ressources scolaires” ;
- navigation par chapitre ;
- vue cartographique complète par programme ;
- bibliothèque pédagogique indépendante des supports publiés.

## Ce qui est visible côté formateur

- classement matière/chapitre dans l’upload support ;
- affichage matière/chapitre dans le dashboard supports ;
- administration plus fine encore majoritairement en admin Django.

## Position UX dans le produit

La couche “school resources” n’est pas encore un parcours autonome.
Aujourd’hui, elle joue surtout un rôle de :

- métadonnée de tri ;
- aide au filtrage ;
- préparation d’une future structuration plus pédagogique.

## Écart avec Prototype 6

Prototype 6 ouvre l’idée d’un futur espace plus riche “par matière, niveau et
chapitre”.

L’application réelle est plus sobre :

- la taxonomie existe ;
- l’exploration autonome par cursus n’existe pas encore ;
- la médiathèque reste le conteneur principal.

## Recommandation UX

Pour les prochaines PR UI :

- ne pas promettre un “curriculum browser” complet tant qu’il n’existe pas ;
- continuer à traiter matière/chapitre comme une couche d’organisation, pas
  comme un produit séparé ;
- préparer une future navigation école/ressources seulement quand les
  contenus et besoins terrain seront assez stables.
