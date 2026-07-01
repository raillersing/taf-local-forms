# UX Trainer Journeys

## Rôle du parcours formateur

Le formateur pilote :

- l’ouverture des modules ;
- la diffusion de l’accès élèves ;
- le suivi des réponses ;
- l’export ;
- la médiathèque ;
- le réseau local ;
- la configuration et la sauvegarde ;
- les opérations avancées via admin.

## Journey T1 — Se connecter et ouvrir le cockpit

Point de départ :

- `/dashboard/`

Étapes :

1. si non connecté, écran login admin ;
2. après connexion, arrivée sur le cockpit ;
3. lecture immédiate des sections et indicateurs.

Attendu UX :

- cockpit perçu comme hub ;
- accès aux tâches critiques en un écran ;
- pas besoin d’aller dans l’admin pour les gestes de séance.

## Journey T2 — Vérifier l’accès élèves

Point de départ :

- section `Accès élèves` du cockpit

Étapes :

1. le formateur lit l’URL recommandée ;
2. il voit si l’IP vient de :
   - la requête LAN ;
   - la configuration ;
   - la détection candidate ;
3. il copie l’URL ou bascule en projection.

Attendu UX :

- éviter les faux positifs ;
- si l’IP est absente, le cockpit doit orienter vers réseau/configuration ;
- ne jamais conseiller `localhost` aux élèves.

## Journey T3 — Ouvrir ou fermer les réponses d’un module

Point de départ :

- section `Modules` du cockpit

Étapes :

1. le formateur repère les badges d’état ;
2. il ouvre le dashboard module si besoin ;
3. il clique sur le toggle d’ouverture/fermeture.

Attendu UX :

- action réversible ;
- lisibilité immédiate du nouvel état ;
- très faible ambiguïté entre “session active” et “réponses ouvertes”.

## Journey T4 — Suivre les réponses et les scores

Point de départ :

- `/dashboard/module-X/`

Étapes :

1. lecture des cartes de stats ;
2. usage des filtres classe/groupe si disponibles ;
3. lecture de la table des réponses ;
4. lecture de la progression des activités ;
5. export CSV au besoin.

Attendu UX :

- cohérence entre modules ;
- filtres toujours en haut ;
- export facilement trouvable ;
- empty state explicite si aucune réponse.

## Journey T5 — Télécharger un export CSV

Point de départ :

- cockpit ou dashboard module

Étapes :

1. clic sur un lien d’export ;
2. téléchargement immédiat.

Attendu UX :

- pas de détour inutile ;
- vocabulaire simple ;
- cohérence forte entre nom du module et nom de l’action.

## Journey T6 — Vérifier le réseau local

Point de départ :

- `/dashboard/network/`

Étapes :

1. lire l’adresse recommandée ;
2. vérifier l’état :
   - IP actuelle ;
   - IP configurée ;
   - IP recommandée ;
   - source ;
   - statut ;
3. ouvrir si besoin les liens élèves ou formateur ;
4. décider de passer par configuration ou contrôle LAN.

Attendu UX :

- réseau = page de lecture et de diagnostic ;
- ne pas mélanger avec les actions lourdes du helper ;
- avertissements visibles sans être paniquants.

## Journey T7 — Corriger la configuration réseau

Point de départ :

- `/dashboard/settings/`

Étapes :

1. lire les champs éditables ;
2. injecter éventuellement l’IP détectée ;
3. enregistrer une valeur ;
4. relancer Docker si nécessaire.

Attendu UX :

- page clairement “paramètres” ;
- ne jamais exposer `SECRET_KEY` ;
- validation des champs réseau stricte ;
- aide contextuelle par variable.

## Journey T8 — Orchestrer le LAN avec le helper

Point de départ :

- `/dashboard/network-control/`

Étapes :

1. vérifier que l’on est bien sur `localhost:8010` ;
2. lire le statut helper ;
3. exécuter l’action pertinente :
   - sync ;
   - actualiser ;
   - tester URL ;
   - copier URL ;
   - désactiver LAN ;
   - redémarrer app ;
4. lire le résultat JSON et le statut global.

Attendu UX :

- page orientée opérations ;
- fort guidage pas à pas ;
- aucune ambiguïté sur la dépendance au helper PowerShell ;
- garde-fou fort quand la page est ouverte via l’URL LAN.

## Journey T9 — Utiliser la projection salle

Point de départ :

- `/dashboard/projection/`

Étapes :

1. ouvrir la page ;
2. afficher l’URL élève en grand ;
3. générer/afficher le QR local ;
4. déclencher le plein écran ;
5. revenir au cockpit.

Attendu UX :

- très peu de distraction ;
- lisibilité forte à distance ;
- fallback correct si fullscreen indisponible.

## Journey T10 — Gérer les supports pédagogiques

Point de départ :

- `/dashboard/supports/`

Étapes :

1. lire le volume brouillons/publiés ;
2. voir matière, chapitre, type, module, source ;
3. ouvrir l’upload ;
4. vérifier le rendu public si publié.

Attendu UX :

- lecture rapide du statut ;
- brouillon/public immédiatement visible ;
- liens détail/watch/download clairs ;
- admin réservé aux corrections avancées.

## Journey T11 — Ajouter un support

Point de départ :

- `/dashboard/supports/upload/`

Étapes :

1. remplir titre, type, module, fichier ;
2. ajouter matière/chapitre si utile ;
3. renseigner source et licence ;
4. décider brouillon ou publié ;
5. enregistrer.

Attendu UX :

- upload = formulaire pédagogique et non technique ;
- messages très clairs pour poids, format et cohérence matière/chapitre ;
- texte rappelant que le support reste privé tant que non publié.

## Journey T12 — Sauvegarder et vérifier la base active

Point de départ :

- `/dashboard/backup/`

Étapes :

1. voir le moteur actif ;
2. lire la commande de backup ;
3. comprendre les volumes à préserver ;
4. éviter les commandes destructives.

Attendu UX :

- page très didactique ;
- posture prudente ;
- pas de bouton destructif ;
- rappel constant anti `down -v`.

## Journey T13 — Basculer vers l’admin avancé

Point de départ :

- cockpit / navigation formateur

Étapes :

1. clic `Admin avancé` ;
2. ouverture de Django admin ;
3. exécution d’opérations non encore couvertes par le cockpit.

Attendu UX :

- admin assumé comme zone experte ;
- séparation claire avec l’UX terrain ;
- pas de mélange de ton entre cockpit et admin.

## Recommandations prioritaires côté formateur

- documenter plus fortement la différence entre réseau, configuration et
  contrôle LAN ;
- rendre plus homogènes les actions “ouvrir”, “voir”, “exporter” ;
- densifier le cockpit uniquement si les parcours restent scannables ;
- garder l’admin comme échappatoire, pas comme flux normal de séance.
