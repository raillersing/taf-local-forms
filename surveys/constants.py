"""Métadonnées centralisées des modules TAfHSSiM.

Cette source unique est utilisée par les vues et templates pour garantir la
cohérence des titres, scores max, durées estimées, résumés et URLs.
"""

from django.urls import reverse

MODULE_METADATA = {
    "MODULE_1": {
        "number": 1,
        "title_key": "title",
        "max_score": 51,
        "estimated_duration": 20,
        "summary": (
            "Ce questionnaire de première prise de contact aide l'équipe TAfHSSiM à "
            "mieux connaître ton accès aux outils numériques, tes habitudes, tes "
            "besoins et ce que tu aimerais apprendre. Ce n'est pas un examen."
        ),
        "student_url_name": "surveys:student_module_1_detail",
        "detail_url_name": "surveys:student_module_1_detail",
        "form_url_name": "surveys:module_1",
        "dashboard_url_name": None,
        "csv_url_name": None,
        "pedagogy_partial": "surveys/partials/module_1_pedagogy.html",
    },
    "MODULE_2": {
        "number": 2,
        "title_key": "title",
        "max_score": 5,
        "estimated_duration": 10,
        "summary": (
            "Internet est un grand réseau qui relie des ordinateurs, des téléphones, "
            "des serveurs et des sites web dans le monde. Il peut aider à apprendre, "
            "faire des recherches, communiquer et préparer son avenir. Mais il faut "
            "savoir chercher correctement et rester prudent."
        ),
        "student_url_name": "surveys:student_module_2_detail",
        "detail_url_name": "surveys:student_module_2_detail",
        "form_url_name": "surveys:module_2",
        "dashboard_url_name": "surveys:dashboard_module_2",
        "csv_url_name": "surveys:export_module_2_csv",
        "pedagogy_partial": "surveys/partials/module_2_pedagogy.html",
    },
    "MODULE_3": {
        "number": 3,
        "title_key": "title",
        "max_score": 7,
        "estimated_duration": 12,
        "summary": (
            "La recherche efficace, c'est trouver rapidement l'information utile "
            "pour un besoin précis. On commence par reformuler sa question en mots "
            "clés, on compare plusieurs résultats, on garde les plus fiables et on "
            "note ce qu'on a compris."
        ),
        "student_url_name": "surveys:student_module_3_detail",
        "detail_url_name": "surveys:student_module_3_detail",
        "form_url_name": "surveys:module_3",
        "dashboard_url_name": "surveys:dashboard_module_3",
        "csv_url_name": "surveys:export_module_3_csv",
        "pedagogy_partial": "surveys/partials/module_3_pedagogy.html",
    },
    "MODULE_4": {
        "number": 4,
        "title_key": "title",
        "max_score": 7,
        "estimated_duration": 12,
        "summary": (
            "Vérifier une information, c'est s'assurer qu'elle est fiable avant de "
            "la croire ou de la partager. On regarde qui l'a publiée, quand, avec "
            "quelles preuves, et on la compare avec d'autres sources sérieuses."
        ),
        "student_url_name": "surveys:student_module_4_detail",
        "detail_url_name": "surveys:student_module_4_detail",
        "form_url_name": "surveys:module_4",
        "dashboard_url_name": "surveys:dashboard_module_4",
        "csv_url_name": "surveys:export_module_4_csv",
        "pedagogy_partial": "surveys/partials/module_4_pedagogy.html",
    },
    "MODULE_5": {
        "number": 5,
        "title_key": "title",
        "max_score": 7,
        "estimated_duration": 12,
        "summary": (
            "L'email sert à communiquer sérieusement avec un professeur, une école, "
            "une université ou une organisation. Un bon email contient : un destinataire, "
            "un objet clair, une salutation, un message court, une formule de politesse, "
            "une signature et parfois une pièce jointe. Règle simple : clair, poli, complet, relu."
        ),
        "student_url_name": "surveys:student_module_5_detail",
        "detail_url_name": "surveys:student_module_5_detail",
        "form_url_name": "surveys:module_5",
        "dashboard_url_name": "surveys:dashboard_module_5",
        "csv_url_name": "surveys:export_module_5_csv",
        "pedagogy_partial": "surveys/partials/module_5_pedagogy.html",
    },
    "MODULE_6": {
        "number": 6,
        "title_key": "title",
        "max_score": 7,
        "estimated_duration": 12,
        "summary": (
            "Une ressource éducative en ligne est un contenu qui aide à apprendre : cours, vidéo, "
            "exercice, PDF, dictionnaire, schéma ou quiz. Une bonne ressource est utile, claire, "
            "adaptée à ton niveau et reliée à une matière scolaire. Règle simple : chercher, choisir, tester, noter."
        ),
        "student_url_name": "surveys:student_module_6_detail",
        "detail_url_name": "surveys:student_module_6_detail",
        "form_url_name": "surveys:module_6",
        "dashboard_url_name": "surveys:dashboard_module_6",
        "csv_url_name": "surveys:export_module_6_csv",
        "pedagogy_partial": "surveys/partials/module_6_pedagogy.html",
    },
    "MODULE_7": {
        "number": 7,
        "title_key": "title",
        "max_score": 7,
        "estimated_duration": 12,
        "summary": (
            "La sécurité en ligne, ce sont les bons gestes pour protéger tes comptes, tes fichiers, "
            "tes photos et tes informations. Les risques les plus courants sont : mot de passe volé, "
            "lien suspect, faux message, arnaque, cyberharcèlement et partage trop rapide. "
            "Règle simple : protéger, vérifier, demander de l'aide."
        ),
        "student_url_name": "surveys:student_module_7_detail",
        "detail_url_name": "surveys:student_module_7_detail",
        "form_url_name": "surveys:module_7",
        "dashboard_url_name": "surveys:dashboard_module_7",
        "csv_url_name": "surveys:export_module_7_csv",
        "pedagogy_partial": "surveys/partials/module_7_pedagogy.html",
    },
    "MODULE_8": {
        "number": 8,
        "title_key": "title",
        "max_score": 7,
        "estimated_duration": 15,
        "summary": (
            "Le Module 8 est le module de synthèse. Tu vas utiliser tout ce que tu as appris "
            "depuis le début : chercher une information, vérifier une source, choisir une ressource, "
            "et produire un travail personnel. Tu réaliseras une mini-fiche d'apprentissage sur un "
            "sujet de ton choix, en suivant une démarche complète : besoin → recherche → sélection "
            "→ vérification → production."
        ),
        "student_url_name": "surveys:student_module_8_detail",
        "detail_url_name": "surveys:student_module_8_detail",
        "form_url_name": "surveys:module_8",
        "dashboard_url_name": "surveys:dashboard_module_8",
        "csv_url_name": "surveys:export_module_8_csv",
        "pedagogy_partial": "surveys/partials/module_8_pedagogy.html",
    },
}


def get_module_metadata(code: str) -> dict:
    """Retourne une copie des métadonnées du module ou un dictionnaire vide."""
    return dict(MODULE_METADATA.get(code, {}))


def get_module_detail_url(code: str) -> str:
    """URL de détail du module (côté étudiant)."""
    meta = MODULE_METADATA.get(code)
    if meta and meta.get("detail_url_name"):
        return reverse(meta["detail_url_name"])
    return ""


def get_module_form_url(code: str) -> str:
    """URL du formulaire élève du module."""
    meta = MODULE_METADATA.get(code)
    if meta and meta.get("form_url_name"):
        return reverse(meta["form_url_name"])
    return ""


def get_module_dashboard_url(code: str) -> str:
    """URL du dashboard formateur du module."""
    meta = MODULE_METADATA.get(code)
    if meta and meta.get("dashboard_url_name"):
        return reverse(meta["dashboard_url_name"])
    return ""


def get_module_csv_url(code: str) -> str:
    """URL d'export CSV du module."""
    meta = MODULE_METADATA.get(code)
    if meta and meta.get("csv_url_name"):
        return reverse(meta["csv_url_name"])
    return ""
