# UX State And Error Matrix

## Objectif

Lister les états UX récurrents à traiter explicitement dans toute future PR UI.

## Matrice

| Zone | État | Déclencheur | Comportement actuel | Risque UX | Recommandation |
|---|---|---|---|---|---|
| Accueil | normal | app accessible | deux CTA clairs | faible | conserver |
| Modules | open | session active + réponses ouvertes | badge vert + CTA questionnaire | faible | conserver |
| Modules | consult only | session active + réponses fermées | badge warning + CTA consultation | moyen | harmoniser wording |
| Modules | unavailable | pas de session active | badge indisponible / 503 | faible | conserver |
| Questionnaire | validation error | champ invalide | erreur champ | faible | garder proche du champ |
| Questionnaire | duplicate | réponse déjà existante | message doublon | moyen | rendre encore plus explicite |
| Questionnaire | submit success | POST valide | redirect merci | faible | conserver |
| Questionnaire | permission by session | page succès directe | redirect vers questionnaire | faible | conserver |
| Cockpit | no LAN URL | pas d’IP exploitable | message `Disponible après configuration réseau` | moyen | garder prudent |
| Cockpit | stale LAN IP | IP configurée ≠ IP courante | alerte warning | faible | conserver |
| Cockpit | empty data | aucune réponse | stats faibles, tables vides | moyen | unifier empty states |
| Projection | ready | URL élèves disponible + JS chargé | URL, étapes et QR visibles | faible | conserver |
| Projection | LAN not ready | pas d’URL élèves exploitable | `URL LAN non configurée` + renvoi vers Réseau | faible | conserver |
| Projection | stale LAN IP | IP LAN obsolète détectée | alerte warning dans la page | faible | conserver |
| Projection | QR unavailable | bibliothèque QR ou JS indisponible | page reste lisible, QR absent | moyen | documenter explicitement cet état dégradé |
| Projection | copy success | clic `Copier l'URL` réussi | feedback `URL copiée.` | faible | conserver |
| Projection | copy unavailable | navigateur sans clipboard fiable | feedback erreur | moyen | garder un message simple |
| Projection | fullscreen unavailable | appareil ou navigateur incompatible | feedback erreur | moyen | conserver `type="button"` et message bref |
| Projection | fullscreen denied | refus `requestFullscreen()` | feedback erreur | moyen | conserver |
| Dashboard module | empty | aucune réponse module | ligne tableau vide | moyen | rendre plus visible |
| Export | protected | non connecté | redirect login | faible | conforme |
| Réseau | not configured | aucune IP config | message warning | faible | conforme |
| Réseau | LAN request | accès via IP privée | source requête | faible | conforme |
| Réseau | localhost misuse | localhost sans config | avertissement explicite | faible | conforme |
| Settings | save success | POST valide | message de sauvegarde | faible | conforme |
| Settings | save error | valeur interdite | message erreur | moyen | mieux structurer visuellement |
| Network control | helper missing | helper indisponible | bloc d’aide scripts | faible | conforme |
| Network control | wrong origin | page ouverte via LAN | alerte localhost | faible | conforme |
| Network control | loading | action helper en cours | `En cours...` | faible | préserver |
| Network control | timeout | helper ne répond pas | erreur timeout | moyen | clarifier encore |
| Supports public | empty | aucun publié | empty state | faible | conforme |
| Supports public | filtered empty | filtres sans résultat | empty state générique | moyen | distinguer “aucun résultat” |
| Support detail | draft access | slug brouillon | 404 | faible | conforme |
| Support watch | non-video | support non vidéo | 404 | faible | conforme |
| Upload | required field | champ manquant | message champ obligatoire | faible | conforme |
| Upload | invalid extension | extension refusée | message format | faible | conforme |
| Upload | oversized file | taille dépassée | message 20MB/80MB | faible | conforme |
| Upload | chapter mismatch | chapitre autre matière | message cohérence | faible | conforme |
| Backup | operational warning | lecture page | avertissement anti-destruction | faible | conserver |
| Presence | background refresh | polling cockpit | compteurs dynamiques | moyen | rendre erreurs invisibles mais sûres |
| Presence | heartbeat ok | POST JSON accepté | présence fraîche comptée côté cockpit | faible | conserver |
| Presence | heartbeat expired | absence de nouveau signal au-delà du TTL | présence disparaît des compteurs actifs | moyen | expliquer côté cockpit si besoin futur |
| Presence | polling interrupted | JS coupé, onglet figé ou script bloqué | plus de rafraîchissement silencieux | moyen | documenter comme état dégradé sans bruit élève |
| Presence | session closed | module fermé ou session absente | heartbeat `404` côté serveur | moyen | prévoir lecture cockpit, pas de message élève |
| Presence | browser quit | `beforeunload` ou fermeture brutale | dernier heartbeat envoyé ou présence expirera | moyen | accepter l’approximation locale |
| Presence | unstable network | POST heartbeat perdu ou navigateur hors ligne | présence peut expirer puis revenir | élevé | garder la logique tolérante et silencieuse |

## États à préserver absolument

- doublon questionnaire ;
- fermeture des réponses sans casser la consultation ;
- brouillon non public ;
- blocage des pages formateur sans login ;
- blocage des pages staff sans privilège ;
- helper LAN uniquement via localhost ;
- avertissement IP LAN obsolète.

## États à améliorer en priorité

- distinction “aucun support” vs “aucun résultat après filtre” ;
- retour visuel après toggle ouverture/fermeture des réponses ;
- lisibilité des erreurs de configuration réseau ;
- lisibilité des empty states dans les dashboards modules ;
- hiérarchisation des résultats dans `network-control`.
- visualisation formateur de la présence dégradée sans polluer l’écran élève ;
- couverture documentaire et, plus tard, testable des états projection navigateur.
