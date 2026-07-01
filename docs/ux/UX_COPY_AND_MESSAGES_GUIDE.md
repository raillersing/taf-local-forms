# UX Copy And Messages Guide

## But

Normaliser le texte UX avant les prochaines PR UI.

## Principes

- français simple ;
- phrases courtes ;
- vocabulaire non technique côté étudiant ;
- ton opérationnel, calme et précis côté formateur ;
- toujours préférer une consigne actionnable à une explication abstraite.

## 1. Consignes étudiant

- style attendu : direct, rassurant, concret.
- format recommandé :
  - une action ;
  - un résultat attendu ;
  - un rappel si erreur fréquente.

Exemples cibles :

- `Choisis le module demandé par le formateur.`
- `Entre exactement 2 chiffres.`
- `Lis les questions puis envoie une seule réponse.`

## 2. Messages succès

- succès étudiant :
  - `Réponse enregistrée. Merci.`
- succès formateur :
  - `Action terminée.`
  - `Valeur enregistrée.`
  - `Support ajouté avec succès.`

Règle :

- pas de célébration excessive ;
- pas de jargon ;
- confirmer simplement l’effet utile.

## 3. Doublon

Message cible :

- `Une réponse existe déjà pour cet identifiant dans cette session.`
- aide recommandée :
  - `Si tu penses qu'il y a une erreur, appelle le formateur.`

À éviter :

- `duplicate entry`
- `integrity error`
- `enregistrement impossible`

## 4. Session fermée ou indisponible

Messages cibles :

- `Les réponses sont fermées pour ce module.`
- `Tu peux encore consulter le questionnaire.`
- `Aucune session active pour ce module.`

## 5. Erreur réseau

Messages formateur cibles :

- `Adresse LAN non configurée.`
- `L'adresse actuelle diffère de l'IP configurée.`
- `Le test LAN n'a pas abouti. Vérifie le Wi-Fi, le pare-feu et l'IP utilisée.`

Règle :

- citer l’étape suivante utile ;
- éviter les formulations purement système.

## 6. Docker / WSL indisponible

Messages formateur cibles :

- `Docker n'est pas disponible sur cet environnement.`
- `Vérifie l'intégration WSL de Docker Desktop avant de relancer le test.`
- `Le helper LAN est indisponible depuis cette session.`

Règle :

- dire explicitement si l’état est bloquant ou non ;
- distinguer `WARN` et `FAIL` quand l’application HTTP répond déjà.

## 7. Support brouillon

Messages cibles :

- côté public : aucun message, accès refusé en 404
- côté formateur :
  - `Brouillon`
  - `Ce support n'est pas visible par les élèves.`

## 8. Fichier invalide

Messages cibles :

- `Format non autorisé.`
- `Le fichier dépasse la taille maximale autorisée.`
- `Le chapitre choisi ne correspond pas à la matière.`

Règle :

- si possible, citer la contrainte utile : type, poids, cohérence.

## 9. Vidéo lente

Messages cibles :

- `La vidéo peut prendre un moment à démarrer sur ce téléphone.`
- `Attends quelques secondes puis réessaie si besoin.`

Règle :

- ne pas promettre un streaming fluide ;
- rappeler le contexte local.

## 10. Export vide

Messages cibles :

- `Aucune réponse à exporter pour ce module.`
- `Ouvre la session ou attends les premières réponses avant de relancer l'export.`

## 11. Action formateur réussie / échouée

Succès :

- `Action terminée.`
- `Configuration mise à jour.`
- `URL copiée.`

Erreur :

- `Copie indisponible sur ce navigateur.`
- `Plein écran indisponible sur cet appareil.`
- `Impossible d'activer le plein écran.`
- `Le helper ne répond pas.`

## 12. Formulations à éviter

- termes anglais non nécessaires ;
- messages purement techniques ;
- `Erreur inconnue` sans contexte ;
- injonctions ambiguës ;
- phrases longues côté étudiant.

## 13. Décision éditoriale UX v1

Le texte UX v1 est considéré assez mûr si :

- les parcours étudiant restent compréhensibles pour un lycéen ;
- les messages formateur restent exploitables sans lire le code ;
- les messages réseau et projection restent cohérents avec la réalité terrain WSL/LAN.
