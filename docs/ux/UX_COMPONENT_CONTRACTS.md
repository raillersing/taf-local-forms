# UX Component Contracts

## But

Définir les contrats minimaux des composants UI avant toute nouvelle PR design.

Un contrat composant précise :

- son rôle ;
- ses variantes admises ;
- ses contraintes d’usage ;
- les erreurs à éviter.

## 1. Boutons

- Rôle : déclencher une action claire, visible, univoque.
- Variantes admises : primaire, secondaire, ghost, danger limité au back-office contrôlé.
- Contrat :
  - un bouton principal par zone d’action ;
  - libellé verbe + objet clair ;
  - `type="submit"` seulement pour un vrai envoi de formulaire ;
  - `type="button"` pour copie, projection, helper JS, toggles non submit.
- Refus :
  - deux primaires concurrents dans une même carte ;
  - libellé vague (`Valider`, `OK`) sans contexte ;
  - bouton technique visible côté étudiant.

## 2. Cartes

- Rôle : regrouper un objectif unique.
- Contrat :
  - un titre clair ;
  - un sous-texte bref ;
  - une action principale maximum ;
  - espacement lisible sur mobile.
- Refus :
  - carte fourre-tout mélangeant diagnostic, action et historique sans hiérarchie.

## 3. Badges / Pills

- Rôle : signaler un état rapide.
- États admis :
  - succès/ouvert/publié ;
  - avertissement/consultation/brouillon ;
  - indisponible/fermé si nécessaire.
- Contrat :
  - un badge ne remplace jamais un texte explicatif ;
  - couleur + texte toujours présents.

## 4. Formulaires

- Rôle : collecter une réponse ou configurer un paramètre.
- Contrat :
  - label visible pour chaque champ ;
  - message d’erreur textuel proche du champ ;
  - aide concise si une contrainte n’est pas évidente ;
  - bouton submit identifiable sans ambiguïté ;
  - CSRF sur chaque POST Django.
- Refus :
  - placeholder comme seul label ;
  - erreur seulement en couleur ;
  - jargon technique côté élève.

## 5. Filtres

- Rôle : réduire un catalogue sans perdre l’utilisateur.
- Contrat :
  - filtres regroupés et identifiables ;
  - résultat vide distingué d’un catalogue globalement vide ;
  - retour visuel sur les filtres actifs.

## 6. Tableaux

- Rôle : lecture dense côté formateur.
- Contrat :
  - colonnes stables ;
  - intitulés explicites ;
  - lecture acceptable sur écran portable ;
  - empty state textuel si aucune ligne.
- Refus :
  - tableau incompréhensible sur mobile sans alternative ;
  - colonnes techniques non expliquées.

## 7. Breadcrumbs

- Rôle : rappeler la position dans le produit.
- Contrat :
  - présents sur les pages formateur structurantes ;
  - dernier niveau non cliquable ;
  - libellés courts.
- Refus :
  - breadcrumb plus verbeux que le titre de page.

## 8. Details / Diagnostics

- Rôle : exposer l’information technique sans polluer le flux principal.
- Contrat :
  - diagnostics avancés dans `details`, cartes secondaires ou blocs dédiés ;
  - le premier niveau de lecture reste compréhensible sans ouvrir le détail.
- Refus :
  - dump technique brut au-dessus de l’action principale.

## 9. Alertes

- Rôle : signaler un état important ou bloquant.
- Contrat :
  - succès : confirmer une action terminée ;
  - warning : prévenir sans paniquer ;
  - erreur : dire ce qui bloque et quoi faire ensuite.
- Refus :
  - alerte sans prochaine étape ;
  - alerte rouge pour un simple état informatif.

## 10. Empty States

- Rôle : expliquer l’absence de contenu.
- Contrat :
  - dire pourquoi il n’y a rien ;
  - proposer l’étape suivante si utile ;
  - distinguer vide global, vide filtré, vide temporaire.

## 11. États d’erreur

- Rôle : éviter l’ambiguïté et limiter la charge cognitive.
- Contrat :
  - message court ;
  - cause lisible ;
  - action conseillée si possible ;
  - pas de stack trace ni de jargon côté étudiant.

## 12. Contrats par zones sensibles

### Réseau / helper

- les résultats techniques détaillés restent derrière une couche de lecture expert ;
- les actions helper n’apparaissent jamais dans le parcours étudiant ;
- `localhost` doit être rappelé quand il conditionne le succès de l’action.

### Projection

- la carte projection doit rester lisible à distance ;
- l’URL est toujours lisible même sans QR ;
- les actions JS restent secondaires par rapport à l’information principale.

### Supports

- `Publié` et `Brouillon` doivent être immédiatement distinguables ;
- document, vidéo et téléchargement doivent rester reconnaissables sans interprétation.
