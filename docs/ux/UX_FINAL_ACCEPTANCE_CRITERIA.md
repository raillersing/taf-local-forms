# UX Final Acceptance Criteria

## But

Transformer les audits UX v1 en critères concrets de validation pour toute PR UI.

Un écran ou un lot UI n'est accepté que si :

- il respecte les parcours et actions décrits dans `docs/ux/`;
- il ne dégrade ni auth, ni réseau local, ni anti-doublon, ni médiathèque ;
- il améliore la lisibilité réelle pour la classe, sur téléphone élève et poste formateur.

## Statuts

- `DONE` : critère satisfait et vérifiable dans l'interface réelle
- `PARTIAL` : base présente, amélioration encore attendue
- `FUTURE` : volontairement reporté hors UX v1

## 1. Étudiant

### Accueil et entrée

- `DONE` : l’accueil sépare clairement `Entrer côté étudiant` et `Ouvrir le cockpit formateur`.
- `DONE` : aucun lien dashboard, réseau, admin, helper ou diagnostic n’apparaît dans le parcours étudiant.
- `DONE` : les CTA principaux restent compréhensibles sur téléphone sans zoom horizontal.

### Catalogue modules

- `DONE` : chaque module affiche un état compréhensible (`ouvert`, `consultation`, `indisponible`).
- `DONE` : le CTA d’entrée dans un module correspond à l’état réel de la session.
- `PARTIAL` : les libellés `voir`, `commencer`, `consulter` doivent encore être harmonisés dans un lot UI dédié.

### Formulaires et réponses

- `DONE` : les champs obligatoires et erreurs de validation sont textuels, proches du champ concerné.
- `DONE` : l’anti-doublon reste explicite et ne pousse pas l’élève à contourner le système.
- `DONE` : une session fermée reste consultable sans permettre l’envoi.
- `PARTIAL` : les états `merci`, `doublon` et `indisponible` doivent encore gagner en hiérarchie visuelle.

## 2. Formateur

### Cockpit

- `DONE` : `/dashboard/` reste la porte d’entrée unique des outils formateur.
- `DONE` : le cockpit reste protégé par login.
- `DONE` : les accès réseau, projection, supports et exports restent visibles sans exposer les outils staff aux élèves.
- `PARTIAL` : la densité visuelle du cockpit doit encore être allégée dans un lot UI spécifique.

### Dashboards modules et exports

- `DONE` : les pages modules permettent lecture des réponses, export CSV et pilotage d’ouverture.
- `DONE` : l’export vide ou peu rempli ne doit jamais produire d’interface ambiguë.
- `PARTIAL` : les états vides de dashboards modules doivent être plus distinctifs.

## 3. Réseau / Projection

### Réseau

- `DONE` : `/dashboard/network/` reste la page de lecture et diagnostic.
- `DONE` : la page explicite que l’IP utile est l’IP de la machine, pas une IP WSL ou Docker.
- `DONE` : les messages réseau restent compréhensibles par un formateur non développeur.

### Network Control

- `DONE` : `/dashboard/network-control/` reste distincte de `network` et `settings`.
- `DONE` : la page rappelle explicitement l’usage `localhost`.
- `DONE` : les diagnostics techniques détaillés restent dans des blocs expert, pas dans le parcours étudiant.
- `PARTIAL` : la hiérarchie des retours helper (`helper absent`, `timeout`, `sync ok`, `restart fail`) reste à mieux scénariser visuellement.

### Projection

- `DONE` : `/dashboard/projection/` affiche URL élèves, QR et étapes de connexion.
- `DONE` : `Copier l’URL`, `Plein écran` et `Retour cockpit` restent visibles et cohérents.
- `DONE` : l’état `URL LAN non configurée` est documenté et accepté comme état explicite.
- `DONE` : l’absence de QR ou de JS ne doit pas empêcher la lecture de l’URL.
- `PARTIAL` : tests navigateur réels `clipboard/fullscreen` encore absents.

### Présence heartbeat

- `DONE` : `/presence/heartbeat/` est traité comme action technique silencieuse, pas comme page produit.
- `DONE` : les états `heartbeat ok`, `expired`, `session closed`, `unstable network` sont maintenant référencés.
- `PARTIAL` : la visualisation cockpit des états dégradés reste à mieux définir.

## 4. Modules / Réponses / Exports

- `DONE` : les modules 2 à 8 gardent une logique uniforme.
- `DONE` : l’élève ne voit jamais un succès direct sans soumission valide.
- `DONE` : les exports restent côté formateur, protégés et compatibles avec la sécurité CSV.
- `PARTIAL` : le wording des messages de fermeture, doublon et succès doit encore être normalisé.

## 5. Médiathèque / Supports / Vidéo

- `DONE` : seuls les supports publiés sont visibles publiquement.
- `DONE` : les brouillons restent strictement côté formateur.
- `DONE` : les pages `detail`, `watch` et `download` suivent un parcours simple et local.
- `PARTIAL` : la distinction `aucun support publié` / `aucun résultat après filtre` doit devenir explicite.
- `PARTIAL` : la guidance de l’upload support peut être encore simplifiée.

## 6. Matières scolaires futures

- `DONE` : sujet/chapitre existent comme base de classement sans devenir un produit autonome.
- `FUTURE` : hub dédié matières/chapitres.
- `FUTURE` : navigation élève par matière.
- `FUTURE` : UX complète de programme scolaire.

## Définition “UX v1 done”

### Complet maintenant

- séparation étudiant/formateur ;
- catalogue modules et formulaires utilisables ;
- cockpit protégé ;
- réseau/projection documentés ;
- heartbeat documenté ;
- médiathèque publique et dashboard supports cadrés ;
- roadmap UX et matrice de traçabilité prêtes pour review.

### Reste volontairement futur

- refonte visuelle avancée du cockpit ;
- scénarisation complète des états dégradés helper ;
- hub matières scolaires ;
- tests navigateur réels avancés pour interactions JS ;
- perfectionnement éditorial fin de tous les messages.

### Verdict

Verdict UX v1 : `DONE avec réserves connues`

Réserves :

- `network-control` reste la principale zone `RISK/PARTIAL` ;
- plusieurs raffinements UI restent nécessaires avant une “v2 premium” alignée plus finement à Prototype 6.
