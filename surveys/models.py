from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


school_id_validator = RegexValidator(
    regex=r"^\d{2}$",
    message="Le numero d'identification doit contenir exactement 2 chiffres.",
)


class Student(models.Model):
    CLASS_LEVEL_SECONDE = "seconde"
    CLASS_LEVEL_PREMIERE = "premiere"
    CLASS_LEVEL_AUTRE = "autre"
    CLASS_LEVEL_CHOICES = [
        (CLASS_LEVEL_SECONDE, "Seconde"),
        (CLASS_LEVEL_PREMIERE, "Premiere"),
        (CLASS_LEVEL_AUTRE, "Autre"),
    ]

    school_id_number = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
        verbose_name="Numero d'identification a l'ecole",
    )
    full_name = models.CharField(max_length=255, verbose_name="Nom et prenom")
    class_level = models.CharField(max_length=20, choices=CLASS_LEVEL_CHOICES, verbose_name="Classe / niveau")
    group_name = models.CharField(max_length=100, blank=True, verbose_name="Groupe ou salle")

    class Meta:
        ordering = ["school_id_number", "full_name"]

    def __str__(self) -> str:
        return f"{self.school_id_number} - {self.full_name}"


class TrainingModule(models.Model):
    code = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class TrainingSession(models.Model):
    module = models.ForeignKey(TrainingModule, on_delete=models.PROTECT, related_name="sessions")
    date = models.DateField()
    location = models.CharField(max_length=255)
    trainer_name = models.CharField(max_length=255)
    session_code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date", "session_code"]
        constraints = [
            models.UniqueConstraint(
                fields=["module"],
                condition=Q(is_active=True),
                name="unique_active_session_per_module",
            )
        ]

    def __str__(self) -> str:
        return f"{self.session_code} ({self.module.code})"


class Submission(models.Model):
    SELF_EVAL_LEVEL_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("bien", "Bien"),
        ("tres_bien", "Tres bien"),
    ]
    SELF_EVAL_USAGE_CHOICES = [
        ("jamais", "Jamais"),
        ("rarement", "Rarement"),
        ("parfois", "Parfois"),
        ("souvent", "Souvent"),
    ]
    SELF_EVAL_BROWSER_CHOICES = [
        ("non", "Non"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
    ]
    TRUE_FALSE_UNKNOWN_CHOICES = [
        ("vrai", "Vrai"),
        ("faux", "Faux"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    PRACTICAL_SUBJECT_CHOICES = [
        ("francais", "Francais"),
        ("mathematiques", "Mathematiques"),
        ("sciences_physiques", "Sciences physiques"),
        ("sciences_naturelles", "Sciences naturelles"),
        ("anglais", "Anglais"),
        ("histoire_geographie", "Histoire-Geographie"),
        ("informatique", "Informatique"),
        ("autre", "Autre"),
    ]
    CONFIDENCE_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_beaucoup", "Oui, beaucoup"),
    ]
    QUIZ_Q4_OPTION_EXPLANATION = "chercher_une_explication"
    QUIZ_Q4_OPTION_VIDEO = "regarder_une_video_educative"
    QUIZ_Q4_OPTION_DOCUMENT = "trouver_un_document_de_revision"
    QUIZ_Q4_OPTION_WORD = "apprendre_un_nouveau_mot"
    QUIZ_Q4_OPTION_PASSWORD = "donner_son_mot_de_passe"
    QUIZ_Q4_CORRECT_OPTIONS = {
        QUIZ_Q4_OPTION_EXPLANATION,
        QUIZ_Q4_OPTION_VIDEO,
        QUIZ_Q4_OPTION_DOCUMENT,
        QUIZ_Q4_OPTION_WORD,
    }

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_internet_explained = models.CharField(max_length=20, choices=SELF_EVAL_LEVEL_CHOICES)
    auto_eval_learning_usage = models.CharField(max_length=20, choices=SELF_EVAL_USAGE_CHOICES)
    auto_eval_open_browser = models.CharField(max_length=20, choices=SELF_EVAL_BROWSER_CHOICES)

    todo_opened_browser = models.BooleanField(default=False)
    todo_typed_simple_search = models.BooleanField(default=False)
    todo_used_keywords = models.BooleanField(default=False)
    todo_opened_result = models.BooleanField(default=False)
    todo_compared_results = models.BooleanField(default=False)
    todo_found_school_info = models.BooleanField(default=False)
    todo_asked_for_help = models.BooleanField(default=False)
    todo_noted_learning = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4_selected = models.JSONField(default=list)
    quiz_q5 = models.CharField(max_length=50)

    practical_search_text = models.CharField(max_length=255)
    practical_site_text = models.CharField(max_length=255, blank=True)
    practical_subject = models.CharField(max_length=40, choices=PRACTICAL_SUBJECT_CHOICES)

    feedback_understood_today = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_submission_per_session_school_id",
            )
        ]

    def __str__(self) -> str:
        return f"{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "faux":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "vrai":
            score += 1
        if set(self.quiz_q4_selected) == self.QUIZ_Q4_CORRECT_OPTIONS:
            score += 1
        if self.quiz_q5 == "cours_equation_seconde_exemple":
            score += 1
        return score

    def save(self, *args, **kwargs):
        self.school_id_number_snapshot = self.school_id_number_snapshot or self.student.school_id_number
        self.computed_score = self.calculate_score()
        super().save(*args, **kwargs)


class Module3Submission(models.Model):
    SELF_EVAL_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("bien", "Bien"),
        ("tres_bien", "Très bien"),
    ]
    TRUE_FALSE_UNKNOWN_CHOICES = [
        ("vrai", "Vrai"),
        ("faux", "Faux"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    QUIZ_Q5_CHOICES = [
        ("math", "math"),
        ("cours_equation_seconde_exemple", "cours équation seconde exemple"),
        ("internet", "internet"),
        ("video", "vidéo"),
    ]
    QUIZ_Q6_CHOICES = [
        ("photosynthese", "photosynthèse"),
        ("photosynthese_cours_lycee_pdf", "photosynthèse cours lycée PDF"),
        ("plante", "plante"),
        ("facebook_photosynthese", "facebook photosynthèse"),
    ]
    QUIZ_Q7_CHOICES = [
        ("ajouter_matiere_ou_niveau", "Ajouter une matière ou un niveau"),
        ("mots_plus_precis", "Utiliser des mots plus précis"),
        ("comparer_resultats", "Comparer plusieurs résultats"),
        ("garder_memes_mots", "Garder les mêmes mots même si les résultats sont mauvais"),
    ]
    QUIZ_Q7_CORRECT_ANSWERS = {"ajouter_matiere_ou_niveau", "mots_plus_precis", "comparer_resultats"}
    PRACTICAL_SUBJECT_CHOICES = [
        ("francais", "Français"),
        ("mathematiques", "Mathématiques"),
        ("sciences_physiques", "Sciences physiques"),
        ("sciences_naturelles", "Sciences naturelles"),
        ("anglais", "Anglais"),
        ("histoire_geographie", "Histoire-Géographie"),
        ("informatique", "Informatique"),
        ("autre", "Autre"),
    ]
    CONFIDENCE_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_beaucoup", "Oui, beaucoup"),
    ]

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="module3_submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="module3_submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_keywords = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_improve = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_compare = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)

    todo_chose_subject = models.BooleanField(default=False)
    todo_written_question = models.BooleanField(default=False)
    todo_keywords_from_question = models.BooleanField(default=False)
    todo_did_search = models.BooleanField(default=False)
    todo_read_titles = models.BooleanField(default=False)
    todo_opened_result = models.BooleanField(default=False)
    todo_compared_two_results = models.BooleanField(default=False)
    todo_improved_keywords = models.BooleanField(default=False)
    todo_found_useful_resource = models.BooleanField(default=False)
    todo_noted_learning = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q5 = models.CharField(max_length=50, choices=QUIZ_Q5_CHOICES)
    quiz_q6 = models.CharField(max_length=50, choices=QUIZ_Q6_CHOICES)
    quiz_q7_selected = models.JSONField(default=list)

    practical_starting_question = models.CharField(max_length=255)
    practical_keywords_used = models.CharField(max_length=255)
    practical_site_found = models.CharField(max_length=255, blank=True)
    practical_subject = models.CharField(max_length=40, choices=PRACTICAL_SUBJECT_CHOICES)
    practical_what_learned = models.TextField()

    feedback_understood_today = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence_search = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_module3_submission_per_session_school_id",
            )
        ]
        verbose_name = "Module 3 submission"
        verbose_name_plural = "Module 3 submissions"

    def __str__(self) -> str:
        return f"M3-{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "faux":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "vrai":
            score += 1
        if self.quiz_q4 == "faux":
            score += 1
        if self.quiz_q5 == "cours_equation_seconde_exemple":
            score += 1
        if self.quiz_q6 == "photosynthese_cours_lycee_pdf":
            score += 1
        if set(self.quiz_q7_selected) == self.QUIZ_Q7_CORRECT_ANSWERS:
            score += 1
        return score

    def save(self, *args, **kwargs):
        self.school_id_number_snapshot = self.school_id_number_snapshot or self.student.school_id_number
        self.computed_score = self.calculate_score()
        super().save(*args, **kwargs)


class Module4Submission(models.Model):
    SELF_EVAL_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("bien", "Bien"),
        ("tres_bien", "Très bien"),
    ]
    VERIFY_CHOICES = [
        ("jamais", "Jamais"),
        ("rarement", "Rarement"),
        ("parfois", "Parfois"),
        ("souvent", "Souvent"),
    ]
    TRUE_FALSE_UNKNOWN_CHOICES = [
        ("vrai", "Vrai"),
        ("faux", "Faux"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    QUIZ_Q4_CHOICES = [
        ("partager_vite", "La partager rapidement"),
        ("croire_immediatement", "La croire immédiatement"),
        ("verifier_autres_sources", "Vérifier avec d'autres sources"),
        ("ignorer_resultats", "Ignorer tous les autres résultats"),
    ]
    QUIZ_Q5_CHOICES = [
        ("auteur_organisation", "Le site indique l'auteur ou l'organisation"),
        ("preuves_exemples", "Le contenu donne des preuves ou des exemples"),
        ("date_indiquee", "La date est indiquée"),
        ("titre_choquant", "Le titre cherche seulement à choquer"),
        ("retrouvable_ailleurs", "L'information peut être retrouvée sur d'autres sources sérieuses"),
    ]
    QUIZ_Q5_CORRECT_ANSWERS = {"auteur_organisation", "preuves_exemples", "date_indiquee", "retrouvable_ailleurs"}
    QUIZ_Q6_CHOICES = [
        ("titre_choquant", "Le titre est très choquant"),
        ("pas_auteur", "Il n'y a pas d'auteur"),
        ("pas_date", "Il n'y a pas de date"),
        ("preuves_claires", "Il y a des preuves claires"),
        ("partager_vite", "Le message demande de partager très vite"),
    ]
    QUIZ_Q6_CORRECT_ANSWERS = {"titre_choquant", "pas_auteur", "pas_date", "partager_vite"}
    HAS_DATE_CHOICES = [
        ("oui", "Oui"),
        ("non", "Non"),
        ("pas_trouve", "Je n'ai pas trouvé"),
    ]
    HAS_EVIDENCE_CHOICES = [
        ("oui", "Oui"),
        ("non", "Non"),
        ("un_peu", "Un peu"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    YES_NO_CHOICES = [
        ("oui", "Oui"),
        ("non", "Non"),
    ]
    DECISION_CHOICES = [
        ("fiable", "Plutôt fiable"),
        ("douteuse", "Douteuse"),
        ("pas_encore", "Je ne sais pas encore"),
    ]
    CONFIDENCE_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_beaucoup", "Oui, beaucoup"),
    ]

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="module4_submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="module4_submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_explain_source = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_verify_info = models.CharField(max_length=20, choices=VERIFY_CHOICES)
    auto_eval_spot_doubtful = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)

    todo_chose_info = models.BooleanField(default=False)
    todo_opened_first_source = models.BooleanField(default=False)
    todo_checked_publisher = models.BooleanField(default=False)
    todo_checked_date = models.BooleanField(default=False)
    todo_checked_evidence = models.BooleanField(default=False)
    todo_compared_second = models.BooleanField(default=False)
    todo_identified_reliable_sign = models.BooleanField(default=False)
    todo_identified_doubtful_sign = models.BooleanField(default=False)
    todo_decided_reliable_or_not = models.BooleanField(default=False)
    todo_explained_choice = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4 = models.CharField(max_length=40, choices=QUIZ_Q4_CHOICES)
    quiz_q5_selected = models.JSONField(default=list)
    quiz_q6_selected = models.JSONField(default=list)
    quiz_q7 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)

    practical_subject = models.CharField(max_length=255)
    practical_first_source = models.CharField(max_length=255)
    practical_publisher = models.CharField(max_length=255, blank=True)
    practical_has_date = models.CharField(max_length=20, choices=HAS_DATE_CHOICES)
    practical_has_evidence = models.CharField(max_length=20, choices=HAS_EVIDENCE_CHOICES)
    practical_compared = models.CharField(max_length=5, choices=YES_NO_CHOICES)
    practical_second_source = models.CharField(max_length=255, blank=True)
    practical_decision = models.CharField(max_length=20, choices=DECISION_CHOICES)
    practical_explanation = models.TextField()

    feedback_understood_today = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence_verify = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_module4_submission_per_session_school_id",
            )
        ]
        verbose_name = "Module 4 submission"
        verbose_name_plural = "Module 4 submissions"

    def __str__(self) -> str:
        return f"M4-{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "faux":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "vrai":
            score += 1
        if self.quiz_q4 == "verifier_autres_sources":
            score += 1
        if set(self.quiz_q5_selected) == self.QUIZ_Q5_CORRECT_ANSWERS:
            score += 1
        if set(self.quiz_q6_selected) == self.QUIZ_Q6_CORRECT_ANSWERS:
            score += 1
        if self.quiz_q7 == "faux":
            score += 1
        return score

    def save(self, *args, **kwargs):
        self.school_id_number_snapshot = self.school_id_number_snapshot or self.student.school_id_number
        self.computed_score = self.calculate_score()
        super().save(*args, **kwargs)


class FormPresence(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_SUBMITTED = "submitted"
    STATUS_EXPIRED = "expired"

    module_code = models.CharField(max_length=50, db_index=True)
    training_session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE)
    client_id = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(max_length=20, default=STATUS_ACTIVE)
    current_path = models.CharField(max_length=255, blank=True)
    school_id_number = models.CharField(max_length=2, blank=True, null=True)
    class_level = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["module_code", "training_session", "status"]),
            models.Index(fields=["last_seen_at"]),
        ]
        verbose_name = "Présence formulaire"
        verbose_name_plural = "Présences formulaires"

    def __str__(self):
        return f"{self.client_id} @ {self.module_code} ({self.status})"
