# F024 — Audit des sources Modules 5 à 8

## 1. Résumé exécutif

Audit terminé le 23 juin 2026. Les 8 fichiers sources (4 présentations PowerPoint `.pptx`, 4 scripts Google Forms `.gs`) ont été inspectés. Chaque module (5 à 8) suit exactement le même modèle que les Modules 2, 3 et 4 déjà intégrés dans l'application.

| Module | Complexité | Quiz | Scoring max | Champs texte longs | Migration nécessaire |
|--------|-----------|------|-------------|-------------------|---------------------|
| Module 5 – Email | Moyenne | 6 QCM | 6 pts | 4 | Oui |
| Module 6 – Ressources | Moyenne | 6 QCM+Checkbox | 6 pts | 3 | Oui |
| Module 7 – Sécurité | Élevée | 7 QCM+Checkbox | 7 pts | 5 | Oui |
| Module 8 – Synthèse | Élevée | 6 QCM+Checkbox | 6 pts | 7 | Oui |

**Aucun blocage majeur.** Les 4 modules peuvent être intégrés en suivant le pattern existant (model → form → view → template → url → test).

---

## 2. Fichiers audités

### Présentations

| Fichier | Taille | Slides |
|---------|--------|--------|
| `documents/source/presentations/Module_5_TAfHSSiM_Email_Outils_Communication.pptx` | 458 KB | 18 |
| `documents/source/presentations/Module_6_TAfHSSiM_Ressources_Educatives_En_Ligne.pptx` | 420 KB | 18 |
| `documents/source/presentations/Module_7_TAfHSSiM_Securite_En_Ligne.pptx` | 419 KB | 18 |
| `documents/source/presentations/Module_8_TAfHSSiM_Synthese_Exercices_Pratiques.pptx` | 413 KB | 18 |

### Scripts Google Forms

| Fichier | Lignes | Questions totales |
|---------|--------|-------------------|
| `documents/source/forms/TAfHSSiM_Module5_Google_Form_Code.gs` | 195 | Sections: 7, Questions: 25 |
| `documents/source/forms/TAfHSSiM_Module6_Google_Form_Code.gs` | 201 | Sections: 7, Questions: 23 |
| `documents/source/forms/TAfHSSiM_Module7_Google_Form_Code.gs` | 221 | Sections: 7, Questions: 24 |
| `documents/source/forms/TAfHSSiM_Module8_Google_Form_Code.gs` | 195 | Sections: 7, Questions: 25 |

---

## 3. Tableau Modules 5 à 8

| Module | Titre | Type | Complexité | Migration | Risques |
|--------|-------|------|-----------|-----------|---------|
| M5 | Email et outils de communication | Formulaire + quiz | Moyenne | Oui | Questions checkbox multi-sélections (quiz_q5) |
| M6 | Ressources éducatives en ligne | Formulaire + quiz | Moyenne | Oui | Questions checkbox multi-sélections (quiz_q6, q7) |
| M7 | Sécurité en ligne | Formulaire + quiz | Élevée | Oui | Checkbox dans exercice pratique, 7 quiz QCM |
| M8 | Synthèse et exercices pratiques | Formulaire + quiz (synthèse) | Élevée | Oui | 7 champs texte longs, feedback 4 champs |

---

## 4. Détail par module

### 4.1 Module 5 — Email et outils de communication

#### Contenu pédagogique (18 slides)

- Anatomie d'un email (À, Cc, Cci, Objet, Corps, PJ)
- Méthode en 5 lignes (salutation, contexte, demande, remerciement, signature)
- Ton et politesse, pièces jointes, répondre/transférer, organisation
- Sécurité email (mot de passe, liens suspects)
- 2 activités pratiques (+ mini-quiz oral)

#### Structure du formulaire (.gs)

| Section | Contenu | Type |
|---------|---------|------|
| 1. Identification | school_id, full_name, class_level, group | 4 champs (pattern existant) |
| 2. Auto-évaluation | 3 questions « Pas encore / Un peu / Oui / Oui facilement » | RadioSelect |
| 3. Résumé cours | Texte statique | Section header |
| 4. Todo list | 8 tâches (destinataire, objet, salutation, message, politesse, signature, PJ, relecture) | 8 BooleanField |
| 5. Mini-quiz | 6 questions : 4 Vrai/Faux + 2 QCM (objet clair + formule politesse) + 1 checkbox (vérifier avant envoi) | Quiz avec scoring |
| 6. Exercice pratique | À qui écrire, objet, message (paragraph), PJ besoin, fichier, outil adapté | TextField + ChoiceField |
| 7. Feedback | Compris, difficile, sentiment | TextField + ChoiceField |

#### Quiz détaillé

| Question | Type | Bonne réponse | Points |
|----------|------|---------------|--------|
| Q1: Email sert à communiquer avec professeur | V/F | Vrai | 1 |
| Q2: Objet aide destinataire | V/F | Vrai | 1 |
| Q3: Envoyer sans relire | V/F | Faux | 1 |
| Q4: Donner mot de passe par email | V/F | Faux | 1 |
| Q5: Objet le plus clair (choix parmi 4) | QCM | « Demande d'information sur le devoir de mathématiques » | 1 |
| Q6: Formule adaptée pour commencer | QCM | « Bonjour Monsieur / Madame » | 1 |
| Q7: Que vérifier avant d'envoyer (checkbox) | Checkbox | 4 bonnes réponses (pas « mot de passe ») | 1 |

**Scoring max : 7 points**

#### Champs à modéliser

```
Module5Submission:
  # Student link (FK), session (FK), school_id_number_snapshot, timestamps, computed_score
  
  # Auto-évaluation (3 champs)
  auto_eval_email_purpose: SELF_EVAL_CHOICES (pas_encore/un_peu/bien/tres_bien)
  auto_eval_write_email: SELF_EVAL_CHOICES
  auto_eval_attach_file: SELF_EVAL_CHOICES
  
  # Todo (8 booléens)
  todo_spotted_recipient: BooleanField
  todo_written_clear_subject: BooleanField
  todo_started_greeting: BooleanField
  todo_written_short_message: BooleanField
  todo_added_politeness: BooleanField
  todo_signed_name: BooleanField
  todo_checked_attachment: BooleanField
  todo_reread_before_sending: BooleanField
  
  # Quiz (7 champs)
  quiz_q1..q4: TRUE_FALSE_UNKNOWN_CHOICES
  quiz_q5: QUIZ_Q5_CHOICES (objet clair parmi 4)
  quiz_q6: QUIZ_Q6_CHOICES (formule adaptée parmi 4)
  quiz_q7_selected: JSONField (checkbox, 5 options dont 4 correctes)
  
  # Pratique (5 champs)
  practical_who_writing_to: CharField
  practical_email_subject: CharField
  practical_email_message: TextField
  practical_needs_attachment: YES_NO_CHOICES (Oui/Non/Je ne sais pas)
  practical_attachment_file: CharField (optional)
  practical_best_tool: BEST_TOOL_CHOICES (Email / Facebook / Message sans nom / TikTok)
  
  # Feedback (3 champs)
  feedback_understood_today: TextField
  feedback_still_difficult: TextField (blank=True)
  feedback_confidence_email: CONFIDENCE_CHOICES
```

#### Scoring

```python
def calculate_score(self):
    score = 0
    if self.quiz_q1 == "vrai": score += 1
    if self.quiz_q2 == "vrai": score += 1
    if self.quiz_q3 == "faux": score += 1
    if self.quiz_q4 == "faux": score += 1
    if self.quiz_q5 == "demande_information_devoir_mathematiques": score += 1
    if self.quiz_q6 == "bonjour_monsieur_madame": score += 1
    if set(self.quiz_q7_selected) == QUIZ_Q7_CORRECT_ANSWERS: score += 1
    return score
```

#### Templates nécessaires

- `module_5_unavailable.html`
- `module_5_form.html`
- `module_5_success.html`
- `dashboard_module_5.html`
- `partials/module_5_pedagogy.html`

#### Tests nécessaires

- Test soumission formulaire complet
- Test validation doublon
- Test scoring (7 quiz responses)
- Test todo completion tracking
- Test CSV export
- Test dashboard aggregation
- Test contenu pédagogique

---

### 4.2 Module 6 — Ressources éducatives en ligne

#### Contenu pédagogique (18 slides)

- Types de ressources (cours, vidéo, exercice, outil)
- 5 critères de sélection (matière, niveau, langue, objectif, fiabilité)
- Méthode en 5 étapes (besoin, recherche, choix, utilisation, trace)
- Recherche précise vs vague, lire les résultats
- Prendre des notes (3 idées, 2 mots, 1 question)
- Carnet de ressources, bonnes habitudes, pièges
- Activité guidée + mini-défi

#### Structure du formulaire (.gs)

| Section | Contenu |
|---------|---------|
| 1. Identification | 4 champs standards |
| 2. Auto-évaluation | 3 questions (trouver, choisir, garder une ressource) |
| 3. Résumé cours | Texte statique |
| 4. Todo list | 8 tâches (choisir matière, chercher, ouvrir, vérifier niveau, noter titre, noter lien, écrire appris, garder) |
| 5. Mini-quiz | 6 questions : 3 V/F + 1 QCM + 2 checkbox |
| 6. Exercice pratique | Matière, quoi réviser, type ressource, nom/lien, adapté ?, qu'est-ce appris |
| 7. Feedback | Compris, difficile, sentiment |

#### Quiz détaillé

| Question | Type | Bonne réponse | Points |
|----------|------|---------------|--------|
| Q1: Ressource peut être vidéo/PDF/exercice | V/F | Vrai | 1 |
| Q2: Bonne ressource adaptée au niveau | V/F | Vrai | 1 |
| Q3: Regarder vidéo sans notes suffit | V/F | Faux | 1 |
| Q4: Type utile pour s'entraîner | QCM | « Un exercice corrigé » | 1 |
| Q5: Recherche adaptée pour PDF | QCM | « photosynthèse cours lycée PDF » | 1 |
| Q6: Signes ressource utile (checkbox) | Checkbox | 4 signes corrects | 1 |
| Q7: Que faire après avoir trouvé (checkbox) | Checkbox | 4 actions correctes | 1 |

**Scoring max : 7 points**

#### Champs à modéliser

```
Module6Submission:
  auto_eval_find_resource: SELF_EVAL_CHOICES
  auto_eval_choose_resource: SELF_EVAL_CHOICES
  auto_eval_keep_link: SELF_EVAL_CHOICES
  
  # Todo (8 booléens)
  todo_chose_subject: BooleanField
  todo_searched_resource: BooleanField
  todo_opened_video_pdf_exercise: BooleanField
  todo_checked_level: BooleanField
  todo_noted_resource_title: BooleanField
  todo_noted_link_or_site: BooleanField
  todo_written_what_learned: BooleanField
  todo_kept_for_later: BooleanField
  
  # Quiz (7 champs)
  quiz_q1..q3: TRUE_FALSE_UNKNOWN_CHOICES
  quiz_q4: QUIZ_Q4_CHOICES (type entraînement)
  quiz_q5: QUIZ_Q5_CHOICES (recherche PDF)
  quiz_q6_selected: JSONField (signes utilité, 5 options dont 4 correctes)
  quiz_q7_selected: JSONField (actions après trouvé, 5 options dont 4 correctes)
  
  # Pratique (5 champs)
  practical_subject: PRACTICAL_SUBJECT_CHOICES (8 matières)
  practical_what_to_revise: CharField
  practical_resource_type: RESOURCE_TYPE_CHOICES (Vidéo/PDF/Exercice/Dictionnaire/Schéma/Quiz/Autre)
  practical_resource_name_or_link: CharField
  practical_adapted_level: YES_SOMEWHAT_NO_UNKNOWN_CHOICES
  practical_what_learned: TextField
  
  # Feedback (3 champs) — pattern standard
  feedback_understood_today: TextField
  feedback_still_difficult: TextField (blank=True)
  feedback_confidence_resources: CONFIDENCE_CHOICES
```

#### Templates nécessaires

- `module_6_unavailable.html`
- `module_6_form.html`
- `module_6_success.html`
- `dashboard_module_6.html`
- `partials/module_6_pedagogy.html`

---

### 4.3 Module 7 — Sécurité en ligne

#### Contenu pédagogique (18 slides)

- Risques en ligne (compte piraté, arnaque, données exposées, cyberharcèlement)
- Mot de passe (faible vs fort, ne pas partager)
- Validation en deux étapes
- Message suspect et hameçonnage
- Méthode STOP (Stop, Trouver, Observer, Parler)
- Informations personnelles
- Cyberharcèlement
- Appareils partagés
- Téléchargements
- Que faire si on a cliqué ?
- Activité pratique + mini-défi

#### Structure du formulaire (.gs)

| Section | Contenu |
|---------|---------|
| 1. Identification | 4 champs standards |
| 2. Auto-évaluation | 3 questions (mot de passe sûr, message suspect, infos à protéger) |
| 3. Résumé cours | Texte statique |
| 4. Todo list | 8 tâches spécifiques sécurité |
| 5. Mini-quiz | 7 questions : 3 V/F + 1 QCM + 3 checkbox |
| 6. Exercice pratique | 5 champs dont checkbox pour infos et réactions |
| 7. Feedback | 3 champs standards |

#### Quiz détaillé

| Question | Type | Bonne réponse | Points |
|----------|------|---------------|--------|
| Q1: Donner mot de passe à un ami | V/F | Faux | 1 |
| Q2: Mot de passe long et unique protège | V/F | Vrai | 1 |
| Q3: Validation 2 étapes protège plus | V/F | Vrai | 1 |
| Q4: Message urgent cadeau → que faire | QCM | « Vérifier et demander de l'aide » | 1 |
| Q5: Signes message suspect (checkbox) | Checkbox | 4 signes (pas « vient du professeur ») | 1 |
| Q6: Infos à protéger (checkbox) | Checkbox | 4 infos (pas « leçon publique ») | 1 |
| Q7: Si cliqué lien suspect (checkbox) | Checkbox | 3 bonnes réactions (pas « garder secret », pas « donner code ») | 1 |

**Scoring max : 7 points**

#### Champs à modéliser

```
Module7Submission:
  auto_eval_create_password: SELF_EVAL_CHOICES
  auto_eval_spot_suspicious: SELF_EVAL_CHOICES
  auto_eval_protect_info: SELF_EVAL_CHOICES
  
  # Todo (8 booléens)
  todo_identified_weak_password: BooleanField
  todo_written_password_rules: BooleanField
  todo_understood_no_share_code: BooleanField
  todo_observed_suspicious_message: BooleanField
  todo_spotted_two_danger_signs: BooleanField
  todo_applied_stop_method: BooleanField
  todo_listed_info_to_protect: BooleanField
  todo_know_how_to_ask_help: BooleanField
  
  # Quiz (7 champs)
  quiz_q1..q3: TRUE_FALSE_UNKNOWN_CHOICES
  quiz_q4: QUIZ_Q4_CHOICES (que faire si message urgent)
  quiz_q5_selected: JSONField (signes message suspect, 5 options dont 4 correctes)
  quiz_q6_selected: JSONField (infos à protéger, 5 options dont 4 correctes)
  quiz_q7_selected: JSONField (si cliqué suspect, 5 options dont 3 correctes)
  
  # Pratique (5 champs)
  practical_situation_analyzed: SITUATION_CHOICES (Faux message/Lien suspect/Mot de passe/Cyberharcèlement/Partage/Autre)
  practical_describe_situation: TextField
  practical_danger_signs: TextField
  practical_info_to_protect: MultipleChoiceField (checkbox, 7 options)
  practical_good_reaction: MultipleChoiceField (checkbox, 6 options dont 5 correctes)
  practical_explain_choice: TextField
  
  # Feedback (3 champs)
  feedback_understood_today: TextField
  feedback_still_difficult: TextField (blank=True)
  feedback_confidence_security: CONFIDENCE_CHOICES
```

#### Particularité Module 7

- L'exercice pratique a des checkbox intégrées (choix multiples dans le formulaire)
- C'est le plus complexe des modules 5-8
- La méthode STOP a du contenu pédagogique spécifique

---

### 4.4 Module 8 — Synthèse et exercices pratiques

#### Contenu pédagogique (18 slides)

- Rappel Modules 2 à 7
- Mission finale : mini-fiche d'apprentissage
- 6 étapes (besoin → chercher → lire résultats → vérifier source → choisir ressource → produire)
- 3 exercices (mission recherche, mini-fiche, message de partage)
- Présentation en groupe
- Auto-évaluation (6 items)
- Observation formateur

#### Structure du formulaire (.gs)

| Section | Contenu |
|---------|---------|
| 1. Identification | 4 champs standards |
| 2. Auto-évaluation | 3 questions transversales (recherche, source fiable, résumer) |
| 3. Résumé cours | Texte statique (synthèse transversale) |
| 4. Todo list | **10 tâches** (plus que les autres modules) |
| 5. Mini-quiz | 6 questions : 5 V/F + 1 checkbox |
| 6. Exercice pratique | **7 champs** dont 3 ParagraphField et 1 checkbox |
| 7. Feedback | **4 champs** (compris, difficile, sentiment + « une chose à continuer ») |

#### Quiz détaillé

| Question | Type | Bonne réponse | Points |
|----------|------|---------------|--------|
| Q1: Module 8 sert à appliquer compétences | V/F | Vrai | 1 |
| Q2: Bonne recherche commence par question claire | V/F | Vrai | 1 |
| Q3: Suffit de copier premier résultat | V/F | Faux | 1 |
| Q4: Avant d'utiliser info, vérifier source | V/F | Vrai | 1 |
| Q5: Message académique clair et respectueux | V/F | Vrai | 1 |
| Q6: Partager mot de passe avec ami confiance | V/F | Faux | 1 |
| Q7: Que faut-il faire (checkbox) | Checkbox | 5 bonnes actions (pas « copier sans comprendre ») | 1 |

**Scoring max : 7 points**

#### Champs à modéliser

```
Module8Submission:
  auto_eval_do_useful_search: SELF_EVAL_CHOICES
  auto_eval_verify_source: SELF_EVAL_CHOICES
  auto_eval_summarize_own_words: SELF_EVAL_CHOICES
  
  # Todo (10 booléens — le plus long)
  todo_chose_subject: BooleanField
  todo_written_starting_question: BooleanField
  todo_transformed_into_keywords: BooleanField
  todo_found_first_source: BooleanField
  todo_found_second_source: BooleanField
  todo_checked_author_site_date_evidence: BooleanField
  todo_chose_most_useful: BooleanField
  todo_noted_three_ideas: BooleanField
  todo_prepared_short_synthesis: BooleanField
  todo_presented_or_explained: BooleanField
  
  # Quiz (7 champs)
  quiz_q1..q6: TRUE_FALSE_UNKNOWN_CHOICES
  quiz_q7_selected: JSONField (checkbox, 6 options dont 5 correctes)
  
  # Pratique (7 champs)
  practical_subject: PRACTICAL_SUBJECT_CHOICES
  practical_topic: CharField
  practical_starting_question: TextField
  practical_keywords_used: CharField
  practical_first_source: CharField
  practical_second_source: CharField (blank=True)
  practical_verified_elements: MultipleChoiceField (checkbox, 6 options)
  practical_three_ideas: TextField
  practical_synthesis: TextField (4 à 6 lignes)
  practical_academic_message: TextField (blank=True)
  
  # Feedback (4 champs — un de plus)
  feedback_best_success: TextField
  feedback_still_difficult: TextField (blank=True)
  feedback_confidence_internet_studies: CONFIDENCE_CHOICES
  feedback_one_thing_to_practice: TextField (blank=True)
```

#### Particularité Module 8

- Module de **synthèse transversale** : réutilise toutes les compétences M2-M7
- 10 todo items (contre 8 pour les autres)
- 3 ParagraphField dans l'exercice pratique
- 4 champs de feedback (contre 3 pour les autres)
- Le quiz a 7 questions mais 6 sont V/F simples, 1 checkbox → plus simple que M7

---

## 5. Proposition d'architecture d'intégration

Chaque module doit suivre le pattern existant (M2-M4) rigoureusement :

```
1. Model (models.py)
   ├── Module5Submission(Model)
   ├── Module6Submission(Model)
   ├── Module7Submission(Model)
   └── Module8Submission(Model)

2. Form (forms.py)
   ├── Module5SubmissionForm(Form)
   ├── Module6SubmissionForm(Form)
   ├── Module7SubmissionForm(Form)
   └── Module8SubmissionForm(Form)

3. Views (views.py)
   ├── module_5_form, module_5_success, dashboard_module_5, export_module_5_csv
   ├── module_6_form, module_6_success, dashboard_module_6, export_module_6_csv
   ├── module_7_form, module_7_success, dashboard_module_7, export_module_7_csv
   └── module_8_form, module_8_success, dashboard_module_8, export_module_8_csv

4. Templates
   ├── module_{5,6,7,8}_form.html
   ├── module_{5,6,7,8}_success.html
   ├── module_{5,6,7,8}_unavailable.html
   ├── dashboard_module_{5,6,7,8}.html
   └── partials/module_{5,6,7,8}_pedagogy.html

5. URLs (urls.py)
   ├── /module-{5,6,7,8}/
   ├── /module-{5,6,7,8}/success/<id>/
   ├── /dashboard/module-{5,6,7,8}/
   └── /dashboard/export/module-{5,6,7,8}.csv

6. Tests (tests.py)
   ├── test_module_{5,6,7,8}_form_valid
   ├── test_module_{5,6,7,8}_duplicate
   ├── test_module_{5,6,7,8}_scoring
   ├── test_module_{5,6,7,8}_dashboard
   ├── test_module_{5,6,7,8}_csv_export
   └── test_module_{5,6,7,8}_pedagogy_content

7. Seed data
   └── Ajouter TrainingModule records MODULE_5 à MODULE_8
```

### Modifications additionnelles

- `surveys/views.py` : mettre à jour `URL_MAP` dans `student_modules` et `summary_map` dans `student_module_detail`
- `surveys/views.py` : mettre à jour `dashboard_home` pour inclure M5-M8 dans l'agrégation
- `templates/surveys/student_modules.html` : ajouter les cartes M5-M8
- `templates/surveys/student_module_detail.html` : ajouter les onglets M5-M8
- `templates/surveys/dashboard_home.html` : ajouter M5-M8 au tableau de bord
- Dashboard navigation : mettre à jour les onglets pour inclure M5-M8

---

## 6. Recommandation de découpage PR

### Option A : 4 PR séquentiels (recommandée)

| PR | ID | Contenu | Risque | Tests |
|----|----|---------|--------|-------|
| 1 | **F025** | Module 5 – Email et outils de communication | Faible | ~50 tests |
| 2 | **F026** | Module 6 – Ressources éducatives en ligne | Faible | ~50 tests |
| 3 | **F027** | Module 7 – Sécurité en ligne | Moyen | ~55 tests |
| 4 | **F028** | Module 8 – Synthèse et exercices pratiques | Moyen | ~55 tests |

### Option B : 2 PR (F025 = M5+M6, F026 = M7+M8)

Avantage : plus rapide à merger.
Risque : PR plus grandes, relecture plus longue, conflits potentiels.

### Recommandation finale

**Option A (4 PR séquentiels)** est recommandée car :

1. Chaque module a son propre modèle (`Module5Submission`, etc.) → migration distincte
2. Permet une validation indépendante par module
3. Réduit le risque de conflit par PR
4. Facilite le déploiement terrain progressif (un module à la fois)
5. Pattern identique entre M5 et M6 facilite F025 en lot si souhaité

Proposition pour l'ordre : **M5 → M6 → M7 → M8**

---

## 7. Questions ouvertes

1. **Module 7** : l'exercice pratique a des checkbox dans le formulaire (2 questions avec choix multiples). Faut-il les stocker comme champs séparés ou comme JSONField ?
   → Recommandation : JSONField pour `practical_info_to_protect` et `practical_good_reaction` (comme `quiz_q4_selected` dans M2)

2. **Module 8 feedback** : 4 champs au lieu de 3 (ajout de `feedback_one_thing_to_practice`). Faut-il aligner tous les modules sur 4 champs ?
   → Recommandation : 4 champs pour M8 seulement, garder 3 pour les autres

3. **Module 8** : la todo list a 10 items (vs 8 pour les autres modules). Faut-il les garder tous ?
   → Oui, le module de synthèse est plus long

4. **Dashboard global** (`dashboard_home`) : il faudra l'étendre pour intégrer M5-M8. Faut-il une réarchitecture du dashboard ou une extension incrémentale ?
   → Extension incrémentale : ajouter des blocs dans `dashboard_home` pour M5-M8

5. **Présence temps réel** : faut-il étendre `FormPresence` pour supporter M5-M8 ?
   → Oui, mettre à jour le heartbeat pour accepter les codes modules M5-M8

6. **Seeds** : les commandes de création de session (`create_module_X_session`) devront être créées ou étendues pour M5-M8 (comme pour M2-M4)

---

## 8. Validations à exécuter pour chaque module

| Validation | Commande |
|-----------|----------|
| Django system checks | `manage.py check` |
| Tests en survol | `manage.py test surveys.tests -k module_5` (et 6, 7, 8) |
| Tests complets | `manage.py test surveys.tests` |
| Migrations check | `manage.py makemigrations --check --dry-run` |
| Whitespace | `git diff --check` |
| Docker config | `docker compose config` |
| Aucun secret | Vérifier le diff |
| Form accessible | `curl -I http://localhost:8010/module-5/` |
| Dashboard accessible | `curl -I http://localhost:8010/dashboard/module-5/` (après login) |
| Export CSV | `curl -I http://localhost:8010/dashboard/export/module-5.csv` (après login) |

---

## 9. Estimation effort

| Module | Model | Form | Views | Templates | Tests | Total estimé |
|--------|-------|------|-------|-----------|-------|-------------|
| M5 | 1 | 1 | 4 | 5 | ~50 | ~350 lignes |
| M6 | 1 | 1 | 4 | 5 | ~50 | ~350 lignes |
| M7 | 1 | 1 | 4 | 5 | ~55 | ~400 lignes |
| M8 | 1 | 1 | 4 | 5 | ~55 | ~400 lignes |
| **Total** | **4** | **4** | **16** | **20** | **~210** | **~1500 lignes** |

Chaque module ajoutera ~100-120 tests à la suite existante (255 tests actuellement → ~355-375 après F025-F028).
