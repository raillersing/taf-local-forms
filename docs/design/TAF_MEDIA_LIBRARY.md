# TAF Media Library

## 1. Objectif médiathèque locale

F038M pose une première fondation de médiathèque locale pour TAf Local Forms.
Cette phase couvre les documents pédagogiques publiés, leur catalogue public et
un dashboard formateur minimal.

## 2. Routes ajoutées

- `/supports/`
- `/supports/<slug>/`
- `/supports/<slug>/download/`
- `/dashboard/supports/`

## 3. Modèle `LearningResource`

Le modèle stocke :

- titre
- slug unique
- description
- type de support
- numéro de module optionnel
- fichier
- source
- licence
- statut publié/brouillon
- dates de création et mise à jour

## 4. Visibilité publié / brouillon

- un support brouillon n'apparaît pas dans le catalogue public ;
- un détail brouillon retourne `404` côté public ;
- un téléchargement brouillon retourne `404` côté public ;
- le dashboard formateur liste tous les supports.

## 5. Gestion fichiers

- `MEDIA_URL = "/media/"`
- `MEDIA_ROOT = BASE_DIR / "media"`
- en développement, les médias sont servis uniquement en `DEBUG`
- un volume Docker persistant `taf_local_forms_media` est monté sur `/app/media`
- les fichiers runtime restent hors Git

## 6. Sécurité

- le dashboard supports est protégé par authentification ;
- les brouillons restent non publics ;
- les champs source et licence sont prévus pour tracer l'origine des documents ;
- aucun secret ne doit être stocké dans les fichiers médias.

## 7. Limites F038M

- pas encore d'UX complète d'upload formateur ;
- pas encore de vidéo locale ;
- pas encore de matières scolaires structurées ;
- l'administration initiale des supports passe surtout par l'admin Django.

## 8. Prochaines étapes

- F039M : upload formateur
- F040M : vidéo locale
- F041M : matières scolaires
