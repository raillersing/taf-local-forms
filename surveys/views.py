import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import Module2SubmissionForm, Module3SubmissionForm, Module4SubmissionForm
from .models import (
    Module3Submission,
    Module4Submission,
    Student,
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


def home(request: HttpRequest) -> HttpResponse:
    modules = TrainingModule.objects.all().order_by("code")
    module_data = []
    for mod in modules:
        active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
        module_data.append({
            "module": mod,
            "has_active_session": active_session is not None,
        })
    return render(request, "surveys/home.html", {"module_data": module_data})


def module_2_form(request: HttpRequest) -> HttpResponse:
    session = (
        TrainingSession.objects.select_related("module")
        .filter(module__code="MODULE_2", is_active=True)
        .order_by("-date", "session_code")
        .first()
    )

    if session is None:
        return render(request, "surveys/module_2_unavailable.html", status=503)

    if request.method == "POST":
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
        },
    )


def module_2_success(request: HttpRequest, submission_id: int) -> HttpResponse:
    if request.session.get("last_submission_id") != submission_id:
        return redirect("surveys:module_2")
    submission = get_object_or_404(Submission.objects.select_related("session", "student"), pk=submission_id)
    return render(request, "surveys/module_2_success.html", {"submission": submission})


@login_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context

    net_ctx = get_network_access_context(request)
    total_submissions = (
        Submission.objects.count()
        + Module3Submission.objects.count()
        + Module4Submission.objects.count()
    )
    total_students = Student.objects.count()
    avg_score_m2 = Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m3 = Module3Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score_m4 = Module4Submission.objects.aggregate(avg=Avg("computed_score"))["avg"] or 0
    avg_score = (avg_score_m2 + avg_score_m3 + avg_score_m4) / 3
    modules = TrainingModule.objects.all().order_by("code")
    module_list = []
    for mod in modules:
        active_session = TrainingSession.objects.filter(module=mod, is_active=True).first()
        module_list.append({
            "module": mod,
            "has_active_session": active_session is not None,
        })
    context = {
        "total_submissions": total_submissions,
        "total_students": total_students,
        "average_score": avg_score,
        "module_list": module_list,
        "network": net_ctx,
    }
    return render(request, "surveys/dashboard_home.html", context)


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

    if request.method == "POST":
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

    if request.method == "POST":
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


@login_required
def network_access_dashboard(request: HttpRequest) -> HttpResponse:
    from .network import get_network_access_context

    ctx = get_network_access_context(request)
    return render(request, "surveys/dashboard_network.html", ctx)
