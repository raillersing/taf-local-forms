from django.core.validators import MaxLengthValidator, MaxValueValidator, MinLengthValidator, MinValueValidator, RegexValidator
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
    accepting_responses = models.BooleanField(default=True)

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


class Module5Submission(models.Model):
    SELF_EVAL_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("bien", "Bien"),
        ("tres_bien", "Très bien"),
    ]
    YES_NO_UNKNOWN_CHOICES = [
        ("oui", "Oui"),
        ("non", "Non"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    TRUE_FALSE_UNKNOWN_CHOICES = [
        ("vrai", "Vrai"),
        ("faux", "Faux"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    QUIZ_Q5_CHOICES = [
        ("salut", "Salut"),
        ("question", "Question"),
        ("demande_information_devoir_mathematiques", "Demande d'information sur le devoir de mathématiques"),
        ("important", "Important !!!"),
    ]
    QUIZ_Q6_CHOICES = [
        ("yo_prof", "Yo prof"),
        ("bonjour_monsieur_madame", "Bonjour Monsieur / Madame,"),
        ("eh", "Eh"),
        ("reponds_vite", "Réponds vite"),
    ]
    QUIZ_Q7_OPTION_DESTINATAIRE = "bon_destinataire"
    QUIZ_Q7_OPTION_OBJET = "objet_message"
    QUIZ_Q7_OPTION_POLITESSE = "politesse_message"
    QUIZ_Q7_OPTION_PJ = "piece_jointe_annoncee"
    QUIZ_Q7_OPTION_PASSWORD = "mot_de_passe_compte"
    QUIZ_Q7_CORRECT_ANSWERS = {
        QUIZ_Q7_OPTION_DESTINATAIRE,
        QUIZ_Q7_OPTION_OBJET,
        QUIZ_Q7_OPTION_POLITESSE,
        QUIZ_Q7_OPTION_PJ,
    }
    BEST_TOOL_CHOICES = [
        ("email", "Email"),
        ("facebook_public", "Commentaire public sur Facebook"),
        ("message_sans_nom", "Message sans nom"),
        ("tiktok", "Publication TikTok"),
    ]
    CONFIDENCE_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_beaucoup", "Oui, beaucoup"),
    ]

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="module5_submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="module5_submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_email_purpose = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_write_email = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_attach_file = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)

    todo_spotted_recipient = models.BooleanField(default=False)
    todo_written_clear_subject = models.BooleanField(default=False)
    todo_started_greeting = models.BooleanField(default=False)
    todo_written_short_message = models.BooleanField(default=False)
    todo_added_politeness = models.BooleanField(default=False)
    todo_signed_name = models.BooleanField(default=False)
    todo_checked_attachment = models.BooleanField(default=False)
    todo_reread_before_sending = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q5 = models.CharField(max_length=50, choices=QUIZ_Q5_CHOICES)
    quiz_q6 = models.CharField(max_length=50, choices=QUIZ_Q6_CHOICES)
    quiz_q7_selected = models.JSONField(default=list)

    practical_who_writing_to = models.CharField(max_length=255)
    practical_email_subject = models.CharField(max_length=255)
    practical_email_message = models.TextField()
    practical_needs_attachment = models.CharField(max_length=20, choices=YES_NO_UNKNOWN_CHOICES)
    practical_attachment_file = models.CharField(max_length=255, blank=True)
    practical_best_tool = models.CharField(max_length=40, choices=BEST_TOOL_CHOICES)

    feedback_understood_today = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence_email = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_module5_submission_per_session_school_id",
            )
        ]
        verbose_name = "Module 5 submission"
        verbose_name_plural = "Module 5 submissions"

    def __str__(self) -> str:
        return f"M5-{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "vrai":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "faux":
            score += 1
        if self.quiz_q4 == "faux":
            score += 1
        if self.quiz_q5 == "demande_information_devoir_mathematiques":
            score += 1
        if self.quiz_q6 == "bonjour_monsieur_madame":
            score += 1
        if set(self.quiz_q7_selected) == self.QUIZ_Q7_CORRECT_ANSWERS:
            score += 1
        return score

    def save(self, *args, **kwargs):
        self.school_id_number_snapshot = self.school_id_number_snapshot or self.student.school_id_number
        self.computed_score = self.calculate_score()
        super().save(*args, **kwargs)



class Module6Submission(models.Model):
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
    QUIZ_Q4_CHOICES = [
        ("exercice_corrige", "Un exercice corrigé"),
        ("publicite", "Une publicité"),
        ("rumeur", "Une rumeur"),
        ("mot_de_passe", "Un mot de passe"),
    ]
    QUIZ_Q5_CHOICES = [
        ("svt", "svt"),
        ("photosynthese_cours_lycee_pdf", "photosynthèse cours lycée PDF"),
        ("video_drole", "vidéo drôle"),
        ("internet", "internet"),
    ]
    QUIZ_Q6_OPTION_EXPLIQUE = "explique_clement_la_lecon"
    QUIZ_Q6_OPTION_EXERCICES = "propose_exercices"
    QUIZ_Q6_OPTION_NIVEAU = "correspond_niveau"
    QUIZ_Q6_OPTION_MATIERE = "liee_matiere_scolaire"
    QUIZ_Q6_OPTION_PASSWORD = "demande_mot_de_passe"
    QUIZ_Q6_CORRECT_ANSWERS = {
        QUIZ_Q6_OPTION_EXPLIQUE,
        QUIZ_Q6_OPTION_EXERCICES,
        QUIZ_Q6_OPTION_NIVEAU,
        QUIZ_Q6_OPTION_MATIERE,
    }
    QUIZ_Q7_OPTION_LIEN = "noter_lien"
    QUIZ_Q7_OPTION_COMPRIS = "ecrire_compris"
    QUIZ_Q7_OPTION_REVISER = "utiliser_reviser"
    QUIZ_Q7_OPTION_GARDER = "garder_dossier"
    QUIZ_Q7_OPTION_PASSWORD = "partager_mot_de_passe"
    QUIZ_Q7_CORRECT_ANSWERS = {
        QUIZ_Q7_OPTION_LIEN,
        QUIZ_Q7_OPTION_COMPRIS,
        QUIZ_Q7_OPTION_REVISER,
        QUIZ_Q7_OPTION_GARDER,
    }
    RESOURCE_TYPE_CHOICES = [
        ("video", "Vidéo"),
        ("pdf_fiche", "PDF / fiche"),
        ("exercice_corrige", "Exercice corrigé"),
        ("dictionnaire", "Dictionnaire / traduction"),
        ("schema_image", "Schéma / image"),
        ("quiz", "Quiz"),
        ("autre", "Autre"),
    ]
    YES_SOMEWHAT_NO_UNKNOWN_CHOICES = [
        ("oui", "Oui"),
        ("un_peu", "Un peu"),
        ("non", "Non"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
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

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="module6_submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="module6_submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_find_resource = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_choose_resource = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_keep_link = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)

    todo_chose_subject = models.BooleanField(default=False)
    todo_searched_resource = models.BooleanField(default=False)
    todo_opened_video_pdf_exercise = models.BooleanField(default=False)
    todo_checked_level = models.BooleanField(default=False)
    todo_noted_resource_title = models.BooleanField(default=False)
    todo_noted_link_or_site = models.BooleanField(default=False)
    todo_written_what_learned = models.BooleanField(default=False)
    todo_kept_for_later = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4 = models.CharField(max_length=40, choices=QUIZ_Q4_CHOICES)
    quiz_q5 = models.CharField(max_length=50, choices=QUIZ_Q5_CHOICES)
    quiz_q6_selected = models.JSONField(default=list)
    quiz_q7_selected = models.JSONField(default=list)

    practical_subject = models.CharField(max_length=40, choices=PRACTICAL_SUBJECT_CHOICES)
    practical_what_to_revise = models.CharField(max_length=255)
    practical_resource_type = models.CharField(max_length=40, choices=RESOURCE_TYPE_CHOICES)
    practical_resource_name_or_link = models.CharField(max_length=255)
    practical_adapted_level = models.CharField(max_length=20, choices=YES_SOMEWHAT_NO_UNKNOWN_CHOICES)
    practical_what_learned = models.TextField()

    feedback_understood_today = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence_resources = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_module6_submission_per_session_school_id",
            )
        ]
        verbose_name = "Module 6 submission"
        verbose_name_plural = "Module 6 submissions"

    def __str__(self) -> str:
        return f"M6-{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "vrai":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "faux":
            score += 1
        if self.quiz_q4 == "exercice_corrige":
            score += 1
        if self.quiz_q5 == "photosynthese_cours_lycee_pdf":
            score += 1
        if set(self.quiz_q6_selected) == self.QUIZ_Q6_CORRECT_ANSWERS:
            score += 1
        if set(self.quiz_q7_selected) == self.QUIZ_Q7_CORRECT_ANSWERS:
            score += 1
        return score

    def save(self, *args, **kwargs):
        self.school_id_number_snapshot = self.school_id_number_snapshot or self.student.school_id_number
        self.computed_score = self.calculate_score()
        super().save(*args, **kwargs)


class Module7Submission(models.Model):
    AUTO_EVAL_M7_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_facilement", "Oui, facilement"),
    ]
    TRUE_FALSE_UNKNOWN_CHOICES = [
        ("vrai", "Vrai"),
        ("faux", "Faux"),
        ("je_ne_sais_pas", "Je ne sais pas"),
    ]
    QUIZ_Q4_CHOICES = [
        ("cliquer_tout_de_suite", "Cliquer tout de suite"),
        ("partager_amis", "Partager à tous mes amis"),
        ("verifier_demander_aide", "Vérifier et demander de l'aide"),
        ("donner_mot_de_passe", "Donner mon mot de passe"),
    ]
    QUIZ_Q5_OPTION_MDP = "demande_mot_de_passe"
    QUIZ_Q5_OPTION_CADEAU = "promet_cadeau"
    QUIZ_Q5_OPTION_VITE = "agir_vite"
    QUIZ_Q5_OPTION_LIEN = "lien_bizarre"
    QUIZ_Q5_OPTION_PROF = "message_prof"
    QUIZ_Q5_CORRECT_ANSWERS = {
        QUIZ_Q5_OPTION_MDP,
        QUIZ_Q5_OPTION_CADEAU,
        QUIZ_Q5_OPTION_VITE,
        QUIZ_Q5_OPTION_LIEN,
    }
    QUIZ_Q6_OPTION_MDP = "mot_de_passe"
    QUIZ_Q6_OPTION_ADRESSE = "adresse_personnelle"
    QUIZ_Q6_OPTION_TEL = "numero_telephone"
    QUIZ_Q6_OPTION_PHOTOS = "photos_privees"
    QUIZ_Q6_OPTION_LECON = "lecon_publique"
    QUIZ_Q6_CORRECT_ANSWERS = {
        QUIZ_Q6_OPTION_MDP,
        QUIZ_Q6_OPTION_ADRESSE,
        QUIZ_Q6_OPTION_TEL,
        QUIZ_Q6_OPTION_PHOTOS,
    }
    QUIZ_Q7_OPTION_PARLER = "parler_adulte"
    QUIZ_Q7_OPTION_CHANGER = "changer_mdp"
    QUIZ_Q7_OPTION_CONSEIL = "ne_plus_utiliser"
    QUIZ_Q7_OPTION_SECRET = "garder_secret"
    QUIZ_Q7_OPTION_DONNER = "donner_code"
    QUIZ_Q7_CORRECT_ANSWERS = {
        QUIZ_Q7_OPTION_PARLER,
        QUIZ_Q7_OPTION_CHANGER,
        QUIZ_Q7_OPTION_CONSEIL,
    }
    SITUATION_CHOICES = [
        ("faux_message", "Faux message"),
        ("lien_suspect", "Lien suspect"),
        ("mot_de_passe", "Mot de passe"),
        ("cyberharcelement", "Cyberharcèlement"),
        ("partage_info", "Partage d'information personnelle"),
        ("autre", "Autre"),
    ]
    PROTECT_INFO_CHOICES = [
        ("mot_de_passe", "Mot de passe"),
        ("code_sms", "Code reçu par SMS ou application"),
        ("adresse", "Adresse personnelle"),
        ("telephone", "Numéro de téléphone"),
        ("photos_privees", "Photos privées"),
        ("nom_ecole", "Nom de l'école"),
        ("aucune", "Aucune information personnelle"),
    ]
    REACTION_CHOICES = [
        ("ne_pas_cliquer", "Ne pas cliquer"),
        ("ne_pas_repondre", "Ne pas répondre"),
        ("demander_aide", "Demander de l'aide"),
        ("bloquer_signaler", "Bloquer ou signaler si nécessaire"),
        ("garder_preuve", "Garder une preuve si c'est grave"),
        ("partager_vite", "Partager le message rapidement"),
    ]
    CONFIDENCE_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_beaucoup", "Oui, beaucoup"),
    ]

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="module7_submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="module7_submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_password = models.CharField(max_length=20, choices=AUTO_EVAL_M7_CHOICES)
    auto_eval_suspect = models.CharField(max_length=20, choices=AUTO_EVAL_M7_CHOICES)
    auto_eval_personal_info = models.CharField(max_length=20, choices=AUTO_EVAL_M7_CHOICES)

    todo_identified_weak_password = models.BooleanField(default=False)
    todo_written_password_rules = models.BooleanField(default=False)
    todo_understood_no_code_sharing = models.BooleanField(default=False)
    todo_observed_suspect_message = models.BooleanField(default=False)
    todo_spotted_danger_signs = models.BooleanField(default=False)
    todo_applied_stop_method = models.BooleanField(default=False)
    todo_listed_personal_info = models.BooleanField(default=False)
    todo_ask_help = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4 = models.CharField(max_length=40, choices=QUIZ_Q4_CHOICES)
    quiz_q5_selected = models.JSONField(default=list)
    quiz_q6_selected = models.JSONField(default=list)
    quiz_q7_selected = models.JSONField(default=list)

    practical_situation = models.CharField(max_length=30, choices=SITUATION_CHOICES)
    practical_describe = models.TextField()
    practical_danger_signs = models.TextField()
    practical_protect_selected = models.JSONField(default=list)
    practical_good_reaction_selected = models.JSONField(default=list)
    practical_explain = models.TextField()

    feedback_understood_today = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence_security = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_module7_submission_per_session_school_id",
            )
        ]
        verbose_name = "Module 7 submission"
        verbose_name_plural = "Module 7 submissions"

    def __str__(self) -> str:
        return f"M7-{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "faux":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "vrai":
            score += 1
        if self.quiz_q4 == "verifier_demander_aide":
            score += 1
        if set(self.quiz_q5_selected) == self.QUIZ_Q5_CORRECT_ANSWERS:
            score += 1
        if set(self.quiz_q6_selected) == self.QUIZ_Q6_CORRECT_ANSWERS:
            score += 1
        if set(self.quiz_q7_selected) == self.QUIZ_Q7_CORRECT_ANSWERS:
            score += 1
        return score

    def save(self, *args, **kwargs):
        self.school_id_number_snapshot = self.school_id_number_snapshot or self.student.school_id_number
        self.computed_score = self.calculate_score()
        super().save(*args, **kwargs)


class Module8Submission(models.Model):
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
    QUIZ_Q7_OPTION_CLARIFIER = "formuler_question_claire"
    QUIZ_Q7_OPTION_MOTS_CLES = "choisir_mots_cles"
    QUIZ_Q7_OPTION_SOURCE = "verifier_source"
    QUIZ_Q7_OPTION_COMPARER = "comparer_sources"
    QUIZ_Q7_OPTION_COPIER = "copier_sans_comprendre"
    QUIZ_Q7_OPTION_RESUMER = "resumer_propres_mots"
    QUIZ_Q7_CORRECT_ANSWERS = {
        QUIZ_Q7_OPTION_CLARIFIER,
        QUIZ_Q7_OPTION_MOTS_CLES,
        QUIZ_Q7_OPTION_SOURCE,
        QUIZ_Q7_OPTION_COMPARER,
        QUIZ_Q7_OPTION_RESUMER,
    }
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
    VERIFIED_ELEMENTS_CHOICES = [
        ("auteur_identifie", "L'auteur est identifiable"),
        ("site_connu", "Le site est connu ou fiable"),
        ("date_publiee", "La date de publication est indiquée"),
        ("sources_citees", "Les sources sont citées"),
        ("contenu_exact", "Le contenu correspond à ce que je cherche"),
        ("informations_coherentes", "Les informations sont cohérentes entre elles"),
    ]
    CONFIDENCE_CHOICES = [
        ("pas_encore", "Pas encore"),
        ("un_peu", "Un peu"),
        ("oui", "Oui"),
        ("oui_beaucoup", "Oui, beaucoup"),
    ]

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="module8_submissions")
    session = models.ForeignKey(TrainingSession, on_delete=models.PROTECT, related_name="module8_submissions")
    school_id_number_snapshot = models.CharField(
        max_length=2,
        validators=[MinLengthValidator(2), MaxLengthValidator(2), school_id_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_eval_search = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_source = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)
    auto_eval_summarize = models.CharField(max_length=20, choices=SELF_EVAL_CHOICES)

    todo_chose_subject = models.BooleanField(default=False)
    todo_written_question = models.BooleanField(default=False)
    todo_transformed_keywords = models.BooleanField(default=False)
    todo_found_first_source = models.BooleanField(default=False)
    todo_found_second_source = models.BooleanField(default=False)
    todo_checked_source_quality = models.BooleanField(default=False)
    todo_chose_most_useful = models.BooleanField(default=False)
    todo_noted_three_ideas = models.BooleanField(default=False)
    todo_prepared_synthesis = models.BooleanField(default=False)
    todo_presented_explained = models.BooleanField(default=False)

    quiz_q1 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q2 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q3 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q4 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q5 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q6 = models.CharField(max_length=20, choices=TRUE_FALSE_UNKNOWN_CHOICES)
    quiz_q7_selected = models.JSONField(default=list)

    practical_subject = models.CharField(max_length=40, choices=PRACTICAL_SUBJECT_CHOICES)
    practical_topic = models.CharField(max_length=255)
    practical_starting_question = models.TextField()
    practical_keywords_used = models.CharField(max_length=255)
    practical_first_source = models.CharField(max_length=255)
    practical_second_source = models.CharField(max_length=255, blank=True)
    practical_verified_elements = models.JSONField(default=list)
    practical_three_ideas = models.TextField()
    practical_synthesis = models.TextField()
    practical_academic_message = models.TextField(blank=True)

    feedback_best_success = models.TextField()
    feedback_still_difficult = models.TextField(blank=True)
    feedback_confidence = models.CharField(max_length=20, choices=CONFIDENCE_CHOICES)
    feedback_one_thing_to_practice = models.TextField(blank=True)

    computed_score = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "school_id_number_snapshot"],
                name="unique_module8_submission_per_session_school_id",
            )
        ]
        verbose_name = "Module 8 submission"
        verbose_name_plural = "Module 8 submissions"

    def __str__(self) -> str:
        return f"M8-{self.school_id_number_snapshot} - {self.session.session_code}"

    def calculate_score(self) -> int:
        score = 0
        if self.quiz_q1 == "vrai":
            score += 1
        if self.quiz_q2 == "vrai":
            score += 1
        if self.quiz_q3 == "faux":
            score += 1
        if self.quiz_q4 == "vrai":
            score += 1
        if self.quiz_q5 == "vrai":
            score += 1
        if self.quiz_q6 == "faux":
            score += 1
        if set(self.quiz_q7_selected) == self.QUIZ_Q7_CORRECT_ANSWERS:
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
            models.Index(fields=["status", "last_seen_at"]),
            models.Index(fields=["client_id", "module_code", "training_session"]),
        ]
        verbose_name = "Présence formulaire"
        verbose_name_plural = "Présences formulaires"

    def __str__(self):
        return f"{self.client_id} @ {self.module_code} ({self.status})"


class LearningResource(models.Model):
    RESOURCE_TYPE_DOCUMENT = "document"
    RESOURCE_TYPE_IMAGE = "image"
    RESOURCE_TYPE_AUDIO = "audio"
    RESOURCE_TYPE_VIDEO = "video"
    RESOURCE_TYPE_OTHER = "other"
    RESOURCE_TYPE_CHOICES = [
        (RESOURCE_TYPE_DOCUMENT, "Document"),
        (RESOURCE_TYPE_IMAGE, "Image"),
        (RESOURCE_TYPE_AUDIO, "Audio"),
        (RESOURCE_TYPE_OTHER, "Autre"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=20,
        choices=RESOURCE_TYPE_CHOICES,
        default=RESOURCE_TYPE_DOCUMENT,
    )
    module_number = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(2), MaxValueValidator(8)],
    )
    file = models.FileField(upload_to="learning_resources/%Y/%m/")
    source = models.CharField(max_length=255, blank=True)
    license_label = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["module_number", "title", "-updated_at"]
        verbose_name = "Support pédagogique"
        verbose_name_plural = "Supports pédagogiques"

    def __str__(self) -> str:
        return self.title

    @property
    def is_video(self) -> bool:
        return self.resource_type == self.RESOURCE_TYPE_VIDEO
