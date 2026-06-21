import os
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Student, Submission, TrainingModule, TrainingSession


class SeedModule2CommandTests(TestCase):
    def test_seed_module2_creates_expected_module_and_active_session(self):
        call_command("seed_module2")

        module = TrainingModule.objects.get(code="MODULE_2")
        session = TrainingSession.objects.get(session_code="M2-ANDO-001")

        self.assertEqual(module.title, "Module 2 - Comprendre Internet")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module2_is_idempotent(self):
        call_command("seed_module2")
        call_command("seed_module2")

        self.assertEqual(TrainingModule.objects.filter(code="MODULE_2").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M2-ANDO-001").count(), 1)

    def test_seed_module2_does_not_overwrite_existing_session_details(self):
        call_command("seed_module2")
        session = TrainingSession.objects.get(session_code="M2-ANDO-001")
        session.location = "Autre lieu"
        session.trainer_name = "Autre formateur"
        session.is_active = False
        session.save()

        call_command("seed_module2")
        session.refresh_from_db()

        self.assertEqual(session.location, "Autre lieu")
        self.assertEqual(session.trainer_name, "Autre formateur")
        self.assertFalse(session.is_active)


class SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_2",
            title="Module 2 - Comprendre Internet",
            description="Comprendre Internet comme outil d'apprentissage.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M2-ANDO-001",
            is_active=True,
        )
        self.student = Student.objects.create(
            school_id_number="01",
            full_name="Rakoto Aina",
            class_level=Student.CLASS_LEVEL_SECONDE,
            group_name="Salle A",
        )
        self.other_student = Student.objects.create(
            school_id_number="01",
            full_name="Rabe Hery",
            class_level=Student.CLASS_LEVEL_PREMIERE,
            group_name="Salle B",
        )

    def make_submission(self, student):
        return Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_internet_explained="un_peu",
            auto_eval_learning_usage="parfois",
            auto_eval_open_browser="oui",
            todo_opened_browser=True,
            todo_typed_simple_search=True,
            todo_used_keywords=True,
            todo_opened_result=True,
            todo_compared_results=True,
            todo_found_school_info=True,
            todo_asked_for_help=False,
            todo_noted_learning=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4_selected=[
                Submission.QUIZ_Q4_OPTION_EXPLANATION,
                Submission.QUIZ_Q4_OPTION_VIDEO,
                Submission.QUIZ_Q4_OPTION_DOCUMENT,
                Submission.QUIZ_Q4_OPTION_WORD,
            ],
            quiz_q5="cours_equation_seconde_exemple",
            practical_search_text="cours equation seconde exemple",
            practical_site_text="www.exemple.mg",
            practical_subject="mathematiques",
            feedback_understood_today="Internet peut aider pour reviser les cours.",
            feedback_still_difficult="",
            feedback_confidence="oui",
        )

    def test_duplicate_school_id_snapshot_is_blocked_for_same_session(self):
        self.make_submission(self.student)

        with self.assertRaises(IntegrityError):
            self.make_submission(self.other_student)

    def test_score_is_computed_on_save(self):
        submission = self.make_submission(self.student)

        self.assertEqual(submission.computed_score, 5)


class Module2FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_2",
            title="Module 2 - Comprendre Internet",
            description="Comprendre Internet comme outil d'apprentissage.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M2-ANDO-001",
            is_active=True,
        )

    def valid_payload(self):
        return {
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_internet_explained": "un_peu",
            "auto_eval_learning_usage": "parfois",
            "auto_eval_open_browser": "oui",
            "todo_opened_browser": "on",
            "todo_typed_simple_search": "on",
            "todo_used_keywords": "on",
            "todo_opened_result": "on",
            "todo_compared_results": "on",
            "todo_found_school_info": "on",
            "todo_noted_learning": "on",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4_selected": [
                Submission.QUIZ_Q4_OPTION_EXPLANATION,
                Submission.QUIZ_Q4_OPTION_VIDEO,
                Submission.QUIZ_Q4_OPTION_DOCUMENT,
                Submission.QUIZ_Q4_OPTION_WORD,
            ],
            "quiz_q5": "cours_equation_seconde_exemple",
            "practical_search_text": "cours equation seconde exemple",
            "practical_site_text": "www.exemple.mg",
            "practical_subject": "mathematiques",
            "feedback_understood_today": "J'ai compris qu'Internet aide a apprendre.",
            "feedback_still_difficult": "",
            "feedback_confidence": "oui",
        }

    def test_module_2_form_get(self):
        response = self.client.get(reverse("surveys:module_2"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 2 - Comprendre Internet")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_2"), data=self.valid_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Submission.objects.count(), 1)
        submission = Submission.objects.get()
        self.assertEqual(submission.school_id_number_snapshot, "01")
        self.assertEqual(submission.computed_score, 5)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"

        response = self.client.post(reverse("surveys:module_2"), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre exactement 2 chiffres")
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Submission.objects.count(), 0)

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_2"), data=self.valid_payload())
        payload = self.valid_payload()
        payload["full_name"] = "Autre eleve"

        response = self.client.post(reverse("surveys:module_2"), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Une réponse existe déjà pour ce numéro")
        self.assertEqual(Submission.objects.count(), 1)

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_2"), data=self.valid_payload())
        submission = Submission.objects.get()
        other_client = self.client_class()

        response = other_client.get(reverse("surveys:module_2_success", args=[submission.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_2"))

    def test_module_2_form_returns_503_when_no_active_session_exists(self):
        self.session.is_active = False
        self.session.save()

        response = self.client.get(reverse("surveys:module_2"))

        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Le formulaire n'est pas disponible maintenant.", status_code=503)

    def test_home_page_returns_200(self):
        response = self.client.get(reverse("surveys:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenue")
        self.assertContains(response, "TAfHSSiM")

    def test_home_page_shows_module_2_when_active(self):
        response = self.client.get(reverse("surveys:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 2 - Comprendre Internet")
        self.assertContains(response, "Disponible")
        self.assertContains(response, "Répondre au questionnaire")

    def test_home_page_shows_module_2_unavailable_when_no_active_session(self):
        self.session.is_active = False
        self.session.save()

        response = self.client.get(reverse("surveys:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 2 - Comprendre Internet")
        self.assertContains(response, "Indisponible")
        self.assertContains(response, "Aucune session active")


class DashboardAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="formateur",
            password="motdepasse-solide-123",
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_2"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_2_csv"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_cockpit_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_cockpit_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cockpit formateur")
        self.assertContains(response, "Dashboard Module 2")
        self.assertContains(response, "Accès réseau")
        self.assertContains(response, "Admin Django")
        self.assertContains(response, "Export CSV")


class DashboardCsvTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="formateur",
            password="motdepasse-solide-123",
        )
        self.module = TrainingModule.objects.create(
            code="MODULE_2",
            title="Module 2 - Comprendre Internet",
            description="Comprendre Internet comme outil d'apprentissage.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M2-ANDO-001",
            is_active=True,
        )
        self.student = Student.objects.create(
            school_id_number="01",
            full_name="Rakoto Aina",
            class_level=Student.CLASS_LEVEL_SECONDE,
            group_name="Salle A",
        )
        Submission.objects.create(
            student=self.student,
            session=self.session,
            school_id_number_snapshot="01",
            auto_eval_internet_explained="un_peu",
            auto_eval_learning_usage="parfois",
            auto_eval_open_browser="oui",
            todo_opened_browser=True,
            todo_typed_simple_search=True,
            todo_used_keywords=True,
            todo_opened_result=True,
            todo_compared_results=False,
            todo_found_school_info=True,
            todo_asked_for_help=False,
            todo_noted_learning=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4_selected=[
                Submission.QUIZ_Q4_OPTION_EXPLANATION,
                Submission.QUIZ_Q4_OPTION_VIDEO,
                Submission.QUIZ_Q4_OPTION_DOCUMENT,
                Submission.QUIZ_Q4_OPTION_WORD,
            ],
            quiz_q5="cours_equation_seconde_exemple",
            practical_search_text="cours equation seconde exemple",
            practical_site_text="www.exemple.mg",
            practical_subject="mathematiques",
            feedback_understood_today="Internet aide pour l'ecole.",
            feedback_still_difficult="",
            feedback_confidence="oui",
        )

    def test_dashboard_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_module_2"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Score moyen")
        self.assertContains(response, "Rakoto Aina")

    def test_dashboard_filter_by_class_level_limits_results(self):
        other_student = Student.objects.create(
            school_id_number="02",
            full_name="Rasoanaivo Mira",
            class_level=Student.CLASS_LEVEL_PREMIERE,
            group_name="Salle B",
        )
        Submission.objects.create(
            student=other_student,
            session=self.session,
            school_id_number_snapshot="02",
            auto_eval_internet_explained="bien",
            auto_eval_learning_usage="souvent",
            auto_eval_open_browser="oui",
            todo_opened_browser=True,
            todo_typed_simple_search=True,
            todo_used_keywords=True,
            todo_opened_result=True,
            todo_compared_results=True,
            todo_found_school_info=True,
            todo_asked_for_help=False,
            todo_noted_learning=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4_selected=[
                Submission.QUIZ_Q4_OPTION_EXPLANATION,
                Submission.QUIZ_Q4_OPTION_VIDEO,
                Submission.QUIZ_Q4_OPTION_DOCUMENT,
                Submission.QUIZ_Q4_OPTION_WORD,
            ],
            quiz_q5="cours_equation_seconde_exemple",
            practical_search_text="cours histoire premiere",
            practical_site_text="www.exemple2.mg",
            practical_subject="histoire_geographie",
            feedback_understood_today="Internet aide à réviser.",
            feedback_still_difficult="",
            feedback_confidence="oui",
        )
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(
            reverse("surveys:dashboard_module_2"),
            {"class_level": Student.CLASS_LEVEL_SECONDE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rakoto Aina")
        self.assertNotContains(response, "Rasoanaivo Mira")

    def test_csv_export_contains_submission_data(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:export_module_2_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Rakoto Aina", response.content.decode())
        self.assertIn("school_id_number", response.content.decode())

    def test_csv_export_sanitizes_formula_like_cells(self):
        self.student.full_name = "=cmd"
        self.student.save()
        submission = Submission.objects.get()
        submission.practical_search_text = "+danger"
        submission.feedback_understood_today = "@risk"
        submission.feedback_still_difficult = "-test"
        submission.save()
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:export_module_2_csv"))
        content = response.content.decode()

        self.assertIn("'=cmd", content)
        self.assertIn("'+danger", content)
        self.assertIn("'@risk", content)
        self.assertIn("'-test", content)


class NetworkAccessDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="formateur",
            password="motdepasse-solide-123",
        )

    def test_network_page_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_network"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_network_page_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_network"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/module-2/")
        self.assertContains(response, "/dashboard/module-2/")
        self.assertContains(response, "/dashboard/export/module-2.csv")
        self.assertContains(response, "/admin/")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_warning_when_host_is_localhost(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(
            reverse("surveys:dashboard_network"),
            HTTP_HOST="127.0.0.1:8010",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "127.0.0.1")
        self.assertContains(response, "ne fonctionne que sur cet ordinateur")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_recommended_host_uses_env_var_when_set(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        with patch.dict(os.environ, {"TAF_LAN_HOST": "192.168.0.102"}, clear=False):
            response = self.client.get(reverse("surveys:dashboard_network"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "192.168.0.102")


class TrainingSessionConstraintTests(TestCase):
    def test_only_one_active_session_per_module_is_allowed(self):
        module = TrainingModule.objects.create(
            code="MODULE_2",
            title="Module 2 - Comprendre Internet",
            description="Comprendre Internet comme outil d'apprentissage.",
        )
        TrainingSession.objects.create(
            module=module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M2-ANDO-001",
            is_active=True,
        )

        with self.assertRaises(IntegrityError):
            TrainingSession.objects.create(
                module=module,
                date=date(2026, 6, 19),
                location="Lycee Andohalo Antananarivo",
                trainer_name="Formateur TAfHSSiM",
                session_code="M2-ANDO-002",
                is_active=True,
            )
