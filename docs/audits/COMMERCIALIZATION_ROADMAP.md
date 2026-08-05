# Feuille de route de productisation

Référence : `COMMERCIAL_READINESS_AUDIT_2026-07-12.md`.

## Principe

La base fonctionnelle doit être conservée. Une réécriture complète augmenterait
le risque sur les sessions, le scoring, les exports et l'anti-doublon. La bonne
stratégie est une stabilisation incrémentale, avec un commit et une validation
humaine par tranche.

## P0 - Rendre le produit livrable

### Tranche 1 - Baseline de release

- Résoudre le test Paramètres/Réseau et obtenir 100 % des tests au vert.
- Clôturer les modifications non commitées par lots cohérents.
- Aligner numéro de version, tag, notes de version et documentation.
- Exécuter l'acceptation manuelle élève/formateur sur 360, 390, 768 et 1366 px.
- Livrable : candidat de release reproductible, sans migration inattendue.

### Tranche 2 - Installation portable

- Supprimer les chemins utilisateur et la distribution WSL codés en dur.
- Ajouter un préflight Windows/WSL/Docker avec messages d'erreur actionnables.
- Créer une commande d'installation idempotente et une commande de diagnostic.
- Tester installation, arrêt, redémarrage et désinstallation non destructive sur
  une seconde machine Windows.
- Livrable : installation assistée en moins de 30 minutes.

### Tranche 3 - Sécurité et confidentialité

- Refuser les secrets et mots de passe de démonstration au démarrage hors test.
- Définir le modèle de menace du LAN de confiance et la stratégie HTTP/TLS.
- Rédiger notice élèves, rétention, suppression, export et rôles de traitement.
- Vérifier permissions formateur/admin, sessions, CSRF, uploads et CSV.
- Livrable : revue sécurité `APPROVE` et dossier de conformité validé humainement.

### Tranche 4 - Sauvegarde et reprise

- Rendre sauvegarde/restauration PostgreSQL compatibles avec Compose.
- Inclure médias, métadonnées, version d'application et somme de contrôle.
- Tester une restauration sur une pile vierge et documenter le RPO/RTO.
- Ajouter une sauvegarde avant toute migration de release.
- Livrable : procès-verbal de restauration réussie.

### Tranche 5 - Qualification terrain

- Tester un vrai téléphone sur Wi-Fi/hotspot et le port 8011.
- Tester 100 soumissions POST concurrentes sans doublons ni perte de réponse.
- Tester exports, vidéo, upload, coupure réseau et reprise après redémarrage.
- Faire signer la recette par un formateur et un responsable produit.
- Livrable : fiche terrain complète, sans `SKIP` critique.

### Tranche 6 - Cadre commercial

- Choisir et ajouter la licence logicielle et les notices tierces.
- Vérifier les droits sur logo, textes pédagogiques, documents et vidéos.
- Définir plateformes supportées, support, mises à jour et fin de vie.
- Livrable : dossier juridique et offre d'installation accompagnée.

## P1 - Rendre le produit maintenable

- Scinder progressivement vues, formulaires et tests par domaines : élèves,
  modules, supports, cockpit, réseau et exploitation.
- Conserver modèles, migrations, noms d'URL et contrats template pendant chaque
  extraction ; interdire les refactorings massifs sans tests de caractérisation.
- Ajouter CI : checks Django, tests, migrations, Compose, statiques et scans.
- Verrouiller les dépendances, générer un SBOM et définir le processus de mise à
  jour de sécurité.
- Séparer migration contrôlée et démarrage web ; ajouter un healthcheck web.
- Ajouter tests navigateur des parcours critiques et audit accessibilité.

Critère de sortie : une release peut être reconstruite depuis un tag, installée
sur une machine propre et restaurée sans connaissance implicite du développeur.

## P2 - Industrialiser l'offre

- Fournir un installateur ou paquet signé si le marché exige du self-service.
- Ajouter un assistant local de configuration réseau et de diagnostic.
- Définir canal de mises à jour, rollback, support et collecte de diagnostics
  explicitement consentie et sans données élèves.
- Produire guide administrateur, guide formateur et fiche de dépannage versionnés.

## Ordre recommandé

Ne pas commencer la modularisation P1 avant la baseline verte de la tranche 1.
Ne pas vendre comme produit autonome avant la clôture complète de P0. Une offre
pilote accompagnée reste possible avec accord explicite sur les limites, une
sauvegarde vérifiée et une présence technique pendant la séance.
