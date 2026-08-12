import csv
import json
import mimetypes
import os
from urllib.parse import quote
from collections import Counter
from datetime import datetime, timedelta

from django import forms as django_forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.db import IntegrityError, connection
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .constants import (
    MODULE_METADATA,
    get_module_csv_url,
    get_module_dashboard_url,
    get_module_detail_url,
    get_module_form_url,
    get_module_metadata,
)
from .dashboard_metrics import (
    active_session_for_module,
    dashboard_totals,
    find_student_by_identity,
    module_score_metrics,
    sessions_with_responses_count,
    submission_queryset,
    unique_student_identities,
)
from .forms import (
    LearningResourceForm,
    MODULE1_FIELD_DEFINITIONS,
    Module1SubmissionForm,
    Module2SubmissionForm,
    Module3SubmissionForm,
    Module4SubmissionForm,
    Module5SubmissionForm,
    Module6SubmissionForm,
    Module7SubmissionForm,
    Module8SubmissionForm,
)
from .models import (
    FormPresence,
    LearningResource,
    Module1Submission,
    Module3Submission,
    Module4Submission,
    Module5Submission,
    Module6Submission,
    Module7Submission,
    Module8Submission,
    EditRequest,
    NetworkPhoneCheck,
    Student,
    Subject,
    Submission,
    TrainingModule,
    TrainingSession,
)


def _build_preview_items(form) -> list[dict]:
    from django import forms
    preview_items = []
    for name, field in form.fields.items():
        value = form.cleaned_data.get(name)
        if value is None or value == "" or value == []:
            display_value = "Non renseigné"
        elif isinstance(field, forms.MultipleChoiceField):
            choice_dict = dict(field.choices)
            display_value = ", ".join(choice_dict.get(v, str(v)) for v in value)
        elif isinstance(field, forms.ChoiceField):
            choice_dict = dict(field.choices)
            display_value = choice_dict.get(value, str(value))
        elif isinstance(field, forms.BooleanField):
            display_value = "Oui" if value else "Non"
        else:
            display_value = str(value)
        preview_items.append({
            'label': field.label,
            'value': display_value,
            'name': name
        })
    return preview_items


def _get_submission_initial_data(submission, module_number: int) -> dict:
    from django.forms.models import model_to_dict
    data = model_to_dict(submission)
    if module_number == 1:
        pass
    else:
        data["full_name"] = submission.student.full_name
        data["class_level"] = submission.student.class_level
        data["group_name"] = submission.student.group_name
    return data


def sanitize_csv_cell(value):
    if value is None:
        return ""
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


QUESTION_INSIGHT_EXCLUDED_FIELDS = {
    "full_name", "class_level", "group_name",
    "paper_full_name", "paper_class_level", "paper_school_name", "paper_date",
}


def _question_section(field_name: str) -> str:
    prefixes = {
        "auto_eval_": "Auto-évaluation",
        "todo_": "Activités réalisées",
        "quiz_": "Compréhension",
        "practical_": "Mise en pratique",
        "feedback_": "Retour des élèves",
    }
    for prefix, label in prefixes.items():
        if field_name.startswith(prefix):
            return label
    return "Questionnaire"


def _insight_interpretation(kind: str, answered: int, top_label: str = "", top_rate: float = 0) -> str:
    if not answered:
        return "Pas encore assez de réponses pour dégager une tendance."
    if kind == "boolean":
        if top_rate >= 75:
            return "Étape largement réalisée par le groupe. L’acquis paraît bien installé."
        if top_rate >= 50:
            return "Étape réalisée par une majorité, mais encore à consolider avec une partie du groupe."
        return "Étape encore peu réalisée. Prévoir une reprise ou un accompagnement ciblé."
    if kind in {"choice", "multiple"}:
        if top_rate >= 60:
            return f"Une tendance nette se dégage vers « {top_label} » ({top_rate:.0f} %)."
        return "Les réponses sont partagées. Vérifier les écarts avec le groupe avant de poursuivre."
    if kind == "number":
        return "La moyenne situe le groupe, mais les valeurs basses et hautes restent utiles pour adapter l’accompagnement."
    return "Réponses qualitatives : les extraits anonymisés permettent de repérer les besoins et difficultés récurrents."


def _build_question_insights(submissions, form_class, field_definitions=None) -> list[dict]:
    records = list(submissions)
    if field_definitions is None:
        fields = [
            (name, field.label or name.replace("_", " "), field)
            for name, field in form_class.base_fields.items()
            if name not in QUESTION_INSIGHT_EXCLUDED_FIELDS and records and hasattr(records[0], name)
        ]
    else:
        fields = []
        for name, label, kind, choices in field_definitions:
            if kind == "multiple":
                field = django_forms.MultipleChoiceField(choices=choices or [], required=False)
            elif kind == "choice":
                field = django_forms.ChoiceField(choices=choices or [], required=False)
            elif kind == "boolean":
                field = django_forms.BooleanField(required=False)
            else:
                field = django_forms.CharField(required=False)
            fields.append((name, label, field))

    sections: dict[str, list[dict]] = {}
    for name, label, field in fields:
        raw_values = [getattr(record, name, None) for record in records]
        values = [value for value in raw_values if value not in (None, "", [])]
        insight = {"name": name, "label": label, "answered": len(values), "total": len(records)}

        if isinstance(field, django_forms.BooleanField):
            completed = sum(bool(value) for value in raw_values)
            rate = round((completed / len(records)) * 100, 1) if records else 0
            insight.update(kind="boolean", value=rate, options=[
                {"label": "Réalisé", "count": completed, "rate": rate},
                {"label": "À faire", "count": len(records) - completed, "rate": round(100 - rate, 1) if records else 0},
            ], interpretation=_insight_interpretation("boolean", len(records), "Réalisé", rate))
        elif isinstance(field, django_forms.MultipleChoiceField):
            choice_labels = dict(field.choices)
            counts = Counter(item for value in values for item in value)
            options = [
                {"label": str(choice_labels.get(value, value)), "count": count,
                 "rate": round((count / len(values)) * 100, 1) if values else 0}
                for value, count in counts.most_common()
            ]
            top = options[0] if options else {"label": "", "rate": 0}
            insight.update(kind="multiple", options=options,
                           interpretation=_insight_interpretation("multiple", len(values), top["label"], top["rate"]))
        elif isinstance(field, django_forms.ChoiceField):
            choice_labels = dict(field.choices)
            counts = Counter(values)
            options = [
                {"label": str(choice_labels.get(value, value)), "count": count,
                 "rate": round((count / len(values)) * 100, 1) if values else 0}
                for value, count in counts.most_common()
            ]
            top = options[0] if options else {"label": "", "rate": 0}
            insight.update(kind="choice", options=options,
                           interpretation=_insight_interpretation("choice", len(values), top["label"], top["rate"]))
        elif isinstance(field, (django_forms.IntegerField, django_forms.FloatField, django_forms.DecimalField)):
            numeric_values = [float(value) for value in values]
            insight.update(kind="number", average=round(sum(numeric_values) / len(numeric_values), 1) if numeric_values else 0,
                           minimum=min(numeric_values) if numeric_values else 0, maximum=max(numeric_values) if numeric_values else 0,
                           interpretation=_insight_interpretation("number", len(numeric_values)))
        else:
            excerpts = [str(value).strip()[:180] for value in values if str(value).strip()][:3]
            insight.update(kind="text", excerpts=excerpts,
                           interpretation=_insight_interpretation("text", len(values)))

        sections.setdefault(_question_section(name), []).append(insight)
    return [{"title": title, "questions": questions} for title, questions in sections.items()]


def _mark_presence_submitted(request, module_code, session):
    client_id = request.POST.get("taf_client_id", "").strip()
    if client_id:
        FormPresence.objects.filter(
            client_id=client_id,
            module_code=module_code,
            training_session=session,
            status=FormPresence.STATUS_ACTIVE,
        ).update(status=FormPresence.STATUS_SUBMITTED)


@never_cache
def home(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/home.html", _build_home_context(request))


def _build_home_context(request: HttpRequest | None = None) -> dict:
    from .network import get_network_access_context

    modules_total = TrainingModule.objects.count() or 7
    modules_open = (
        TrainingSession.objects.filter(is_active=True, accepting_responses=True)
        .values("module_id")
        .distinct()
        .count()
    )
    total_submissions = (
        Submission.objects.count()
        + Module1Submission.objects.count()
        + Module3Submission.objects.count()
        + Module4Submission.objects.count()
        + Module5Submission.objects.count()
        + Module6Submission.objects.count()
        + Module7Submission.objects.count()
        + Module8Submission.objects.count()
    )
    net_ctx = get_network_access_context(request) if request else {}
    return {
        "modules_total": modules_total,
        "modules_open": modules_open,
        "total_submissions": total_submissions,
        "published_resources_count": _published_resources_queryset().count(),
        "network": net_ctx,
        "student_access_url": net_ctx.get("recommended_student_base_url", ""),
        "student_access_ready": bool(net_ctx.get("recommended_student_base_url", "")),
    }


def _prototype_module_title(module: TrainingModule) -> str:
    prefix = f"Module {module.code.removeprefix('MODULE_')} - "
    if module.title.startswith(prefix):
        return module.title[len(prefix):]
    return module.title


def _max_score_for_module(module_code: str) -> int:
    meta = MODULE_METADATA.get(module_code, {})
    return meta.get("max_score", 0)


def _published_resources_queryset():
    return LearningResource.objects.filter(is_published=True).select_related("subject", "chapter")


def _build_cockpit_context(request: HttpRequest) -> dict:
    from .network import get_network_access_context

    net_ctx = get_network_access_context(request)
    published_resources_count = _published_resources_queryset().count()
    total_resources_count = LearningResource.objects.count()
    active_totals = dashboard_totals(active_only=True)
    historical_totals = dashboard_totals(active_only=False)

    modules = TrainingModule.objects.all().order_by("code")
    module_list = []
    modules_open = 0
    active_module = None
    global_score_sum = 0
    global_score_max = 0
    for mod in modules:
        module_number = mod.code.removeprefix("MODULE_")
        active_session = active_session_for_module(mod.code)
        accepting = active_session.accepting_responses if active_session else False
        if accepting:
            modules_open += 1
        active_queryset = submission_queryset(mod.code, active_session) if active_session else submission_queryset(mod.code).none()
        historical_queryset = submission_queryset(mod.code)
        submission_count = active_queryset.count()
        active_student_count = len(unique_student_identities([active_queryset]))
        historical_submission_count = historical_queryset.count()
        max_score = _max_score_for_module(mod.code)
        module_score_sum, module_score_max, avg_score = module_score_metrics(mod.code, active_queryset)
        global_score_sum += module_score_sum
        global_score_max += module_score_max
        module_item = {
            "module": mod,
            "module_number": module_number,
            "export_url_name": f"surveys:export_module_{module_number}_csv",
            "display_title": _prototype_module_title(mod),
            "has_active_session": active_session is not None,
            "accepting_responses": accepting,
            "active_session_id": active_session.pk if active_session else None,
            "submission_count": submission_count,
            "active_student_count": active_student_count,
            "historical_submission_count": historical_submission_count,
            "max_score": max_score,
            "average_score": avg_score,
            "score_available": avg_score is not None,
            "score_sum": module_score_sum,
            "score_max": module_score_max,
            "session_status": (
                ("Réponses ouvertes" if accepting else "Séance active · réponses fermées")
                if active_session
                else "Aucune séance active"
            ),
            "dashboard_url": reverse(f"surveys:dashboard_module_{module_number}"),
        }
        module_list.append(module_item)
        if active_module is None and active_session is not None:
            active_module = module_item

    average_score = round((global_score_sum / global_score_max) * 100, 1) if global_score_max else 0

    student_access_url = ""
    if net_ctx.get("recommended_lan_host"):
        student_access_url = net_ctx.get("student_form_url", "")

    if active_module is None:
        cockpit_action = {
            "kind": "empty",
            "eyebrow": "Prochaine étape",
            "title": "Aucune séance active",
            "description": "Ouvrez le pilotage des modules pour préparer la prochaine séance.",
            "label": "Ouvrir le pilotage des modules",
            "url": reverse("surveys:dashboard_modules"),
        }
    elif not student_access_url:
        cockpit_action = {
            "kind": "attention",
            "eyebrow": "Accès à vérifier",
            "title": "Le réseau élèves n’est pas prêt",
            "description": "Vérifiez l’adresse locale avant de lancer les réponses de la classe.",
            "label": "Vérifier le réseau",
            "url": reverse("surveys:dashboard_network"),
        }
    elif active_module["accepting_responses"]:
        cockpit_action = {
            "kind": "active",
            "eyebrow": "Séance en cours",
            "title": active_module["display_title"],
            "description": "Les réponses sont ouvertes. Suivez la participation et les résultats de ce module.",
            "label": "Ouvrir le suivi du module",
            "url": active_module["dashboard_url"],
        }
    else:
        cockpit_action = {
            "kind": "paused",
            "eyebrow": "Séance en pause",
            "title": active_module["display_title"],
            "description": "La séance existe, mais les réponses sont fermées. Consultez son état ou choisissez un autre module.",
            "label": "Voir les modules",
            "url": reverse("surveys:dashboard_modules"),
        }

    return {
        "total_submissions": active_totals.submissions,
        "total_students": active_totals.unique_students,
        "historical_submissions": historical_totals.submissions,
        "historical_students": historical_totals.unique_students,
        "historical_sessions": sessions_with_responses_count(),
        "average_score": average_score,
        "module_list": module_list,
        "modules_open": modules_open,
        "active_module": active_module,
        "network": net_ctx,
        "student_access_url": student_access_url,
        "student_access_ready": bool(student_access_url),
        "projection_url": "/dashboard/projection/",
        "has_lan_host": bool(net_ctx.get("configured_host")),
        "published_resources_count": published_resources_count,
        "total_resources_count": total_resources_count,
        "metrics_updated_at": timezone.now(),
        "cockpit_action": cockpit_action,
    }


@never_cache
def student_modules(request: HttpRequest) -> HttpResponse:
    modules = TrainingModule.objects.all().order_by("code")
    module_data = []
    for mod in modules:
        active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
        module_data.append({
            "module": mod,
            "display_title": _prototype_module_title(mod),
            "has_active_session": active_session is not None,
            "active_session": active_session,
            "detail_url": get_module_detail_url(mod.code),
        })
    return render(request, "surveys/student_modules.html", {"module_data": module_data})


@never_cache
def student_module_detail(request: HttpRequest, module_code: str) -> HttpResponse:
    mod = get_object_or_404(TrainingModule, code=module_code)
    active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
    accepting = active_session.accepting_responses if active_session else False
    meta = get_module_metadata(module_code)

    return render(request, "surveys/student_module_detail.html", {
        "module": mod,
        "active_session": active_session,
        "has_active_session": active_session is not None,
        "accepting_responses": accepting,
        "summary": meta.get("summary", ""),
        "questionnaire_url": get_module_form_url(module_code),
        "estimated_duration": meta.get("estimated_duration", 10),
        "max_score": meta.get("max_score", 0),
        "module_number": meta.get("number", module_code.removeprefix("MODULE_")),
        "pedagogy_partial": meta.get("pedagogy_partial", ""),
    })


@never_cache
def project(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/project.html", {})


@never_cache
def school_subjects(request: HttpRequest) -> HttpResponse:
    subjects = Subject.objects.filter(is_active=True).order_by("sort_order", "name")
    return render(request, "surveys/school_subjects.html", {"subjects": subjects})


def _module1_form_sections(form):
    sections = [
        ("Partie 1 — Informations générales", ["q1_age", "q2_gender", "q3_location", "q3_location_other", "q4_device_use"]),
        ("Partie 2 — Accès aux équipements numériques", ["q5_home_devices", "q6_device_owner", "q7_device_frequency", "q8_keyboard", "q9_mouse"]),
        ("Partie 3 — Accès à Internet", ["q10_internet_use", "q11_internet_location", "q12_internet_problems", "q12_internet_problems_other", "q13_internet_uses"]),
        ("Partie 4 — Compétences numériques de base", [f"q{i}_{name}" for i, name in [(14, "power_device"), (15, "wifi"), (16, "open_app"), (17, "write_text"), (18, "save_file"), (19, "find_file"), (20, "photo_scan")]]),
        ("Partie 5 — Email et communication", ["q21_email", "q22_create_email", "q23_send_email", "q24_attach_email", "q25_apps"]),
        ("Partie 6 — Recherche d’information", ["q26_search_method", "q27_google_search", "q28_verify_information", "q29_internet_truth", "q30_search_explanation"]),
        ("Partie 7 — Sécurité numérique", ["q31_secure_password", "q32_share_password", "q33_suspect_message", "q34_online_harassment_actions", "q35_protect_personal_information"]),
        ("Partie 8 — Utilisation du numérique pour les études", ["q36_learn_lesson", "q37_educational_video", "q38_pdf", "q39_dictionary_translation", "q40_subjects", "q40_subject_other"]),
        ("Partie 9 — Motivation et besoins", ["q41_motivations", "q41_motivation_other", "q42_first_learning", "q43_training_commitment", "q44_regular_attendance", "q45_preferred_schedule", "q45_schedule_other"]),
        ("Partie 10 — Petite auto-évaluation", ["q46_digital_level", "q47_search_level", "q48_device_confidence"]),
        ("Partie 11 — Questions ouvertes simples", ["q49_greatest_difficulty", "q50_after_training", "q51_question_or_concern"]),
    ]
    multiple_names = {name for name, _label, kind, _choices in MODULE1_FIELD_DEFINITIONS if kind == "multiple"}
    return [
        {
            "title": title,
            "fields": [{"field": form[name], "kind": "choice" if name in multiple_names or form[name].field.widget.__class__.__name__ == "RadioSelect" else "field"} for name in names],
        }
        for title, names in sections
    ]


@never_cache
def module_1_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_1", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_1_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module1SubmissionForm()
            return render(request, "surveys/module_1_form.html", {
                "form": form, "sections": _module1_form_sections(form), "session": session,
                "module": session.module, "module_1_summary": get_module_metadata("MODULE_1").get("summary", ""),
                "accepting_responses": False,
            }, status=403)

        paper_full_name = request.POST.get("paper_full_name", "").strip()
        paper_class_level = request.POST.get("paper_class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if paper_full_name:
            if Module1Submission.objects.filter(session=session, paper_full_name=paper_full_name).exists():
                sub_id_in_session = request.session.get("last_module1_submission_id")
                is_this_submission = False
                if sub_id_in_session:
                    try:
                        ex_sub = Module1Submission.objects.get(pk=sub_id_in_session)
                        if ex_sub.paper_full_name == paper_full_name:
                            is_this_submission = True
                    except Module1Submission.DoesNotExist:
                        pass
                if not is_this_submission:
                    has_duplicate = True

        if has_duplicate:
            form = Module1SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 1})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(request, "surveys/module_1_form.html", {
                "form": form, "sections": _module1_form_sections(form), "session": session,
                "module": session.module, "module_1_summary": get_module_metadata("MODULE_1").get("summary", ""),
                "accepting_responses": True,
            })

        form = Module1SubmissionForm(request.POST)
        if form.is_valid():
            preview_data = dict(form.cleaned_data)
            if preview_data.get("paper_date"):
                preview_data["paper_date"] = preview_data["paper_date"].isoformat()
            request.session["module_1_preview_data"] = preview_data
            return redirect("surveys:module_1_preview")
    else:
        preview_data = request.session.get("module_1_preview_data")
        sub_id_in_session = request.session.get("last_module1_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module1_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module1Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 1)
            except Module1Submission.DoesNotExist:
                pass

        if preview_data:
            preview_data = dict(preview_data)
            if isinstance(preview_data.get("paper_date"), str):
                from datetime import date
                preview_data["paper_date"] = date.fromisoformat(preview_data["paper_date"])
            initial_data.update(preview_data)

        form = Module1SubmissionForm(initial=initial_data if initial_data else None)

    return render(request, "surveys/module_1_form.html", {
        "form": form, "sections": _module1_form_sections(form), "session": session,
        "module": session.module, "module_1_summary": get_module_metadata("MODULE_1").get("summary", ""),
        "accepting_responses": accepting,
        "is_editing": is_editing,
    })


@never_cache
def module_1_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_1", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_1_unavailable.html", status=503)

    preview_data = request.session.get("module_1_preview_data")
    if not preview_data:
        return redirect("surveys:module_1")

    preview_data = dict(preview_data)
    if isinstance(preview_data.get("paper_date"), str):
        from datetime import date
        preview_data["paper_date"] = date.fromisoformat(preview_data["paper_date"])

    form = Module1SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_1")

    if request.method == "POST":
        paper_full_name = form.cleaned_data["paper_full_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module1_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module1Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module1Submission.DoesNotExist:
                pass

        paper_class = form.cleaned_data["paper_class_level"].strip().casefold()
        if "seconde" in paper_class:
            student_class_level = Student.CLASS_LEVEL_SECONDE
        elif "première" in paper_class or "premiere" in paper_class:
            student_class_level = Student.CLASS_LEVEL_PREMIERE
        else:
            student_class_level = Student.CLASS_LEVEL_AUTRE

        student = find_student_by_identity(paper_full_name, student_class_level)
        if student and Module1Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("paper_full_name", "Une réponse existe déjà pour ce nom et cette classe pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(paper_full_name.split()),
                    class_level=student_class_level,
                    group_name="",
                )

            submission_data = dict(form.cleaned_data)
            for field_name in ("q46_digital_level", "q47_search_level", "q48_device_confidence"):
                if submission_data[field_name] == "":
                    submission_data[field_name] = None
                elif submission_data[field_name] is not None:
                    submission_data[field_name] = int(submission_data[field_name])

            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module1Submission.objects.create(
                        student=student, session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("paper_full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_1_preview_data", None)
                request.session["last_module1_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_1", session)
                return redirect("surveys:module_1_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_1",
        },
    )


@never_cache
def module_1_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module1_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_1")
    submission = get_object_or_404(Module1Submission.objects.select_related("session", "student"), pk=submission_id)
    meta = get_module_metadata("MODULE_1")
    return render(request, "surveys/module_1_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60]})


@never_cache
@login_required
def dashboard_module_1(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_1")
    selected_session = session_context["selected_session"]
    submissions = (
        Module1Submission.objects.select_related("student", "session")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Module1Submission.objects.none()
    )
    rows = []
    for submission in submissions:
        rows.append({
            "submission": submission,
            "answers": [(label, _module1_export_value(name, getattr(submission, name))) for name, label, _kind, _choices in MODULE1_FIELD_DEFINITIONS],
        })
    return render(request, "surveys/dashboard_module_1.html", {
        "submissions": submissions,
        "rows": rows,
        "total_count": submissions.count(),
        "question_insights": _build_question_insights(submissions, Module1SubmissionForm, MODULE1_FIELD_DEFINITIONS),
        "breadcrumbs": [("Modules", "surveys:dashboard_modules"), "Module 1"],
        **session_context,
    })


def _module1_export_value(field_name, value):
    choice_map = {
        name: dict(choices or []) for name, _label, kind, choices in MODULE1_FIELD_DEFINITIONS if kind in {"choice", "multiple"}
    }
    if isinstance(value, list):
        return " | ".join(choice_map.get(field_name, {}).get(item, item) for item in value)
    return choice_map.get(field_name, {}).get(value, value or "")


def _filter_export_session(request: HttpRequest, module_code: str, submissions):
    session_id = request.GET.get("session_id", "").strip()
    if session_id.isdigit():
        return submissions.filter(session_id=int(session_id), session__module__code=module_code)
    return submissions


@never_cache
@login_required
def export_module_1_csv(request: HttpRequest) -> HttpResponse:
    submissions = Module1Submission.objects.select_related("student", "session").filter(session__module__code="MODULE_1").order_by("-created_at")
    submissions = _filter_export_session(request, "MODULE_1", submissions)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="module-1-prise-contact.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["Date d'enregistrement", "Session", "Nom et prénom(s)", "Classe / Niveau", "Établissement", "Date du questionnaire"] + [label for _name, label, _kind, _choices in MODULE1_FIELD_DEFINITIONS])
    for submission in submissions:
        row = [submission.created_at, submission.session.session_code, submission.paper_full_name, submission.paper_class_level, submission.paper_school_name, submission.paper_date]
        row.extend(_module1_export_value(name, getattr(submission, name)) for name, _label, _kind, _choices in MODULE1_FIELD_DEFINITIONS)
        writer.writerow([sanitize_csv_cell(value) for value in row])
    return response


@never_cache
def support_list(request: HttpRequest) -> HttpResponse:
    resources = _published_resources_queryset().order_by(
        "module_number",
        "subject__sort_order",
        "chapter__sort_order",
        "title",
    )
    subjects = Subject.objects.filter(is_active=True).order_by("sort_order", "name")
    selected_subject = request.GET.get("subject", "").strip()
    selected_level = request.GET.get("level", "").strip()
    selected_module = request.GET.get("module", "").strip()
    selected_type = request.GET.get("type", "").strip()
    if selected_subject:
        resources = resources.filter(subject__slug=selected_subject)
    if selected_level:
        resources = resources.filter(subject__class_level=selected_level)
    if selected_module.isdigit():
        resources = resources.filter(module_number=int(selected_module))
    if selected_type in {LearningResource.RESOURCE_TYPE_DOCUMENT, LearningResource.RESOURCE_TYPE_VIDEO}:
        resources = resources.filter(resource_type=selected_type)
    return render(
        request,
        "surveys/support_list.html",
        {
            "resources": resources,
            "subjects": subjects,
            "level_choices": Student.CLASS_LEVEL_CHOICES,
            "module_choices": range(2, 9),
            "selected_subject": selected_subject,
            "selected_level": selected_level,
            "selected_module": selected_module,
            "selected_type": selected_type,
        },
    )


@never_cache
def support_detail(request: HttpRequest, slug: str) -> HttpResponse:
    resource = get_object_or_404(_published_resources_queryset(), slug=slug)
    return render(request, "surveys/support_detail.html", {"resource": resource})


@never_cache
def support_watch(request: HttpRequest, slug: str) -> HttpResponse:
    resource = get_object_or_404(_published_resources_queryset(), slug=slug)
    if not resource.is_video or not resource.file:
        raise Http404("Vidéo indisponible")
    return render(request, "surveys/support_watch.html", {"resource": resource})


def support_download(request: HttpRequest, slug: str) -> FileResponse:
    resource = get_object_or_404(_published_resources_queryset(), slug=slug)
    if not resource.file:
        raise Http404("Fichier indisponible")
    try:
        file_handle = resource.file.open("rb")
    except FileNotFoundError as exc:
        raise Http404("Fichier indisponible") from exc
    content_type, _ = mimetypes.guess_type(resource.file.name)
    response = FileResponse(file_handle, as_attachment=True, filename=resource.file.name.rsplit("/", 1)[-1])
    if content_type:
        response["Content-Type"] = content_type
    return response


@never_cache
def module_2_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_2", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_2_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module2SubmissionForm()
            return render(
                request,
                "surveys/module_2_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_2_summary": get_module_metadata("MODULE_2").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module2SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 2})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_2_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_2_summary": get_module_metadata("MODULE_2").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module2SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_2_preview_data"] = form.cleaned_data
            return redirect("surveys:module_2_preview")
    else:
        preview_data = request.session.get("module_2_preview_data")
        sub_id_in_session = request.session.get("last_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 2)
            except Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module2SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_2_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_2_summary": get_module_metadata("MODULE_2").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_2_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_2", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_2_unavailable.html", status=503)

    preview_data = request.session.get("module_2_preview_data")
    if not preview_data:
        return redirect("surveys:module_2")

    form = Module2SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_2")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Submission.objects.get(pk=sub_id_in_session, session=session)
            except Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_2_preview_data", None)
                request.session["last_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_2", session)
                return redirect("surveys:module_2_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_2",
        },
    )


@never_cache
def module_2_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_2")
    submission = get_object_or_404(Submission.objects.select_related("session", "student"), pk=submission_id)
    meta = get_module_metadata("MODULE_2")
    return render(request, "surveys/module_2_success.html", {
        "submission": submission,
        "module_title": meta.get("summary", "")[:60] if meta.get("summary") else "Module 2",
        "max_score": meta.get("max_score", 5),
    })


@never_cache
@login_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/dashboard_home.html", _build_cockpit_context(request))


@never_cache
@login_required
def dashboard_start(request: HttpRequest) -> HttpResponse:
    """Friendly, trainer-facing startup runbook for the local classroom app."""
    return render(request, "surveys/dashboard_start.html")


@never_cache
@login_required
def dashboard_modules(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/dashboard_modules.html", _build_cockpit_context(request))


@never_cache
@staff_member_required
def dashboard_advanced(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "surveys/dashboard_advanced.html",
        {
            "db_engine": connection.vendor,
        },
    )


@never_cache
@login_required
def dashboard_projection(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/dashboard_projection.html", _build_cockpit_context(request))


@never_cache
@login_required
def dashboard_exports(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/dashboard_exports.html", _build_cockpit_context(request))


@never_cache
@login_required
def dashboard_supports(request: HttpRequest) -> HttpResponse:
    resources = LearningResource.objects.select_related("subject", "chapter").order_by("-updated_at", "title")
    context = {
        "resources": resources,
        "published_count": resources.filter(is_published=True).count(),
        "draft_count": resources.filter(is_published=False).count(),
    }
    return render(request, "surveys/dashboard_supports.html", context)


@never_cache
@login_required
def dashboard_support_upload(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = LearningResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save()
            status_label = "publié" if resource.is_published else "enregistré en brouillon"
            messages.success(request, f"Le support « {resource.title} » a été {status_label}.")
            return redirect("surveys:dashboard_supports")
    else:
        form = LearningResourceForm()

    return render(request, "surveys/dashboard_support_upload.html", {"form": form})







@never_cache
def module_5_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_5", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_5_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module5SubmissionForm()
            return render(
                request,
                "surveys/module_5_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_5_summary": get_module_metadata("MODULE_5").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Module5Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_module5_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module5SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 5})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_5_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_5_summary": get_module_metadata("MODULE_5").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module5SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_5_preview_data"] = form.cleaned_data
            return redirect("surveys:module_5_preview")
    else:
        preview_data = request.session.get("module_5_preview_data")
        sub_id_in_session = request.session.get("last_module5_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module5_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module5Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 5)
            except Module5Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module5SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_5_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_5_summary": get_module_metadata("MODULE_5").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_5_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_5", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_5_unavailable.html", status=503)

    preview_data = request.session.get("module_5_preview_data")
    if not preview_data:
        return redirect("surveys:module_5")

    form = Module5SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_5")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module5_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module5Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module5Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Module5Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module5Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_5_preview_data", None)
                request.session["last_module5_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_5", session)
                return redirect("surveys:module_5_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_5",
        },
    )


@never_cache
def module_5_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module5_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_5")
    submission = get_object_or_404(
        Module5Submission.objects.select_related("session", "student"), pk=submission_id
    )
    meta = get_module_metadata("MODULE_5")
    return render(request, "surveys/module_5_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60], "max_score": meta.get("max_score", 7)})


def _select_dashboard_session(request: HttpRequest, module_code: str):
    sessions = list(
        TrainingSession.objects.filter(module__code=module_code)
        .select_related("module")
        .order_by("-is_active", "-date", "session_code")
    )
    selected_session = None
    requested_id = request.GET.get("session_id", "").strip()
    if requested_id.isdigit():
        selected_session = next(
            (session for session in sessions if session.pk == int(requested_id)),
            None,
        )
    if selected_session is None:
        selected_session = next((session for session in sessions if session.is_active), None)
    if selected_session is None and sessions:
        selected_session = sessions[0]
    return selected_session, sessions


def _dashboard_session_context(request: HttpRequest, module_code: str) -> dict:
    selected_session, sessions = _select_dashboard_session(request, module_code)
    return {
        "selected_session": selected_session,
        "available_sessions": sessions,
        "selected_session_id": selected_session.pk if selected_session else "",
    }


@never_cache
@login_required
def dashboard_module_5(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_5")
    selected_session = session_context["selected_session"]
    submissions = (
        Module5Submission.objects.select_related("student", "session", "session__module")
        .filter(session=selected_session) if selected_session else
        Module5Submission.objects.none()
    )
    submissions = submissions.order_by("-created_at")
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_spotted_recipient", "Destinataire repéré"),
        ("todo_written_clear_subject", "Objet clair écrit"),
        ("todo_started_greeting", "Salutation"),
        ("todo_written_short_message", "Message court et précis"),
        ("todo_added_politeness", "Formule de politesse"),
        ("todo_signed_name", "Signature"),
        ("todo_checked_attachment", "Pièce jointe vérifiée"),
        ("todo_reread_before_sending", "Relecture avant envoi"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    context = {
        "submissions": submissions,
        "total_submissions": total_submissions,
        "total_students": submissions.values("student_id").distinct().count(),
        "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
        "todo_completion": todo_completion,
        "class_level_choices": Student.CLASS_LEVEL_CHOICES,
        "selected_class_level": class_level,
        "selected_group_name": group_name,
        **session_context,
    }
    context["question_insights"] = _build_question_insights(submissions, Module5SubmissionForm)
    return render(request, "surveys/dashboard_module_5.html", context)


@never_cache
@login_required
def export_module_5_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module5Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_5")
        .order_by("created_at")
    )
    submissions = _filter_export_session(request, "MODULE_5", submissions)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-5.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "full_name",
            "class_level",
            "group_name",
            "auto_eval_email_purpose",
            "auto_eval_write_email",
            "auto_eval_attach_file",
            "todo_spotted_recipient",
            "todo_written_clear_subject",
            "todo_started_greeting",
            "todo_written_short_message",
            "todo_added_politeness",
            "todo_signed_name",
            "todo_checked_attachment",
            "todo_reread_before_sending",
            "quiz_q1",
            "quiz_q2",
            "quiz_q3",
            "quiz_q4",
            "quiz_q5",
            "quiz_q6",
            "quiz_q7_selected",
            "practical_who_writing_to",
            "practical_email_subject",
            "practical_email_message",
            "practical_needs_attachment",
            "practical_attachment_file",
            "practical_best_tool",
            "feedback_understood_today",
            "feedback_still_difficult",
            "feedback_confidence_email",
            "computed_score",
        ]
    )
    for submission in submissions:
        writer.writerow(
            [
                submission.created_at.isoformat(),
                submission.session.session_code,
                sanitize_csv_cell(submission.student.full_name),
                submission.student.get_class_level_display(),
                sanitize_csv_cell(submission.student.group_name),
                submission.get_auto_eval_email_purpose_display(),
                submission.get_auto_eval_write_email_display(),
                submission.get_auto_eval_attach_file_display(),
                submission.todo_spotted_recipient,
                submission.todo_written_clear_subject,
                submission.todo_started_greeting,
                submission.todo_written_short_message,
                submission.todo_added_politeness,
                submission.todo_signed_name,
                submission.todo_checked_attachment,
                submission.todo_reread_before_sending,
                submission.get_quiz_q1_display(),
                submission.get_quiz_q2_display(),
                submission.get_quiz_q3_display(),
                submission.get_quiz_q4_display(),
                submission.quiz_q5,
                submission.quiz_q6,
                sanitize_csv_cell("|".join(submission.quiz_q7_selected)),
                sanitize_csv_cell(submission.practical_who_writing_to),
                sanitize_csv_cell(submission.practical_email_subject),
                sanitize_csv_cell(submission.practical_email_message),
                submission.get_practical_needs_attachment_display(),
                sanitize_csv_cell(submission.practical_attachment_file),
                submission.practical_best_tool,
                sanitize_csv_cell(submission.feedback_understood_today),
                sanitize_csv_cell(submission.feedback_still_difficult),
                submission.get_feedback_confidence_email_display(),
                submission.computed_score,
            ]
        )
    return response


@never_cache
def module_6_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_6", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_6_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module6SubmissionForm()
            return render(
                request,
                "surveys/module_6_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_6_summary": get_module_metadata("MODULE_6").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Module6Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_module6_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module6SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 6})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_6_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_6_summary": get_module_metadata("MODULE_6").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module6SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_6_preview_data"] = form.cleaned_data
            return redirect("surveys:module_6_preview")
    else:
        preview_data = request.session.get("module_6_preview_data")
        sub_id_in_session = request.session.get("last_module6_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module6_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module6Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 6)
            except Module6Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module6SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_6_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_6_summary": get_module_metadata("MODULE_6").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_6_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_6", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_6_unavailable.html", status=503)

    preview_data = request.session.get("module_6_preview_data")
    if not preview_data:
        return redirect("surveys:module_6")

    form = Module6SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_6")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module6_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module6Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module6Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Module6Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module6Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_6_preview_data", None)
                request.session["last_module6_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_6", session)
                return redirect("surveys:module_6_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_6",
        },
    )


@never_cache
def module_6_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module6_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_6")
    submission = get_object_or_404(
        Module6Submission.objects.select_related("session", "student"), pk=submission_id
    )
    meta = get_module_metadata("MODULE_6")
    return render(request, "surveys/module_6_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60], "max_score": meta.get("max_score", 7)})


@never_cache
@login_required
def dashboard_module_6(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_6")
    selected_session = session_context["selected_session"]
    submissions = (
        Module6Submission.objects.select_related("student", "session", "session__module")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Module6Submission.objects.none()
    )
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_chose_subject", "Matière choisie"),
        ("todo_searched_resource", "Ressource cherchée"),
        ("todo_opened_video_pdf_exercise", "Vidéo/PDF/exercice ouvert"),
        ("todo_checked_level", "Niveau vérifié"),
        ("todo_noted_resource_title", "Titre noté"),
        ("todo_noted_link_or_site", "Lien noté"),
        ("todo_written_what_learned", "Apprentissage écrit"),
        ("todo_kept_for_later", "Gardé pour réviser"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    context = {
        "submissions": submissions,
        "total_submissions": total_submissions,
        "total_students": submissions.values("student_id").distinct().count(),
        "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
        "todo_completion": todo_completion,
        "class_level_choices": Student.CLASS_LEVEL_CHOICES,
        "selected_class_level": class_level,
        "selected_group_name": group_name,
    }
    context["question_insights"] = _build_question_insights(submissions, Module6SubmissionForm)
    context.update(session_context)
    return render(request, "surveys/dashboard_module_6.html", context)


@never_cache
@login_required
def export_module_6_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module6Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_6")
        .order_by("created_at")
    )
    submissions = _filter_export_session(request, "MODULE_6", submissions)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-6.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "full_name",
            "class_level",
            "group_name",
            "auto_eval_find_resource",
            "auto_eval_choose_resource",
            "auto_eval_keep_link",
            "todo_chose_subject",
            "todo_searched_resource",
            "todo_opened_video_pdf_exercise",
            "todo_checked_level",
            "todo_noted_resource_title",
            "todo_noted_link_or_site",
            "todo_written_what_learned",
            "todo_kept_for_later",
            "quiz_q1",
            "quiz_q2",
            "quiz_q3",
            "quiz_q4",
            "quiz_q5",
            "quiz_q6_selected",
            "quiz_q7_selected",
            "practical_subject",
            "practical_what_to_revise",
            "practical_resource_type",
            "practical_resource_name_or_link",
            "practical_adapted_level",
            "practical_what_learned",
            "feedback_understood_today",
            "feedback_still_difficult",
            "feedback_confidence_resources",
            "computed_score",
        ]
    )
    for submission in submissions:
        writer.writerow(
            [
                submission.created_at.isoformat(),
                submission.session.session_code,
                sanitize_csv_cell(submission.student.full_name),
                submission.student.get_class_level_display(),
                sanitize_csv_cell(submission.student.group_name),
                submission.get_auto_eval_find_resource_display(),
                submission.get_auto_eval_choose_resource_display(),
                submission.get_auto_eval_keep_link_display(),
                submission.todo_chose_subject,
                submission.todo_searched_resource,
                submission.todo_opened_video_pdf_exercise,
                submission.todo_checked_level,
                submission.todo_noted_resource_title,
                submission.todo_noted_link_or_site,
                submission.todo_written_what_learned,
                submission.todo_kept_for_later,
                submission.get_quiz_q1_display(),
                submission.get_quiz_q2_display(),
                submission.get_quiz_q3_display(),
                submission.get_quiz_q4_display(),
                submission.quiz_q5,
                sanitize_csv_cell("|".join(submission.quiz_q6_selected)),
                sanitize_csv_cell("|".join(submission.quiz_q7_selected)),
                submission.get_practical_subject_display(),
                sanitize_csv_cell(submission.practical_what_to_revise),
                submission.practical_resource_type,
                sanitize_csv_cell(submission.practical_resource_name_or_link),
                submission.get_practical_adapted_level_display(),
                sanitize_csv_cell(submission.practical_what_learned),
                sanitize_csv_cell(submission.feedback_understood_today),
                sanitize_csv_cell(submission.feedback_still_difficult),
                submission.get_feedback_confidence_resources_display(),
                submission.computed_score,
            ]
        )
    return response


@never_cache
@login_required
def dashboard_module_2(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_2")
    selected_session = session_context["selected_session"]
    submissions = (
        Submission.objects.select_related("student", "session", "session__module")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Submission.objects.none()
    )
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_opened_browser", "Navigateur ouvert"),
        ("todo_typed_simple_search", "Recherche simple écrite"),
        ("todo_used_keywords", "Mots-clés utiles"),
        ("todo_opened_result", "Résultat ouvert"),
        ("todo_compared_results", "Deux résultats comparés"),
        ("todo_found_school_info", "Information utile trouvée"),
        ("todo_asked_for_help", "A demande de l'aide"),
        ("todo_noted_learning", "A noté un apprentissage"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    context = {
        "submissions": submissions,
        "total_submissions": total_submissions,
        "total_students": submissions.values("student_id").distinct().count(),
        "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
        "todo_completion": todo_completion,
        "class_level_choices": Student.CLASS_LEVEL_CHOICES,
        "selected_class_level": class_level,
        "selected_group_name": group_name,
    }
    context["question_insights"] = _build_question_insights(submissions, Module2SubmissionForm)
    context.update(session_context)
    return render(request, "surveys/dashboard_module_2.html", context)


@never_cache
@login_required
def export_module_2_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_2")
        .order_by("created_at")
    )
    submissions = _filter_export_session(request, "MODULE_2", submissions)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-2.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "full_name",
            "class_level",
            "group_name",
            "auto_eval_internet_explained",
            "auto_eval_learning_usage",
            "auto_eval_open_browser",
            "todo_opened_browser",
            "todo_typed_simple_search",
            "todo_used_keywords",
            "todo_opened_result",
            "todo_compared_results",
            "todo_found_school_info",
            "todo_asked_for_help",
            "todo_noted_learning",
            "quiz_q1",
            "quiz_q2",
            "quiz_q3",
            "quiz_q4_selected",
            "quiz_q5",
            "practical_search_text",
            "practical_site_text",
            "practical_subject",
            "feedback_understood_today",
            "feedback_still_difficult",
            "feedback_confidence",
            "computed_score",
        ]
    )
    for submission in submissions:
        writer.writerow(
            [
                submission.created_at.isoformat(),
                submission.session.session_code,
                sanitize_csv_cell(submission.student.full_name),
                submission.student.get_class_level_display(),
                sanitize_csv_cell(submission.student.group_name),
                submission.get_auto_eval_internet_explained_display(),
                submission.get_auto_eval_learning_usage_display(),
                submission.get_auto_eval_open_browser_display(),
                submission.todo_opened_browser,
                submission.todo_typed_simple_search,
                submission.todo_used_keywords,
                submission.todo_opened_result,
                submission.todo_compared_results,
                submission.todo_found_school_info,
                submission.todo_asked_for_help,
                submission.todo_noted_learning,
                submission.get_quiz_q1_display(),
                submission.get_quiz_q2_display(),
                submission.get_quiz_q3_display(),
                sanitize_csv_cell("|".join(submission.quiz_q4_selected)),
                submission.quiz_q5,
                sanitize_csv_cell(submission.practical_search_text),
                sanitize_csv_cell(submission.practical_site_text),
                submission.get_practical_subject_display(),
                sanitize_csv_cell(submission.feedback_understood_today),
                sanitize_csv_cell(submission.feedback_still_difficult),
                submission.get_feedback_confidence_display(),
                submission.computed_score,
            ]
        )
    return response




@never_cache
def module_3_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_3", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_3_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module3SubmissionForm()
            return render(
                request,
                "surveys/module_3_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_3_summary": get_module_metadata("MODULE_3").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Module3Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_module3_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module3SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 3})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_3_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_3_summary": get_module_metadata("MODULE_3").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module3SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_3_preview_data"] = form.cleaned_data
            return redirect("surveys:module_3_preview")
    else:
        preview_data = request.session.get("module_3_preview_data")
        sub_id_in_session = request.session.get("last_module3_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module3_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module3Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 3)
            except Module3Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module3SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_3_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_3_summary": get_module_metadata("MODULE_3").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_3_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_3", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_3_unavailable.html", status=503)

    preview_data = request.session.get("module_3_preview_data")
    if not preview_data:
        return redirect("surveys:module_3")

    form = Module3SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_3")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module3_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module3Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module3Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Module3Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module3Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_3_preview_data", None)
                request.session["last_module3_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_3", session)
                return redirect("surveys:module_3_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_3",
        },
    )


@never_cache
def module_3_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module3_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_3")
    submission = get_object_or_404(
        Module3Submission.objects.select_related("session", "student"), pk=submission_id
    )
    meta = get_module_metadata("MODULE_3")
    return render(request, "surveys/module_3_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60], "max_score": meta.get("max_score", 7)})


@never_cache
@login_required
def dashboard_module_3(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_3")
    selected_session = session_context["selected_session"]
    submissions = (
        Module3Submission.objects.select_related("student", "session", "session__module")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Module3Submission.objects.none()
    )
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_chose_subject", "Matière scolaire choisie"),
        ("todo_written_question", "Question de départ écrite"),
        ("todo_keywords_from_question", "Question transformée en mots-clés"),
        ("todo_did_search", "Recherche lancée"),
        ("todo_read_titles", "Titres des résultats lus"),
        ("todo_opened_result", "Résultat utile ouvert"),
        ("todo_compared_two_results", "Deux résultats comparés"),
        ("todo_improved_keywords", "Recherche améliorée avec meilleurs mots-clés"),
        ("todo_found_useful_resource", "Ressource utile trouvée"),
        ("todo_noted_learning", "Apprentissage noté"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    context = {
        "submissions": submissions,
        "total_submissions": total_submissions,
        "total_students": submissions.values("student_id").distinct().count(),
        "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
        "todo_completion": todo_completion,
        "class_level_choices": Student.CLASS_LEVEL_CHOICES,
        "selected_class_level": class_level,
        "selected_group_name": group_name,
    }
    context["question_insights"] = _build_question_insights(submissions, Module3SubmissionForm)
    context.update(session_context)
    return render(request, "surveys/dashboard_module_3.html", context)


@never_cache
@login_required
def export_module_3_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module3Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_3")
        .order_by("created_at")
    )
    submissions = _filter_export_session(request, "MODULE_3", submissions)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-3.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "full_name",
            "class_level",
            "group_name",
            "auto_eval_keywords",
            "auto_eval_improve",
            "auto_eval_compare",
            "todo_chose_subject",
            "todo_written_question",
            "todo_keywords_from_question",
            "todo_did_search",
            "todo_read_titles",
            "todo_opened_result",
            "todo_compared_two_results",
            "todo_improved_keywords",
            "todo_found_useful_resource",
            "todo_noted_learning",
            "quiz_q1",
            "quiz_q2",
            "quiz_q3",
            "quiz_q4",
            "quiz_q5",
            "quiz_q6",
            "quiz_q7_selected",
            "practical_starting_question",
            "practical_keywords_used",
            "practical_site_found",
            "practical_subject",
            "practical_what_learned",
            "feedback_understood_today",
            "feedback_still_difficult",
            "feedback_confidence_search",
            "computed_score",
        ]
    )
    for submission in submissions:
        writer.writerow(
            [
                submission.created_at.isoformat(),
                submission.session.session_code,
                sanitize_csv_cell(submission.student.full_name),
                submission.student.get_class_level_display(),
                sanitize_csv_cell(submission.student.group_name),
                submission.get_auto_eval_keywords_display(),
                submission.get_auto_eval_improve_display(),
                submission.get_auto_eval_compare_display(),
                submission.todo_chose_subject,
                submission.todo_written_question,
                submission.todo_keywords_from_question,
                submission.todo_did_search,
                submission.todo_read_titles,
                submission.todo_opened_result,
                submission.todo_compared_two_results,
                submission.todo_improved_keywords,
                submission.todo_found_useful_resource,
                submission.todo_noted_learning,
                submission.get_quiz_q1_display(),
                submission.get_quiz_q2_display(),
                submission.get_quiz_q3_display(),
                submission.get_quiz_q4_display(),
                submission.quiz_q5,
                submission.quiz_q6,
                sanitize_csv_cell("|".join(submission.quiz_q7_selected)),
                sanitize_csv_cell(submission.practical_starting_question),
                sanitize_csv_cell(submission.practical_keywords_used),
                sanitize_csv_cell(submission.practical_site_found),
                submission.get_practical_subject_display(),
                sanitize_csv_cell(submission.practical_what_learned),
                sanitize_csv_cell(submission.feedback_understood_today),
                sanitize_csv_cell(submission.feedback_still_difficult),
                submission.get_feedback_confidence_search_display(),
                submission.computed_score,
            ]
        )
    return response




@never_cache
def module_4_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_4", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_4_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module4SubmissionForm()
            return render(
                request,
                "surveys/module_4_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_4_summary": get_module_metadata("MODULE_4").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Module4Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_module4_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module4SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 4})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_4_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_4_summary": get_module_metadata("MODULE_4").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module4SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_4_preview_data"] = form.cleaned_data
            return redirect("surveys:module_4_preview")
    else:
        preview_data = request.session.get("module_4_preview_data")
        sub_id_in_session = request.session.get("last_module4_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module4_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module4Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 4)
            except Module4Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module4SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_4_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_4_summary": get_module_metadata("MODULE_4").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_4_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_4", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_4_unavailable.html", status=503)

    preview_data = request.session.get("module_4_preview_data")
    if not preview_data:
        return redirect("surveys:module_4")

    form = Module4SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_4")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module4_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module4Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module4Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Module4Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module4Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_4_preview_data", None)
                request.session["last_module4_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_4", session)
                return redirect("surveys:module_4_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_4",
        },
    )


@never_cache
def module_4_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module4_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_4")
    submission = get_object_or_404(
        Module4Submission.objects.select_related("session", "student"), pk=submission_id
    )
    meta = get_module_metadata("MODULE_4")
    return render(request, "surveys/module_4_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60], "max_score": meta.get("max_score", 7)})


@never_cache
@login_required
def dashboard_module_4(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_4")
    selected_session = session_context["selected_session"]
    submissions = (
        Module4Submission.objects.select_related("student", "session", "session__module")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Module4Submission.objects.none()
    )
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_chose_info", "Information choisie"),
        ("todo_opened_first_source", "Première source ouverte"),
        ("todo_checked_publisher", "Auteur/organisation vérifié"),
        ("todo_checked_date", "Date de publication cherchée"),
        ("todo_checked_evidence", "Preuves/chiffres/exemples vérifiés"),
        ("todo_compared_second", "Comparaison avec deuxième source"),
        ("todo_identified_reliable_sign", "Signe de fiabilité identifié"),
        ("todo_identified_doubtful_sign", "Signe de doute identifié"),
        ("todo_decided_reliable_or_not", "Décision prise sur la fiabilité"),
        ("todo_explained_choice", "Choix expliqué"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    decision_summary = {}
    for value, _ in Module4Submission.DECISION_CHOICES:
        count = submissions.filter(practical_decision=value).count()
        decision_summary[dict(Module4Submission.DECISION_CHOICES)[value]] = count

    context = {
        "submissions": submissions,
        "total_submissions": total_submissions,
        "total_students": submissions.values("student_id").distinct().count(),
        "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
        "todo_completion": todo_completion,
        "decision_summary": decision_summary,
        "class_level_choices": Student.CLASS_LEVEL_CHOICES,
        "selected_class_level": class_level,
        "selected_group_name": group_name,
    }
    context["question_insights"] = _build_question_insights(submissions, Module4SubmissionForm)
    context.update(session_context)
    return render(request, "surveys/dashboard_module_4.html", context)


@never_cache
@login_required
def export_module_4_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module4Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_4")
        .order_by("created_at")
    )
    submissions = _filter_export_session(request, "MODULE_4", submissions)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-4.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "full_name",
            "class_level",
            "group_name",
            "auto_eval_explain_source",
            "auto_eval_verify_info",
            "auto_eval_spot_doubtful",
            "todo_chose_info",
            "todo_opened_first_source",
            "todo_checked_publisher",
            "todo_checked_date",
            "todo_checked_evidence",
            "todo_compared_second",
            "todo_identified_reliable_sign",
            "todo_identified_doubtful_sign",
            "todo_decided_reliable_or_not",
            "todo_explained_choice",
            "quiz_q1",
            "quiz_q2",
            "quiz_q3",
            "quiz_q4",
            "quiz_q5_selected",
            "quiz_q6_selected",
            "quiz_q7",
            "practical_subject",
            "practical_first_source",
            "practical_publisher",
            "practical_has_date",
            "practical_has_evidence",
            "practical_compared",
            "practical_second_source",
            "practical_decision",
            "practical_explanation",
            "feedback_understood_today",
            "feedback_still_difficult",
            "feedback_confidence_verify",
            "computed_score",
        ]
    )
    for submission in submissions:
        writer.writerow(
            [
                submission.created_at.isoformat(),
                submission.session.session_code,
                sanitize_csv_cell(submission.student.full_name),
                submission.student.get_class_level_display(),
                sanitize_csv_cell(submission.student.group_name),
                submission.get_auto_eval_explain_source_display(),
                submission.get_auto_eval_verify_info_display(),
                submission.get_auto_eval_spot_doubtful_display(),
                submission.todo_chose_info,
                submission.todo_opened_first_source,
                submission.todo_checked_publisher,
                submission.todo_checked_date,
                submission.todo_checked_evidence,
                submission.todo_compared_second,
                submission.todo_identified_reliable_sign,
                submission.todo_identified_doubtful_sign,
                submission.todo_decided_reliable_or_not,
                submission.todo_explained_choice,
                submission.get_quiz_q1_display(),
                submission.get_quiz_q2_display(),
                submission.get_quiz_q3_display(),
                submission.quiz_q4,
                sanitize_csv_cell("|".join(submission.quiz_q5_selected)),
                sanitize_csv_cell("|".join(submission.quiz_q6_selected)),
                submission.get_quiz_q7_display(),
                sanitize_csv_cell(submission.practical_subject),
                sanitize_csv_cell(submission.practical_first_source),
                sanitize_csv_cell(submission.practical_publisher),
                submission.get_practical_has_date_display(),
                submission.get_practical_has_evidence_display(),
                submission.practical_compared,
                sanitize_csv_cell(submission.practical_second_source),
                submission.get_practical_decision_display(),
                sanitize_csv_cell(submission.practical_explanation),
                sanitize_csv_cell(submission.feedback_understood_today),
                sanitize_csv_cell(submission.feedback_still_difficult),
                submission.get_feedback_confidence_verify_display(),
                submission.computed_score,
            ]
        )
    return response


@never_cache
def module_7_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_7", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_7_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module7SubmissionForm()
            return render(
                request,
                "surveys/module_7_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_7_summary": get_module_metadata("MODULE_7").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Module7Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_module7_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module7SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 7})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_7_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_7_summary": get_module_metadata("MODULE_7").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module7SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_7_preview_data"] = form.cleaned_data
            return redirect("surveys:module_7_preview")
    else:
        preview_data = request.session.get("module_7_preview_data")
        sub_id_in_session = request.session.get("last_module7_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module7_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module7Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 7)
            except Module7Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module7SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_7_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_7_summary": get_module_metadata("MODULE_7").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_7_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_7", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_7_unavailable.html", status=503)

    preview_data = request.session.get("module_7_preview_data")
    if not preview_data:
        return redirect("surveys:module_7")

    form = Module7SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_7")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module7_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module7Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module7Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Module7Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module7Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_7_preview_data", None)
                request.session["last_module7_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_7", session)
                return redirect("surveys:module_7_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_7",
        },
    )


@never_cache
def module_7_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module7_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_7")
    submission = get_object_or_404(
        Module7Submission.objects.select_related("session", "student"), pk=submission_id
    )
    meta = get_module_metadata("MODULE_7")
    return render(request, "surveys/module_7_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60], "max_score": meta.get("max_score", 7)})


@never_cache
@login_required
def dashboard_module_7(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_7")
    selected_session = session_context["selected_session"]
    submissions = (
        Module7Submission.objects.select_related("student", "session", "session__module")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Module7Submission.objects.none()
    )
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_identified_weak_password", "Mot de passe faible identifié"),
        ("todo_written_password_rules", "Règles mot de passe écrites"),
        ("todo_understood_no_code_sharing", "Non-partage de code compris"),
        ("todo_observed_suspect_message", "Message suspect observé"),
        ("todo_spotted_danger_signs", "Signes de danger repérés"),
        ("todo_applied_stop_method", "Méthode STOP appliquée"),
        ("todo_listed_personal_info", "Infos personnelles listées"),
        ("todo_ask_help", "Demander de l'aide"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    context = {
        "submissions": submissions,
        "total_submissions": total_submissions,
        "total_students": submissions.values("student_id").distinct().count(),
        "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
        "todo_completion": todo_completion,
        "class_level_choices": Student.CLASS_LEVEL_CHOICES,
        "selected_class_level": class_level,
        "selected_group_name": group_name,
    }
    context["question_insights"] = _build_question_insights(submissions, Module7SubmissionForm)
    context.update(session_context)
    return render(request, "surveys/dashboard_module_7.html", context)


@never_cache
@login_required
def export_module_7_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module7Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_7")
        .order_by("created_at")
    )
    submissions = _filter_export_session(request, "MODULE_7", submissions)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-7.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "full_name",
            "class_level",
            "group_name",
            "auto_eval_password",
            "auto_eval_suspect",
            "auto_eval_personal_info",
            "todo_identified_weak_password",
            "todo_written_password_rules",
            "todo_understood_no_code_sharing",
            "todo_observed_suspect_message",
            "todo_spotted_danger_signs",
            "todo_applied_stop_method",
            "todo_listed_personal_info",
            "todo_ask_help",
            "quiz_q1",
            "quiz_q2",
            "quiz_q3",
            "quiz_q4",
            "quiz_q5_selected",
            "quiz_q6_selected",
            "quiz_q7_selected",
            "practical_situation",
            "practical_describe",
            "practical_danger_signs",
            "practical_protect_selected",
            "practical_good_reaction_selected",
            "practical_explain",
            "feedback_understood_today",
            "feedback_still_difficult",
            "feedback_confidence_security",
            "computed_score",
        ]
    )
    for submission in submissions:
        writer.writerow(
            [
                submission.created_at.isoformat(),
                submission.session.session_code,
                sanitize_csv_cell(submission.student.full_name),
                submission.student.get_class_level_display(),
                sanitize_csv_cell(submission.student.group_name),
                submission.get_auto_eval_password_display(),
                submission.get_auto_eval_suspect_display(),
                submission.get_auto_eval_personal_info_display(),
                submission.todo_identified_weak_password,
                submission.todo_written_password_rules,
                submission.todo_understood_no_code_sharing,
                submission.todo_observed_suspect_message,
                submission.todo_spotted_danger_signs,
                submission.todo_applied_stop_method,
                submission.todo_listed_personal_info,
                submission.todo_ask_help,
                submission.get_quiz_q1_display(),
                submission.get_quiz_q2_display(),
                submission.get_quiz_q3_display(),
                submission.get_quiz_q4_display(),
                sanitize_csv_cell("|".join(submission.quiz_q5_selected)),
                sanitize_csv_cell("|".join(submission.quiz_q6_selected)),
                sanitize_csv_cell("|".join(submission.quiz_q7_selected)),
                submission.practical_situation,
                sanitize_csv_cell(submission.practical_describe),
                sanitize_csv_cell(submission.practical_danger_signs),
                sanitize_csv_cell("|".join(submission.practical_protect_selected)),
                sanitize_csv_cell("|".join(submission.practical_good_reaction_selected)),
                sanitize_csv_cell(submission.practical_explain),
                sanitize_csv_cell(submission.feedback_understood_today),
                sanitize_csv_cell(submission.feedback_still_difficult),
                submission.get_feedback_confidence_security_display(),
                submission.computed_score,
            ]
        )
    return response


# ---- Module 8 ----

@never_cache
def module_8_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_8", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_8_unavailable.html", status=503)

    accepting = session.accepting_responses
    is_editing = False

    if request.method == "POST":
        if not accepting:
            form = Module8SubmissionForm()
            return render(
                request,
                "surveys/module_8_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_8_summary": get_module_metadata("MODULE_8").get("summary", ""),
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        full_name = request.POST.get("full_name", "").strip()
        class_level = request.POST.get("class_level", "").strip()

        # Check duplicate before full form validation
        has_duplicate = False
        if full_name:
            student = find_student_by_identity(full_name, class_level)
            if student:
                ex_sub = Module8Submission.objects.filter(session=session, student=student).first()
                if ex_sub:
                    sub_id_in_session = request.session.get("last_module8_submission_id")
                    if sub_id_in_session != ex_sub.pk:
                        has_duplicate = True

        if has_duplicate:
            form = Module8SubmissionForm(request.POST)
            from django.utils.safestring import mark_safe
            from django.urls import reverse
            request_url = reverse("surveys:request_edit", kwargs={"module_number": 8})
            btn_html = f'''
            <div class="edit-request-box" style="margin-top: 1rem; padding: 1.25rem; border: 1px solid var(--accent-light, #3b82f6); border-radius: 8px; background-color: #f0f9ff; color: #075985; text-align: left;">
                <p style="margin: 0 0 0.75rem 0; font-weight: 600;">Une réponse existe déjà pour ce nom pendant cette séance.</p>
                <p style="margin: 0 0 1rem 0; font-size: 0.95rem;">Si tu as cliqué sur enregistré par erreur ou si tu souhaites corriger tes réponses, tu peux envoyer une demande de modification au formateur.</p>
                <button type="submit" formaction="{request_url}" class="secondary-button" style="display: inline-flex; align-items: center; justify-content: center; min-height: 38px; border: 2px solid var(--accent-light, #3b82f6); color: var(--accent-light, #3b82f6); border-radius: 6px; padding: 0 1rem; font-weight: 600; cursor: pointer; transition: background-color 0.2s; background: white;">
                    Demander une modification au formateur
                </button>
            </div>
            '''
            form.add_error(None, mark_safe(btn_html))
            return render(
                request,
                "surveys/module_8_form.html",
                {
                    "form": form,
                    "session": session,
                    "module": session.module,
                    "module_8_summary": get_module_metadata("MODULE_8").get("summary", ""),
                    "accepting_responses": True,
                },
            )

        form = Module8SubmissionForm(request.POST)
        if form.is_valid():
            request.session["module_8_preview_data"] = form.cleaned_data
            return redirect("surveys:module_8_preview")
    else:
        preview_data = request.session.get("module_8_preview_data")
        sub_id_in_session = request.session.get("last_module8_submission_id")
        if sub_id_in_session and not request.session.get("active_edit_request_id"):
            request.session.pop("last_module8_submission_id", None)
            sub_id_in_session = None

        initial_data = {}
        if sub_id_in_session:
            try:
                ex_sub = Module8Submission.objects.get(pk=sub_id_in_session)
                is_editing = True
                initial_data = _get_submission_initial_data(ex_sub, 8)
            except Module8Submission.DoesNotExist:
                pass

        if preview_data:
            initial_data.update(preview_data)

        form = Module8SubmissionForm(initial=initial_data if initial_data else None)

    return render(
        request,
        "surveys/module_8_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_8_summary": get_module_metadata("MODULE_8").get("summary", ""),
            "accepting_responses": accepting,
            "is_editing": is_editing,
        },
    )


@never_cache
def module_8_preview(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_8", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, "surveys/module_8_unavailable.html", status=503)

    preview_data = request.session.get("module_8_preview_data")
    if not preview_data:
        return redirect("surveys:module_8")

    form = Module8SubmissionForm(preview_data)
    if not form.is_valid():
        return redirect("surveys:module_8")

    if request.method == "POST":
        full_name = form.cleaned_data["full_name"]
        class_level = form.cleaned_data["class_level"]
        group_name = form.cleaned_data["group_name"]

        # Check duplicate
        has_duplicate = False
        sub_id_in_session = request.session.get("last_module8_submission_id")
        submission = None
        if sub_id_in_session:
            try:
                submission = Module8Submission.objects.get(pk=sub_id_in_session, session=session)
            except Module8Submission.DoesNotExist:
                pass

        student = find_student_by_identity(full_name, class_level)
        if student and Module8Submission.objects.filter(session=session, student=student).exists():
            if not submission or submission.student != student:
                has_duplicate = True

        if has_duplicate:
            form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
        else:
            if not student:
                student = Student.objects.create(
                    full_name=" ".join(full_name.split()),
                    class_level=class_level,
                    group_name=group_name,
                )
            elif student.group_name != group_name:
                student.group_name = group_name
                student.save(update_fields=["group_name"])

            submission_data = {
                key: value
                for key, value in form.cleaned_data.items()
                if key not in {"full_name", "class_level", "group_name"}
            }
            try:
                if submission:
                    submission.student = student
                    for k, v in submission_data.items():
                        setattr(submission, k, v)
                    submission.save()
                else:
                    submission = Module8Submission.objects.create(
                        student=student,
                        session=session,
                        **submission_data,
                    )
            except IntegrityError:
                form.add_error("full_name", "Une réponse existe déjà pour ce nom pendant cette séance. Demande au formateur si tu dois modifier ta réponse.")
            else:
                active_req_id = request.session.pop("active_edit_request_id", None)
                if active_req_id:
                    try:
                        req = EditRequest.objects.get(pk=active_req_id)
                        req.status = EditRequest.STATUS_COMPLETED
                        req.one_time_token = None
                        req.save()
                    except EditRequest.DoesNotExist:
                        pass

                request.session.pop("module_8_preview_data", None)
                request.session["last_module8_submission_id"] = submission.pk
                _mark_presence_submitted(request, "MODULE_8", session)
                return redirect("surveys:module_8_success", submission_id=submission.pk)

    preview_items = _build_preview_items(form)
    return render(
        request,
        "surveys/module_preview.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "preview_items": preview_items,
            "edit_url_name": "surveys:module_8",
        },
    )


@never_cache
def module_8_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    sess_key = "last_module8_submission_id"
    if request.session.get(sess_key) != submission_id and request.session.get("successful_submission_id") != submission_id:
        return redirect("surveys:module_8")
    submission = get_object_or_404(
        Module8Submission.objects.select_related("session", "student"), pk=submission_id
    )
    meta = get_module_metadata("MODULE_8")
    return render(request, "surveys/module_8_success.html", {"submission": submission, "module_title": meta.get("summary", "")[:60], "max_score": meta.get("max_score", 7)})


@never_cache
@login_required
def dashboard_module_8(request: HttpRequest) -> HttpResponse:
    session_context = _dashboard_session_context(request, "MODULE_8")
    selected_session = session_context["selected_session"]
    submissions = (
        Module8Submission.objects.select_related("student", "session")
        .filter(session=selected_session).order_by("-created_at") if selected_session else
        Module8Submission.objects.none()
    )
    class_level = request.GET.get("class_level", "").strip()
    group_name = request.GET.get("group_name", "").strip()
    if class_level:
        submissions = submissions.filter(student__class_level=class_level)
    if group_name:
        submissions = submissions.filter(student__group_name__iexact=group_name)

    todo_fields = [
        ("todo_chose_subject", "Matière choisie"),
        ("todo_written_question", "Question formulée"),
        ("todo_transformed_keywords", "Mots-clés préparés"),
        ("todo_found_first_source", "Première source trouvée"),
        ("todo_found_second_source", "Deuxième source trouvée"),
        ("todo_checked_source_quality", "Qualité des sources vérifiée"),
        ("todo_chose_most_useful", "Source utile choisie"),
        ("todo_noted_three_ideas", "Trois idées notées"),
        ("todo_prepared_synthesis", "Synthèse préparée"),
        ("todo_presented_explained", "Présentation réalisée"),
    ]
    total_submissions = submissions.count()
    todo_completion = []
    for field_name, label in todo_fields:
        completed = submissions.filter(**{field_name: True}).count()
        rate = round((completed / total_submissions) * 100, 1) if total_submissions else 0
        todo_completion.append({"label": label, "rate": rate})

    return render(
        request,
        "surveys/dashboard_module_8.html",
        {
            "submissions": submissions,
            "total_submissions": total_submissions,
            "total_students": submissions.values("student_id").distinct().count(),
            "average_score": submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0,
            "todo_completion": todo_completion,
            "class_level_choices": Student.CLASS_LEVEL_CHOICES,
            "selected_class_level": class_level,
            "selected_group_name": group_name,
            "question_insights": _build_question_insights(submissions, Module8SubmissionForm),
            **session_context,
            "breadcrumbs": [("Modules", "surveys:dashboard_modules"), "Module 8"],
        },
    )


@never_cache
@login_required
def export_module_8_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module8Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_8")
        .order_by("-created_at")
    )
    submissions = _filter_export_session(request, "MODULE_8", submissions)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="module-8-synthese.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow([
        "Date", "Session", "Numero", "Nom", "Classe", "Groupe",
        "Auto-eval: rechercher", "Auto-eval: verifier source", "Auto-eval: resumer",
        "Todo: matiere choisie", "Todo: question ecrite", "Todo: mots-cles",
        "Todo: 1ere source", "Todo: 2e source", "Todo: qualite verifiee",
        "Todo: source choisie", "Todo: 3 idees notees", "Todo: synthese preparee",
        "Todo: presente/explique",
        "Quiz Q1", "Quiz Q2", "Quiz Q3", "Quiz Q4", "Quiz Q5", "Quiz Q6", "Quiz Q7",
        "Pratique: matiere", "Pratique: sujet", "Pratique: question depart",
        "Pratique: mots-cles", "Pratique: 1ere source", "Pratique: 2e source",
        "Pratique: elements verifies", "Pratique: 3 idees", "Pratique: synthese",
        "Pratique: message academique",
        "Feedback: reussi", "Feedback: difficile", "Feedback: confiance",
        "Feedback: a pratiquer",
        "Score",
    ])
    for submission in submissions:
        writer.writerow([
            submission.created_at.strftime("%Y-%m-%d %H:%M"),
            submission.session.session_code,
            sanitize_csv_cell(submission.student.full_name),
            submission.student.class_level,
            submission.student.group_name,
            submission.get_auto_eval_search_display(),
            submission.get_auto_eval_source_display(),
            submission.get_auto_eval_summarize_display(),
            "Oui" if submission.todo_chose_subject else "",
            "Oui" if submission.todo_written_question else "",
            "Oui" if submission.todo_transformed_keywords else "",
            "Oui" if submission.todo_found_first_source else "",
            "Oui" if submission.todo_found_second_source else "",
            "Oui" if submission.todo_checked_source_quality else "",
            "Oui" if submission.todo_chose_most_useful else "",
            "Oui" if submission.todo_noted_three_ideas else "",
            "Oui" if submission.todo_prepared_synthesis else "",
            "Oui" if submission.todo_presented_explained else "",
            submission.get_quiz_q1_display(),
            submission.get_quiz_q2_display(),
            submission.get_quiz_q3_display(),
            submission.get_quiz_q4_display(),
            submission.get_quiz_q5_display(),
            submission.get_quiz_q6_display(),
            sanitize_csv_cell("|".join(submission.quiz_q7_selected)),
            submission.get_practical_subject_display(),
            sanitize_csv_cell(submission.practical_topic),
            sanitize_csv_cell(submission.practical_starting_question),
            sanitize_csv_cell(submission.practical_keywords_used),
            sanitize_csv_cell(submission.practical_first_source),
            sanitize_csv_cell(submission.practical_second_source),
            sanitize_csv_cell("|".join(submission.practical_verified_elements)),
            sanitize_csv_cell(submission.practical_three_ideas),
            sanitize_csv_cell(submission.practical_synthesis),
            sanitize_csv_cell(submission.practical_academic_message),
            sanitize_csv_cell(submission.feedback_best_success),
            sanitize_csv_cell(submission.feedback_still_difficult),
            submission.get_feedback_confidence_display(),
            sanitize_csv_cell(submission.feedback_one_thing_to_practice),
            submission.computed_score,
        ])
    return response


@never_cache
@login_required
def network_access_dashboard(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context

    ctx = get_network_access_context(request)
    ctx["wifi_shared_checked"] = request.session.get("wifi_shared_checked", False)
    ctx["phone_test_checked"] = request.session.get("phone_test_checked", False)
    ctx["last_phone_test"] = NetworkPhoneCheck.objects.select_related("checked_by").first()
    return render(request, "surveys/dashboard_network.html", ctx)


@never_cache
def presence_heartbeat(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "invalid JSON"}, status=400)
    module_code = data.get("module_code", "").strip()
    client_id = data.get("client_id", "").strip()
    if not module_code or not client_id:
        return JsonResponse({"error": "module_code and client_id required"}, status=400)
    session = (
        TrainingSession.objects.filter(module__code=module_code, is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if not session:
        return JsonResponse({"error": "no active session"}, status=404)
    class_level = data.get("class_level", "").strip() or None
    current_path = data.get("current_path", "").strip() or ""
    cutoff = timezone.now() - timedelta(seconds=60)
    FormPresence.objects.filter(
        client_id=client_id,
        module_code=module_code,
        training_session=session,
        last_seen_at__lt=cutoff,
        status=FormPresence.STATUS_ACTIVE,
    ).update(status=FormPresence.STATUS_EXPIRED)
    now = timezone.now()
    presence, created = FormPresence.objects.update_or_create(
        client_id=client_id,
        module_code=module_code,
        training_session=session,
        defaults={
            "status": FormPresence.STATUS_ACTIVE,
            "current_path": current_path,
            "class_level": class_level,
            "last_seen_at": now,
        },
    )
    return JsonResponse({"ok": True})


@never_cache
@login_required
def dashboard_backup(request: HttpRequest) -> HttpResponse:
    from django.conf import settings

    db_engine = "postgresql" if settings.DB_HOST else "sqlite"
    historical_totals = dashboard_totals(active_only=False)
    context = {
        "db_engine": db_engine,
        "db_host": getattr(settings, "DB_HOST", ""),
        "db_port": getattr(settings, "DATABASES", {}).get("default", {}).get("PORT", "5432"),
        "db_name": getattr(settings, "DATABASES", {}).get("default", {}).get("NAME", "taf_local_forms"),
        "db_path": getattr(settings, "DATABASE_PATH", ""),
        "backup_command": "bash scripts/dev/taf-db-backup",
        "total_submissions": historical_totals.submissions,
        "total_students": historical_totals.unique_students,
    }
    return render(request, "surveys/dashboard_backup.html", context)


@never_cache
@login_required
def dashboard_presence_json(request: HttpRequest) -> JsonResponse:
    cutoff = timezone.now() - timedelta(seconds=60)
    active = FormPresence.objects.filter(
        status=FormPresence.STATUS_ACTIVE,
        last_seen_at__gte=cutoff,
    )
    total = active.count()
    by_module = {}
    for p in active.values("module_code").annotate(count=Count("id")):
        by_module[p["module_code"]] = p["count"]
    return JsonResponse({
        "total": total,
        "by_module": by_module,
        "timestamp": timezone.now().isoformat(),
    })


@never_cache
@login_required
def dashboard_lan_status_json(request: HttpRequest) -> JsonResponse:
    """Return the server-side LAN candidate for the cockpit refresh fallback."""
    from .network import get_network_access_context

    net_ctx = get_network_access_context(request)
    return JsonResponse({
        "recommended_lan_host": net_ctx.get("recommended_lan_host", ""),
        "recommended_lan_port": net_ctx.get("recommended_lan_port", "8011"),
        "student_port": net_ctx.get("student_port", "8011"),
        "detected_ip_candidates": net_ctx.get("detected_ip_candidates", []),
        "source": net_ctx.get("lan_host_source", "missing"),
        "timestamp": timezone.now().isoformat(),
    })


@never_cache
@staff_member_required
def dashboard_settings(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context
    from .settings_config import apply_setting, get_filtered_settings

    saved = None
    error = None
    if request.method == "POST":
        key = request.POST.get("key", "").strip()
        value = request.POST.get("value", "").strip()
        if key:
            ok, msg = apply_setting(key, value)
            if ok:
                saved = msg
            else:
                error = msg
        if request.POST.get("next") == "network":
            return redirect("surveys:dashboard_network")

    net_ctx = get_network_access_context(request)
    settings = get_filtered_settings()
    context = {
        "settings": settings,
        "detected_ip_candidates": net_ctx["detected_ip_candidates"],
        "recommended_host": net_ctx["recommended_host"],
        "port": net_ctx["port"],
        "saved": saved,
        "error": error,
        "current_request_is_lan": net_ctx["current_request_is_lan"],
        "recommended_lan_host": net_ctx["recommended_lan_host"],
        "recommended_lan_port": net_ctx["recommended_lan_port"],
        "lan_host_source": net_ctx["lan_host_source"],
        "lan_host_stale": net_ctx["lan_host_stale"],
        "helper_url": "http://127.0.0.1:8019",
        "is_localhost": net_ctx["current_request_host"] in ("localhost", "127.0.0.1", "[::1]"),
    }
    return render(request, "surveys/dashboard_settings.html", context)


@staff_member_required
@never_cache
@login_required
@require_POST
def dashboard_use_current_address(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context, _is_private_ip, _parse_host_port
    from .settings_config import apply_lan_settings

    net_ctx = get_network_access_context(request)
    posted_host = request.POST.get("lan_host", "").strip()
    if posted_host:
        host = posted_host
        if not _is_private_ip(host):
            messages.error(request, "L'adresse détectée n'est pas une IP LAN valide.")
            return redirect("surveys:dashboard_settings")
    elif net_ctx["current_request_is_lan"]:
        host = net_ctx["current_request_host"]
    else:
        messages.error(request, "L'adresse actuelle n'est pas une IP LAN valide.")
        return redirect("surveys:dashboard_settings")

    # The request may arrive through the student portproxy (8011). Keep the
    # trainer/Docker port separate from the student LAN port.
    port = net_ctx.get("student_port") or "8011"

    ok, msg = apply_lan_settings(host, port)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("surveys:dashboard_network")


@staff_member_required
@never_cache
@login_required
@require_POST
def toggle_module_responses(request: HttpRequest, module_code: str) -> HttpResponse:
    session = (
        TrainingSession.objects.filter(module__code=module_code, is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if not session:
        messages.error(request, f"Aucune session active pour {module_code}.")
        return redirect("surveys:dashboard_home")
    session.accepting_responses = not session.accepting_responses
    session.save(update_fields=["accepting_responses"])
    status = "ouvertes" if session.accepting_responses else "fermées"
    messages.success(request, f"Réponses {status} pour {session.module.title}.")
    return redirect("surveys:dashboard_home")


@never_cache
@staff_member_required
@login_required
def network_control(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context

    net_ctx = get_network_access_context(request)
    current_host = net_ctx.get("current_request_host", "")
    is_localhost = current_host in ("localhost", "127.0.0.1", "[::1]")
    helper_port = 8019
    helper_url = f"http://127.0.0.1:{helper_port}"
    configured_port = net_ctx.get("configured_port") or "8010"
    lan_port = net_ctx.get("recommended_lan_port") or "8011"
    windows_project_path = os.environ.get("TAF_WINDOWS_PROJECT_PATH", "").strip().rstrip("\\/")
    windows_helper_folder_path = (
        f"{windows_project_path}\\scripts\\windows" if windows_project_path else r"scripts\windows"
    )
    windows_helper_folder_uri = ""
    if windows_project_path:
        windows_helper_folder_uri = "file:///" + quote(
            f"{windows_project_path.replace(chr(92), '/')}/scripts/windows/",
            safe=":/",
        )

    context = {
        "net_ctx": net_ctx,
        "is_localhost": is_localhost,
        "helper_url": helper_url,
        "helper_port": helper_port,
        "lan_port": lan_port,
        "docker_port": configured_port,
        "windows_helper_folder_path": windows_helper_folder_path,
        "windows_helper_folder_uri": windows_helper_folder_uri,
    }
    return render(request, "surveys/dashboard_network_control.html", context)


@never_cache
@login_required
@staff_member_required
@require_POST
def network_checklist(request: HttpRequest) -> JsonResponse:
    key = request.POST.get("key", "").strip()
    checked = request.POST.get("checked", "false").lower() == "true"
    if key in {"wifi_shared_checked", "phone_test_checked"}:
        request.session[key] = checked
        if key == "phone_test_checked" and checked:
            from .network import get_network_access_context

            net_ctx = get_network_access_context(request)
            student_url = net_ctx.get("student_form_url", "")
            lan_host = net_ctx.get("recommended_lan_host", "")
            if student_url and lan_host:
                NetworkPhoneCheck.objects.create(
                    checked_by=request.user,
                    student_url=student_url,
                    lan_host=lan_host,
                )
        return JsonResponse({"ok": True, "key": key, "checked": checked})
    return JsonResponse({"ok": False, "error": "Clé inconnue"}, status=400)


@never_cache
def request_edit(request: HttpRequest, module_number: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("surveys:home")

    full_name = (request.POST.get("full_name") or request.POST.get("paper_full_name") or "").strip()
    class_level_raw = (request.POST.get("class_level") or request.POST.get("paper_class_level") or "").strip().casefold()

    if not full_name:
        return HttpResponse("Nom manquant", status=400)

    module_code = f"MODULE_{module_number}"
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code=module_code, is_active=True)
        .order_by("-date", "session_code")
        .first()
    )
    if session is None:
        return render(request, f"surveys/module_{module_number}_unavailable.html", status=503)

    if "seconde" in class_level_raw:
        student_class_level = Student.CLASS_LEVEL_SECONDE
    elif "première" in class_level_raw or "premiere" in class_level_raw:
        student_class_level = Student.CLASS_LEVEL_PREMIERE
    else:
        student_class_level = Student.CLASS_LEVEL_AUTRE

    student = find_student_by_identity(full_name, student_class_level)

    if not student:
        return HttpResponse("Élève non trouvé", status=400)

    from django.apps import apps
    if module_code == "MODULE_2":
        submission_model = apps.get_model("surveys", "Submission")
    else:
        submission_model = apps.get_model("surveys", f"Module{module_number}Submission")

    submission_exists = submission_model.objects.filter(student=student, session=session).exists()
    if not submission_exists:
        return HttpResponse("Aucune réponse enregistrée trouvée pour cet élève", status=400)

    edit_req = EditRequest.objects.filter(
        student=student,
        session=session,
        module_code=module_code,
        status__in=[EditRequest.STATUS_PENDING, EditRequest.STATUS_APPROVED]
    ).first()

    if not edit_req:
        edit_req = EditRequest.objects.create(
            student=student,
            session=session,
            module_code=module_code,
            status=EditRequest.STATUS_PENDING
        )

    return render(request, "surveys/edit_request_submitted.html", {
        "edit_request": edit_req,
        "session": session,
        "module": session.module,
    })


@never_cache
def activate_edit_request(request: HttpRequest, module_number: int, token: str) -> HttpResponse:
    module_code = f"MODULE_{module_number}"
    edit_req = get_object_or_404(
        EditRequest,
        module_code=module_code,
        one_time_token=token,
        status=EditRequest.STATUS_APPROVED
    )

    if edit_req.expires_at and timezone.now() > edit_req.expires_at:
        edit_req.status = EditRequest.STATUS_EXPIRED
        edit_req.one_time_token = None
        edit_req.save()
        return render(request, "surveys/edit_request_expired.html", status=410)

    from django.apps import apps
    if module_code == "MODULE_2":
        submission_model = apps.get_model("surveys", "Submission")
    else:
        submission_model = apps.get_model("surveys", f"Module{module_number}Submission")

    submission = get_object_or_404(submission_model, student=edit_req.student, session=edit_req.session)

    session_key = "last_submission_id" if module_number == 2 else f"last_module{module_number}_submission_id"
    request.session[session_key] = submission.pk
    request.session["active_edit_request_id"] = edit_req.pk

    return redirect(f"surveys:module_{module_number}")


@never_cache
@login_required
@staff_member_required
def dashboard_edit_requests(request: HttpRequest) -> HttpResponse:
    # Auto-expire approved requests that have passed their expiration time
    EditRequest.objects.filter(
        status=EditRequest.STATUS_APPROVED,
        expires_at__lt=timezone.now()
    ).update(status=EditRequest.STATUS_EXPIRED, one_time_token=None)

    requests = EditRequest.objects.select_related("student", "session", "session__module").all()

    from django.urls import reverse
    req_data = []
    for r in requests:
        link = ""
        if r.status == EditRequest.STATUS_APPROVED and r.one_time_token:
            try:
                mod_num = int(r.module_code.split("_")[1])
            except (IndexError, ValueError):
                mod_num = 2
            link = request.build_absolute_uri(
                reverse("surveys:activate_edit_request", kwargs={"module_number": mod_num, "token": r.one_time_token})
            )
        req_data.append({
            "request": r,
            "link": link
        })

    return render(request, "surveys/dashboard_edit_requests.html", {
        "edit_requests_data": req_data,
    })


@never_cache
@login_required
@staff_member_required
@require_POST
def approve_edit_request(request: HttpRequest, pk: int) -> HttpResponse:
    import secrets
    edit_req = get_object_or_404(EditRequest, pk=pk)
    if edit_req.status == EditRequest.STATUS_PENDING:
        edit_req.status = EditRequest.STATUS_APPROVED
        edit_req.one_time_token = secrets.token_urlsafe(32)
        edit_req.expires_at = timezone.now() + timedelta(minutes=15)
        edit_req.save()
        messages.success(request, f"La demande de modification pour {edit_req.student.full_name} a été approuvée.")
    return redirect("surveys:dashboard_edit_requests")


@never_cache
@login_required
@staff_member_required
@require_POST
def reject_edit_request(request: HttpRequest, pk: int) -> HttpResponse:
    edit_req = get_object_or_404(EditRequest, pk=pk)
    if edit_req.status == EditRequest.STATUS_PENDING:
        edit_req.status = EditRequest.STATUS_REJECTED
        edit_req.save()
        messages.success(request, f"La demande de modification pour {edit_req.student.full_name} a été rejetée.")
    return redirect("surveys:dashboard_edit_requests")


@never_cache
@login_required
@staff_member_required
@require_POST
def revoke_edit_request(request: HttpRequest, pk: int) -> HttpResponse:
    edit_req = get_object_or_404(EditRequest, pk=pk)
    if edit_req.status == EditRequest.STATUS_APPROVED:
        edit_req.status = EditRequest.STATUS_CANCELLED
        edit_req.one_time_token = None
        edit_req.save()
        messages.success(request, f"Le lien de modification pour {edit_req.student.full_name} a été révoqué.")
    return redirect("surveys:dashboard_edit_requests")
