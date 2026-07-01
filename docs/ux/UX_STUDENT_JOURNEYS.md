# UX Student Journeys

## Principes

Le parcours étudiant doit rester :

- simple ;
- lisible sur téléphone ;
- sans jargon technique ;
- sans exposition du back-office ;
- compatible avec trois états de séance :
  - ouverte ;
  - consultation seulement ;
  - indisponible.

## Journey S1 — Entrer dans l’application

Point de départ :

- `/`

Étapes :

1. l’élève voit deux entrées distinctes : étudiant et formateur ;
2. il clique `Entrer côté étudiant` ;
3. il arrive sur `/modules/`.

Attendu UX :

- hiérarchie très claire ;
- aucun doute sur la bonne entrée ;
- rappel implicite que les outils formateur ne sont pas pour lui.

Risques :

- confusion entre “module” et “questionnaire” ;
- clic sur “Aide formateur” non utile à l’élève.

## Journey S2 — Choisir un module ouvert

Point de départ :

- `/modules/`

Étapes :

1. l’élève parcourt les cartes modules ;
2. il repère le badge :
   - `Réponses ouvertes`
   - `Consultation seulement`
   - `Indisponible`
3. il clique `Voir le module`.

Attendu UX :

- comprendre avant le clic si l’envoi est possible ;
- ne pas forcer l’élève à découvrir l’état seulement après ouverture.

État critique :

- les modules non disponibles doivent rester clairement désactivés.

## Journey S3 — Comprendre le module avant de répondre

Point de départ :

- `/modules/module-X/`

Étapes :

1. lecture du titre et du badge d’état ;
2. lecture du bloc pédagogique ;
3. lecture de la synthèse et des repères ;
4. clic sur :
   - `Commencer le questionnaire` si ouvert ;
   - `Consulter le questionnaire` si fermé.

Attendu UX :

- le détail module doit réduire l’angoisse du questionnaire ;
- le contenu pédagogique doit servir d’amorce, pas de surcharge.

## Journey S4 — Répondre au questionnaire

Point de départ :

- `/module-X/`

Étapes communes :

1. l’élève remplit ses informations ;
2. il suit les sections du formulaire ;
3. il clique `Envoyer`.

Attendu UX :

- structure en blocs ;
- ordre pédagogique logique ;
- message clair pour le numéro à 2 chiffres ;
- action finale visible en bas de page ;
- présence heartbeat invisible comme mécanique, sans perturber.

## Journey S5 — Cas “réponses fermées”

Point de départ :

- questionnaire ouvert en mode consultation

Étapes :

1. l’élève voit l’alerte de fermeture ;
2. il peut encore lire le contenu ;
3. il ne voit pas de bouton d’envoi actif.

Attendu UX :

- ne pas faire croire que l’envoi est encore possible ;
- garder un usage pédagogique de lecture.

Message actuel :

- `Les réponses sont fermées pour ce module.`

## Journey S6 — Cas “session indisponible”

Point de départ :

- accès direct à `/module-X/` sans session active

Étapes :

1. l’élève tombe sur la page indisponible ;
2. il comprend que le formateur doit activer la séance.

Attendu UX :

- message court ;
- pas de jargon ;
- retour facile vers `Modules`.

## Journey S7 — Corriger une erreur de saisie

Cas couverts :

- numéro élève invalide ;
- champ requis vide ;
- doublon de réponse.

Attendu UX :

- erreur au plus près du champ ;
- texte simple ;
- ton non accusateur ;
- conservation maximale des autres réponses déjà saisies.

Messages critiques :

- `Entre exactement 2 chiffres`
- `Une réponse existe déjà pour ce numéro`

## Journey S8 — Confirmation après envoi

Point de départ :

- redirect vers `/module-X/success/<id>/`

Étapes :

1. l’élève voit `Merci` ;
2. il comprend que la réponse est enregistrée ;
3. il peut quitter la page sans douter.

Attendu UX :

- confirmation courte et rassurante ;
- pas de surcharge ;
- éviter de proposer trop d’actions concurrentes.

## Journey S9 — Utiliser la médiathèque publique

Point de départ :

- `/supports/`

Étapes :

1. l’élève ouvre le catalogue ;
2. il filtre éventuellement par matière, niveau, module ;
3. il ouvre un détail support ;
4. il télécharge ou regarde une vidéo.

Attendu UX :

- aucun brouillon visible ;
- filtres simples ;
- distinction claire document / vidéo ;
- fallback téléchargement pour les vidéos lentes.

## Journey S10 — Regarder une vidéo publiée

Point de départ :

- `/supports/<slug>/watch/`

Étapes :

1. ouverture du player HTML5 ;
2. lecture locale ;
3. si besoin, téléchargement du MP4.

Attendu UX :

- explication réseau simple ;
- pas d’autoplay ;
- bouton de secours visible.

## Recommandations prioritaires côté étudiant

- unifier encore les messages de fermeture / indisponibilité ;
- rendre plus explicite le passage “détail module” → “questionnaire” ;
- garder les formulaires en blocs courts avec respiration visuelle ;
- éviter toute montée en complexité du menu étudiant ;
- rendre la médiathèque encore plus lisible pour documents vs vidéos.
