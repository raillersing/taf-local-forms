from django import forms

from .models import Student, Submission


class Module2SubmissionForm(forms.Form):
    school_id_number = forms.CharField(
        label="Numero d'identification a l'ecole",
        min_length=2,
        max_length=2,
        help_text="Exemple : 01, 09, 39",
        error_messages={
            "required": "Entre ton numero d'identification.",
            "min_length": "Entre exactement 2 chiffres, par exemple 01.",
            "max_length": "Entre exactement 2 chiffres, par exemple 01.",
        },
    )
    full_name = forms.CharField(label="Nom et prenom", max_length=255)
    class_level = forms.ChoiceField(label="Classe / niveau", choices=Student.CLASS_LEVEL_CHOICES)
    group_name = forms.CharField(label="Groupe ou salle", max_length=100, required=False)

    auto_eval_internet_explained = forms.ChoiceField(
        label="Je sais expliquer ce qu'est Internet.",
        choices=Submission.SELF_EVAL_LEVEL_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_learning_usage = forms.ChoiceField(
        label="J'ai deja utilise Internet pour apprendre une lecon.",
        choices=Submission.SELF_EVAL_USAGE_CHOICES,
        widget=forms.RadioSelect,
    )
    auto_eval_open_browser = forms.ChoiceField(
        label="Je sais ouvrir un navigateur Internet.",
        choices=Submission.SELF_EVAL_BROWSER_CHOICES,
        widget=forms.RadioSelect,
    )

    todo_opened_browser = forms.BooleanField(label="J'ai ouvert le navigateur.", required=False)
    todo_typed_simple_search = forms.BooleanField(label="J'ai ecrit une recherche simple.", required=False)
    todo_used_keywords = forms.BooleanField(label="J'ai utilise des mots-cles utiles.", required=False)
    todo_opened_result = forms.BooleanField(label="J'ai ouvert un resultat de recherche.", required=False)
    todo_compared_results = forms.BooleanField(label="J'ai compare au moins deux resultats.", required=False)
    todo_found_school_info = forms.BooleanField(
        label="J'ai trouve une information utile pour une matiere scolaire.",
        required=False,
    )
    todo_asked_for_help = forms.BooleanField(
        label="J'ai demande de l'aide quand je ne comprenais pas.",
        required=False,
    )
    todo_noted_learning = forms.BooleanField(
        label="J'ai note une chose importante apprise pendant la seance.",
        required=False,
    )

    quiz_q1 = forms.ChoiceField(
        label="1. Internet sert seulement a utiliser Facebook.",
        choices=Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q2 = forms.ChoiceField(
        label="2. Pour chercher une lecon, il vaut mieux utiliser des mots-cles simples.",
        choices=Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q3 = forms.ChoiceField(
        label="3. Quand je trouve une information sur Internet, je dois parfois verifier si elle est fiable.",
        choices=Submission.TRUE_FALSE_UNKNOWN_CHOICES,
        widget=forms.RadioSelect,
    )
    quiz_q4_selected = forms.MultipleChoiceField(
        label="4. Que peut-on faire avec Internet pour les etudes ?",
        choices=[
            (Submission.QUIZ_Q4_OPTION_EXPLANATION, "Chercher une explication"),
            (Submission.QUIZ_Q4_OPTION_VIDEO, "Regarder une video educative"),
            (Submission.QUIZ_Q4_OPTION_DOCUMENT, "Trouver un document de revision"),
            (Submission.QUIZ_Q4_OPTION_WORD, "Apprendre un nouveau mot"),
            (Submission.QUIZ_Q4_OPTION_PASSWORD, "Donner son mot de passe a un ami"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    quiz_q5 = forms.ChoiceField(
        label="5. Quel exemple est une bonne recherche ?",
        choices=[
            ("math", "math"),
            ("cours_equation_seconde_exemple", "cours equation seconde exemple"),
            ("fb_video", "fb video"),
            ("internet", "internet"),
        ],
        widget=forms.RadioSelect,
    )

    practical_search_text = forms.CharField(
        label="Ecris une recherche que tu as faite pendant la seance.",
        max_length=255,
    )
    practical_site_text = forms.CharField(
        label="Ecris le nom ou l'adresse du site que tu as trouve.",
        max_length=255,
        required=False,
    )
    practical_subject = forms.ChoiceField(
        label="Cette information peut m'aider dans quelle matiere ?",
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
