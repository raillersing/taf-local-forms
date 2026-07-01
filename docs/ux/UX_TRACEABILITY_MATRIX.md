# UX Traceability Matrix

## Résumé exécutif

Cet audit vérifie la traçabilité entre :

- les documents UX F045A ;
- le code Django réel (`urls.py`, `views.py`, `forms.py`) ;
- les templates et assets runtime ;
- les tests existants ;
- la cible Prototype 6 ;
- les références de cadrage disponibles dans `docs/specs/`.

Verdict global :

- `OK` pour la séparation étudiant/formateur, les parcours modules, la médiathèque publique, le cockpit, les exports, la protection login/staff et la plupart des états critiques ;
- `PARTIAL` pour la traçabilité brute aux PDFs de spécification, car les trois PDFs présents dans `docs/specs/` ne sont pas text-extractibles automatiquement dans cet environnement ;
- `OK` pour la couverture documentaire de `dashboard_projection` et de `presence_heartbeat`, désormais fichés explicitement ;
- `OK` pour l’existence d’un pack final d’acceptation UX v1, qui rend les futurs contrôles UI plus normatifs ;
- `RISK` limité mais réel sur `/dashboard/network-control/`, dont l’UX dépend d’un helper PowerShell externe et d’états LAN non simulés par les tests Django.

Synthèse chiffrée :

- `53` routes Django inspectées dans `surveys/urls.py`
- `51` actions UX documentées dans `UX_ACTION_CATALOG.md`
- `24` exigences tracées dans cette matrice
- `0` route sans fiche d’action UX explicite
- `4` documents normatifs d’acceptation UX ajoutés
- `6` actions UX seulement partiellement testées côté interaction réelle

## Limites de preuve

Sources PDF présentes mais non text-extractibles automatiquement ici :

- `docs/specs/TAf_Local_Forms_Cahier_Charges_Technique_v0_1.pdf`
- `docs/specs/TAf_Local_Forms_Cahier_Charges_Metier_Non_Technique_v0_1.pdf`
- `docs/specs/TAf_Local_Forms_Guide_Developpement_v0_1.pdf`

Conséquence :

- les exigences ci-dessous sont tracées d’abord par le code, les docs UX F045A, `README.md`, les docs design/field relisibles et les tests ;
- la référence PDF reste canonique, mais sa preuve textuelle est marquée `PARTIAL` quand elle n’est pas recoupée mot pour mot par une source lisible dans le repo.

## Verdict sur la complétude UX F045A

Verdict F045A seul : `PARTIAL`

Motif :

- F045A couvre bien la carte produit, la navigation, les parcours, les états et les écarts Prototype 6 ;
- F045A ne couvrait pas encore explicitement toute la traçabilité route/vue/template/test ;
- F045A ne formalisait pas assez les trous de couverture sur `dashboard_projection`, `presence_heartbeat` et les interactions helper LAN.

Verdict après F045B : `OK` comme référence UX v1 documentaire, avec garde-fous

Verdict après F047C : `OK` comme référence d’acceptation UX v1 pour les futures PR UI

Conditions :

- suffisant pour des PR UI contrôlées sur navigation, modules, cockpit, supports et états ;
- compléter avant toute correction code sensible sur `network-control` si la PR touche les interactions helper, les retours d’erreur ou la logique localhost/LAN.

## Matrice exigences métier -> parcours UX -> action UX -> route -> template -> vue -> test

| ID | Exigence métier vérifiée | Parcours UX | Action UX | Route(s) | Template(s) | Vue / Forme | Preuve test | Statut |
|---|---|---|---|---|---|---|---|---|
| BM-01 | Séparer clairement entrée étudiant et entrée formateur | `UX_STUDENT_JOURNEYS`, `UX_TRAINER_JOURNEYS` | `UX-A001`, `UX-A002` | `/` | `home.html` | `home()` | tests home links vers modules/dashboard | `OK` |
| BM-02 | Permettre aux élèves de parcourir les modules sans login | étudiant | `UX-M001`, `UX-M002` | `/modules/`, `/modules/module-2/` à `/modules/module-8/` | `student_modules.html`, `student_module_detail.html` | `student_modules()`, `student_module_detail()` | tests navigation étudiante, absence liens dashboard | `OK` |
| BM-03 | Permettre la réponse aux questionnaires quand une session active existe | étudiant | `UX-M004`, `UX-M005` | `/module-2/` à `/module-8/` | `module_X_form.html` | `module_X_form()`, `ModuleXSubmissionForm` | nombreux tests POST valides par module | `OK` |
| BM-04 | Empêcher les doublons accidentels sur un même identifiant élève/session | étudiant | `UX-M006` | `/module-2/` à `/module-8/` | `module_X_form.html` | `module_X_form()` | tests duplicate prevention et retour erreur | `OK` |
| BM-05 | Laisser consulter un questionnaire fermé sans autoriser l’envoi | étudiant | `UX-M003` | `/module-2/` à `/module-8/` | `module_X_form.html` | `module_X_form()` | tests modules fermés consultables / POST bloqué | `OK` |
| BM-06 | Afficher un état indisponible si aucune session active n’existe | étudiant | `UX-M008` | `/module-2/` à `/module-8/` | `module_X_unavailable.html` | `module_X_form()` | tests 503 / unavailable par modules | `OK` |
| BM-07 | Confirmer clairement l’envoi d’une réponse | étudiant | `UX-M007` | `/module-X/success/<id>/` | `module_X_success.html` | `module_X_success()` | tests redirect, session gate, success page | `OK` |
| BM-08 | Permettre au formateur d’ouvrir un cockpit protégé | formateur | `UX-D001` | `/dashboard/` | `dashboard_home.html` | `dashboard_home()` | tests 302 sans login, 200 avec login | `OK` |
| BM-09 | Permettre au formateur de suivre modules, exports et présence | formateur | `UX-D003`, `UX-D005`, `UX-B002` | `/dashboard/module-X/`, `/dashboard/export/module-X.csv`, `/dashboard/presence.json` | dashboards modules, `dashboard_home.html` | `dashboard_module_X()`, `export_module_X_csv()`, `dashboard_presence_json()` | tests dashboards/login, exports CSV, presence json | `OK` |
| BM-10 | Permettre au staff d’ouvrir/fermer les réponses d’un module | formateur staff | `UX-D004` | `/dashboard/modules/<module_code>/toggle-responses/` | cockpit / dashboards | `toggle_module_responses()` | tests route staff only | `OK` |
| BM-11 | Donner au formateur les bonnes URLs élèves et les diagnostics LAN | formateur | `UX-N001`, `UX-N002`, `UX-N003` | `/dashboard/network/`, `/dashboard/settings/`, `/dashboard/settings/use-current-address/` | `dashboard_network.html`, `dashboard_settings.html` | `network_access_dashboard()`, `dashboard_settings()`, `dashboard_use_current_address()` | tests réseau/settings/login/staff/messages | `OK` |
| BM-12 | Fournir une page d’action réseau dédiée au helper local | formateur staff | `UX-N004` à `UX-N007` | `/dashboard/network-control/` | `dashboard_network_control.html` | `network_control()` | tests page, boutons, helper endpoint, localhost warning | `PARTIAL` |
| BM-13 | Proposer un mode projection salle lisible | formateur | `UX-P001`, `UX-P002`, `UX-P003`, `UX-P004` | `/dashboard/projection/` | `dashboard_projection.html` | `dashboard_projection()` | tests login + rendu projection | `OK` |
| BM-14 | Mettre à disposition des supports publics publiés seulement | étudiant/public | `UX-A003`, `UX-S001` à `UX-S006` | `/supports/`, `/supports/<slug>/`, `/watch/`, `/download/` | `support_list.html`, `support_detail.html`, `support_watch.html` | `support_list()`, `support_detail()`, `support_watch()`, `support_download()` | tests 200/404, watch video, download, filtres | `OK` |
| BM-15 | Permettre au formateur de gérer des brouillons et publications de supports | formateur | `UX-L001` à `UX-L006` | `/dashboard/supports/`, `/dashboard/supports/upload/` | `dashboard_supports.html`, `dashboard_support_upload.html` | `dashboard_supports()`, `dashboard_support_upload()`, `LearningResourceForm` | tests login, draft/public, tailles, formats, slug, sujet/chapitre | `OK` |
| BM-16 | Permettre la lecture vidéo locale simple sans streaming lourd | étudiant/public | `UX-S006` | `/supports/<slug>/watch/` | `support_watch.html` | `support_watch()` | tests `<video>` + `preload="metadata"` | `OK` |
| BM-17 | Préparer un futur classement scolaire par matière/chapitre sans en faire un produit autonome aujourd’hui | étudiant/formateur | `UX-L005`, `UX_SCHOOL_RESOURCES` | filtres `/supports/`, upload support | `support_list.html`, `dashboard_support_upload.html`, `dashboard_supports.html` | `support_list()`, `LearningResourceForm` | tests filtres + cohérence sujet/chapitre | `OK` |
| BM-18 | Donner une vue sauvegarde non destructive après séance | formateur | `UX-B001` | `/dashboard/backup/` | `dashboard_backup.html` | `dashboard_backup()` | tests page backup existante/protégée | `OK` |

## Matrice exigences techniques -> action UX -> preuve code/test

| ID | Exigence technique / guide dev | Action UX liée | Preuve code | Preuve test | Statut |
|---|---|---|---|---|---|
| BT-01 | Frontend local, pas de CDN en runtime | cockpit, projection, modules, supports | `static/css/app.css`, `static/js/taf_projection.js`, `static/js/vendor/qrcode.js` local | tests présence fichiers et templates | `OK` |
| BT-02 | Dashboard/export/réseau protégés par login | `UX-D001`, `UX-D003`, `UX-D005`, `UX-N001` à `UX-N007`, `UX-B001` | `@login_required` sur vues dashboard/export/network | nombreux tests `302`/`403` sans login | `OK` |
| BT-03 | Pages sensibles de pilotage limitées au staff | `UX-D004`, `UX-N002`, `UX-N003`, `UX-N004` à `UX-N007` | `@staff_member_required` + `@require_POST` selon cas | tests `dashboard_settings`, `toggle`, `network_control` staff only | `OK` |
| BT-04 | CSRF conservé sur les POST Django | `toggle`, settings save, use-current-address, upload support, forms modules | formulaires HTML avec `{% csrf_token %}`, vues POST Django natives | tests POST réussis/échoués ; absence de contournement observé | `OK` |
| BT-05 | Anti-doublon questionnaire conservé | `UX-M006` | recherche de doublon + `IntegrityError` guard dans vues modules | tests duplicate response | `OK` |
| BT-06 | Export CSV assaini contre les cellules de formule | `UX-D005` | `sanitize_csv_cell()` dans `views.py` | tests `sanitizes_formula_like_cells` modules 2 à 8 | `OK` |
| BT-07 | Brouillon support non public | `UX-L001`, `UX-L003`, `UX-L004` | `_published_resources_queryset()` + 404 draft | tests détail/download/watch draft en 404 | `OK` |
| BT-08 | Helper LAN localhost-only avec CORS borné | `UX-N004` à `UX-N007` | `network_control()` impose `127.0.0.1:8019`, template avertit hors localhost | tests helper scripts `127.0.0.1`, no wildcard CORS, no `0.0.0.0` | `OK` |
| BT-09 | Pas d’action destructive Docker documentée ou embarquée | backup, helper LAN | docs field + backup page + scripts helper | tests absence `down -v` / prune | `OK` |
| BT-10 | Accessibilité mobile minimale : labels, QR local, feedback simple | cockpit, projection, questionnaires, supports | base/app.css, templates avec labels, `aria-live`, skip-link | tests nav/breadcrumbs/projection/copy presence | `PARTIAL` |
| BT-11 | Présence live en arrière-plan, sans exposer de page sensible publique | `UX-B002`, `UX-B003` | `/presence/heartbeat/` POST JSON, `/dashboard/presence.json` login | tests 405/400/404/200 + polling intervals 30s/15s | `OK` |
| BT-12 | Source de vérité réseau explicite : localhost formateur, 8011 élèves | `UX-N001`, projection, cockpit | `dashboard_network.html`, `dashboard_network_control.html`, `README.md` | tests réseau et messages IP | `OK` |

## Matrice Prototype 6 -> écran réel -> écart -> priorité

| Zone Prototype 6 | Écran réel | Écart principal | Priorité | Statut |
|---|---|---|---|---|
| Accueil public avec double entrée | `/` | très proche, wording réel plus opérationnel | P1 | `OK` |
| Catalogue modules étudiant lisible mobile | `/modules/`, `/modules/module-X/` | proche, mais moins scénarisé visuellement que le prototype | P1 | `OK` |
| Questionnaire + confirmation + doublon | `/module-X/`, `/module-X/success/` | structure réelle plus sobre ; état doublon géré mais moins mis en scène | P0 | `PARTIAL` |
| Cockpit formateur en hub unique | `/dashboard/` | hub réel fonctionnel mais dense | P1 | `PARTIAL` |
| Projection QR grand format | `/dashboard/projection/` | fonctionnel, testé et maintenant fiché ; reste un futur raffinement visuel possible | P0 | `OK` |
| Réseau diagnostic | `/dashboard/network/` | réel plus technique, plus proche du terrain que du prototype | P0 | `OK` |
| Contrôle LAN | `/dashboard/network-control/` | réel beaucoup plus opérationnel que le prototype ; dépendance helper externe | P0 | `RISK` |
| Gestion supports | `/supports/`, `/dashboard/supports/`, `/dashboard/supports/upload/` | couverture réelle bonne, mais UX d’upload moins guidée | P1 | `PARTIAL` |
| Ressources scolaires futures | pas de hub dédié courant | Prototype anticipe un espace futur, le code réel reste limité au classement support | P3 | `OUT_OF_SCOPE` |
| Sauvegarde / médias / restauration | `/dashboard/backup/` | réel focalisé backup non destructif, prototype plus large | P2 | `PARTIAL` |

## Liste des actions UX couvertes

Actions documentées F045A relues et recoupées :

- section A : `UX-A001` à `UX-A004`
- section B : `UX-M001` à `UX-M008`
- section C : `UX-S001` à `UX-S006`
- section D : `UX-D001` à `UX-D005`
- section E : `UX-N001` à `UX-N007`
- section F : `UX-L001` à `UX-L006`
- section G : `UX-B001` à `UX-B003`
- section H : `UX-P001` à `UX-P004`

Total vérifié : `51` actions.

## Liste des actions UX manquantes ou ambiguës

| Action manquante / ambiguë | Route / zone | Motif | Statut |
|---|---|---|---|
| Distinguer “résultat helper réussi” vs “résultat helper exploitable par le formateur” | `/dashboard/network-control/` | la page montre JSON brut + statuts, mais la fiche reste encore trop haut niveau | `PARTIAL` |

## Liste des routes sans action UX documentée

Routes Django réelles inspectées sans fiche d’action explicite : aucune.

Remarque :

- certaines routes restent couvertes par des actions génériques multi-modules (`/module-X/`, `/dashboard/module-X/`, `/dashboard/export/module-X.csv`), mais elles ne sont pas orphelines.

## Liste des actions UX sans test ou avec test seulement partiel

| Action UX | Couverture actuelle | Verdict |
|---|---|---|
| `UX-D002` copier l’URL élèves depuis le cockpit | présence DOM et JS partagés, pas de test navigateur réel clipboard sur cockpit | `PARTIAL` |
| `UX-N004` configurer et rendre accessible | présence boutons/scripts testée, pas d’intégration helper renvoyant un état réel | `PARTIAL` |
| `UX-N005` tester l’URL élèves | présence bouton/scripts testée, pas de résultat helper simulé | `PARTIAL` |
| `UX-N006` redémarrer l’application | présence bouton/scripts testée, pas de résultat helper simulé | `PARTIAL` |
| `UX-N007` désactiver l’accès LAN | présence confirmation/scripts testée, pas de résultat helper simulé | `PARTIAL` |
| `UX-P002` copier l’URL depuis la projection | présence DOM et JS partagés, pas de test navigateur réel clipboard | `PARTIAL` |
| `UX-P003` plein écran projection | présence du bouton et du JS, pas de test navigateur réel fullscreen | `PARTIAL` |
| `UX-B002` présence live en erreur / endpoint indisponible | endpoint JSON testé, pas de test d’état dégradé visible côté cockpit | `PARTIAL` |
| `UX-B003` heartbeat étudiant en réseau instable | endpoint et intervalle testés, pas de test de panne navigateur ou fermeture réelle d’onglet | `PARTIAL` |
| `UX-S001` empty state filtré vs empty state absolu | filtres testés, distinction UX textuelle non testée | `PARTIAL` |

## Liste des états / erreurs incomplets

| Zone | Manque principal | Statut |
|---|---|---|
| Projection | états documentés ; reste à tester plus finement les cas navigateur réels `copie` et `fullscreen` | `PARTIAL` |
| Network control | hiérarchie des erreurs helper encore très brute pour le formateur | `PARTIAL` |
| Supports publics | “aucun support publié” et “aucun résultat après filtre” restent trop proches | `PARTIAL` |
| Dashboards modules | empty states présents mais peu différenciés | `PARTIAL` |
| Présence live | états documentés, mais pas encore visualisés côté cockpit en cas de polling dégradé | `PARTIAL` |
| Settings réseau | validation visible mais documentation UX encore back-office | `PARTIAL` |

## Focus spécial `/dashboard/network-control/`

### Ce qui est solide

- route protégée par `login + staff`
- avertissement explicite si la page est ouverte depuis une URL LAN
- helper limité à `127.0.0.1:8019`
- boutons d’action lisibles
- tests nombreux sur la présence des garde-fous
- helper scripts audités contre secrets, wildcard CORS et commandes Docker destructives

### Ce qui reste partiel

- pas de test d’intégration réel entre page Django et helper PowerShell ;
- pas de simulation de tous les retours JSON métier/terrain dans `surveys.tests` ;
- retour JSON affiché brut dans la page, utile techniquement mais encore lourd UX ;
- dépendance externe au contexte Windows/WSL non simulable dans les tests Django purs.

### Verdict spécial

`/dashboard/network-control/` est correctement borné fonctionnellement et côté sécurité documentaire, mais son UX reste `RISK/PARTIAL` tant que la couche helper n’est pas testée ou mockée plus finement dans un futur lot ciblé.

## Priorités de correction recommandées

1. `P0` : pour toute future PR sur `network-control`, définir au moins une matrice de résultats helper (`helper absent`, `timeout`, `sync ok`, `LAN test fail`, `restart fail`).
2. `P1` : distinguer les empty states du catalogue supports.
3. `P1` : visualiser côté cockpit l’état dégradé de présence live sans bruit pour les élèves.
4. `P1` : lier explicitement futures PR UI au présent audit de traçabilité.
5. `P2` : renforcer les tests navigateur réels autour de `copie` et `fullscreen` en projection si un outillage front est ajouté plus tard.
6. `P3` : conserver les “ressources scolaires complètes” hors périmètre tant qu’aucune route dédiée n’est mergée sur `main`.

## Décision finale

Décision :

- `F045A seul` n’était pas encore suffisant comme référence UX v1 complète ;
- `F045A + F045B` forment maintenant une référence UX v1 exploitable pour les prochaines PR UI ;
- la projection et le heartbeat sont maintenant couverts documentairement ; le prochain manque principal reste la matrice de résultats helper pour `network-control`.

Conclusion de gouvernance :

- pas besoin de compléter `models.py`, `views.py`, `forms.py`, `urls.py`, `templates` runtime ou `static` dans cette mission ;
- la suite logique est une petite PR documentaire de consolidation F045A/F045B, puis seulement des PR UI ciblées par lot.
