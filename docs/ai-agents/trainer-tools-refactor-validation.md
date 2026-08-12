# Validation F041–F043 — parcours formateur

## Périmètre

Cette fiche valide le parcours formateur après la réduction des outils :

- Cockpit : `/dashboard/`
- Préparation de l’accès élèves : `/dashboard/network/`
- Contrôle technique LAN : `/dashboard/network-control/`
- Modules, exports, sauvegarde et demandes élèves

Les pages restent protégées par authentification et le parcours étudiant ne
doit jamais afficher ces entrées.

## Contrôles automatisés

À exécuter depuis la racine du dépôt :

```sh
.venv-wsl/bin/python manage.py check
.venv-wsl/bin/python manage.py test surveys.tests
.venv-wsl/bin/python manage.py makemigrations --check --dry-run
docker compose config
git diff --check
```

Les tests couvrent notamment les routes protégées, la séparation étudiant /
formateur, les états réseau non confirmés, les boutons non-submit, les
confirmations d’actions sensibles, les raccourcis du module actif et l’absence
de secrets dans le diagnostic téléchargé.

## Scénarios terrain à exécuter

| Scénario | Vérification attendue | Preuve à conserver |
|---|---|---|
| 360 px | Aucun défilement horizontal bloquant ; l’action principale reste visible | capture mobile |
| Zoom 200 % | Le bouton et le statut restent lisibles et atteignables | capture navigateur |
| Clavier | Tab suit le parcours ; focus visible ; `details` s’ouvre au clavier | capture ou note de test |
| Helper indisponible | État `Non confirmé` et consigne PowerShell exploitable | capture de `/dashboard/network-control/` |
| IP changée | Adresse configurée distinguée de l’adresse détectée ; aucune confirmation implicite | capture avant/après |
| Aucune session active | Cockpit propose le pilotage des modules et n’invente aucun résultat | capture Cockpit |
| Même réseau | Test téléphone confirmé et URL élèves accessible | note du formateur |
| Autre réseau | Échec explicite, sans présenter l’accès comme prêt | note du formateur |
| Module actif | Accès rapide au suivi et à l’export du module affiché | capture Cockpit |
| Action sensible | Confirmation avant synchronisation, désactivation ou redémarrage | capture de la confirmation |
| Retour | Retour au Cockpit conservant le contexte de séance | parcours chronométré |

## Critère de décision

F043 est déclarable terminé après exécution de la matrice terrain sur le poste
formateur et un téléphone réel. Les tests automatisés seuls ne remplacent
pas cette vérification réseau.
