# Feuille de route — Refonte des outils formateur

## Objectif

Réduire la redondance des outils du parcours formateur et rendre chaque page
orientée vers une seule prochaine action, tout en conservant les routes,
l’authentification, le fonctionnement hors ligne et les diagnostics LAN.

## Principes retenus

- Une tâche métier = un point d’entrée principal.
- Les détails techniques restent dans des sections secondaires.
- Le parcours « Préparer l’accès élèves » devient la référence pour l’état LAN,
  l’URL, le QR code et le test téléphone.
- La Projection reste un écran de diffusion destiné à la classe.
- Les données, exports, sauvegardes et supports restent des responsabilités
  distinctes.
- Les états utilisent un vocabulaire commun : Prêt, À vérifier, En cours,
  Non confirmé, Erreur et Terminé.
- Les actions sensibles demandent une confirmation explicite et expliquent
  leur impact.

## Lots approuvés

### F040 — Dédoublonnage et nouvelle arborescence

Fusionner « Guide de démarrage », « Réseau élèves » et « Paramètres réseau »
dans un parcours « Préparer l’accès élèves ».

- conserver une page principale de préparation ;
- intégrer statut serveur, IP, QR code, checklist et test téléphone ;
- reléguer le Contrôle LAN aux diagnostics et actions techniques ;
- déplacer les paramètres dans une section « Configuration avancée » ;
- conserver Projection comme espace de diffusion ;
- ne supprimer une route qu’après vérification de ses usages et redirections.

Critères d’acceptation : une seule entrée principale pour préparer l’accès,
aucune action réseau essentielle présentée sous plusieurs libellés concurrents,
routes protégées et parcours LAN existants conservés.

### F041 — États et libellés métier communs

Standardiser les messages et les libellés visibles par le formateur.

- remplacer les intitulés techniques par des actions métier ;
- afficher la source de toute information réseau ;
- distinguer clairement « détecté », « configuré » et « confirmé » ;
- harmoniser les états vide, chargement, succès, attention et erreur ;
- mettre à jour les tests de contenu et d’accessibilité.

Critères d’acceptation : un même état utilise le même libellé sur toutes les
pages et aucune donnée non vérifiée n’est présentée comme confirmée.

### F042 — Actions sensibles, historique et accès rapides

Rendre les opérations techniques et les raccourcis plus sûrs et plus lisibles.

- regrouper synchronisation IP, ouverture/désactivation de port et restauration
  sous « Actions avancées » ;
- ajouter confirmation, impact et résultat pour les opérations sensibles ;
- conserver un historique court des actions formateur récentes ;
- ajouter des accès rapides vers le module actif, l’export filtré et les
  demandes élèves ;
- garder les exports contextuels cohérents avec la session affichée.

Critères d’acceptation : aucune action sensible ne s’exécute sans intention
explicite, et chaque raccourci conserve le contexte module/session.

### F043 — Validation terrain UX complète

Valider la refonte sur les scénarios réels avant déclaration de fin.

- écran de 360 px minimum ;
- zoom navigateur à 200 % ;
- clavier et focus visible ;
- helper Windows indisponible ;
- aucune session active ;
- réseau non confirmé ou IP changée ;
- téléphone sur le même réseau et téléphone sur un autre réseau ;
- ouverture d’un module, export, sauvegarde et retour au Cockpit.

Critères d’acceptation : parcours principal compréhensible sans aide orale,
aucun défilement horizontal bloquant et résultats documentés avec preuves.

## Ordre d’exécution

F040 → F041 → F042 → F043. Chaque lot doit être validé et committe séparément.
Une régression d’authentification, de données ou de fonctionnement LAN impose
un arrêt avant le lot suivant.
