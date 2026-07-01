# UX Media Library

## Périmètre

Ce document couvre :

- `/supports/`
- `/supports/<slug>/`
- `/supports/<slug>/watch/`
- `/supports/<slug>/download/`
- `/dashboard/supports/`
- `/dashboard/supports/upload/`

## Promesse UX actuelle

La médiathèque locale fournit :

- un catalogue public filtrable ;
- des détails clairs pour chaque ressource ;
- des téléchargements directs ;
- une lecture locale des vidéos publiées ;
- une zone formateur pour brouillons et uploads ;
- une séparation stricte entre public et brouillon.

## Public vs formateur

### Côté étudiant/public

- seuls les supports publiés apparaissent ;
- les brouillons sont invisibles ;
- les détails brouillon retournent `404` ;
- les vidéos publiées peuvent être regardées ;
- les téléchargements sont autorisés sur les ressources publiées.

### Côté formateur

- tous les supports apparaissent ;
- distinction brouillon / publié ;
- accès à l’upload ;
- liens admin pour besoins avancés.

## Catalogue public

### Objectifs UX

- retrouver vite un support ;
- filtrer sans expertise ;
- comprendre type, module, matière, source.

### Éléments visibles

- badges type ;
- badges module ;
- badge matière ;
- description ;
- métadonnées ;
- actions :
  - voir le détail ;
  - regarder ;
  - télécharger.

## Détail support

### Objectif UX

- donner du contexte avant l’action finale ;
- clarifier licence, source, matière, chapitre ;
- éviter le téléchargement aveugle.

### Actions

- télécharger ;
- regarder la vidéo si applicable ;
- revenir au catalogue.

## Lecture vidéo locale

### Objectif UX

- lecture simple, locale, sans player externe ;
- fallback téléchargement si réseau lent.

### Contraintes terrain

- MP4 uniquement ;
- pas de streaming adaptatif ;
- le Wi-Fi de classe peut être un goulot ;
- le message d’aide doit rester court.

## Dashboard supports formateur

### Objectif UX

- donner une vue simple des ressources ;
- distinguer le statut de publication ;
- offrir un point d’entrée vers l’upload ;
- éviter de tout renvoyer à l’admin.

### Limites UX actuelles

- pas encore de filtres dashboard ;
- édition avancée encore en admin ;
- table fonctionnelle mais moins guidée que Prototype 6.

## Upload support

### Objectif UX

- créer rapidement un document ou une vidéo pédagogique ;
- classer si utile ;
- décider brouillon ou publié.

### Points forts actuels

- formulaire clair ;
- aide sur tailles et formats ;
- rappel brouillon/public ;
- validation serveur robuste ;
- gestion matière/chapitre déjà présente.

### Frictions UX actuelles

- relation matière/chapitre pas encore très guidée ;
- aucun aperçu de fichier ;
- aucune édition dashboard après création ;
- pas de workflow batch.

## Décisions UX à conserver

- brouillon non public par défaut ;
- lecture vidéo HTML5 simple ;
- détails support avant téléchargement ;
- aucun CDN ;
- vocabulaire pédagogique plutôt que technique.

## Recommandations futures

- ajouter un meilleur guidage “document vs vidéo” ;
- clarifier encore le statut brouillon/public dans la liste formateur ;
- introduire plus tard un filtre dashboard sans basculer dans une interface
  trop lourde ;
- préserver la sobriété pour la salle de classe.
