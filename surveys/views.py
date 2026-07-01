import csv
import json
import mimetypes
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ChapterForm,
    LearningResourceForm,
    Module2SubmissionForm,
    Module3SubmissionForm,
    Module4SubmissionForm,
    Module5SubmissionForm,
    Module6SubmissionForm,
    Module7SubmissionForm,
    Module8SubmissionForm,
    SubjectForm,
)
from .models import (
    Chapter,
    FormPresence,
    LearningResource,
    Module3Submission,
    Module4Submission,
    Module5Submission,
    Module6Submission,
    Module7Submission,
    Module8Submission,
    Student,
    Subject,
    Submission,
    TrainingModule,
    TrainingSession,
)


MODULE_2_SUMMARY = (
    "Internet est un grand réseau qui relie des ordinateurs, des téléphones, "
    "des serveurs et des sites web dans le monde. Il peut aider à apprendre, "
    "faire des recherches, communiquer et préparer son avenir. Mais il faut "
    "savoir chercher correctement et rester prudent."
)


def sanitize_csv_cell(value):
    if value is None:
        return ""
    text = str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _mark_presence_submitted(request, module_code, session):
    client_id = request.POST.get("taf_client_id", "").strip()
    if client_id:
        FormPresence.objects.filter(
            client_id=client_id,
            module_code=module_code,
            training_session=session,
            status=FormPresence.STATUS_ACTIVE,
        ).update(status=FormPresence.STATUS_SUBMITTED)


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/home.html")


def _published_resources_queryset():
    return LearningResource.objects.filter(is_published=True).select_related("subject", "chapter")


def _build_cockpit_context(request: HttpRequest) -> dict:
    from .network import get_network_access_context

    net_ctx = get_network_access_context(request)
    published_resources_count = _published_resources_queryset().count()
    total_resources_count = LearningResource.objects.count()
    total_submissions = (
        Submission.objects.count()
        + Module3Submission.objects.count()
        + Module4Submission.objects.count()
        + Module5Submission.objects.count()
        + Module6Submission.objects.count()
        + Module7Submission.objects.count()
        + Module8Submission.objects.count()
    )
    total_students = Student.objects.count()
    avg_score_m2 = Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m3 = Module3Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m4 = Module4Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m5 = Module5Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m6 = Module6Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m7 = Module7Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m8 = Module8Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score = (avg_score_m2 + avg_score_m3 + avg_score_m4 + avg_score_m5 + avg_score_m6 + avg_score_m7 + avg_score_m8) / 7
    modules = TrainingModule.objects.all().order_by("code")
    module_list = []
    modules_open = 0
    for mod in modules:
        active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
        accepting = active_session.accepting_responses if active_session else False
        if accepting:
            modules_open += 1
        module_list.append({
            "module": mod,
            "has_active_session": active_session is not None,
            "accepting_responses": accepting,
            "active_session_id": active_session.pk if active_session else None,
        })

    student_access_url = ""
    if net_ctx.get("recommended_lan_host"):
        student_access_url = net_ctx.get("student_form_url", "")

    return {
        "total_submissions": total_submissions,
        "total_students": total_students,
        "average_score": avg_score,
        "module_list": module_list,
        "modules_open": modules_open,
        "network": net_ctx,
        "student_access_url": student_access_url,
        "student_access_ready": bool(student_access_url),
        "projection_url": "/dashboard/projection/",
        "has_lan_host": bool(net_ctx.get("configured_host")),
        "published_resources_count": published_resources_count,
        "total_resources_count": total_resources_count,
    }


def student_modules(request: HttpRequest) -> HttpResponse:
    from django.urls import reverse
    URL_MAP = {
        "MODULE_2": "surveys:student_module_2_detail",
        "MODULE_3": "surveys:student_module_3_detail",
        "MODULE_4": "surveys:student_module_4_detail",
        "MODULE_5": "surveys:student_module_5_detail",
        "MODULE_6": "surveys:student_module_6_detail",
        "MODULE_7": "surveys:student_module_7_detail",
        "MODULE_8": "surveys:student_module_8_detail",
    }
    modules = TrainingModule.objects.all().order_by("code")
    module_data = []
    for mod in modules:
        active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
        detail_url = reverse(URL_MAP[mod.code])
        module_data.append({
            "module": mod,
            "has_active_session": active_session is not None,
            "active_session": active_session,
            "detail_url": detail_url,
        })
    return render(request, "surveys/student_modules.html", {"module_data": module_data})


def student_module_detail(request: HttpRequest, module_code: str) -> HttpResponse:
    mod = get_object_or_404(TrainingModule, code=module_code)
    active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
    accepting = active_session.accepting_responses if active_session else False

    summary_map = {
        "MODULE_2": MODULE_2_SUMMARY,
        "MODULE_3": MODULE_3_SUMMARY,
        "MODULE_4": MODULE_4_SUMMARY,
        "MODULE_5": MODULE_5_SUMMARY,
        "MODULE_6": MODULE_6_SUMMARY,
        "MODULE_7": MODULE_7_SUMMARY,
        "MODULE_8": MODULE_8_SUMMARY,
    }
    summary = summary_map.get(module_code, "")

    return render(request, "surveys/student_module_detail.html", {
        "module": mod,
        "active_session": active_session,
        "has_active_session": active_session is not None,
        "accepting_responses": accepting,
        "summary": summary,
    })


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
    if selected_subject:
        resources = resources.filter(subject__slug=selected_subject)
    if selected_level:
        resources = resources.filter(subject__class_level=selected_level)
    if selected_module.isdigit():
        resources = resources.filter(module_number=int(selected_module))
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
        },
    )


def support_detail(request: HttpRequest, slug: str) -> HttpResponse:
    resource = get_object_or_404(_published_resources_queryset(), slug=slug)
    return render(request, "surveys/support_detail.html", {"resource": resource})


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
                    "module_2_summary": MODULE_2_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module2SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro. Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro. Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_2", session)
                    return redirect("surveys:module_2_success", submission_id=submission.pk)
    else:
        form = Module2SubmissionForm()

    return render(
        request,
        "surveys/module_2_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_2_summary": MODULE_2_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_2_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_submission_id") != submission_id:
        return redirect("surveys:module_2")
    submission = get_object_or_404(Submission.objects.select_related("session", "student"), pk=submission_id)
    return render(request, "surveys/module_2_success.html", {"submission": submission})


@login_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/dashboard_home.html", _build_cockpit_context(request))


@login_required
def dashboard_projection(request: HttpRequest) -> HttpResponse:
    return render(request, "surveys/dashboard_projection.html", _build_cockpit_context(request))


@login_required
def dashboard_supports(request: HttpRequest) -> HttpResponse:
    resources = LearningResource.objects.select_related("subject", "chapter").order_by("-updated_at", "title")
    context = {
        "resources": resources,
        "published_count": resources.filter(is_published=True).count(),
        "draft_count": resources.filter(is_published=False).count(),
    }
    return render(request, "surveys/dashboard_supports.html", context)


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


def _subject_dashboard_queryset():
    return Subject.objects.prefetch_related("chapters").order_by("sort_order", "name")


@login_required
def dashboard_subjects(request: HttpRequest) -> HttpResponse:
    subjects = _subject_dashboard_queryset()
    chapters = Chapter.objects.select_related("subject").order_by("subject__sort_order", "sort_order", "title")
    context = {
        "subjects": subjects,
        "active_subject_count": subjects.filter(is_active=True).count(),
        "inactive_subject_count": subjects.filter(is_active=False).count(),
        "active_chapter_count": chapters.filter(is_active=True).count(),
        "inactive_chapter_count": chapters.filter(is_active=False).count(),
    }
    return render(request, "surveys/dashboard_subjects.html", context)


@login_required
def dashboard_subject_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f"La matière « {subject.name} » a été enregistrée.")
            return redirect("surveys:dashboard_subjects")
    else:
        form = SubjectForm(initial={"is_active": True})
    return render(
        request,
        "surveys/dashboard_subject_form.html",
        {"form": form, "page_title": "Créer une matière", "submit_label": "Enregistrer la matière"},
    )


@login_required
def dashboard_subject_edit(request: HttpRequest, subject_id: int) -> HttpResponse:
    subject = get_object_or_404(Subject, pk=subject_id)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f"La matière « {subject.name} » a été mise à jour.")
            return redirect("surveys:dashboard_subjects")
    else:
        form = SubjectForm(instance=subject)
    return render(
        request,
        "surveys/dashboard_subject_form.html",
        {
            "form": form,
            "subject": subject,
            "page_title": f"Modifier la matière : {subject.name}",
            "submit_label": "Enregistrer les changements",
        },
    )


@login_required
@require_POST
def dashboard_subject_toggle(request: HttpRequest, subject_id: int) -> HttpResponse:
    subject = get_object_or_404(Subject, pk=subject_id)
    subject.is_active = not subject.is_active
    subject.save(update_fields=["is_active"])
    state = "activée" if subject.is_active else "désactivée"
    messages.success(request, f"La matière « {subject.name} » a été {state}.")
    return redirect("surveys:dashboard_subjects")


@login_required
def dashboard_chapter_create(request: HttpRequest) -> HttpResponse:
    initial = {"is_active": True}
    subject_id = request.GET.get("subject")
    if subject_id and subject_id.isdigit():
        initial["subject"] = int(subject_id)
    if request.method == "POST":
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save()
            messages.success(request, f"Le chapitre « {chapter.title} » a été enregistré.")
            return redirect("surveys:dashboard_subjects")
    else:
        form = ChapterForm(initial=initial)
    return render(
        request,
        "surveys/dashboard_chapter_form.html",
        {"form": form, "page_title": "Créer un chapitre", "submit_label": "Enregistrer le chapitre"},
    )


@login_required
def dashboard_chapter_edit(request: HttpRequest, chapter_id: int) -> HttpResponse:
    chapter = get_object_or_404(Chapter.objects.select_related("subject"), pk=chapter_id)
    if request.method == "POST":
        form = ChapterForm(request.POST, instance=chapter)
        if form.is_valid():
            chapter = form.save()
            messages.success(request, f"Le chapitre « {chapter.title} » a été mis à jour.")
            return redirect("surveys:dashboard_subjects")
    else:
        form = ChapterForm(instance=chapter)
    return render(
        request,
        "surveys/dashboard_chapter_form.html",
        {
            "form": form,
            "chapter": chapter,
            "page_title": f"Modifier le chapitre : {chapter.title}",
            "submit_label": "Enregistrer les changements",
        },
    )


@login_required
@require_POST
def dashboard_chapter_toggle(request: HttpRequest, chapter_id: int) -> HttpResponse:
    chapter = get_object_or_404(Chapter.objects.select_related("subject"), pk=chapter_id)
    chapter.is_active = not chapter.is_active
    chapter.save(update_fields=["is_active"])
    state = "activé" if chapter.is_active else "désactivé"
    messages.success(request, f"Le chapitre « {chapter.title} » a été {state}.")
    return redirect("surveys:dashboard_subjects")


MODULE_5_SUMMARY = (
    "L'email sert à communiquer sérieusement avec un professeur, une école, "
    "une université ou une organisation. Un bon email contient : un destinataire, "
    "un objet clair, une salutation, un message court, une formule de politesse, "
    "une signature et parfois une pièce jointe. Règle simple : clair, poli, complet, relu."
)

MODULE_6_SUMMARY = (
    "Une ressource éducative en ligne est un contenu qui aide à apprendre : cours, vidéo, "
    "exercice, PDF, dictionnaire, schéma ou quiz. Une bonne ressource est utile, claire, "
    "adaptée à ton niveau et reliée à une matière scolaire. Règle simple : chercher, choisir, tester, noter."
)

MODULE_7_SUMMARY = (
    "La sécurité en ligne, ce sont les bons gestes pour protéger tes comptes, tes fichiers, "
    "tes photos et tes informations. Les risques les plus courants sont : mot de passe volé, "
    "lien suspect, faux message, arnaque, cyberharcèlement et partage trop rapide. "
    "Règle simple : protéger, vérifier, demander de l'aide."
)

MODULE_8_SUMMARY = (
    "Le Module 8 est le module de synthèse. Tu vas utiliser tout ce que tu as appris "
    "depuis le début : chercher une information, vérifier une source, choisir une ressource, "
    "et produire un travail personnel. Tu réaliseras une mini-fiche d'apprentissage sur un "
    "sujet de ton choix, en suivant une démarche complète : besoin → recherche → sélection "
    "→ vérification → production."
)


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
                    "module_5_summary": MODULE_5_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module5SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Module5Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro pendant cette séance. "
                    "Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Module5Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro pendant cette séance. "
                        "Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_module5_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_5", session)
                    return redirect("surveys:module_5_success", submission_id=submission.pk)
    else:
        form = Module5SubmissionForm()

    return render(
        request,
        "surveys/module_5_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_5_summary": MODULE_5_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_5_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_module5_submission_id") != submission_id:
        return redirect("surveys:module_5")
    submission = get_object_or_404(
        Module5Submission.objects.select_related("session", "student"), pk=submission_id
    )
    return render(request, "surveys/module_5_success.html", {"submission": submission})


@login_required
def dashboard_module_5(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module5Submission.objects.select_related("student", "session", "session__module")
        .filter(session__module__code="MODULE_5")
        .order_by("-created_at")
    )
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
    }
    return render(request, "surveys/dashboard_module_5.html", context)


@login_required
def export_module_5_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module5Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_5")
        .order_by("created_at")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-5.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "school_id_number",
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
                submission.school_id_number_snapshot,
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
                    "module_6_summary": MODULE_6_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module6SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Module6Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro pendant cette séance. "
                    "Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Module6Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro pendant cette séance. "
                        "Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_module6_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_6", session)
                    return redirect("surveys:module_6_success", submission_id=submission.pk)
    else:
        form = Module6SubmissionForm()

    return render(
        request,
        "surveys/module_6_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_6_summary": MODULE_6_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_6_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_module6_submission_id") != submission_id:
        return redirect("surveys:module_6")
    submission = get_object_or_404(
        Module6Submission.objects.select_related("session", "student"), pk=submission_id
    )
    return render(request, "surveys/module_6_success.html", {"submission": submission})


@login_required
def dashboard_module_6(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module6Submission.objects.select_related("student", "session", "session__module")
        .filter(session__module__code="MODULE_6")
        .order_by("-created_at")
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
    return render(request, "surveys/dashboard_module_6.html", context)


@login_required
def export_module_6_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module6Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_6")
        .order_by("created_at")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-6.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "school_id_number",
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
                submission.school_id_number_snapshot,
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


@login_required
def dashboard_module_2(request: HttpRequest) -> HttpResponse:
    submissions = (
        Submission.objects.select_related("student", "session", "session__module")
        .filter(session__module__code="MODULE_2")
        .order_by("-created_at")
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
    return render(request, "surveys/dashboard_module_2.html", context)


@login_required
def export_module_2_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_2")
        .order_by("created_at")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-2.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "school_id_number",
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
                submission.school_id_number_snapshot,
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


MODULE_3_SUMMARY = (
    "Une recherche efficace commence par de bons mots-clés. Il ne faut pas écrire "
    "toute une longue phrase. Il faut choisir les mots importants, lire les premiers "
    "résultats, comparer plusieurs liens, puis améliorer la recherche si nécessaire."
)


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
                    "module_3_summary": MODULE_3_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module3SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Module3Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro pendant cette séance. "
                    "Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Module3Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro pendant cette séance. "
                        "Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_module3_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_3", session)
                    return redirect("surveys:module_3_success", submission_id=submission.pk)
    else:
        form = Module3SubmissionForm()

    return render(
        request,
        "surveys/module_3_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_3_summary": MODULE_3_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_3_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_module3_submission_id") != submission_id:
        return redirect("surveys:module_3")
    submission = get_object_or_404(
        Module3Submission.objects.select_related("session", "student"), pk=submission_id
    )
    return render(request, "surveys/module_3_success.html", {"submission": submission})


@login_required
def dashboard_module_3(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module3Submission.objects.select_related("student", "session", "session__module")
        .filter(session__module__code="MODULE_3")
        .order_by("-created_at")
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
    return render(request, "surveys/dashboard_module_3.html", context)


@login_required
def export_module_3_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module3Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_3")
        .order_by("created_at")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-3.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "school_id_number",
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
                submission.school_id_number_snapshot,
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


MODULE_4_SUMMARY = (
    "Sur Internet, toutes les informations ne sont pas toujours vraies. "
    "Une source fiable donne des informations claires, vérifiables et sérieuses. "
    "Avant de croire ou partager une information, il faut regarder qui l'a publiée, "
    "quand elle a été publiée, quelles preuves sont données, et comparer avec "
    "d'autres sources."
)


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
                    "module_4_summary": MODULE_4_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module4SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Module4Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro pendant cette séance. "
                    "Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Module4Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro pendant cette séance. "
                        "Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_module4_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_4", session)
                    return redirect("surveys:module_4_success", submission_id=submission.pk)
    else:
        form = Module4SubmissionForm()

    return render(
        request,
        "surveys/module_4_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_4_summary": MODULE_4_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_4_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_module4_submission_id") != submission_id:
        return redirect("surveys:module_4")
    submission = get_object_or_404(
        Module4Submission.objects.select_related("session", "student"), pk=submission_id
    )
    return render(request, "surveys/module_4_success.html", {"submission": submission})


@login_required
def dashboard_module_4(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module4Submission.objects.select_related("student", "session", "session__module")
        .filter(session__module__code="MODULE_4")
        .order_by("-created_at")
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
    return render(request, "surveys/dashboard_module_4.html", context)


@login_required
def export_module_4_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module4Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_4")
        .order_by("created_at")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-4.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "school_id_number",
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
                submission.school_id_number_snapshot,
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
                    "module_7_summary": MODULE_7_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module7SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Module7Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro pendant cette séance. "
                    "Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Module7Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro pendant cette séance. "
                        "Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_module7_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_7", session)
                    return redirect("surveys:module_7_success", submission_id=submission.pk)
    else:
        form = Module7SubmissionForm()

    return render(
        request,
        "surveys/module_7_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_7_summary": MODULE_7_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_7_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_module7_submission_id") != submission_id:
        return redirect("surveys:module_7")
    submission = get_object_or_404(
        Module7Submission.objects.select_related("session", "student"), pk=submission_id
    )
    return render(request, "surveys/module_7_success.html", {"submission": submission})


@login_required
def dashboard_module_7(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module7Submission.objects.select_related("student", "session", "session__module")
        .filter(session__module__code="MODULE_7")
        .order_by("-created_at")
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
    return render(request, "surveys/dashboard_module_7.html", context)


@login_required
def export_module_7_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module7Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_7")
        .order_by("created_at")
    )
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="module-7.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "timestamp",
            "session_code",
            "school_id_number",
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
                submission.school_id_number_snapshot,
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
                    "module_8_summary": MODULE_8_SUMMARY,
                    "accepting_responses": False,
                    "closed_error": "Les réponses sont fermées pour ce module. Tu peux consulter les questions, mais tu ne peux pas envoyer de réponse.",
                },
                status=403,
            )
        form = Module8SubmissionForm(request.POST)
        if form.is_valid():
            school_id_number = form.cleaned_data["school_id_number"]
            duplicate_exists = Module8Submission.objects.filter(
                session=session,
                school_id_number_snapshot=school_id_number,
            ).exists()
            if duplicate_exists:
                form.add_error(
                    "school_id_number",
                    "Une réponse existe déjà pour ce numéro pendant cette séance. "
                    "Demande au formateur si tu dois modifier ta réponse.",
                )
            else:
                student = Student.objects.create(
                    school_id_number=school_id_number,
                    full_name=form.cleaned_data["full_name"],
                    class_level=form.cleaned_data["class_level"],
                    group_name=form.cleaned_data["group_name"],
                )
                submission_data = {
                    key: value
                    for key, value in form.cleaned_data.items()
                    if key not in {"school_id_number", "full_name", "class_level", "group_name"}
                }
                try:
                    submission = Module8Submission.objects.create(
                        student=student,
                        session=session,
                        school_id_number_snapshot=school_id_number,
                        **submission_data,
                    )
                except IntegrityError:
                    student.delete()
                    form.add_error(
                        "school_id_number",
                        "Une réponse existe déjà pour ce numéro pendant cette séance. "
                        "Demande au formateur si tu dois modifier ta réponse.",
                    )
                else:
                    request.session["last_module8_submission_id"] = submission.pk
                    _mark_presence_submitted(request, "MODULE_8", session)
                    return redirect("surveys:module_8_success", submission_id=submission.pk)
    else:
        form = Module8SubmissionForm()

    return render(
        request,
        "surveys/module_8_form.html",
        {
            "form": form,
            "session": session,
            "module": session.module,
            "module_8_summary": MODULE_8_SUMMARY,
            "accepting_responses": accepting,
        },
    )


def module_8_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_module8_submission_id") != submission_id:
        return redirect("surveys:module_8")
    submission = get_object_or_404(
        Module8Submission.objects.select_related("session", "student"), pk=submission_id
    )
    return render(request, "surveys/module_8_success.html", {"submission": submission})


@login_required
def dashboard_module_8(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module8Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_8")
        .order_by("-created_at")
    )
    todo_fields = [
        "todo_chose_subject", "todo_written_question", "todo_transformed_keywords",
        "todo_found_first_source", "todo_found_second_source", "todo_checked_source_quality",
        "todo_chose_most_useful", "todo_noted_three_ideas", "todo_prepared_synthesis",
        "todo_presented_explained",
    ]
    total_count = submissions.count()
    todo_counts = {}
    for field in todo_fields:
        completed = submissions.filter(**{field: True}).count()
        todo_counts[field] = completed
    avg_score = submissions.aggregate(avg=Avg("computed_score"))["avg"] or 0
    from django.urls import reverse
    breadcrumbs = [("Modules", "surveys:dashboard_modules"), "Module 8"]
    return render(
        request,
        "surveys/dashboard_module_8.html",
        {
            "submissions": submissions,
            "total_count": total_count,
            "todo_counts": todo_counts,
            "todo_fields": todo_fields,
            "avg_score": round(avg_score, 1),
            "breadcrumbs": breadcrumbs,
        },
    )


@login_required
def export_module_8_csv(request: HttpRequest) -> HttpResponse:
    submissions = (
        Module8Submission.objects.select_related("student", "session")
        .filter(session__module__code="MODULE_8")
        .order_by("-created_at")
    )
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
            submission.school_id_number_snapshot,
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


@login_required
def network_access_dashboard(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context

    ctx = get_network_access_context(request)
    return render(request, "surveys/dashboard_network.html", ctx)


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
    school_id_number = data.get("school_id_number", "").strip() or None
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
            "school_id_number": school_id_number,
            "class_level": class_level,
            "last_seen_at": now,
        },
    )
    return JsonResponse({"ok": True})


@login_required
def dashboard_backup(request: HttpRequest) -> HttpResponse:
    from django.conf import settings

    db_engine = "postgresql" if settings.DB_HOST else "sqlite"
    context = {
        "db_engine": db_engine,
        "db_host": getattr(settings, "DB_HOST", ""),
        "db_port": getattr(settings, "DATABASES", {}).get("default", {}).get("PORT", "5432"),
        "db_name": getattr(settings, "DATABASES", {}).get("default", {}).get("NAME", "taf_local_forms"),
        "db_path": getattr(settings, "DATABASE_PATH", ""),
        "backup_command": "bash scripts/dev/taf-db-backup",
        "total_submissions": (
            Submission.objects.count()
            + Module3Submission.objects.count()
            + Module4Submission.objects.count()
            + Module5Submission.objects.count()
            + Module6Submission.objects.count()
            + Module7Submission.objects.count()
            + Module8Submission.objects.count()
        ),
    }
    return render(request, "surveys/dashboard_backup.html", context)


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


@staff_member_required
@login_required
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
    }
    return render(request, "surveys/dashboard_settings.html", context)


@staff_member_required
@login_required
@require_POST
def dashboard_use_current_address(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context, _is_private_ip, _parse_host_port
    from .settings_config import apply_lan_settings

    net_ctx = get_network_access_context(request)
    if not net_ctx["current_request_is_lan"]:
        messages.error(request, "L'adresse actuelle n'est pas une IP LAN valide.")
        return redirect("surveys:dashboard_settings")

    host = net_ctx["current_request_host"]
    port = net_ctx["current_port"] or net_ctx.get("configured_port") or "8010"

    ok, msg = apply_lan_settings(host, port)
    if ok:
        messages.success(request, msg)
    else:
        messages.error(request, msg)
    return redirect("surveys:dashboard_settings")


@staff_member_required
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


@staff_member_required
@login_required
def network_control(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context

    net_ctx = get_network_access_context(request)
    current_host = net_ctx.get("current_request_host", "")
    is_localhost = current_host in ("localhost", "127.0.0.1", "[::1]")
    helper_port = 8019
    helper_url = f"http://127.0.0.1:{helper_port}"

    context = {
        "net_ctx": net_ctx,
        "is_localhost": is_localhost,
        "helper_url": helper_url,
        "helper_port": helper_port,
        "lan_port": 8011,
        "docker_port": 8010,
    }
    return render(request, "surveys/dashboard_network_control.html", context)
