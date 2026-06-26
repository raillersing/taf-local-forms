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
- `/dashboard/supports/upload/`

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

## 7. Upload formateur F039M

- la route `/dashboard/supports/upload/` est protégée par login ;
- le formulaire crée directement un `LearningResource` sans nouvelle migration ;
- les formats autorisés sont : PDF, DOCX, PPTX, PNG, JPG, JPEG et TXT ;
- la taille maximale par fichier est fixée à 20 MB ;
- le fichier est obligatoire ;
- le support peut être enregistré en brouillon ou publié ;
- le slug est généré automatiquement à partir du titre avec suffixe unique si besoin ;
- les extensions dangereuses ou inconnues sont refusées côté serveur.

## 8. Limites sécurité F039M

- pas de scan antivirus externe dans cette phase ;
- pas de détection MIME avancée avec dépendance externe ;
- pas de remplacement de fichier, suppression ou édition avancée ;
- la vidéo locale reste hors périmètre.

## 9. Vidéo locale F040M

- la route publique vidéo est `/supports/<slug>/watch/` ;
- seul le format MP4 est accepté pour la lecture vidéo MVP ;
- la taille maximale d'une vidéo MP4 est fixée à 80 MB ;
- le lecteur utilise HTML natif : `<video controls preload="metadata">` ;
- aucun autoplay n'est activé ;
- les brouillons vidéo restent non publics ;
- un lien de téléchargement de secours reste disponible ;
- aucun streaming adaptatif, transcodage ou player JavaScript externe n'est ajouté.

## 10. Limites terrain vidéo

- le Wi-Fi de classe peut devenir lent si la vidéo est lourde ;
- il faut tester la lecture sur Android et laptop avant séance ;
- il reste conseillé de compresser les vidéos avant la séance ;
- le téléchargement local peut être préférable si la lecture directe saccade.

## 11. Limites F038M/F039M/F040M

- pas encore d'UX complète d'upload formateur ;
- pas encore de matières scolaires structurées ;
- l'administration initiale des supports passe encore en partie par l'admin Django.

## 12. Prochaines étapes

- amélioration de l'édition support ;
- F041M : matières scolaires
- tests terrain vidéo
