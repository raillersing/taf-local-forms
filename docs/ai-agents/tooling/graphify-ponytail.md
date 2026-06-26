# Graphify + Ponytail — Outillage agent TAf Local Forms

## 1. But

Graphify et Ponytail sont des outils pour agents IA. Ce ne sont pas des
dépendances runtime Django.

Graphify :

- cartographie le repo ;
- produit un knowledge graph ;
- aide les agents à comprendre la structure avant de modifier le code ;
- doit être utilisé pour réduire les recherches répétitives dans le repo.

Ponytail :

- applique une logique anti-over-engineering ;
- force l’agent à réutiliser l’existant ;
- limite les nouvelles dépendances ;
- exige la plus petite PR utile.

## 2. Règles de sécurité

- jamais de `.env`
- jamais de dumps SQL
- jamais de bases locales
- jamais de backups
- jamais de logs sensibles
- jamais de médias runtime
- jamais de secrets dans Graphify
- jamais de fichiers sensibles dans `graphify-out/`
- jamais de configuration globale sans accord humain

## 3. Règles projet

- Graphify/Ponytail ne remplacent pas `AGENTS.md`.
- Graphify/Ponytail ne remplacent pas les tests.
- Ponytail ne doit jamais supprimer :
- validation
- sécurité
- accessibilité
- backup
- protection données
- anti-doublon
- auth dashboard/export/réseau
- Graphify doit aider à comprendre, pas décider seul.

## 4. Installation Graphify recommandée

Documenter, sans exécuter automatiquement :

```bash
uv tool install graphifyy
# ou
pipx install graphifyy
```

Installation projet, seulement après accord humain :

```bash
graphify install --project --platform codex
graphify install --project --platform opencode
graphify install --project --platform agents
```

Notes :

- Le package PyPI attendu est `graphifyy`.
- La commande CLI reste `graphify`.
- Pour Codex, la commande dans le chat peut être `$graphify` selon la plateforme.
- Pour OpenCode, suivre la commande de plateforme indiquée par Graphify.
- Ne pas utiliser d’option nécessitant API key sans accord humain.

## 5. Usage Graphify recommandé

Documenter, sans exécuter automatiquement :

```bash
graphify . --no-viz
graphify query "Quels fichiers structurent les modules TAfHSSiM ?"
graphify query "Quelles routes et vues sont liées aux dashboards formateur ?"
graphify query "Quels fichiers sont touchés avant d’ajouter la médiathèque ?"
```

Règles :

- lire `graphify-out/GRAPH_REPORT.md` seulement si ce fichier existe et a été revu ;
- préférer les requêtes ciblées `graphify query` au fait de relire tout le repo ;
- ne pas committer `graphify-out/` dans cette première tâche.

## 6. Sorties Graphify

- `graphify-out/graph.html`
- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`

Politique initiale :

- `graphify-out/` reste non committé jusqu’à revue humaine ;
- `GRAPH_REPORT.md` pourra être committé plus tard seulement après vérification anti-secret ;
- `graph.json` et `graph.html` ne sont pas committés dans F033T.

## 7. Installation Ponytail recommandée

Documenter, sans exécuter automatiquement :

Codex :

```bash
codex plugin marketplace add DietrichGebert/ponytail
codex
# puis ouvrir /plugins, installer Ponytail,
# ouvrir /hooks, revoir et approuver les hooks si acceptés par l’humain
```

OpenCode :

```json
{
  "plugin": ["@dietrichgebert/ponytail"]
}
```

Règles :

- ne pas modifier automatiquement `opencode.json` si cela risque de casser un workflow existant ;
- documenter l’option ;
- proposer une intégration projet seulement si le fichier existe déjà et si la modification est sûre.

## 8. Mode Ponytail attendu pour ce projet

Niveaux :

- `lite` : rappel léger
- `full` : recommandé par défaut
- `ultra` : seulement pour audits anti-over-engineering
- `off` : désactivé temporairement si l’humain le demande

Règles Ponytail à appliquer :

1. Est-ce nécessaire ?
2. Existe déjà dans le code ?
3. La bibliothèque standard suffit-elle ?
4. Django sait-il déjà le faire ?
5. Une dépendance installée le fait-elle déjà ?
6. Une petite modification suffit-elle ?
7. Sinon seulement : écrire le minimum robuste.

## 9. Workflow agent avant chaque tâche future

1. Lire `AGENTS.md`.
2. Lire `docs/ai-agents/tooling/graphify-ponytail.md`.
3. Si disponible et validé, consulter `graphify-out/GRAPH_REPORT.md`.
4. Utiliser Ponytail pour réduire le scope.
5. Identifier les fichiers réellement nécessaires.
6. Éviter les nouvelles dépendances.
7. Vérifier les tests.
8. Ne jamais sacrifier sécurité/données/accessibilité.
9. Créer une petite PR ciblée.

## 10. Application aux prochaines tâches

- `F034A` : archivage prototype/PDF et plan d’intégration, aucun changement fonctionnel.
- `F035` : design system CSS local, sans backend.
- `F036` : navigation étudiant/formateur, routes existantes conservées.
- `F037` : cockpit + QR local, pas de CDN.
- `F038` : médiathèque avec migrations dédiées et backup préalable.

## 11. État projet pour F033T

- Aucun lancement automatique de Graphify n’est autorisé dans cette mission.
- Aucun plugin Ponytail n’est installé globalement dans cette mission.
- `opencode.json` n’existe pas actuellement dans ce dépôt ; l’option OpenCode reste donc documentaire.
- `graphify-out/` ne doit pas être committé dans F033T.
