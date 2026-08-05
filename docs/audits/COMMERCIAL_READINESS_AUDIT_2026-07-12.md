# Audit de commercialisation - TAf Local Forms

Date de l'audit : 12 juillet 2026

Branche auditée : `feat/f054m-prototype-6-full-ui-refresh`

Portée : code, configuration, sécurité, données, exploitation LAN, UX, tests,
documentation et installation. Les bases, fichiers `.env`, journaux, sauvegardes
et médias runtime n'ont pas été lus.

## Verdict

**BLOCK pour une commercialisation autonome en l'état.**

L'application constitue une base sérieuse pour un **pilote scolaire local
supervisé**. Elle possède déjà les parcours élèves des modules 2 à 8, le cockpit
formateur protégé, les sessions, l'anti-doublon, les exports, les supports, le
mode projection, PostgreSQL et les outils LAN. Elle n'est toutefois pas encore
un produit installable, maintenable et exploitable sans intervention du
développeur.

Positionnement réaliste :

- aujourd'hui : prototype avancé / pilote supervisé ;
- après les actions P0 : offre locale installée et accompagnée par un technicien ;
- après les actions P1 : produit commercial répétable et maintenable ;
- exposition Internet publique : hors périmètre et non autorisée sans une
  architecture de sécurité dédiée.

## Synthèse des preuves

| Domaine | État | Conclusion |
|---|---|---|
| Fonctionnel | Solide | Modules 2 à 8, sessions, exports, supports et cockpit sont présents. |
| Tests | Bloquant | 575 tests exécutés : 574 réussis, 1 échec sur l'ancienne page Paramètres. |
| Charge | Partiel | 1 500 GET, 100 utilisateurs concurrents, 0 échec, moyenne 1 316 ms. Les soumissions POST concurrentes ne sont pas validées. |
| Docker | Bon localement | Services web et PostgreSQL actifs et sains ; `/`, `/modules/`, `/supports/` répondent 200. |
| Terrain | Partiel | Smoke check : 14 PASS, 0 FAIL, 3 SKIP. Téléphone réel et port LAN 8011 non confirmés. |
| Sécurité | Bloquant | Secret de développement utilisable par défaut ; HTTP LAN non chiffré ; politique de données élèves absente. |
| Sauvegarde | Bloquant | Volumes persistants présents, mais sauvegarde PostgreSQL et restauration sur machine vierge non démontrées. |
| Portabilité | Bloquant | Des scripts Windows imposent `Ubuntu` et `/home/raillersing/projects/taf-local-forms`. |
| UX/accessibilité | Partiel | UI avancée, mais validation visuelle, mobile réel, clavier et navigateurs non clôturée. |
| Maintenance | À renforcer | Fichiers métier et tests très volumineux, aucune CI détectée, dépendances non verrouillées. |
| Juridique | Bloquant | Aucune licence, notice de confidentialité, politique de rétention ou inventaire des droits de contenu détecté. |

## Blocages P0

### 1. Branche non publiable

La branche contient un grand nombre de modifications non validées. La suite
`surveys.tests` échoue sur
`F023DashboardSettingsTests.test_settings_identifies_postgresql_without_exposing_sqlite_as_active` :
la route `/dashboard/settings/` redirige désormais (302), alors que le test
attend encore une page 200 contenant `PostgreSQL`.

Action : décider officiellement si Paramètres est supprimé ou fusionné dans
Réseau, mettre à jour le contrat, le test, la navigation et la documentation,
puis obtenir une suite complète verte.

### 2. Secrets et configuration

`config/settings.py` et Docker Compose acceptent des valeurs de développement
prévisibles pour `SECRET_KEY` et PostgreSQL. `manage.py check --deploy` remonte
cinq alertes : HSTS, redirection HTTPS, secret faible, cookies de session et
CSRF non sécurisés.

Pour un produit LAN HTTP, HSTS et les cookies `Secure` nécessitent une décision
d'architecture plutôt qu'une activation aveugle. En revanche, le démarrage doit
échouer si le secret ou le mot de passe de base conserve une valeur par défaut.

### 3. Données d'élèves mineurs

L'application collecte notamment identifiant scolaire, nom, classe, groupe et
réponses. L'accès formateur est protégé et aucun affichage public de ces données
n'a été identifié. Il manque cependant une notice compréhensible, la base légale
ou le consentement applicable, une durée de conservation, une procédure
d'effacement/export et une définition des responsabilités établissement/éditeur.

### 4. Sauvegarde et restauration

Les volumes Docker PostgreSQL et média sont persistants et ne doivent jamais
être supprimés avec `docker compose down -v`. Le script de sauvegarde dépend de
variables et outils hôte qui ne garantissent pas la détection de PostgreSQL dans
la configuration Docker par défaut. Aucun test de restauration complète sur une
machine vierge n'a été prouvé pendant cet audit.

Action : fournir une commande Docker Compose unique pour sauvegarder, vérifier,
restaurer et effectuer un exercice de reprise documenté.

### 5. Installation LAN non portable

Les scripts `taf-lan-sync.ps1` et `taf-lan-helper.ps1` contiennent le nom de
distribution WSL `Ubuntu` et le chemin absolu du poste de développement. Une
installation sous un autre utilisateur ou dans un autre dossier peut donc
démarrer Django mais échouer lors de la configuration réseau Windows.

Action : détecter la distribution et le dépôt, accepter des paramètres
explicites, ajouter un préflight, puis tester sur une seconde machine réelle.

### 6. Cadre commercial absent

Aucun fichier `LICENSE`, `NOTICE` ou inventaire des licences/droits des contenus,
logos et supports n'a été détecté. Une version commerciale exige aussi des
conditions d'utilisation, une politique de support, une procédure de mise à
jour et une matrice des plateformes supportées.

## Risques P1

- Les fichiers `views.py`, `models.py`, `forms.py` et `tests.py` concentrent de
  nombreuses responsabilités. Une modularisation par domaine améliorera les
  revues sans modifier le schéma ni les URL.
- Il n'existe pas de pipeline CI détecté pour reproduire automatiquement les
  contrôles Django, Docker et sécurité.
- `requirements.txt` utilise des plages de versions sans verrou ni hachage ; la
  reproductibilité et l'inventaire logiciel ne sont pas garantis.
- Les migrations sont lancées automatiquement au démarrage du conteneur web ;
  une mise à niveau commerciale doit séparer sauvegarde, migration et démarrage.
- Aucun healthcheck du service web n'est défini dans Compose.
- Le test de charge couvre des GET, pas 100 soumissions simultanées, exports ou
  uploads. Le débit observé ne constitue pas une garantie de capacité.
- Le smoke terrain a ignoré les routes authentifiées faute d'identifiants et les
  détails média faute de slugs publiés.
- L'acceptation UX reste partielle : pas de preuve automatisée multi-navigateur,
  de test lecteur d'écran, ni de validation finale sur téléphone 360/390 px.
- La documentation diverge : SQLite/PostgreSQL, version `v0.1.0`/`v0.2.0`, route
  Paramètres et ports 8010/8011 ne sont pas décrits uniformément.
- Les PDF de spécification n'ont pas fourni de texte exploitable localement ; la
  conformité détaillée aux cahiers des charges reste donc **Non confirmée**.

## Protections déjà présentes

- Authentification Django pour cockpit, administration, exports et outils LAN.
- Protection CSRF active.
- Filtrage public des supports publiés ; brouillons protégés par 404.
- Neutralisation des préfixes de formules dans les exports CSV.
- Contraintes et contrôles anti-doublon sur les soumissions.
- Aucune dépendance CDN nécessaire au fonctionnement en classe.
- Volumes persistants pour PostgreSQL et médias.
- `pip check`, `manage.py check`, contrôle des migrations et configuration
  Compose valides pendant l'audit.

## Validations exécutées

| Commande | Résultat |
|---|---|
| `scripts/dev/taf-skills-status` | OK |
| `scripts/dev/taf-graphify-status` | OK, aucune extraction lancée |
| `scripts/dev/taf-ponytail-check` | OK |
| `git diff --check` | OK avant ajout du rapport |
| `.venv-wsl/bin/python manage.py check` | OK |
| `.venv-wsl/bin/python manage.py check --deploy` | 5 avertissements de sécurité |
| `.venv-wsl/bin/python manage.py makemigrations --check --dry-run` | `No changes detected` |
| `.venv-wsl/bin/python manage.py test surveys.tests` | ÉCHEC : 574/575 réussis |
| `.venv-wsl/bin/python -m pip check` | OK |
| `docker compose config` | OK |
| `docker compose ps` | Web et PostgreSQL actifs/sains |
| `scripts/dev/taf-field-smoke-check` | 14 PASS, 0 FAIL, 3 SKIP |
| `scripts/dev/taf-load-smoke http://127.0.0.1:8010 100` | 1 500/1 500 GET réussis |

## Décision recommandée

Ne pas réécrire l'application. Geler les fonctionnalités et mener une refonte
de **productisation ciblée** selon
`docs/audits/COMMERCIALIZATION_ROADMAP.md`. La vente ou le déploiement chez un
tiers doit attendre la clôture des P0, une restauration réussie sur une machine
vierge et une validation terrain avec un téléphone réel.
