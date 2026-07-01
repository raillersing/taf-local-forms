# UX Network Control

## Page concernée

- `/dashboard/network-control/`

## Statut UX

Cette page est l'une des plus sensibles de toute l'application :

- elle n'est pas destinée aux élèves ;
- elle ne sert pas seulement à informer, mais à agir sur l'accès LAN ;
- elle dépend d'un helper PowerShell local ;
- elle impose une distinction forte entre usage `localhost` et usage LAN ;
- elle mélange opérations réseau, sécurité locale et feedback asynchrone.

## Rôle précis de la page

Le rôle UX de `/dashboard/network-control/` n'est pas :

- d'être une page diagnostic générale ;
- d'être une page de configuration `.env` ;
- d'être un cockpit réseau “joli”.

Son rôle est :

- d’exécuter des gestes opérationnels terrain de manière encadrée ;
- de vérifier si le helper LAN répond ;
- de guider le formateur étape par étape ;
- d'expliquer pourquoi les boutons ne fonctionnent pas depuis l'URL LAN ;
- d'exposer un statut global lisible.

## Préconditions d’usage

### Préconditions techniques

- utilisateur connecté ;
- rôle staff ;
- application locale accessible ;
- helper PowerShell disponible sur `127.0.0.1:8019` ;
- de préférence page ouverte depuis `http://localhost:8010/dashboard/network-control/`.

### Préconditions pédagogiques

- le formateur sait qu’il configure l’accès des élèves, pas seulement son
  navigateur ;
- il sait que `localhost` ne doit pas être partagé aux élèves.

## Structure visible réelle

1. Alerte si la page est ouverte depuis l'URL LAN
2. Assistant en 7 étapes
3. Carte de statut global
4. Statut du helper
5. État du réseau
6. Zone d’actions
7. Bloc “helper non disponible”
8. Bloc résultat brut JSON
9. Liens vers réseau/configuration

## Les 7 étapes affichées

1. Helper local
2. Application locale
3. IP Wi-Fi
4. Portproxy
5. Pare-feu
6. Django autorise l’IP
7. URL élèves accessible

## Actions utilisateur documentées

### NC-01 — Actualiser l’état

- But : rafraîchir le diagnostic sans modifier la configuration
- Risque : faible
- Dépendance : helper
- État d’échec : helper introuvable, timeout

### NC-02 — Configurer et rendre accessible

- But : synchroniser portproxy, pare-feu et accès LAN
- Risque : moyen
- Dépendance : helper + OS Windows + privilèges adaptés
- État d’échec : helper absent, rejet système, mauvaise IP

### NC-03 — Tester l’URL élèves

- But : vérifier l’accessibilité réelle
- Risque : faible
- Dépendance : helper + réseau
- État d’échec : URL non accessible malgré configuration partielle

### NC-04 — Copier l’URL élèves

- But : partager vite l’adresse
- Risque : faible
- Dépendance : navigateur / presse-papiers
- État d’échec : fallback copy requis

### NC-05 — Désactiver l’accès LAN

- But : retirer l’ouverture réseau
- Risque : moyen
- Dépendance : helper
- État d’échec : règles non supprimées

### NC-06 — Redémarrer l’application

- But : relancer le service web
- Risque : moyen
- Dépendance : helper + Docker
- État d’échec : Docker absent ou conteneur non relançable

## États UX critiques

### 1. Page ouverte depuis LAN

Comportement réel :

- alerte haute priorité ;
- instruction explicite d’ouvrir `http://localhost:8010/dashboard/network-control/`.

Décision UX :

- cet état doit rester bloquant dans le sens pédagogique ;
- il ne faut pas masquer les boutons, mais il faut expliciter qu’ils ne sont
  pas exécutables dans ce contexte.

### 2. Helper indisponible

Comportement réel :

- message d’erreur ;
- section dédiée “Helper LAN non disponible” ;
- scripts PowerShell documentés ;
- rappel que le helper n’écoute que sur `127.0.0.1`.

Décision UX :

- bon pattern ;
- mérite une meilleure hiérarchisation visuelle lors d’une future refonte.

### 3. Requête en cours

Comportement réel :

- libellé bouton remplacé par `En cours...` ;
- usage d’`AbortController` ;
- timeout à 8 secondes.

Décision UX :

- très bon garde-fou opérationnel ;
- à préserver absolument lors des futures PR UI.

### 4. Résultat helper

Comportement réel :

- rendu JSON brut dans un bloc résultat ;
- carte message succès/erreur distincte.

Décision UX :

- acceptable pour un usage expert ;
- pourrait être progressivement traduit en feedback plus humain.

## Écarts avec le Prototype 6

- Prototype 6 pense en “cockpit riche”, mais ne documente pas assez cette page
  comme outil d’exploitation locale ;
- l’application réelle est plus proche d’un assistant Ops que d’une simple vue
  dashboard ;
- le besoin de `localhost` est une contrainte terrain essentielle à conserver,
  même si elle complique la pureté du parcours UX.

## Recommandations UX

- garder la page explicitement orientée “action locale” ;
- ne pas la fusionner avec `/dashboard/network/` ;
- ne pas la fusionner avec `/dashboard/settings/` ;
- renforcer la différence :
  - `network` = voir / diagnostiquer ;
  - `network-control` = agir ;
  - `settings` = configurer.

## Critères de réussite pour futures PR UI

- aucune ambiguïté sur l’usage localhost ;
- feedback plus lisible des 7 étapes ;
- états succès/erreur mieux hiérarchisés ;
- actions critiques toujours protégées login + staff ;
- aucun changement de logique helper dans une PR purement UI.
