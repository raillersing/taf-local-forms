from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Chapter, LearningResource, Module1Submission, Module3Submission, Module4Submission, Module5Submission, Module6Submission, Module7Submission, Module8Submission, Student, Subject, Submission


LEARNING_RESOURCE_MAX_UPLOAD_SIZE = 20 * 1024 * 1024
LEARNING_RESOURCE_VIDEO_MAX_UPLOAD_SIZE = 80 * 1024 * 1024
LEARNING_RESOURCE_ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".mp4",
}
LEARNING_RESOURCE_VIDEO_EXTENSIONS = {".mp4"}
LEARNING_RESOURCE_NON_VIDEO_EXTENSIONS = LEARNING_RESOURCE_ALLOWED_EXTENSIONS - LEARNING_RESOURCE_VIDEO_EXTENSIONS


MODULE1_FIELD_DEFINITIONS = [
    ("q1_age", "1. Quel est ton âge ?", "choice", [("moins_14", "Moins de 14 ans"), ("14_16", "14 à 16 ans"), ("17_19", "17 à 19 ans"), ("20_plus", "20 ans ou plus")]),
    ("q2_gender", "2. Es-tu :", "choice", [("fille", "Fille"), ("garcon", "Garçon"), ("prefere_pas_repondre", "Je préfère ne pas répondre")]),
    ("q3_location", "3. Où habites-tu principalement ?", "choice", [("pres_ecole", "Près de l'école"), ("loin_ecole", "Loin de l'école"), ("ville", "En ville"), ("peripherie", "En périphérie / quartier éloigné"), ("autre", "Autre")]),
    ("q3_location_other", "Précision pour la question 3 — Autre", "text", None),
    ("q4_device_use", "4. As-tu déjà utilisé un téléphone, une tablette ou un ordinateur ?", "choice", [("souvent", "Oui, souvent"), ("parfois", "Oui, parfois"), ("rarement", "Rarement"), ("jamais", "Jamais")]),
    ("q5_home_devices", "5. À la maison, as-tu accès à un appareil numérique ?", "multiple", [("telephone_personnel", "Téléphone personnel"), ("telephone_familial", "Téléphone familial"), ("ordinateur", "Ordinateur"), ("tablette", "Tablette"), ("aucun", "Aucun appareil")]),
    ("q6_device_owner", "6. Si tu utilises un appareil, à qui appartient-il ?", "choice", [("moi", "À moi"), ("parents", "À mes parents"), ("frere_soeur", "À mon frère / ma sœur"), ("ami", "À un ami"), ("autre", "À quelqu'un d'autre"), ("aucun", "Je n'utilise pas d'appareil")]),
    ("q7_device_frequency", "7. À quelle fréquence utilises-tu un téléphone, une tablette ou un ordinateur ?", "choice", [("tous_jours", "Tous les jours"), ("quelques_fois_semaine", "Quelques fois par semaine"), ("quelques_fois_mois", "Quelques fois par mois"), ("presque_jamais", "Presque jamais"), ("jamais", "Jamais")]),
    ("q8_keyboard", "8. Sais-tu utiliser un clavier pour écrire un texte ?", "choice", [("facilement", "Oui, facilement"), ("lentement", "Oui, mais lentement"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q9_mouse", "9. Sais-tu utiliser une souris ou un pavé tactile d'ordinateur ?", "choice", [("facilement", "Oui, facilement"), ("un_peu", "Un peu"), ("non", "Non"), ("jamais_essaye", "Je n'ai jamais essayé")]),
    ("q10_internet_use", "10. As-tu déjà utilisé Internet ?", "choice", [("souvent", "Oui, souvent"), ("parfois", "Oui, parfois"), ("rarement", "Rarement"), ("jamais", "Jamais")]),
    ("q11_internet_location", "11. Où utilises-tu Internet le plus souvent ?", "choice", [("maison", "À la maison"), ("ecole", "À l'école"), ("cybercafe", "Dans un cybercafé"), ("ami_famille", "Chez un ami / famille"), ("telephone_proche", "Avec le téléphone d'un proche"), ("jamais", "Je n'utilise pas Internet")]),
    ("q12_internet_problems", "12. Quel est ton principal problème pour utiliser Internet ? Plusieurs réponses possibles.", "multiple", [("pas_appareil", "Je n'ai pas d'appareil"), ("coute_cher", "Internet coûte cher"), ("connexion_lente", "La connexion est lente"), ("pas_electricite", "Il n'y a pas souvent d'électricité"), ("difficile", "Je ne sais pas bien utiliser Internet"), ("parents", "Mes parents ne me laissent pas utiliser Internet"), ("aucun", "Je n'ai pas de problème particulier"), ("autre", "Autre")]),
    ("q12_internet_problems_other", "Précision pour la question 12 — Autre", "text", None),
    ("q13_internet_uses", "13. Pour toi, Internet sert surtout à quoi ? Plusieurs réponses possibles.", "multiple", [("reseaux_sociaux", "Réseaux sociaux"), ("videos", "Regarder des vidéos"), ("jouer", "Jouer"), ("recherches_ecole", "Faire des recherches pour l'école"), ("messages", "Envoyer des messages"), ("apprendre", "Apprendre de nouvelles choses"), ("opportunites", "Chercher des opportunités / formations"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q14_power_device", "14. Sais-tu allumer et éteindre correctement un ordinateur ou une tablette ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q15_wifi", "15. Sais-tu te connecter à un réseau Wi-Fi ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q16_open_app", "16. Sais-tu ouvrir une application ou un logiciel ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q17_write_text", "17. Sais-tu écrire un petit texte sur un téléphone, une tablette ou un ordinateur ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q18_save_file", "18. Sais-tu enregistrer un fichier ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q19_find_file", "19. Sais-tu retrouver un fichier déjà enregistré ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q20_photo_scan", "20. Sais-tu prendre une photo ou scanner un document avec un téléphone ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q21_email", "21. As-tu une adresse email personnelle ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q22_create_email", "22. Sais-tu créer une adresse email ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q23_send_email", "23. Sais-tu envoyer un email ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q24_attach_email", "24. Sais-tu joindre un fichier ou une photo dans un email ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q25_apps", "25. As-tu déjà utilisé ces applications ? Coche ce que tu connais ou utilises.", "multiple", [("gmail", "Gmail"), ("google", "Google"), ("youtube", "YouTube"), ("facebook", "Facebook"), ("whatsapp", "WhatsApp"), ("messenger", "Messenger"), ("google_docs", "Google Docs"), ("google_drive", "Google Drive"), ("zoom_meet", "Zoom / Google Meet"), ("aucune", "Aucune")]),
    ("q26_search_method", "26. Quand tu cherches une information pour l'école, que fais-tu le plus souvent ?", "choice", [("professeur", "Je demande à un professeur"), ("ami", "Je demande à un ami"), ("google", "Je cherche sur Google"), ("facebook", "Je regarde sur Facebook"), ("youtube", "Je regarde une vidéo YouTube"), ("ne_sais_pas", "Je ne sais pas comment chercher")]),
    ("q27_google_search", "27. Sais-tu faire une recherche sur Google ?", "choice", [("facilement", "Oui, facilement"), ("difficulte", "Oui, mais avec difficulté"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q28_verify_information", "28. Quand tu trouves une information sur Internet, vérifies-tu si elle est vraie ?", "choice", [("souvent", "Oui, souvent"), ("parfois", "Parfois"), ("rarement", "Rarement"), ("jamais", "Jamais"), ("ne_sais_pas", "Je ne sais pas comment vérifier")]),
    ("q29_internet_truth", "29. Pour toi, toutes les informations sur Internet sont vraies.", "choice", [("vrai", "Vrai"), ("faux", "Faux"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q30_search_explanation", "30. Si tu ne comprends pas un mot ou une leçon, sais-tu chercher une explication sur Internet ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q31_secure_password", "31. Sais-tu ce qu'est un mot de passe sécurisé ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q32_share_password", "32. Est-ce une bonne idée de donner son mot de passe à un ami ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q33_suspect_message", "33. As-tu déjà vu ou reçu un message suspect sur Internet ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q34_online_harassment_actions", "34. Si quelqu'un t'insulte ou te menace en ligne, que dois-tu faire ? Plusieurs réponses possibles.", "multiple", [("insultes", "Répondre avec des insultes"), ("preuve", "Garder une preuve"), ("adulte", "En parler à un adulte ou responsable"), ("bloquer", "Bloquer la personne"), ("rien", "Ne rien faire"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q35_protect_personal_information", "35. Sais-tu protéger tes informations personnelles sur Internet ?", "choice", [("oui", "Oui"), ("un_peu", "Un peu"), ("non", "Non")]),
    ("q36_learn_lesson", "36. As-tu déjà utilisé Internet pour apprendre une leçon ?", "choice", [("souvent", "Oui, souvent"), ("parfois", "Oui, parfois"), ("rarement", "Rarement"), ("jamais", "Jamais")]),
    ("q37_educational_video", "37. As-tu déjà regardé une vidéo éducative ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q38_pdf", "38. As-tu déjà utilisé un document PDF pour apprendre ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas ce qu'est un PDF")]),
    ("q39_dictionary_translation", "39. As-tu déjà utilisé un dictionnaire ou une traduction en ligne ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas")]),
    ("q40_subjects", "40. Dans quelles matières aimerais-tu utiliser Internet pour progresser ? Plusieurs réponses possibles.", "multiple", [("francais", "Français"), ("mathematiques", "Mathématiques"), ("sciences_physiques", "Sciences physiques"), ("sciences_naturelles", "Sciences naturelles"), ("anglais", "Anglais"), ("histoire_geographie", "Histoire-Géographie"), ("informatique", "Informatique"), ("autre", "Autre")]),
    ("q40_subject_other", "Précision pour la question 40 — Autre", "text", None),
    ("q41_motivations", "41. Pourquoi veux-tu participer à ce projet ?", "multiple", [("apprendre_internet", "Apprendre à utiliser Internet"), ("reussir_ecole", "Mieux réussir à l'école"), ("appareil", "Utiliser un ordinateur ou une tablette"), ("avenir", "Préparer mon avenir"), ("metiers_numerique", "Découvrir les métiers du numérique"), ("parents_professeurs", "Parents / professeurs m'ont conseillé"), ("autre", "Autre")]),
    ("q41_motivation_other", "Précision pour la question 41 — Autre", "text", None),
    ("q42_first_learning", "42. Qu'aimerais-tu apprendre en premier ? Choisis 3 réponses maximum.", "multiple", [("ordinateur_tablette", "Utiliser un ordinateur ou une tablette"), ("internet", "Utiliser Internet"), ("email", "Créer et utiliser une adresse email"), ("recherches", "Faire des recherches pour l'école"), ("docs_word", "Utiliser Google Docs ou Word"), ("presentation", "Faire une présentation"), ("securite", "Être en sécurité sur Internet"), ("metiers", "Découvrir les métiers du numérique"), ("creer", "Créer quelque chose avec la technologie")]),
    ("q43_training_commitment", "43. Es-tu prêt(e) à suivre les formations sérieusement ?", "choice", [("oui", "Oui"), ("non", "Non"), ("ne_sais_pas", "Je ne sais pas encore")]),
    ("q44_regular_attendance", "44. Peux-tu être présent(e) régulièrement pendant les activités ?", "choice", [("oui", "Oui"), ("non", "Non"), ("depend_horaire", "Cela dépend de l'horaire")]),
    ("q45_preferred_schedule", "45. Quel horaire serait le plus facile pour toi ?", "multiple", [("matin", "Matin"), ("apres_midi", "Après-midi"), ("mercredi", "Mercredi"), ("samedi", "Samedi"), ("vacances", "Pendant les vacances"), ("autre", "Autre")]),
    ("q45_schedule_other", "Précision pour la question 45 — Autre", "text", None),
    ("q46_digital_level", "46. Note ton niveau actuel en numérique (1 à 5).", "choice", [(str(i), str(i)) for i in range(1, 6)]),
    ("q47_search_level", "47. Note ton niveau en recherche sur Internet (1 à 5).", "choice", [(str(i), str(i)) for i in range(1, 6)]),
    ("q48_device_confidence", "48. Note ta confiance à utiliser un ordinateur ou une tablette (1 à 5).", "choice", [(str(i), str(i)) for i in range(1, 6)]),
    ("q49_greatest_difficulty", "49. Quelle est la plus grande difficulté que tu rencontres avec Internet ou les appareils numériques ?", "textarea", None),
    ("q50_after_training", "50. Qu'est-ce que tu aimerais être capable de faire après cette formation ?", "textarea", None),
    ("q51_question_or_concern", "51. As-tu une question ou une inquiétude concernant le projet ?", "textarea", None),
]


class Module1SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro technique à l'école",
        min_length=2,
        max_length=2,
        help_text="Identifiant de suivi fourni par le formateur (exemple : 01).",
        error_messages={"required": "Entre le numéro fourni par le formateur."},
    )
    paper_full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    paper_class_level = forms.CharField(label="Classe / Niveau", max_length=100)
    paper_school_name = forms.CharField(label="Établissement", max_length=255)
    paper_date = forms.DateField(label="Date", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, label, kind, choices in MODULE1_FIELD_DEFINITIONS:
            if kind == "choice":
                self.fields[name] = forms.ChoiceField(label=label, choices=choices, required=False, widget=forms.RadioSelect)
            elif kind == "multiple":
                self.fields[name] = forms.MultipleChoiceField(label=label, choices=choices, required=False, widget=forms.CheckboxSelectMultiple)
            elif kind == "textarea":
                self.fields[name] = forms.CharField(label=label, required=False, widget=forms.Textarea(attrs={"rows": 4}))
            else:
                self.fields[name] = forms.CharField(label=label, max_length=255, required=False)

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value

    def clean_q42_first_learning(self):
        value = self.cleaned_data.get("q42_first_learning", [])
        if len(value) > 3:
            raise forms.ValidationError("Choisis 3 réponses maximum.")
        return value


class Module2SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l’école",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_internet_explained = forms.ChoiceField(
        label="Je sais expliquer ce qu'est Internet.",
        choices=Submission.SELF_EVAL_LEVEL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_learning_usage = forms.ChoiceField(
        label="J'ai déjà utilisé Internet pour apprendre un cours.",
        choices=Submission.SELF_EVAL_USAGE_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_open_browser = forms.ChoiceField(
        label="Je sais ouvrir un navigateur.",
        choices=Submission.SELF_EVAL_BROWSER_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_opened_browser = forms.BooleanField(label="J'ai ouvert le navigateur.", required=False)
    todo_typed_simple_search = forms.BooleanField(label="J'ai écrit une recherche simple.", required=False)
    todo_used_keywords = forms.BooleanField(label="J'ai utilisé des mots-clés utiles.", required=False)
    todo_opened_result = forms.BooleanField(label="J'ai ouvert un résultat de recherche.", required=False)
    todo_compared_results = forms.BooleanField(label="J'ai comparé au moins deux résultats.", required=False)
    todo_found_school_info = forms.BooleanField(
        label="J'ai trouvé une information utile pour un cours.",
        required=False,
    )
    todo_asked_for_help = forms.BooleanField(
        label="J'ai demande de l'aide quand je ne comprenais pas.",
        required=False,
    )
    todo_noted_learning = forms.BooleanField(
        label="J'ai noté une chose importante apprise pendant la séance.",
        required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Internet sert seulement a utiliser Facebook.",
        choices=Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Pour chercher un cours, il vaut mieux utiliser des mots-clés simples.",
        choices=Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Quand je trouve une information sur Internet, je dois parfois vérifier si elle est fiable.",
        choices=Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4_selected = forms.MultipleChoiceField(
        label="4. Que peux-tu faire avec Internet pour étudier ?",
        choices=[
            (Submission.QUIZ_Q4_OPTION_EXPLANATION, "Chercher une explication"),
            (Submission.QUIZ_Q4_OPTION_VIDEO, "Regarder une vidéo éducative"),
            (Submission.QUIZ_Q4_OPTION_DOCUMENT, "Trouver un document de révision"),
            (Submission.QUIZ_Q4_OPTION_WORD, "Apprendre un nouveau mot"),
            (Submission.QUIZ_Q4_OPTION_PASSWORD, "Donner son mot de passe à un ami"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q5 = forms.ChoiceField(
        label="5. Quel exemple est une bonne recherche ?",
        choices=[
            ("math", "math"),
            ("cours_equation_seconde_exemple", "cours équation seconde exemple"),
            ("fb_video", "fb video"),
            ("internet", "internet"),
        ],
        widget=forms.RadioSelect,
    )

    practical_search_text = forms.CharField(
        label="Écris une recherche que tu as faite pendant la séance.",
        max_length=255,
    )
    practical_site_text = forms.CharField(
        label="Écris le nom ou l'adresse du site que tu as trouvé.",
        max_length=255,
        required=False,
    )
    practical_subject = forms.ChoiceField(
        label="Cette information peut m'aider dans quelle matière ?",
        choices=Submission.PRACTICAL_SUBJECT_CHOICES,
    )
    feedback_understood_today = forms.CharField(
        label="Ce que j'ai compris aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )
    feedback_confidence = forms.ChoiceField(
        label="Je me sens plus capable d'utiliser Internet pour apprendre.",
        choices=Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value


class LearningResourceForm(forms.ModelForm):
    resource_type = forms.ChoiceField(
        choices=[
            (LearningResource.RESOURCE_TYPE_DOCUMENT, "Document"),
            (LearningResource.RESOURCE_TYPE_IMAGE, "Image"),
            (LearningResource.RESOURCE_TYPE_AUDIO, "Audio"),
            (LearningResource.RESOURCE_TYPE_VIDEO, "Vidéo"),
            (LearningResource.RESOURCE_TYPE_OTHER, "Autre"),
        ],
        label="Type de support",
    )

    class Meta:
        model = LearningResource
        fields = [
            "title",
            "description",
            "resource_type",
            "module_number",
            "subject",
            "chapter",
            "file",
            "source",
            "license_label",
            "is_published",
        ]
        labels = {
            "title": "Titre du support",
            "description": "Description",
            "resource_type": "Type de support",
            "module_number": "Module lié",
            "subject": "Matière",
            "chapter": "Chapitre",
            "file": "Fichier",
            "source": "Source",
            "license_label": "Licence",
            "is_published": "Publier immédiatement",
        }
        help_texts = {
            "title": "Titre lisible pour les élèves et le formateur.",
            "description": "Résumé court du contenu du support.",
            "module_number": "Optionnel. Laisse vide pour un support général.",
            "subject": "Optionnel. Classe le support par matière si utile.",
            "chapter": "Optionnel. Choisis un chapitre de la matière sélectionnée.",
            "file": "Formats autorisés : PDF, DOCX, PPTX, PNG, JPG, JPEG, TXT et MP4. Taille maximale : 20 MB, ou 80 MB pour une vidéo MP4.",
            "source": "Exemple : TAfHSSiM, professeur, manuel local.",
            "license_label": "Exemple : usage classe, libre diffusion, CC BY.",
            "is_published": "Décoche pour garder ce support en brouillon.",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].queryset = Subject.objects.filter(is_active=True).order_by("sort_order", "name")
        self.fields["chapter"].queryset = Chapter.objects.none()
        self.fields["resource_type"].widget.attrs["class"] = "taf-select"
        self.fields["module_number"].widget.attrs["class"] = "taf-input"
        self.fields["subject"].widget.attrs["class"] = "taf-select"
        self.fields["chapter"].widget.attrs["class"] = "taf-select"
        self.fields["title"].widget.attrs["class"] = "taf-input"
        self.fields["source"].widget.attrs["class"] = "taf-input"
        self.fields["license_label"].widget.attrs["class"] = "taf-input"
        self.fields["description"].widget.attrs["class"] = "taf-textarea"
        self.fields["file"].widget.attrs["class"] = "taf-input"
        self.fields["file"].widget.attrs["accept"] = ",".join(sorted(LEARNING_RESOURCE_ALLOWED_EXTENSIONS))
        subject_id = None
        if self.is_bound:
            subject_id = self.data.get("subject") or None
        elif self.instance.pk and self.instance.subject_id:
            subject_id = str(self.instance.subject_id)
        if subject_id:
            self.fields["chapter"].queryset = Chapter.objects.filter(
                subject_id=subject_id,
                is_active=True,
            ).order_by("sort_order", "title")

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")
        resource_type = self.cleaned_data.get("resource_type")
        if not uploaded_file:
            raise forms.ValidationError("Ajoute un fichier avant d'enregistrer ce support.")

        if not getattr(uploaded_file, "name", ""):
            raise forms.ValidationError("Le nom du fichier est invalide.")

        name = uploaded_file.name.strip()
        dot_index = name.rfind(".")
        extension = name[dot_index:].lower() if dot_index != -1 else ""
        if not extension:
            raise forms.ValidationError("Le fichier doit avoir une extension reconnue.")
        if extension not in LEARNING_RESOURCE_ALLOWED_EXTENSIONS:
            raise forms.ValidationError(
                "Format non autorisé. Utilise un fichier PDF, DOCX, PPTX, PNG, JPG, JPEG, TXT ou MP4."
            )

        if resource_type == LearningResource.RESOURCE_TYPE_VIDEO:
            if extension not in LEARNING_RESOURCE_VIDEO_EXTENSIONS:
                raise forms.ValidationError("Pour une vidéo, utilise uniquement un fichier MP4.")
            content_type = getattr(uploaded_file, "content_type", "") or ""
            if content_type and not content_type.startswith("video/") and content_type not in {"application/mp4", "application/octet-stream"}:
                raise forms.ValidationError("Le fichier vidéo envoyé n'est pas reconnu comme un MP4 valide.")
            if uploaded_file.size > LEARNING_RESOURCE_VIDEO_MAX_UPLOAD_SIZE:
                raise forms.ValidationError("La vidéo dépasse la taille maximale autorisée de 80 MB.")
        else:
            if extension in LEARNING_RESOURCE_VIDEO_EXTENSIONS:
                raise forms.ValidationError("Choisis le type « Vidéo » pour envoyer un fichier MP4.")
            if uploaded_file.size > LEARNING_RESOURCE_MAX_UPLOAD_SIZE:
                raise forms.ValidationError("Le fichier dépasse la taille maximale autorisée de 20 MB.")
        return uploaded_file

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Entre un titre pour ce support.")
        return title

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title", "")
        subject = cleaned_data.get("subject")
        chapter = cleaned_data.get("chapter")
        if chapter and not subject:
            cleaned_data["subject"] = chapter.subject
            subject = chapter.subject
        if chapter and subject and chapter.subject_id != subject.id:
            self.add_error("chapter", "Choisis un chapitre de la matière sélectionnée.")
        if title:
            base_slug = slugify(title)
            if not base_slug:
                raise forms.ValidationError("Le titre doit permettre de générer un slug valide.")
            slug = base_slug
            index = 2
            queryset = LearningResource.objects.all()
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            while queryset.filter(slug=slug).exists():
                slug = f"{base_slug}-{index}"
                index += 1
            self.instance.slug = slug
        return cleaned_data

    def _post_clean(self):
        opts = self._meta
        exclude = self._get_validation_exclusions()
        exclude.add("resource_type")
        try:
            self.instance = forms.models.construct_instance(self, self.instance, opts.fields, opts.exclude)
        except ValidationError as e:
            self._update_errors(e)

        try:
            self.instance.full_clean(exclude=exclude, validate_unique=False)
        except ValidationError as e:
            self._update_errors(e)

        if self._validate_unique:
            self.validate_unique()


class Module4SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l'école",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_explain_source = forms.ChoiceField(
        label="Je sais expliquer ce qu'est une source fiable.",
        choices=Module4Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_verify_info = forms.ChoiceField(
        label="Je vérifie une information avant de la croire.",
        choices=Module4Submission.VERIFY_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_spot_doubtful = forms.ChoiceField(
        label="Je sais repérer une information douteuse.",
        choices=Module4Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_chose_info = forms.BooleanField(
        label="J'ai choisi une information ou un sujet à vérifier.", required=False,
    )
    todo_opened_first_source = forms.BooleanField(
        label="J'ai ouvert une première source.", required=False,
    )
    todo_checked_publisher = forms.BooleanField(
        label="J'ai regardé qui a publié l'information.", required=False,
    )
    todo_checked_date = forms.BooleanField(
        label="J'ai cherché la date de publication.", required=False,
    )
    todo_checked_evidence = forms.BooleanField(
        label="J'ai regardé s'il y a des preuves, chiffres ou exemples.", required=False,
    )
    todo_compared_second = forms.BooleanField(
        label="J'ai comparé avec une deuxième source.", required=False,
    )
    todo_identified_reliable_sign = forms.BooleanField(
        label="J'ai identifié au moins un signe de fiabilité.", required=False,
    )
    todo_identified_doubtful_sign = forms.BooleanField(
        label="J'ai identifié au moins un signe de doute.", required=False,
    )
    todo_decided_reliable_or_not = forms.BooleanField(
        label="J'ai décidé si l'information semble fiable ou non.", required=False,
    )
    todo_explained_choice = forms.BooleanField(
        label="J'ai expliqué mon choix avec mes propres mots.", required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Tout ce qu'on trouve sur Internet est vrai.",
        choices=Module4Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Une source fiable indique souvent qui publie l'information.",
        choices=Module4Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Une information sans auteur, sans date et sans preuve peut être douteuse.",
        choices=Module4Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4 = forms.ChoiceField(
        label="4. Si une information est très surprenante, que dois-je faire ?",
        choices=Module4Submission.QUIZ_Q4_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q5_selected = forms.MultipleChoiceField(
        label="5. Quels signes peuvent montrer qu'une source est plus fiable ?",
        choices=Module4Submission.QUIZ_Q5_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q6_selected = forms.MultipleChoiceField(
        label="6. Quels signes peuvent montrer qu'une information est douteuse ?",
        choices=Module4Submission.QUIZ_Q6_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q7 = forms.ChoiceField(
        label="7. Une publication Facebook est toujours une source fiable pour un devoir scolaire.",
        choices=Module4Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )

    practical_subject = forms.CharField(
        label="Écris le sujet ou l'information que tu as vérifié.",
        max_length=255,
        help_text="Exemple : les volcans à Madagascar, la photosynthèse, une information vue sur Facebook.",
    )
    practical_first_source = forms.CharField(
        label="Écris le nom ou l'adresse de la première source.",
        max_length=255,
    )
    practical_publisher = forms.CharField(
        label="Qui a publié cette information ?",
        max_length=255,
        required=False,
        help_text="Exemple : un professeur, un média, une organisation, un site inconnu.",
    )
    practical_has_date = forms.ChoiceField(
        label="Y a-t-il une date ?",
        choices=Module4Submission.HAS_DATE_CHOICES,
        widget=forms.RadioSelect,
    )
    practical_has_evidence = forms.ChoiceField(
        label="La source donne-t-elle des preuves, chiffres ou exemples ?",
        choices=Module4Submission.HAS_EVIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )
    practical_compared = forms.ChoiceField(
        label="As-tu comparé avec une autre source ?",
        choices=Module4Submission.YES_NO_CHOICES,
        widget=forms.RadioSelect,
    )
    practical_second_source = forms.CharField(
        label="Écris le nom ou l'adresse de la deuxième source.",
        max_length=255,
        required=False,
    )
    practical_decision = forms.ChoiceField(
        label="Selon toi, cette information est :",
        choices=Module4Submission.DECISION_CHOICES,
        widget=forms.RadioSelect,
    )
    practical_explanation = forms.CharField(
        label="Explique ton choix avec tes propres mots.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    feedback_understood_today = forms.CharField(
        label="Ce que j'ai compris aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )
    feedback_confidence_verify = forms.ChoiceField(
        label="Je me sens plus capable de vérifier une information.",
        choices=Module4Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value


class Module3SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l'école",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_keywords = forms.ChoiceField(
        label="Je sais choisir de bons mots-clés.",
        choices=Module3Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_improve = forms.ChoiceField(
        label="Je sais améliorer une recherche quand les résultats ne sont pas bons.",
        choices=Module3Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_compare = forms.ChoiceField(
        label="Je sais comparer deux résultats de recherche.",
        choices=Module3Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_chose_subject = forms.BooleanField(label="J'ai choisi une matière scolaire.", required=False)
    todo_written_question = forms.BooleanField(label="J'ai écrit une question de départ.", required=False)
    todo_keywords_from_question = forms.BooleanField(
        label="J'ai transformé ma question en mots-clés.", required=False,
    )
    todo_did_search = forms.BooleanField(label="J'ai lancé une recherche.", required=False)
    todo_read_titles = forms.BooleanField(label="J'ai lu les titres des premiers résultats.", required=False)
    todo_opened_result = forms.BooleanField(label="J'ai ouvert un résultat utile.", required=False)
    todo_compared_two_results = forms.BooleanField(
        label="J'ai comparé au moins deux résultats.", required=False,
    )
    todo_improved_keywords = forms.BooleanField(
        label="J'ai amélioré ma recherche avec de meilleurs mots-clés.", required=False,
    )
    todo_found_useful_resource = forms.BooleanField(
        label="J'ai trouvé une ressource utile pour apprendre.", required=False,
    )
    todo_noted_learning = forms.BooleanField(
        label="J'ai noté ce que cette ressource m'a appris.", required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Pour chercher efficacement, il faut toujours écrire une très longue phrase.",
        choices=Module3Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Les mots-clés sont les mots importants d'une recherche.",
        choices=Module3Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Si les résultats ne sont pas utiles, je peux changer mes mots-clés.",
        choices=Module3Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4 = forms.ChoiceField(
        label="4. Quand je vois les résultats, je dois regarder seulement le premier lien.",
        choices=Module3Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q5 = forms.ChoiceField(
        label="5. Quelle recherche est la plus précise ?",
        choices=Module3Submission.QUIZ_Q5_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q6 = forms.ChoiceField(
        label="6. Pour trouver un document PDF sur la photosynthèse, quelle recherche est la meilleure ?",
        choices=Module3Submission.QUIZ_Q6_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q7_selected = forms.MultipleChoiceField(
        label="7. Que peut-on faire pour améliorer une recherche ?",
        choices=Module3Submission.QUIZ_Q7_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )

    practical_starting_question = forms.CharField(
        label="Écris ta question de départ.",
        max_length=255,
        help_text="Exemple : Comment résoudre une équation ?",
    )
    practical_keywords_used = forms.CharField(
        label="Écris les mots-clés que tu as utilisés.",
        max_length=255,
        help_text="Exemple : équation seconde exemple simple",
    )
    practical_site_found = forms.CharField(
        label="Écris le nom ou l'adresse du site trouvé.",
        max_length=255,
        required=False,
    )
    practical_subject = forms.ChoiceField(
        label="Cette ressource peut m'aider dans quelle matière ?",
        choices=Module3Submission.PRACTICAL_SUBJECT_CHOICES,
    )
    practical_what_learned = forms.CharField(
        label="Qu'est-ce que cette ressource t'a appris ?",
        widget=forms.Textarea(attrs={"rows": 4}),
    )

    feedback_understood_today = forms.CharField(
        label="Ce que j'ai compris aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
    )
    feedback_confidence_search = forms.ChoiceField(
        label="Je me sens plus capable de chercher efficacement sur Internet.",
        choices=Module3Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value


class Module5SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l'école",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_email_purpose = forms.ChoiceField(
        label="Je sais expliquer à quoi sert une adresse email.",
        choices=Module5Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_write_email = forms.ChoiceField(
        label="Je sais écrire un email simple et poli.",
        choices=Module5Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_attach_file = forms.ChoiceField(
        label="Je sais joindre un fichier ou une photo dans un message.",
        choices=Module5Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_spotted_recipient = forms.BooleanField(
        label="J'ai repéré le destinataire de l'email.", required=False,
    )
    todo_written_clear_subject = forms.BooleanField(
        label="J'ai écrit un objet clair.", required=False,
    )
    todo_started_greeting = forms.BooleanField(
        label="J'ai commencé par une salutation.", required=False,
    )
    todo_written_short_message = forms.BooleanField(
        label="J'ai écrit un message court et précis.", required=False,
    )
    todo_added_politeness = forms.BooleanField(
        label="J'ai ajouté une formule de politesse.", required=False,
    )
    todo_signed_name = forms.BooleanField(
        label="J'ai signé avec mon nom.", required=False,
    )
    todo_checked_attachment = forms.BooleanField(
        label="J'ai vérifié la pièce jointe si besoin.", required=False,
    )
    todo_reread_before_sending = forms.BooleanField(
        label="J'ai relu avant d'envoyer.", required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Un email peut servir à communiquer avec un professeur ou une école.",
        choices=Module5Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. L'objet d'un email doit aider le destinataire à comprendre le sujet.",
        choices=Module5Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Il est recommandé d'envoyer un email sans le relire.",
        choices=Module5Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4 = forms.ChoiceField(
        label="4. Il est acceptable de donner son mot de passe par email à un ami.",
        choices=Module5Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q5 = forms.ChoiceField(
        label="5. Quel objet est le plus clair ?",
        choices=Module5Submission.QUIZ_Q5_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q6 = forms.ChoiceField(
        label="6. Quelle formule est la plus adaptée pour commencer un email à un professeur ?",
        choices=Module5Submission.QUIZ_Q6_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q7_selected = forms.MultipleChoiceField(
        label="7. Que faut-il vérifier avant d'envoyer un email ?",
        choices=[
            (Module5Submission.QUIZ_Q7_OPTION_DESTINATAIRE, "Le bon destinataire"),
            (Module5Submission.QUIZ_Q7_OPTION_OBJET, "L'objet du message"),
            (Module5Submission.QUIZ_Q7_OPTION_POLITESSE, "La politesse du message"),
            (Module5Submission.QUIZ_Q7_OPTION_PJ, "La pièce jointe si elle est annoncée"),
            (Module5Submission.QUIZ_Q7_OPTION_PASSWORD, "Le mot de passe du compte"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )

    practical_who_writing_to = forms.CharField(
        label="À qui veux-tu écrire ?",
        max_length=255,
        help_text="Exemple : professeur de mathématiques, administration, responsable de formation.",
    )
    practical_email_subject = forms.CharField(
        label="Écris l'objet de ton email.",
        max_length=255,
        help_text="Exemple : Demande d'information sur le devoir de français.",
    )
    practical_email_message = forms.CharField(
        label="Écris ton message en quelques phrases.",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Commence par Bonjour, explique ta demande, puis termine poliment.",
    )
    practical_needs_attachment = forms.ChoiceField(
        label="Ton email a-t-il besoin d'une pièce jointe ?",
        choices=Module5Submission.YES_NO_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    practical_attachment_file = forms.CharField(
        label="Si oui, quel fichier veux-tu joindre ?",
        max_length=255,
        required=False,
        help_text="Exemple : devoir.pdf, photo_exercice.jpg, fiche_revision.docx.",
    )
    practical_best_tool = forms.ChoiceField(
        label="Quel outil est le plus adapté pour envoyer un devoir à un professeur ?",
        choices=Module5Submission.BEST_TOOL_CHOICES,
        widget=forms.RadioSelect,
    )

    feedback_understood_today = forms.CharField(
        label="Ce que j'ai compris aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris une ou deux phrases simples.",
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        help_text="Écris ce qui n'est pas encore clair.",
    )
    feedback_confidence_email = forms.ChoiceField(
        label="Après cette séance, je me sens plus capable d'écrire un email correct.",
        choices=Module5Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value


class Module6SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l'école",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_find_resource = forms.ChoiceField(
        label="Je sais trouver une ressource éducative en ligne.",
        choices=Module6Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_choose_resource = forms.ChoiceField(
        label="Je sais choisir une ressource adaptée à mon niveau.",
        choices=Module6Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_keep_link = forms.ChoiceField(
        label="Je sais garder un lien utile pour réviser plus tard.",
        choices=Module6Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_chose_subject = forms.BooleanField(
        label="J'ai choisi une matière à travailler.", required=False,
    )
    todo_searched_resource = forms.BooleanField(
        label="J'ai cherché une ressource éducative.", required=False,
    )
    todo_opened_video_pdf_exercise = forms.BooleanField(
        label="J'ai ouvert une vidéo, un PDF ou un exercice.", required=False,
    )
    todo_checked_level = forms.BooleanField(
        label="J'ai vérifié si le niveau est adapté.", required=False,
    )
    todo_noted_resource_title = forms.BooleanField(
        label="J'ai noté le titre de la ressource.", required=False,
    )
    todo_noted_link_or_site = forms.BooleanField(
        label="J'ai noté le lien ou le nom du site.", required=False,
    )
    todo_written_what_learned = forms.BooleanField(
        label="J'ai écrit ce que j'ai appris.", required=False,
    )
    todo_kept_for_later = forms.BooleanField(
        label="J'ai gardé la ressource pour réviser plus tard.", required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Une ressource éducative en ligne peut être une vidéo, un PDF ou un exercice.",
        choices=Module6Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Une bonne ressource doit être adaptée à mon niveau.",
        choices=Module6Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Il suffit de regarder une vidéo sans prendre de notes pour bien apprendre.",
        choices=Module6Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4 = forms.ChoiceField(
        label="4. Quel type de ressource est utile pour s'entraîner ?",
        choices=Module6Submission.QUIZ_Q4_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q5 = forms.ChoiceField(
        label="5. Quelle recherche est la plus adaptée pour trouver une fiche PDF de révision ?",
        choices=Module6Submission.QUIZ_Q5_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q6_selected = forms.MultipleChoiceField(
        label="6. Quels signes montrent qu'une ressource peut être utile pour réviser ?",
        choices=[
            (Module6Submission.QUIZ_Q6_OPTION_EXPLIQUE, "Elle explique clairement la leçon"),
            (Module6Submission.QUIZ_Q6_OPTION_EXERCICES, "Elle propose des exercices"),
            (Module6Submission.QUIZ_Q6_OPTION_NIVEAU, "Elle correspond à mon niveau"),
            (Module6Submission.QUIZ_Q6_OPTION_MATIERE, "Elle est liée à une matière scolaire"),
            (Module6Submission.QUIZ_Q6_OPTION_PASSWORD, "Elle demande mon mot de passe"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q7_selected = forms.MultipleChoiceField(
        label="7. Que puis-je faire après avoir trouvé une bonne ressource ?",
        choices=[
            (Module6Submission.QUIZ_Q7_OPTION_LIEN, "Noter le lien"),
            (Module6Submission.QUIZ_Q7_OPTION_COMPRIS, "Écrire ce que j'ai compris"),
            (Module6Submission.QUIZ_Q7_OPTION_REVISER, "L'utiliser pour réviser"),
            (Module6Submission.QUIZ_Q7_OPTION_GARDER, "La garder dans un dossier ou un carnet"),
            (Module6Submission.QUIZ_Q7_OPTION_PASSWORD, "La partager avec mon mot de passe"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )

    practical_subject = forms.ChoiceField(
        label="Matière choisie",
        choices=Module6Submission.PRACTICAL_SUBJECT_CHOICES,
    )
    practical_what_to_revise = forms.CharField(
        label="Qu'est-ce que tu veux réviser ?",
        max_length=255,
        help_text="Exemple : équations, photosynthèse, vocabulaire anglais, résumé de texte.",
    )
    practical_resource_type = forms.ChoiceField(
        label="Type de ressource trouvée",
        choices=Module6Submission.RESOURCE_TYPE_CHOICES,
    )
    practical_resource_name_or_link = forms.CharField(
        label="Nom ou lien de la ressource trouvée",
        max_length=255,
        help_text="Écris le nom du site, le titre de la page ou le lien si tu peux.",
    )
    practical_adapted_level = forms.ChoiceField(
        label="Cette ressource est-elle adaptée à ton niveau ?",
        choices=Module6Submission.YES_SOMEWHAT_NO_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    practical_what_learned = forms.CharField(
        label="Qu'est-ce que cette ressource t'a appris ?",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris une ou deux phrases simples.",
    )

    feedback_understood_today = forms.CharField(
        label="Ce que j'ai compris aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris une ou deux phrases simples.",
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        help_text="Écris ce qui n'est pas encore clair.",
    )
    feedback_confidence_resources = forms.ChoiceField(
        label="Après cette séance, je me sens plus capable d'utiliser des ressources éducatives en ligne.",
        choices=Module6Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value


class Module7SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l'école",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_password = forms.ChoiceField(
        label="Je sais créer un mot de passe plus sûr.",
        choices=Module7Submission.AUTO_EVAL_M7_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_suspect = forms.ChoiceField(
        label="Je sais reconnaître un message suspect.",
        choices=Module7Submission.AUTO_EVAL_M7_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_personal_info = forms.ChoiceField(
        label="Je sais quelles informations personnelles je dois protéger.",
        choices=Module7Submission.AUTO_EVAL_M7_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_identified_weak_password = forms.BooleanField(
        label="J'ai identifié un mot de passe faible.", required=False,
    )
    todo_written_password_rules = forms.BooleanField(
        label="J'ai écrit les règles d'un mot de passe plus sûr.", required=False,
    )
    todo_understood_no_code_sharing = forms.BooleanField(
        label="J'ai compris pourquoi il ne faut pas partager un code.", required=False,
    )
    todo_observed_suspect_message = forms.BooleanField(
        label="J'ai observé un exemple de message suspect.", required=False,
    )
    todo_spotted_danger_signs = forms.BooleanField(
        label="J'ai repéré au moins deux signes de danger.", required=False,
    )
    todo_applied_stop_method = forms.BooleanField(
        label="J'ai appliqué la méthode STOP avant de cliquer.", required=False,
    )
    todo_listed_personal_info = forms.BooleanField(
        label="J'ai listé des informations personnelles à protéger.", required=False,
    )
    todo_ask_help = forms.BooleanField(
        label="Je sais demander de l'aide si j'ai un doute.", required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. C'est une bonne idée de donner son mot de passe à un ami proche.",
        choices=Module7Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Un mot de passe long et unique protège mieux un compte.",
        choices=Module7Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. La validation en deux étapes ajoute une protection en plus.",
        choices=Module7Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4 = forms.ChoiceField(
        label="4. Si un message demande de cliquer très vite pour gagner un cadeau, que dois-je faire ?",
        choices=Module7Submission.QUIZ_Q4_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q5_selected = forms.MultipleChoiceField(
        label="5. Quels signes peuvent montrer qu'un message est suspect ?",
        choices=[
            (Module7Submission.QUIZ_Q5_OPTION_MDP, "Il demande mon mot de passe"),
            (Module7Submission.QUIZ_Q5_OPTION_CADEAU, "Il promet un cadeau incroyable"),
            (Module7Submission.QUIZ_Q5_OPTION_VITE, "Il demande d'agir très vite"),
            (Module7Submission.QUIZ_Q5_OPTION_LIEN, "Il contient un lien bizarre"),
            (Module7Submission.QUIZ_Q5_OPTION_PROF, "Il vient clairement de mon professeur avec une consigne expliquée"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q6_selected = forms.MultipleChoiceField(
        label="6. Quelles informations dois-je protéger en ligne ?",
        choices=[
            (Module7Submission.QUIZ_Q6_OPTION_MDP, "Mon mot de passe"),
            (Module7Submission.QUIZ_Q6_OPTION_ADRESSE, "Mon adresse personnelle"),
            (Module7Submission.QUIZ_Q6_OPTION_TEL, "Mon numéro de téléphone"),
            (Module7Submission.QUIZ_Q6_OPTION_PHOTOS, "Mes photos privées"),
            (Module7Submission.QUIZ_Q6_OPTION_LECON, "Une leçon publique partagée par le professeur"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q7_selected = forms.MultipleChoiceField(
        label="7. Si j'ai cliqué sur un lien suspect, que puis-je faire ?",
        choices=[
            (Module7Submission.QUIZ_Q7_OPTION_PARLER, "En parler rapidement à un adulte ou au formateur"),
            (Module7Submission.QUIZ_Q7_OPTION_CHANGER, "Changer mon mot de passe si nécessaire"),
            (Module7Submission.QUIZ_Q7_OPTION_CONSEIL, "Ne plus utiliser le compte sans demander conseil"),
            (Module7Submission.QUIZ_Q7_OPTION_SECRET, "Garder le problème secret"),
            (Module7Submission.QUIZ_Q7_OPTION_DONNER, "Donner le code reçu à la personne qui le demande"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )

    practical_situation = forms.ChoiceField(
        label="Situation analysée",
        choices=Module7Submission.SITUATION_CHOICES,
    )
    practical_describe = forms.CharField(
        label="Décris rapidement la situation.",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Exemple : un message me promet un cadeau et demande de cliquer sur un lien.",
    )
    practical_danger_signs = forms.CharField(
        label="Quels signes de danger as-tu repérés ?",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Écris au moins un signe de danger.",
    )
    practical_protect_selected = forms.MultipleChoiceField(
        label="Quelles informations faut-il protéger dans cette situation ?",
        choices=Module7Submission.PROTECT_INFO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    practical_good_reaction_selected = forms.MultipleChoiceField(
        label="Quelle bonne réaction faut-il avoir ?",
        choices=Module7Submission.REACTION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    practical_explain = forms.CharField(
        label="Explique ton choix avec tes propres mots.",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris une ou deux phrases simples.",
    )

    feedback_understood_today = forms.CharField(
        label="Ce que j'ai compris aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris une ou deux phrases simples.",
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        help_text="Écris ce qui n'est pas encore clair.",
    )
    feedback_confidence_security = forms.ChoiceField(
        label="Après cette séance, je me sens plus capable de me protéger en ligne.",
        choices=Module7Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value


class Module8SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numéro à l'école",
        min_length=2, max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numéro.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prénom(s)", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_search = forms.ChoiceField(
        label="Je sais faire une recherche utile sur Internet pour apprendre.",
        choices=Module8Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_source = forms.ChoiceField(
        label="Je sais vérifier si une source en ligne est fiable.",
        choices=Module8Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_summarize = forms.ChoiceField(
        label="Je sais résumer une information avec mes propres mots.",
        choices=Module8Submission.SELF_EVAL_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_chose_subject = forms.BooleanField(
        label="J'ai choisi une matière à travailler.", required=False,
    )
    todo_written_question = forms.BooleanField(
        label="J'ai écrit ma question de départ.", required=False,
    )
    todo_transformed_keywords = forms.BooleanField(
        label="J'ai transformé ma question en mots-clés.", required=False,
    )
    todo_found_first_source = forms.BooleanField(
        label="J'ai trouvé une première source en ligne.", required=False,
    )
    todo_found_second_source = forms.BooleanField(
        label="J'ai trouvé une deuxième source différente.", required=False,
    )
    todo_checked_source_quality = forms.BooleanField(
        label="J'ai vérifié l'auteur, le site, la date ou les preuves.", required=False,
    )
    todo_chose_most_useful = forms.BooleanField(
        label="J'ai choisi la source la plus utile.", required=False,
    )
    todo_noted_three_ideas = forms.BooleanField(
        label="J'ai noté trois idées importantes.", required=False,
    )
    todo_prepared_synthesis = forms.BooleanField(
        label="J'ai préparé une synthèse courte.", required=False,
    )
    todo_presented_explained = forms.BooleanField(
        label="J'ai présenté ou expliqué ma synthèse.", required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Le Module 8 permet d'appliquer les compétences apprises dans les modules précédents.",
        choices=Module8Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Une bonne recherche sur Internet commence par une question claire.",
        choices=Module8Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Il suffit de copier le premier résultat trouvé pour répondre à une question.",
        choices=Module8Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4 = forms.ChoiceField(
        label="4. Avant d'utiliser une information, il faut vérifier la source.",
        choices=Module8Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q5 = forms.ChoiceField(
        label="5. Un message académique doit être clair et respectueux.",
        choices=Module8Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q6 = forms.ChoiceField(
        label="6. Il est acceptable de partager mon mot de passe avec un ami de confiance.",
        choices=Module8Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q7_selected = forms.MultipleChoiceField(
        label="7. Que faut-il faire quand on cherche une information en ligne ?",
        choices=[
            (Module8Submission.QUIZ_Q7_OPTION_CLARIFIER, "Formuler une question claire avant de chercher"),
            (Module8Submission.QUIZ_Q7_OPTION_MOTS_CLES, "Choisir des mots-clés adaptés"),
            (Module8Submission.QUIZ_Q7_OPTION_SOURCE, "Vérifier la fiabilité de la source"),
            (Module8Submission.QUIZ_Q7_OPTION_COMPARER, "Comparer plusieurs sources"),
            (Module8Submission.QUIZ_Q7_OPTION_COPIER, "Copier sans essayer de comprendre"),
            (Module8Submission.QUIZ_Q7_OPTION_RESUMER, "Résumer l'information avec ses propres mots"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )

    practical_subject = forms.ChoiceField(
        label="Matière choisie",
        choices=Module8Submission.PRACTICAL_SUBJECT_CHOICES,
    )
    practical_topic = forms.CharField(
        label="Quel sujet veux-tu approfondir ?",
        max_length=255,
        help_text="Exemple : équations, photosynthèse, la Révolution française.",
    )
    practical_starting_question = forms.CharField(
        label="Écris ta question de départ.",
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Exemple : Qu'est-ce qui a causé la Révolution française ?",
    )
    practical_keywords_used = forms.CharField(
        label="Quels mots-clés as-tu utilisés pour chercher ?",
        max_length=255,
        help_text="Exemple : causes Révolution française 1789.",
    )
    practical_first_source = forms.CharField(
        label="Écris le titre ou le lien de ta première source.",
        max_length=255,
    )
    practical_second_source = forms.CharField(
        label="Écris le titre ou le lien de ta deuxième source (si tu en as une).",
        max_length=255,
        required=False,
    )
    practical_verified_elements = forms.MultipleChoiceField(
        label="Qu'as-tu vérifié sur tes sources ?",
        choices=Module8Submission.VERIFIED_ELEMENTS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    practical_three_ideas = forms.CharField(
        label="Quelles sont les trois idées importantes que tu as retenues ?",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris trois idées ou informations clés.",
    )
    practical_synthesis = forms.CharField(
        label="Écris une mini-synthèse de 4 à 6 lignes.",
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Résume ce que tu as appris avec tes propres mots.",
    )
    practical_academic_message = forms.CharField(
        label="Message académique (optionnel) : écris un message à ton formateur.",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text="Exemple : un retour sur ce que tu as appris.",
    )

    feedback_best_success = forms.CharField(
        label="Ce que j'ai réussi aujourd'hui :",
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Écris une ou deux phrases sur ce dont tu es fier.",
    )
    feedback_still_difficult = forms.CharField(
        label="Ce qui reste difficile pour moi :",
        widget=forms.Textarea(attrs={"rows": 4}),
        required=False,
        help_text="Écris ce qui n'est pas encore clair.",
    )
    feedback_confidence = forms.ChoiceField(
        label="Après cette séance, je me sens plus à l'aise avec la recherche et l'utilisation d'informations en ligne.",
        choices=Module8Submission.CONFIDENCE_CHOICES,
        widget=forms.RadioSelect,
    )
    feedback_one_thing_to_practice = forms.CharField(
        label="Une chose que je veux continuer à pratiquer :",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
        help_text="Écris une habitude ou compétence à renforcer.",
    )

    def clean_school_id_number(self):
        value = self.cleaned_data["school_id_number"].strip()
        if not value.isdigit() or len(value) != 2:
            raise forms.ValidationError("Entre exactement 2 chiffres, par exemple 01.")
        return value
