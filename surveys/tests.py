import os
from datetime import date
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch

import json

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Chapter, FormPresence, LearningResource, Module3Submission, Module4Submission, Module5Submission, Module6Submission, Module7Submission, Module8Submission, Student, Subject, Submission, TrainingModule, TrainingSession


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
        self.assertContains(response, "Je suis étudiant")
        self.assertContains(response, "Je suis formateur")
        self.assertContains(response, "À propos du projet")

    def test_home_page_shows_module_2_when_active(self):
        response = self.client.get(reverse("surveys:student_modules"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 2 - Comprendre Internet")
        self.assertContains(response, "Réponses ouvertes")
        self.assertContains(response, "Voir le module")

    def test_home_page_shows_module_2_unavailable_when_no_active_session(self):
        self.session.is_active = False
        self.session.save()

        response = self.client.get(reverse("surveys:student_modules"))

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
        self.assertContains(response, "Modules de formation")
        self.assertContains(response, "Accès réseau")
        self.assertContains(response, "Admin avancé")
        self.assertContains(response, "Guide dépannage réseau")
        self.assertContains(response, "Accès élèves")
        self.assertContains(response, "Mode projection")
        self.assertNotContains(response, "https://cdnjs.cloudflare.com")

    def test_projection_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_projection"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_projection_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_projection"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mode projection")
        self.assertContains(response, "Plein écran")
        self.assertContains(response, "Retour cockpit")
        self.assertNotContains(response, "https://cdnjs.cloudflare.com")

    @patch("surveys.network.get_network_access_context")
    def test_cockpit_handles_missing_lan_url(self, mock_network_context):
        mock_network_context.return_value = {
            "configured_host": "",
            "student_form_url": "http://localhost:8010/",
            "recommended_lan_host": "",
            "lan_host_source": "missing",
            "lan_host_stale": False,
        }
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disponible après configuration réseau")
        self.assertContains(response, "URL LAN non configurée")

    def test_projection_tools_do_not_appear_in_student_pages(self):
        response = self.client.get(reverse("surveys:student_modules"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Mode projection")
        self.assertNotContains(response, "/dashboard/projection/")


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


class SeedModule3CommandTests(TestCase):
    def test_seed_module3_creates_expected_module_and_active_session(self):
        call_command("seed_module3")

        module = TrainingModule.objects.get(code="MODULE_3")
        session = TrainingSession.objects.get(session_code="M3-ANDO-001")

        self.assertEqual(module.title, "Module 3 - Recherche efficace")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module3_is_idempotent(self):
        call_command("seed_module3")
        call_command("seed_module3")

        self.assertEqual(TrainingModule.objects.filter(code="MODULE_3").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M3-ANDO-001").count(), 1)

    def test_seed_module3_does_not_overwrite_existing_session_details(self):
        call_command("seed_module3")
        session = TrainingSession.objects.get(session_code="M3-ANDO-001")
        session.location = "Autre lieu"
        session.trainer_name = "Autre formateur"
        session.is_active = False
        session.save()

        call_command("seed_module3")
        session.refresh_from_db()

        self.assertEqual(session.location, "Autre lieu")
        self.assertEqual(session.trainer_name, "Autre formateur")
        self.assertFalse(session.is_active)


class Module3SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_3",
            title="Module 3 - Recherche efficace",
            description="Trouver rapidement des informations utiles.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M3-ANDO-001",
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
        return Module3Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_keywords="bien",
            auto_eval_improve="un_peu",
            auto_eval_compare="tres_bien",
            todo_chose_subject=True,
            todo_written_question=True,
            todo_keywords_from_question=True,
            todo_did_search=True,
            todo_read_titles=True,
            todo_opened_result=True,
            todo_compared_two_results=True,
            todo_improved_keywords=True,
            todo_found_useful_resource=True,
            todo_noted_learning=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4="faux",
            quiz_q5="cours_equation_seconde_exemple",
            quiz_q6="photosynthese_cours_lycee_pdf",
            quiz_q7_selected=list(Module3Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_starting_question="Comment resoudre une equation ?",
            practical_keywords_used="equation seconde exemple",
            practical_site_found="www.exemple.mg",
            practical_subject="mathematiques",
            practical_what_learned="Les equations se resolvent avec des regles simples.",
            feedback_understood_today="J'ai compris comment chercher sur Internet.",
            feedback_still_difficult="",
            feedback_confidence_search="oui",
        )

    def test_duplicate_school_id_snapshot_is_blocked_for_same_session(self):
        self.make_submission(self.student)

        with self.assertRaises(IntegrityError):
            self.make_submission(self.other_student)

    def test_score_is_computed_on_save(self):
        submission = self.make_submission(self.student)

        self.assertEqual(submission.computed_score, 7)


class Module3FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_3",
            title="Module 3 - Recherche efficace",
            description="Trouver rapidement des informations utiles.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M3-ANDO-001",
            is_active=True,
        )
        self.module2 = TrainingModule.objects.create(
            code="MODULE_2",
            title="Module 2 - Comprendre Internet",
            description="Comprendre Internet.",
        )
        self.session2 = TrainingSession.objects.create(
            module=self.module2,
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
            "auto_eval_keywords": "bien",
            "auto_eval_improve": "un_peu",
            "auto_eval_compare": "tres_bien",
            "todo_chose_subject": "on",
            "todo_written_question": "on",
            "todo_keywords_from_question": "on",
            "todo_did_search": "on",
            "todo_read_titles": "on",
            "todo_opened_result": "on",
            "todo_compared_two_results": "on",
            "todo_improved_keywords": "on",
            "todo_found_useful_resource": "on",
            "todo_noted_learning": "on",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4": "faux",
            "quiz_q5": "cours_equation_seconde_exemple",
            "quiz_q6": "photosynthese_cours_lycee_pdf",
            "quiz_q7_selected": list(Module3Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_starting_question": "Comment resoudre une equation ?",
            "practical_keywords_used": "equation seconde exemple",
            "practical_site_found": "www.exemple.mg",
            "practical_subject": "mathematiques",
            "practical_what_learned": "Les equations se resolvent avec des regles simples.",
            "feedback_understood_today": "J'ai compris comment chercher sur Internet.",
            "feedback_still_difficult": "",
            "feedback_confidence_search": "oui",
        }

    def test_module_3_form_get(self):
        response = self.client.get(reverse("surveys:module_3"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 3 - Recherche efficace")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_3"), data=self.valid_payload())

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Module3Submission.objects.count(), 1)
        submission = Module3Submission.objects.get()
        self.assertEqual(submission.school_id_number_snapshot, "01")
        self.assertEqual(submission.computed_score, 7)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"

        response = self.client.post(reverse("surveys:module_3"), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre exactement 2 chiffres")
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Module3Submission.objects.count(), 0)

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_3"), data=self.valid_payload())
        payload = self.valid_payload()
        payload["full_name"] = "Autre eleve"

        response = self.client.post(reverse("surveys:module_3"), data=payload)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Une réponse existe déjà pour ce numéro")
        self.assertEqual(Module3Submission.objects.count(), 1)

    def test_same_school_id_can_submit_module_2_and_module_3_separately(self):
        m2_payload = {
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
            "feedback_understood_today": "J'ai compris.",
            "feedback_still_difficult": "",
            "feedback_confidence": "oui",
        }
        response_m2 = self.client.post(reverse("surveys:module_2"), data=m2_payload)
        self.assertEqual(response_m2.status_code, 302)

        response_m3 = self.client.post(reverse("surveys:module_3"), data=self.valid_payload())
        self.assertEqual(response_m3.status_code, 302)

        self.assertEqual(Student.objects.count(), 2)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Module3Submission.objects.count(), 1)

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_3"), data=self.valid_payload())
        submission = Module3Submission.objects.get()
        other_client = self.client_class()

        response = other_client.get(reverse("surveys:module_3_success", args=[submission.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_3"))

    def test_module_3_form_returns_503_when_no_active_session_exists(self):
        self.session.is_active = False
        self.session.save()

        response = self.client.get(reverse("surveys:module_3"))

        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Le formulaire n'est pas disponible maintenant.", status_code=503)


class DashboardModule3Tests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="formateur",
            password="motdepasse-solide-123",
        )
        self.module = TrainingModule.objects.create(
            code="MODULE_3",
            title="Module 3 - Recherche efficace",
            description="Trouver rapidement des informations utiles.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M3-ANDO-001",
            is_active=True,
        )
        self.student = Student.objects.create(
            school_id_number="01",
            full_name="Rakoto Aina",
            class_level=Student.CLASS_LEVEL_SECONDE,
            group_name="Salle A",
        )
        Module3Submission.objects.create(
            student=self.student,
            session=self.session,
            school_id_number_snapshot="01",
            auto_eval_keywords="bien",
            auto_eval_improve="un_peu",
            auto_eval_compare="tres_bien",
            todo_chose_subject=True,
            todo_written_question=True,
            todo_keywords_from_question=True,
            todo_did_search=True,
            todo_read_titles=True,
            todo_opened_result=True,
            todo_compared_two_results=False,
            todo_improved_keywords=True,
            todo_found_useful_resource=True,
            todo_noted_learning=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4="faux",
            quiz_q5="cours_equation_seconde_exemple",
            quiz_q6="photosynthese_cours_lycee_pdf",
            quiz_q7_selected=list(Module3Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_starting_question="Comment resoudre une equation ?",
            practical_keywords_used="equation seconde exemple",
            practical_site_found="www.exemple.mg",
            practical_subject="mathematiques",
            practical_what_learned="Les equations se resolvent avec des regles simples.",
            feedback_understood_today="J'ai compris comment chercher.",
            feedback_still_difficult="",
            feedback_confidence_search="oui",
        )

    def test_dashboard_module_3_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_3"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_module_3_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_3_csv"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_module_3_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_module_3"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Score moyen")
        self.assertContains(response, "Rakoto Aina")

    def test_csv_export_module_3_contains_submission_data(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:export_module_3_csv"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("Rakoto Aina", response.content.decode())
        self.assertIn("school_id_number", response.content.decode())

    def test_csv_export_module_3_sanitizes_formula_like_cells(self):
        self.student.full_name = "=cmd"
        self.student.save()
        submission = Module3Submission.objects.get()
        submission.practical_starting_question = "+danger"
        submission.feedback_understood_today = "@risk"
        submission.feedback_still_difficult = "-test"
        submission.save()
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:export_module_3_csv"))
        content = response.content.decode()

        self.assertIn("'=cmd", content)
        self.assertIn("'+danger", content)
        self.assertIn("'@risk", content)
        self.assertIn("'-test", content)


class Module3HomeAndCockpitTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_3",
            title="Module 3 - Recherche efficace",
            description="Trouver rapidement des informations utiles.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M3-ANDO-001",
            is_active=True,
        )

    def test_home_page_shows_module_3_when_active(self):
        response = self.client.get(reverse("surveys:student_modules"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 3 - Recherche efficace")
        self.assertContains(response, "Réponses ouvertes")
        self.assertContains(response, "Voir le module")

    def test_home_page_shows_module_3_unavailable_when_no_active_session(self):
        self.session.is_active = False
        self.session.save()

        response = self.client.get(reverse("surveys:student_modules"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 3 - Recherche efficace")
        self.assertContains(response, "Indisponible")
        self.assertContains(response, "Aucune session active")

    def test_cockpit_shows_module_3_when_logged_in(self):
        user = get_user_model().objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 3 - Recherche efficace")
        self.assertContains(response, "Export CSV")


class SeedModule4CommandTests(TestCase):
    def test_seed_module4_creates_expected_module_and_active_session(self):
        call_command("seed_module4")

        module = TrainingModule.objects.get(code="MODULE_4")
        session = TrainingSession.objects.get(session_code="M4-ANDO-001")

        self.assertEqual(module.title, "Module 4 - Sources fiables")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module4_is_idempotent(self):
        call_command("seed_module4")
        call_command("seed_module4")

        self.assertEqual(TrainingModule.objects.filter(code="MODULE_4").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M4-ANDO-001").count(), 1)

    def test_seed_module4_does_not_overwrite_existing_session_details(self):
        call_command("seed_module4")
        session = TrainingSession.objects.get(session_code="M4-ANDO-001")
        session.location = "Autre lieu"
        session.trainer_name = "Autre formateur"
        session.is_active = False
        session.save()

        call_command("seed_module4")
        session.refresh_from_db()

        self.assertEqual(session.location, "Autre lieu")
        self.assertEqual(session.trainer_name, "Autre formateur")
        self.assertFalse(session.is_active)


class Module4SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_4",
            title="Module 4 - Sources fiables",
            description="Evaluer la credibilite d'un contenu.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M4-ANDO-001",
            is_active=True,
        )
        self.student = Student.objects.create(
            school_id_number="01",
            full_name="Rakoto Aina",
            class_level=Student.CLASS_LEVEL_SECONDE,
            group_name="Salle A",
        )

    def make_submission(self, student):
        return Module4Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_explain_source="bien",
            auto_eval_verify_info="parfois",
            auto_eval_spot_doubtful="tres_bien",
            todo_chose_info=True,
            todo_opened_first_source=True,
            todo_checked_publisher=True,
            todo_checked_date=True,
            todo_checked_evidence=True,
            todo_compared_second=True,
            todo_identified_reliable_sign=True,
            todo_identified_doubtful_sign=True,
            todo_decided_reliable_or_not=True,
            todo_explained_choice=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4="verifier_autres_sources",
            quiz_q5_selected=list(Module4Submission.QUIZ_Q5_CORRECT_ANSWERS),
            quiz_q6_selected=list(Module4Submission.QUIZ_Q6_CORRECT_ANSWERS),
            quiz_q7="faux",
            practical_subject="Volcans à Madagascar",
            practical_first_source="www.exemple.mg",
            practical_publisher="Un professeur",
            practical_has_date="oui",
            practical_has_evidence="oui",
            practical_compared="oui",
            practical_second_source="www.exemple2.mg",
            practical_decision="fiable",
            practical_explanation="Les deux sources disent la même chose.",
            feedback_understood_today="J'ai compris comment vérifier une source.",
            feedback_still_difficult="",
            feedback_confidence_verify="oui",
        )

    def test_duplicate_school_id_is_blocked(self):
        self.make_submission(self.student)
        other = Student.objects.create(
            school_id_number="01",
            full_name="Autre eleve",
            class_level=Student.CLASS_LEVEL_SECONDE,
        )
        with self.assertRaises(IntegrityError):
            self.make_submission(other)

    def test_score_is_computed_on_save(self):
        submission = self.make_submission(self.student)
        self.assertEqual(submission.computed_score, 7)


class Module4FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_4",
            title="Module 4 - Sources fiables",
            description="Evaluer la credibilite d'un contenu.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M4-ANDO-001",
            is_active=True,
        )
        self.module2 = TrainingModule.objects.create(
            code="MODULE_2", title="Module 2", description="Test",
        )
        TrainingSession.objects.create(
            module=self.module2,
            date=date(2026, 6, 18),
            location="Lycee Andohalo",
            trainer_name="Formateur",
            session_code="M2-ANDO-001",
            is_active=True,
        )
        self.module3 = TrainingModule.objects.create(
            code="MODULE_3", title="Module 3", description="Test",
        )
        TrainingSession.objects.create(
            module=self.module3,
            date=date(2026, 6, 18),
            location="Lycee Andohalo",
            trainer_name="Formateur",
            session_code="M3-ANDO-001",
            is_active=True,
        )

    def valid_payload(self):
        return {
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_explain_source": "bien",
            "auto_eval_verify_info": "parfois",
            "auto_eval_spot_doubtful": "tres_bien",
            "todo_chose_info": "on",
            "todo_opened_first_source": "on",
            "todo_checked_publisher": "on",
            "todo_checked_date": "on",
            "todo_checked_evidence": "on",
            "todo_compared_second": "on",
            "todo_identified_reliable_sign": "on",
            "todo_identified_doubtful_sign": "on",
            "todo_decided_reliable_or_not": "on",
            "todo_explained_choice": "on",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4": "verifier_autres_sources",
            "quiz_q5_selected": list(Module4Submission.QUIZ_Q5_CORRECT_ANSWERS),
            "quiz_q6_selected": list(Module4Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7": "faux",
            "practical_subject": "Volcans à Madagascar",
            "practical_first_source": "www.exemple.mg",
            "practical_publisher": "Un professeur",
            "practical_has_date": "oui",
            "practical_has_evidence": "oui",
            "practical_compared": "oui",
            "practical_second_source": "www.exemple2.mg",
            "practical_decision": "fiable",
            "practical_explanation": "Les deux sources disent la même chose.",
            "feedback_understood_today": "J'ai compris.",
            "feedback_still_difficult": "",
            "feedback_confidence_verify": "oui",
        }

    def test_module_4_form_get(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 4 - Sources fiables")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_4"), data=self.valid_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Module4Submission.objects.count(), 1)
        submission = Module4Submission.objects.get()
        self.assertEqual(submission.school_id_number_snapshot, "01")
        self.assertEqual(submission.computed_score, 7)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"
        response = self.client.post(reverse("surveys:module_4"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre exactement 2 chiffres")
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Module4Submission.objects.count(), 0)

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_4"), data=self.valid_payload())
        payload = self.valid_payload()
        payload["full_name"] = "Autre eleve"
        response = self.client.post(reverse("surveys:module_4"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Une réponse existe déjà pour ce numéro")
        self.assertEqual(Module4Submission.objects.count(), 1)

    def test_same_school_id_can_submit_all_modules_separately(self):
        m2 = {
            "school_id_number": "01", "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "auto_eval_internet_explained": "un_peu", "auto_eval_learning_usage": "parfois",
            "auto_eval_open_browser": "oui", "quiz_q1": "faux", "quiz_q2": "vrai",
            "quiz_q3": "vrai", "quiz_q4_selected": ["chercher_une_explication"],
            "quiz_q5": "cours_equation_seconde_exemple",
            "practical_search_text": "test", "practical_site_text": "",
            "practical_subject": "mathematiques",
            "feedback_understood_today": "test", "feedback_still_difficult": "",
            "feedback_confidence": "oui",
        }
        self.assertEqual(self.client.post(reverse("surveys:module_2"), data=m2).status_code, 302)

        m3 = {
            "school_id_number": "01", "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "auto_eval_keywords": "bien", "auto_eval_improve": "un_peu",
            "auto_eval_compare": "bien", "quiz_q1": "faux", "quiz_q2": "vrai",
            "quiz_q3": "vrai", "quiz_q4": "faux", "quiz_q5": "cours_equation_seconde_exemple",
            "quiz_q6": "photosynthese_cours_lycee_pdf", "quiz_q7_selected": ["ajouter_matiere_ou_niveau"],
            "practical_starting_question": "test", "practical_keywords_used": "test",
            "practical_site_found": "", "practical_subject": "mathematiques",
            "practical_what_learned": "test",
            "feedback_understood_today": "test", "feedback_still_difficult": "",
            "feedback_confidence_search": "oui",
        }
        self.assertEqual(self.client.post(reverse("surveys:module_3"), data=m3).status_code, 302)

        self.assertEqual(
            self.client.post(reverse("surveys:module_4"), data=self.valid_payload()).status_code, 302,
        )

        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Module3Submission.objects.count(), 1)
        self.assertEqual(Module4Submission.objects.count(), 1)
        self.assertEqual(Student.objects.count(), 3)

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_4"), data=self.valid_payload())
        submission = Module4Submission.objects.get()
        other_client = self.client_class()
        response = other_client.get(reverse("surveys:module_4_success", args=[submission.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_4"))

    def test_module_4_form_returns_503_when_no_active_session(self):
        self.session.is_active = False
        self.session.save()
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Le formulaire n'est pas disponible maintenant.", status_code=503)

    def test_score_calculation_single_choice(self):
        submission = Module4Submission.objects.create(
            student=Student.objects.create(school_id_number="01", full_name="Test", class_level=Student.CLASS_LEVEL_SECONDE),
            session=self.session,
            school_id_number_snapshot="01",
            auto_eval_explain_source="bien", auto_eval_verify_info="parfois",
            auto_eval_spot_doubtful="bien",
            quiz_q1="faux", quiz_q2="vrai", quiz_q3="vrai",
            quiz_q4="verifier_autres_sources",
            quiz_q7="faux",
            quiz_q5_selected=list(Module4Submission.QUIZ_Q5_CORRECT_ANSWERS),
            quiz_q6_selected=list(Module4Submission.QUIZ_Q6_CORRECT_ANSWERS),
            practical_subject="Test", practical_first_source="x",
            practical_has_date="oui", practical_has_evidence="oui",
            practical_compared="oui", practical_decision="fiable",
            practical_explanation="x",
            feedback_understood_today="x", feedback_confidence_verify="oui",
        )
        self.assertEqual(submission.computed_score, 7)

    def test_score_zero_for_wrong_answers(self):
        submission = Module4Submission.objects.create(
            student=Student.objects.create(school_id_number="02", full_name="Test2", class_level=Student.CLASS_LEVEL_SECONDE),
            session=self.session,
            school_id_number_snapshot="02",
            auto_eval_explain_source="pas_encore", auto_eval_verify_info="jamais",
            auto_eval_spot_doubtful="pas_encore",
            quiz_q1="vrai", quiz_q2="faux", quiz_q3="faux",
            quiz_q4="partager_vite",
            quiz_q7="vrai",
            quiz_q5_selected=["titre_choquant"],
            quiz_q6_selected=["preuves_claires"],
            practical_subject="Test", practical_first_source="x",
            practical_has_date="non", practical_has_evidence="non",
            practical_compared="non", practical_decision="douteuse",
            practical_explanation="x",
            feedback_understood_today="x", feedback_confidence_verify="pas_encore",
        )
        self.assertEqual(submission.computed_score, 0)


class DashboardModule4Tests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )
        self.module = TrainingModule.objects.create(
            code="MODULE_4", title="Module 4 - Sources fiables",
            description="Evaluer la credibilite.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module, date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M4-ANDO-001", is_active=True,
        )
        self.student = Student.objects.create(
            school_id_number="01", full_name="Rakoto Aina",
            class_level=Student.CLASS_LEVEL_SECONDE, group_name="Salle A",
        )
        Module4Submission.objects.create(
            student=self.student, session=self.session,
            school_id_number_snapshot="01",
            auto_eval_explain_source="bien", auto_eval_verify_info="parfois",
            auto_eval_spot_doubtful="tres_bien",
            todo_chose_info=True, todo_opened_first_source=True,
            todo_checked_publisher=True, todo_checked_date=True,
            todo_checked_evidence=True, todo_compared_second=False,
            todo_identified_reliable_sign=True, todo_identified_doubtful_sign=True,
            todo_decided_reliable_or_not=True, todo_explained_choice=True,
            quiz_q1="faux", quiz_q2="vrai", quiz_q3="vrai",
            quiz_q4="verifier_autres_sources",
            quiz_q5_selected=list(Module4Submission.QUIZ_Q5_CORRECT_ANSWERS),
            quiz_q6_selected=list(Module4Submission.QUIZ_Q6_CORRECT_ANSWERS),
            quiz_q7="faux",
            practical_subject="Volcans", practical_first_source="www.exemple.mg",
            practical_publisher="Prof", practical_has_date="oui",
            practical_has_evidence="oui", practical_compared="oui",
            practical_second_source="www.exemple2.mg", practical_decision="fiable",
            practical_explanation="Test.",
            feedback_understood_today="Compris.", feedback_still_difficult="",
            feedback_confidence_verify="oui",
        )

    def test_dashboard_module_4_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_4"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_module_4_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_4_csv"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_module_4_renders_for_logged_in(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_4"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Score moyen")
        self.assertContains(response, "Rakoto Aina")

    def test_csv_export_module_4_contains_data(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_4_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn("Rakoto Aina", content)
        self.assertIn("school_id_number", content)
        self.assertIn("computed_score", content)

    def test_csv_export_sanitizes_formula_like_cells(self):
        self.student.full_name = "=cmd"
        self.student.save()
        submission = Module4Submission.objects.get()
        submission.practical_subject = "+danger"
        submission.feedback_understood_today = "@risk"
        submission.feedback_still_difficult = "-test"
        submission.save()
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_4_csv"))
        content = response.content.decode()
        self.assertIn("'=cmd", content)
        self.assertIn("'+danger", content)
        self.assertIn("'@risk", content)
        self.assertIn("'-test", content)


class Module4HomeAndCockpitTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_4", title="Module 4 - Sources fiables",
            description="Evaluer la credibilite.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module, date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M4-ANDO-001", is_active=True,
        )

    def test_home_page_shows_module_4_when_active(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 4 - Sources fiables")
        self.assertContains(response, "Réponses ouvertes")
        self.assertContains(response, "Voir le module")

    def test_home_page_shows_module_4_unavailable_when_no_session(self):
        self.session.is_active = False
        self.session.save()
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 4 - Sources fiables")
        self.assertContains(response, "Indisponible")

    def test_cockpit_shows_module_4_when_logged_in(self):
        user = get_user_model().objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 4 - Sources fiables")
        self.assertContains(response, "Export CSV")


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


class FormPresenceTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        self.session = TrainingSession.objects.get(session_code="M2-ANDO-001")
        self.url = reverse("surveys:presence_heartbeat")

    def test_heartbeat_creates_presence(self):
        response = self.client.post(
            self.url,
            {"module_code": "MODULE_2", "client_id": "test123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(FormPresence.objects.count(), 1)

    def test_heartbeat_updates_presence(self):
        self.client.post(
            self.url,
            {"module_code": "MODULE_2", "client_id": "test123"},
            content_type="application/json",
        )
        self.client.post(
            self.url,
            {"module_code": "MODULE_2", "client_id": "test123", "school_id_number": "05"},
            content_type="application/json",
        )
        self.assertEqual(FormPresence.objects.count(), 1)
        p = FormPresence.objects.first()
        self.assertEqual(p.school_id_number, "05")

    def test_heartbeat_invalid_module_returns_404(self):
        response = self.client.post(
            self.url,
            {"module_code": "INVALID", "client_id": "test123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_heartbeat_no_client_id_returns_400(self):
        response = self.client.post(
            self.url,
            {"module_code": "MODULE_2"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_heartbeat_get_returns_405(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)


class PresenceJsonTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        call_command("seed_module2")
        self.session = TrainingSession.objects.get(session_code="M2-ANDO-001")
        self.user = User.objects.create_user(username="test", password="test")
        self.url = reverse("surveys:dashboard_presence_json")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_counts_active_presence(self):
        self.client.login(username="test", password="test")
        FormPresence.objects.create(
            module_code="MODULE_2",
            training_session=self.session,
            client_id="c1",
            last_seen_at=timezone.now(),
            status=FormPresence.STATUS_ACTIVE,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["by_module"]["MODULE_2"], 1)

    def test_expired_presence_not_counted(self):
        self.client.login(username="test", password="test")
        from datetime import timedelta
        FormPresence.objects.create(
            module_code="MODULE_2",
            training_session=self.session,
            client_id="c1",
            last_seen_at=timezone.now() - timedelta(seconds=120),
            status=FormPresence.STATUS_ACTIVE,
        )
        response = self.client.get(self.url)
        data = response.json()
        self.assertEqual(data["total"], 0)


class DashboardSettingsTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="test", password="test", is_staff=True)
        self.url = reverse("surveys:dashboard_settings")
        self.tmpdir = mkdtemp()
        self._old_db_path = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = os.path.join(self.tmpdir, "db.sqlite3")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        if self._old_db_path is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = self._old_db_path

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_requires_staff(self):
        non_staff = get_user_model().objects.create_user(username="nope", password="test")
        self.client.login(username="nope", password="test")
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 403))

    def test_renders_for_staff(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_settings_page_does_not_expose_secret_key(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertNotContains(response, "change-me-for-docker-local-use")
        self.assertContains(response, "Configuré")

    def test_settings_page_does_not_render_raw_env(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertNotContains(response, ".env")

    def test_shows_taf_host_port(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertContains(response, "TAF_HOST_PORT")

    def test_shows_taf_lan_host(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertContains(response, "TAF_LAN_HOST")

    def test_shows_allowed_hosts(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertContains(response, "ALLOWED_HOSTS")

    def test_shows_csrf_trusted_origins(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertContains(response, "CSRF_TRUSTED_ORIGINS")

    def test_shows_timezone_field(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertContains(response, "TIME_ZONE")

    def test_does_not_show_gpg_key(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertNotContains(response, "GPG_KEY")

    def test_never_exposes_raw_secret_key(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertNotContains(response, "change-me-for-docker-local-use")

    def test_save_taf_lan_host(self):
        self.client.login(username="test", password="test")
        response = self.client.post(self.url, {"key": "TAF_LAN_HOST", "value": "192.168.1.42"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Valeur enregistrée")

    def test_save_taf_host_port(self):
        self.client.login(username="test", password="test")
        response = self.client.post(self.url, {"key": "TAF_HOST_PORT", "value": "9010"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Valeur enregistrée")

    def test_denies_allowed_hosts_star(self):
        self.client.login(username="test", password="test")
        response = self.client.post(self.url, {"key": "ALLOWED_HOSTS", "value": "*"}, follow=True)
        self.assertContains(response, "interdit")

    def test_denies_csrf_origin_without_scheme(self):
        self.client.login(username="test", password="test")
        response = self.client.post(self.url, {"key": "CSRF_TRUSTED_ORIGINS", "value": "192.168.1.42:8010"}, follow=True)
        self.assertContains(response, "http://")


class DashboardNetworkTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="test", password="test")
        self.url = reverse("surveys:dashboard_network")

    def test_requires_login(self):
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_shows_module_2_url(self):
        self.client.login(username="test", password="test")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "module-2")


class CleanupPresenceCommandTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        self.session = TrainingSession.objects.get(session_code="M2-ANDO-001")

    def test_cleanup_expired_presences(self):
        from datetime import timedelta
        FormPresence.objects.create(
            module_code="MODULE_2",
            training_session=self.session,
            client_id="old",
            last_seen_at=timezone.now() - timedelta(seconds=180),
            status=FormPresence.STATUS_ACTIVE,
        )
        FormPresence.objects.create(
            module_code="MODULE_2",
            training_session=self.session,
            client_id="fresh",
            last_seen_at=timezone.now(),
            status=FormPresence.STATUS_ACTIVE,
        )
        call_command("cleanup_presence")
        self.assertEqual(FormPresence.objects.filter(status=FormPresence.STATUS_ACTIVE).count(), 1)
        self.assertEqual(FormPresence.objects.filter(status=FormPresence.STATUS_EXPIRED).count(), 1)


class AdminBrandingTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            username="admin", password="admin", email="admin@example.com"
        )
        self.client.login(username="admin", password="admin")

    def test_admin_site_header_customized(self):
        from django.contrib import admin
        self.assertEqual(admin.site.site_header, "TAf Local Forms")
        self.assertEqual(admin.site.site_title, "TAf Admin")
        self.assertEqual(admin.site.index_title, "Administration formateur")
        self.assertEqual(admin.site.site_url, "/dashboard/")

    def test_admin_page_uses_custom_template(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TAf Local Forms")
        self.assertContains(response, "Cockpit formateur")
        self.assertContains(response, "css/admin.css")
        self.assertContains(response, "Administration formateur")


class NetworkPageDiagnosticsTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="trainer", password="secret")
        self.url = reverse("surveys:dashboard_network")
        self.client.login(username="trainer", password="secret")

    def test_network_page_shows_diagnostic_scripts(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "taf-lan-diagnose")
        self.assertContains(response, "taf-lan-show-status")
        self.assertContains(response, "taf-lan-open-port")

    def test_network_page_shows_wsl_gateway_info(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passerelle WSL")

    def test_network_page_shows_wsl_environment_info(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Environnement")


class NavigationTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="navtest", password="secret", is_staff=True)
        self.client.login(username="navtest", password="secret")

    def test_home_contains_modules_link(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "Je suis étudiant")
        self.assertContains(response, reverse("surveys:student_modules"))

    def test_home_contains_espace_formateur_link_to_dashboard(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "Je suis formateur")
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_logo_links_to_home(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, 'href="/"')

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertIn(response.status_code, (302, 401, 403))

    def test_dashboard_shows_modules(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Modules de formation")

    def test_dashboard_shows_tools(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Accès réseau")
        self.assertContains(response, "Configuration réseau")
        self.assertContains(response, "Admin avancé")

    def test_dashboard_shows_stats(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Total réponses")
        self.assertContains(response, "Total élèves")
        self.assertContains(response, "Modules ouverts")


class AcceptingResponsesModelTests(TestCase):
    def test_accepting_responses_default_true(self):
        module = TrainingModule.objects.create(code="TEST_MOD", title="Test Module")
        session = TrainingSession.objects.create(
            module=module, date=date.today(),
            location="Test", trainer_name="Test",
            session_code="TST-001", is_active=True,
        )
        self.assertTrue(session.accepting_responses)

    def test_toggle_closes_responses(self):
        module = TrainingModule.objects.create(code="TEST_MOD", title="Test Module")
        session = TrainingSession.objects.create(
            module=module, date=date.today(),
            location="Test", trainer_name="Test",
            session_code="TST-002", is_active=True,
        )
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])
        session.refresh_from_db()
        self.assertFalse(session.accepting_responses)

    def test_toggle_reopens_responses(self):
        module = TrainingModule.objects.create(code="TEST_MOD", title="Test Module")
        session = TrainingSession.objects.create(
            module=module, date=date.today(),
            location="Test", trainer_name="Test",
            session_code="TST-003", is_active=True,
            accepting_responses=False,
        )
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        session.refresh_from_db()
        self.assertTrue(session.accepting_responses)


class ToggleResponsesViewTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        self.url_m2 = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_2"})
        self.url_m3 = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_3"})
        self.url_m4 = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_4"})

    def test_toggle_requires_login(self):
        response = self.client.post(self.url_m2)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_requires_staff(self):
        user = get_user_model().objects.create_user(username="regular", password="test")
        self.client.login(username="regular", password="test")
        response = self.client.post(self.url_m2)
        self.assertIn(response.status_code, (302, 403))

    def test_toggle_closes_module_2(self):
        self.client.login(username="staff", password="secret")
        response = self.client.post(self.url_m2, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        self.assertFalse(session.accepting_responses)

    def test_toggle_reopens_module_2(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url_m2)
        self.client.post(self.url_m2, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        self.assertTrue(session.accepting_responses)

    def test_toggle_closes_module_3(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url_m3, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_3", is_active=True)
        self.assertFalse(session.accepting_responses)

    def test_toggle_closes_module_4(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url_m4, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_4", is_active=True)
        self.assertFalse(session.accepting_responses)


class ClosedSubmissionTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        # Close all modules
        for code in ["MODULE_2", "MODULE_3", "MODULE_4"]:
            session = TrainingSession.objects.get(module__code=code, is_active=True)
            session.accepting_responses = False
            session.save(update_fields=["accepting_responses"])

    def test_module_2_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermées")

    def test_module_2_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_2"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_3_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermées")

    def test_module_3_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_3"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_4_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermées")

    def test_module_4_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_4"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_reopened_accepts_submission(self):
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        response = self.client.post(
            reverse("surveys:module_2"),
            {
                "school_id_number": "99",
                "full_name": "Test Student",
                "class_level": "seconde",
                "group_name": "",
                "auto_eval_internet_explained": "bien",
                "auto_eval_learning_usage": "parfois",
                "auto_eval_open_browser": "oui",
                "todo_opened_browser": True,
                "todo_typed_simple_search": True,
                "todo_used_keywords": True,
                "todo_opened_result": True,
                "todo_compared_results": True,
                "todo_found_school_info": True,
                "todo_asked_for_help": True,
                "todo_noted_learning": True,
                "quiz_q1": "faux",
                "quiz_q2": "vrai",
                "quiz_q3": "vrai",
                "quiz_q4_selected": [
                    "chercher_une_explication",
                    "regarder_une_video_educative",
                    "trouver_un_document_de_revision",
                    "apprendre_un_nouveau_mot",
                ],
                "quiz_q5": "cours_equation_seconde_exemple",
                "practical_search_text": "Test search",
                "practical_site_text": "test.com",
                "practical_subject": "informatique",
                "feedback_understood_today": "Tout compris",
                "feedback_still_difficult": "",
                "feedback_confidence": "oui",
            },
        )
        self.assertEqual(response.status_code, 302)  # redirect to success page
        self.assertTrue(Submission.objects.filter(school_id_number_snapshot="99").exists())

    def test_existing_antiduplicate_tests_still_pass(self):
        # Module 2 is closed - re-open and submit once, then verify second submit is rejected
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        data = {
            "school_id_number": "88",
            "full_name": "Dup Test",
            "class_level": "seconde",
            "group_name": "",
            "auto_eval_internet_explained": "bien",
            "auto_eval_learning_usage": "parfois",
            "auto_eval_open_browser": "oui",
            "todo_opened_browser": True,
            "todo_typed_simple_search": True,
            "todo_used_keywords": True,
            "todo_opened_result": True,
            "todo_compared_results": True,
            "todo_found_school_info": True,
            "todo_asked_for_help": True,
            "todo_noted_learning": True,
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4_selected": [
                "chercher_une_explication",
                "regarder_une_video_educative",
                "trouver_un_document_de_revision",
                "apprendre_un_nouveau_mot",
            ],
            "quiz_q5": "cours_equation_seconde_exemple",
            "practical_search_text": "Test search",
            "practical_site_text": "test.com",
            "practical_subject": "informatique",
            "feedback_understood_today": "Tout compris",
            "feedback_still_difficult": "",
            "feedback_confidence": "oui",
        }
        self.client.post(reverse("surveys:module_2"), data)
        # Second submit should fail
        response = self.client.post(reverse("surveys:module_2"), data)
        self.assertContains(response, "existe déjà")


class AdminAdvancedTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            username="super", password="super", email="super@example.com"
        )
        self.client.login(username="super", password="super")

    def test_admin_shows_advanced_title(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Admin avancé")
        self.assertContains(response, "TAf Local Forms")

    def test_admin_links_to_dashboard(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_admin_has_custom_css(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "css/admin.css")

    def test_admin_has_no_raw_secrets(self):
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, "SECRET_KEY")


class F019NavigationUXTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="navux", password="secret", is_staff=True)
        self.client.login(username="navux", password="secret")

    def test_home_contains_modules_link(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "Je suis étudiant")
        self.assertContains(response, reverse("surveys:student_modules"))

    def test_home_contains_espace_formateur(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "Je suis formateur")
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_logo_points_to_home(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, 'href="/"')

    def test_dashboard_shows_full_nav(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Accueil")
        self.assertContains(response, "Cockpit")
        self.assertContains(response, "Réseau")
        self.assertContains(response, "Configuration")
        self.assertContains(response, "Admin avancé")

    def test_dashboard_shows_all_subnav_tabs(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        for tab in ["Vue d'ensemble", "Modules", "Présence", "Réseau", "Exports", "Admin"]:
            self.assertContains(response, tab)

    def test_dashboard_shows_overview_stats(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Total réponses")
        self.assertContains(response, "Total élèves")
        self.assertContains(response, "Score moyen")
        self.assertContains(response, "Modules ouverts")

    def test_dashboard_shows_presence_section(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Présence en direct")
        self.assertContains(response, "presence-module-2")
        self.assertContains(response, "presence-module-3")
        self.assertContains(response, "presence-module-4")

    def test_dashboard_shows_network_section(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Accès réseau")
        self.assertContains(response, "Diagnostic réseau complet")

    def test_dashboard_shows_exports_section(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Exports CSV")
        self.assertContains(response, "Export Module 2")
        self.assertContains(response, "Export Module 3")
        self.assertContains(response, "Export Module 4")

    def test_dashboard_shows_advanced_section(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Outils formateur")
        self.assertContains(response, "Admin avancé")
        self.assertContains(response, "Guide dépannage réseau")

    def test_dashboard_links_have_target_blank(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'rel="noopener noreferrer"')

    def test_dashboard_shows_no_ip_placeholder(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertNotContains(response, "IP_DU_LAPTOP")

    @patch.dict(os.environ, {"TAF_LAN_HOST": "", "PUBLIC_LAN_HOST": "", "TAF_HOST_PORT": ""})
    @patch("surveys.network._get_ip_candidates", return_value=[])
    def test_dashboard_shows_ip_alert_when_not_configured(self, mock_get_ip):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "IP locale non configurée")

    def test_network_page_links_have_target_blank(self):
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'rel="noopener noreferrer"')

    @patch.dict(os.environ, {"TAF_LAN_HOST": "", "PUBLIC_LAN_HOST": "", "TAF_HOST_PORT": ""})
    @patch("surveys.network._get_ip_candidates", return_value=[])
    def test_network_page_shows_ip_alert(self, mock_get_ip):
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertContains(response, "IP locale non configurée")

    def test_subnav_is_present(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "sub-nav")
        self.assertContains(response, "sub-nav-link")


class F019NetworkIPTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username="ipuser", password="secret", is_staff=True)
        self.client.login(username="ipuser", password="secret")

    @override_settings(TAF_LAN_HOST="192.168.0.100")
    def test_dashboard_shows_configured_ip(self):
        import os
        os.environ["TAF_LAN_HOST"] = "192.168.0.100"
        try:
            response = self.client.get(reverse("surveys:dashboard_home"))
            self.assertContains(response, "192.168.0.100")
        finally:
            os.environ.pop("TAF_LAN_HOST", None)

    @override_settings(TAF_LAN_HOST="192.168.0.100")
    def test_dashboard_links_use_configured_ip(self):
        import os
        old_lan = os.environ.get("TAF_LAN_HOST")
        old_port = os.environ.get("TAF_HOST_PORT")
        os.environ["TAF_LAN_HOST"] = "192.168.0.100"
        os.environ.pop("TAF_HOST_PORT", None)
        try:
            response = self.client.get(reverse("surveys:dashboard_home"))
            self.assertContains(response, "http://192.168.0.100:8000/")
        finally:
            if old_lan:
                os.environ["TAF_LAN_HOST"] = old_lan
            else:
                os.environ.pop("TAF_LAN_HOST", None)
            if old_port:
                os.environ["TAF_HOST_PORT"] = old_port

    def test_dashboard_shows_config_link_when_no_ip(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Configurer l'IP locale")
        self.assertContains(response, reverse("surveys:dashboard_settings"))


class F019ModuleFormRegressionTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")

    def test_module_2_accessible(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 2")

    def test_module_3_accessible(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 3")

    def test_module_4_accessible(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 4")

    def test_toggle_still_works(self):
        from django.contrib.auth.models import User
        User.objects.create_user(username="tog", password="tog", is_staff=True)
        self.client.login(username="tog", password="tog")
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        self.assertTrue(session.accepting_responses)
        response = self.client.post(
            reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_2"}),
            follow=True,
        )
        session.refresh_from_db()
        self.assertFalse(session.accepting_responses)
        self.assertEqual(response.status_code, 200)

    def test_closed_submission_blocked(self):
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])
        response = self.client.post(
            reverse("surveys:module_2"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)


class F021PedagogyContentTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")

    def test_student_modules_shows_module_2_pedagogy_summary(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internet est un")

    def test_student_modules_shows_module_3_pedagogy_summary(self):
        response = self.client.get(reverse("surveys:student_module_3_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trouver rapidement")

    def test_student_modules_shows_module_4_pedagogy_summary(self):
        response = self.client.get(reverse("surveys:student_module_4_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "source fiable")

    def test_module_2_form_contains_pedagogy_content(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Internet est un outil")
        self.assertContains(response, "navigateur")
        self.assertContains(response, "moteur de recherche")

    def test_module_3_form_contains_pedagogy_content(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Question")
        self.assertContains(response, "mots-clés")
        self.assertContains(response, "résultats")
        self.assertContains(response, "choix")

    def test_module_4_form_contains_pedagogy_content(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "QUI ?")
        self.assertContains(response, "QUOI ?")
        self.assertContains(response, "QUAND ?")
        self.assertContains(response, "POURQUOI ?")

    def test_module_2_pedagogy_contains_notions_cles(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertContains(response, "Notions clés")
        self.assertContains(response, "Navigateur")
        self.assertContains(response, "Moteur de recherche")

    def test_module_3_pedagogy_contains_4_etapes(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertContains(response, "4 étapes")
        self.assertContains(response, "Je précise ma question")

    def test_module_4_pedagogy_contains_5_questions(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertContains(response, "5 questions")
        self.assertContains(response, "OÙ ?")

    def test_module_2_pedagogy_contains_activites(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertContains(response, "Activité")
        self.assertContains(response, "Reconnaître")

    def test_module_3_pedagogy_contains_bons_mots_cles(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertContains(response, "formule")
        self.assertContains(response, "Matière + notion")

    def test_module_4_pedagogy_contains_3_reflexes(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertContains(response, "3 réflexes")
        self.assertContains(response, "Je regarde la source")

    def test_module_2_pedagogy_contains_a_eviter(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertContains(response, "Copier sans comprendre")
        self.assertContains(response, "Croire tout ce qu'on voit")

    def test_module_3_pedagogy_contains_erreurs_frequentes(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertContains(response, "Erreurs fréquentes")
        self.assertContains(response, "Abandonner trop vite")

    def test_module_4_pedagogy_contains_auteur_organisation(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertContains(response, "L'auteur ou l'organisation")
        self.assertContains(response, "Bon signe")

    def test_module_2_pedagogy_contains_regles_travail(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertContains(response, "Règles de travail")

    def test_module_4_pedagogy_contains_reseaux_sociaux(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertContains(response, "réseaux sociaux")
        self.assertContains(response, "likes")

    def test_module_3_pedagogy_contains_outils_utiles(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertContains(response, "Outils utiles")
        self.assertContains(response, "filetype:pdf")

    def test_student_pages_no_trainer_links(self):
        response_2 = self.client.get(reverse("surveys:module_2"))
        self.assertNotContains(response_2, "Export CSV")
        response_m = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response_m, "/admin/")
        self.assertNotContains(response_m, "Cockpit formateur")


class F022RNavigationRewireTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        self.user = User.objects.create_user(username="f022ruser", password="secret", is_staff=True)

    # --- Logo ---
    def test_logo_points_to_home(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, 'href="/"')

    # --- Landing page ---
    def test_landing_shows_student_choice(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "Je suis étudiant")
        self.assertContains(response, reverse("surveys:student_modules"))

    def test_landing_shows_trainer_choice(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "Je suis formateur")
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_landing_shows_about(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "À propos du projet")

    def test_landing_nav_minimal(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, ">Accueil<")
        self.assertNotContains(response, "Modules</a>")
        self.assertNotContains(response, "Cockpit</a>")

    # --- Student module list ---
    def test_student_modules_status_200(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)

    def test_student_modules_shows_module_list(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertContains(response, "Module 2")
        self.assertContains(response, "Module 3")
        self.assertContains(response, "Module 4")

    def test_student_modules_shows_voir_le_module(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertContains(response, "Voir le module")

    def test_student_modules_no_full_pedagogy(self):
        """Module list should NOT contain the full detailed pedagogy for all modules."""
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Qu'est-ce qu'Internet ?")
        self.assertNotContains(response, "La méthode en 4 étapes")
        self.assertNotContains(response, "Pourquoi vérifier une information")

    def test_student_modules_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Cockpit")
        self.assertNotContains(response, "Dashboard")
        self.assertNotContains(response, "Admin avancé")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "Fermer les réponses")

    def test_student_modules_no_dashboard_nav(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, ">Cockpit<")
        self.assertNotContains(response, ">Réseau<")
        self.assertNotContains(response, ">Configuration<")

    # --- Student module detail pages ---
    def test_student_module_2_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_3_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_3_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_4_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_4_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_2_contains_pedagogy(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertContains(response, "Qu'est-ce qu'Internet ?")
        self.assertContains(response, "Notions clés")

    def test_student_module_3_contains_pedagogy(self):
        response = self.client.get(reverse("surveys:student_module_3_detail"))
        self.assertContains(response, "La méthode en 4 étapes")
        self.assertContains(response, "mots-clés")

    def test_student_module_4_contains_pedagogy(self):
        response = self.client.get(reverse("surveys:student_module_4_detail"))
        self.assertContains(response, "Pourquoi vérifier une information")
        self.assertContains(response, "5 questions")

    def test_student_module_open_shows_commencer(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertContains(response, "Commencer le questionnaire")

    def test_student_module_closed_shows_consulter(self):
        session = TrainingSession.objects.get(module__code="MODULE_2", is_active=True)
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertContains(response, "Consulter le questionnaire")
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])

    def test_student_module_detail_has_return_link(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertContains(response, reverse("surveys:student_modules"))

    def test_student_module_detail_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertNotContains(response, "Cockpit")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "Admin avancé")

    # --- Student form pages ---
    def test_module_2_form_status_200(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)

    def test_module_3_form_status_200(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)

    def test_module_4_form_status_200(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)

    def test_module_form_no_trainer_links(self):
        for url_name in ["surveys:module_2", "surveys:module_3", "surveys:module_4"]:
            response = self.client.get(reverse(url_name))
            self.assertNotContains(response, "Cockpit")
            self.assertNotContains(response, "Admin avancé")
            self.assertNotContains(response, "Export CSV")

    # --- Trainer dashboard ---
    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertIn(response.status_code, (302, 401))

    def test_dashboard_logged_in_shows_trainer_actions(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Consulter formulaire")
        self.assertContains(response, "Export CSV")

    def test_dashboard_no_student_actions(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertNotContains(response, "Commencer le questionnaire")
        self.assertNotContains(response, "Voir le module")

    def test_dashboard_has_trainer_nav(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Cockpit")
        self.assertContains(response, "Réseau")
        self.assertContains(response, "Configuration")
        self.assertContains(response, "Admin avancé")

    def test_dashboard_toggle_staff_only(self):
        self.client.logout()
        response = self.client.post(
            reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_2"})
        )
        self.assertIn(response.status_code, (302, 401, 403))

    def test_dashboard_network_protected(self):
        self.client.logout()
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertIn(response.status_code, (302, 401))

    def test_dashboard_settings_protected(self):
        self.client.logout()
        response = self.client.get(reverse("surveys:dashboard_settings"))
        self.assertIn(response.status_code, (302, 401))

    # --- Network page ---
    def test_network_page_shows_links(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 2")

    def test_network_links_have_target_blank(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'rel="noopener noreferrer"')

    # --- Admin page ---
    def test_admin_accessible(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)

    def test_admin_has_cockpit_link(self):
        self.client.login(username="f022ruser", password="secret")
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, reverse("surveys:dashboard_home"))

    # --- Regression: pedagogy content remains on form pages ---
    def test_module_2_form_has_pedagogy(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertContains(response, "Notions clés")

    def test_module_3_form_has_pedagogy(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertContains(response, "4 étapes")

    def test_module_4_form_has_pedagogy(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertContains(response, "5 questions")


class F019AdminContrastTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            username="superux", password="superux", email="super@example.com"
        )
        self.client.login(username="superux", password="superux")

    def test_admin_shows_cockpit_link(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_admin_has_css(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "css/admin.css")

    def test_admin_no_raw_secrets(self):
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, "SECRET_KEY")

    def test_admin_shows_formateur_tools(self):
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Cockpit formateur")


class F023NetworkIPDetectionTests(TestCase):
    """Tests for network.py LAN IP detection logic (no DB or client needed)."""

    def test_is_private_ip_192_168(self):
        from surveys.network import _is_private_ip
        self.assertTrue(_is_private_ip("192.168.0.101"))

    def test_is_private_ip_10_dot(self):
        from surveys.network import _is_private_ip
        self.assertTrue(_is_private_ip("10.0.0.1"))

    def test_is_private_ip_172_16(self):
        from surveys.network import _is_private_ip
        self.assertTrue(_is_private_ip("172.16.0.1"))

    def test_is_private_ip_172_31(self):
        from surveys.network import _is_private_ip
        self.assertTrue(_is_private_ip("172.31.0.1"))

    def test_is_private_ip_172_32_false(self):
        from surveys.network import _is_private_ip
        self.assertFalse(_is_private_ip("172.32.0.1"))

    def test_is_private_ip_localhost_false(self):
        from surveys.network import _is_private_ip
        self.assertFalse(_is_private_ip("127.0.0.1"))

    def test_is_private_ip_public_false(self):
        from surveys.network import _is_private_ip
        self.assertFalse(_is_private_ip("8.8.8.8"))

    def test_parse_host_port_simple(self):
        from surveys.network import _parse_host_port
        host, port = _parse_host_port("192.168.0.101:8011")
        self.assertEqual(host, "192.168.0.101")
        self.assertEqual(port, "8011")

    def test_parse_host_port_no_port(self):
        from surveys.network import _parse_host_port
        host, port = _parse_host_port("192.168.0.101")
        self.assertEqual(host, "192.168.0.101")
        self.assertEqual(port, "")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_request_lan_host_sets_source_request(self):
        from surveys.network import get_network_access_context
        from django.test import RequestFactory
        rf = RequestFactory()
        request = rf.get("/", HTTP_HOST="192.168.0.101:8011")
        ctx = get_network_access_context(request)
        self.assertEqual(ctx["lan_host_source"], "request")
        self.assertEqual(ctx["recommended_lan_host"], "192.168.0.101")
        self.assertEqual(ctx["recommended_lan_port"], "8011")
        self.assertEqual(ctx["recommended_student_base_url"], "http://192.168.0.101:8011")
        self.assertTrue(ctx["current_request_is_lan"])

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_recommended_student_base_url(self):
        from surveys.network import get_network_access_context
        from django.test import RequestFactory
        rf = RequestFactory()
        request = rf.get("/", HTTP_HOST="192.168.0.101:8011")
        ctx = get_network_access_context(request)
        self.assertEqual(ctx["recommended_student_base_url"], "http://192.168.0.101:8011")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_lan_host_stale_when_mismatch(self):
        import os
        os.environ["TAF_LAN_HOST"] = "192.168.0.100"
        try:
            from surveys.network import get_network_access_context
            from django.test import RequestFactory
            rf = RequestFactory()
            request = rf.get("/", HTTP_HOST="192.168.0.101:8011")
            ctx = get_network_access_context(request)
            self.assertTrue(ctx["lan_host_stale"])
            self.assertEqual(ctx["configured_host"], "192.168.0.100")
        finally:
            os.environ.pop("TAF_LAN_HOST", None)

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_lan_host_not_stale_when_match(self):
        import os
        os.environ["TAF_LAN_HOST"] = "192.168.0.101"
        try:
            from surveys.network import get_network_access_context
            from django.test import RequestFactory
            rf = RequestFactory()
            request = rf.get("/", HTTP_HOST="192.168.0.101:8011")
            ctx = get_network_access_context(request)
            self.assertFalse(ctx["lan_host_stale"])
        finally:
            os.environ.pop("TAF_LAN_HOST", None)

    def test_no_lan_host_shows_unconfigured(self):
        from surveys.network import get_network_access_context
        from django.test import RequestFactory
        rf = RequestFactory()
        request = rf.get("/", HTTP_HOST="localhost:8010")
        ctx = get_network_access_context(request)
        self.assertEqual(ctx["lan_host_source"], "missing")
        self.assertEqual(ctx["recommended_lan_host"], "")
        self.assertFalse(ctx["has_lan_host"])

    def test_no_ip_du_laptop_in_urls(self):
        from surveys.network import get_network_access_context
        from django.test import RequestFactory
        rf = RequestFactory()
        request = rf.get("/", HTTP_HOST="localhost:8010")
        ctx = get_network_access_context(request)
        for key in ("student_form_url", "module_2_url", "module_3_url", "module_4_url", "cockpit_url"):
            self.assertNotIn("<IP_DU_LAPTOP>", ctx[key], f"{key} contains <IP_DU_LAPTOP>")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_warning_contains_stale_message(self):
        import os
        os.environ["TAF_LAN_HOST"] = "192.168.0.100"
        try:
            from surveys.network import get_network_access_context
            from django.test import RequestFactory
            rf = RequestFactory()
            request = rf.get("/", HTTP_HOST="192.168.0.101:8011")
            ctx = get_network_access_context(request)
            stale_warnings = [w for w in ctx["warnings"] if "diffère" in w and "Mets à jour" in w]
            self.assertTrue(len(stale_warnings) >= 1, msg="No stale warning found")
        finally:
            os.environ.pop("TAF_LAN_HOST", None)

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_private_ip_10_dot_is_lan(self):
        from surveys.network import get_network_access_context
        from django.test import RequestFactory
        rf = RequestFactory()
        request = rf.get("/", HTTP_HOST="10.0.0.5:8011")
        ctx = get_network_access_context(request)
        self.assertTrue(ctx["current_request_is_lan"])
        self.assertEqual(ctx["lan_host_source"], "request")


@override_settings(ALLOWED_HOSTS=["*"])
class F023DashboardNetworkTests(TestCase):
    """Tests for the /dashboard/network/ page."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            username="netadmin", password="netadmin", email="net@example.com"
        )
        self.client.login(username="netadmin", password="netadmin")

    def test_network_page_recommends_lan_ip_from_request(self):
        response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="192.168.0.101:8011")
        self.assertContains(response, "http://192.168.0.101:8011")

    def test_network_page_source_label_request(self):
        response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="192.168.0.101:8011")
        self.assertContains(response, "Adresse détectée depuis cette connexion")

    def test_network_page_shows_lan_pill(self):
        response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="192.168.0.101:8011")
        self.assertContains(response, "LAN")

    def test_network_page_shows_8011_reference(self):
        response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="localhost:8010")
        self.assertContains(response, "8011")

    def test_network_page_shows_recommended_ip_on_lan(self):
        response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="192.168.0.101:8011")
        self.assertContains(response, "192.168.0.101")

    def test_network_page_no_ip_du_laptop(self):
        response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="localhost:8010")
        self.assertNotContains(response, "<IP_DU_LAPTOP>")

    def test_network_page_stale_alert(self):
        import os
        os.environ["TAF_LAN_HOST"] = "192.168.0.100"
        try:
            response = self.client.get(reverse("surveys:dashboard_network"), HTTP_HOST="192.168.0.101:8011")
            self.assertContains(response, "Mets à jour la configuration")
        finally:
            os.environ.pop("TAF_LAN_HOST", None)


@override_settings(ALLOWED_HOSTS=["*"])
class F023DashboardSettingsTests(TestCase):
    """Tests for dashboard settings / use current address."""

    def setUp(self):
        import tempfile, os
        self._tmpdir = tempfile.mkdtemp()
        self._old_db_path = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = f"{self._tmpdir}/db.sqlite3"
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            username="setadmin", password="setadmin", email="set@example.com"
        )
        self.client.login(username="setadmin", password="setadmin")

    def tearDown(self):
        import os
        if self._old_db_path is not None:
            os.environ["DATABASE_PATH"] = self._old_db_path
        else:
            os.environ.pop("DATABASE_PATH", None)
        import shutil
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_settings_page_shows_use_current_address_when_lan(self):
        response = self.client.get(reverse("surveys:dashboard_settings"), HTTP_HOST="192.168.0.101:8011")
        self.assertContains(response, "Utiliser l'adresse actuelle")
        self.assertContains(response, "192.168.0.101")

    def test_settings_page_hides_button_on_localhost(self):
        response = self.client.get(reverse("surveys:dashboard_settings"), HTTP_HOST="localhost:8010")
        self.assertNotContains(response, "Utiliser l'adresse actuelle")

    def test_use_current_address_updates_settings(self):
        response = self.client.post(
            reverse("surveys:dashboard_use_current_address"),
            HTTP_HOST="192.168.0.101:8011",
            follow=True,
        )
        self.assertContains(response, "Paramètres LAN synchronisés")

    def test_use_current_address_rejects_localhost(self):
        response = self.client.post(
            reverse("surveys:dashboard_use_current_address"),
            HTTP_HOST="127.0.0.1:8010",
            follow=True,
        )
        self.assertContains(response, "IP LAN valide")

    def test_use_current_address_requires_post(self):
        response = self.client.get(
            reverse("surveys:dashboard_use_current_address"),
            HTTP_HOST="192.168.0.101:8011",
            follow=True,
        )
        self.assertEqual(response.status_code, 405)


class F023SyncLanSettingsCommandTests(TestCase):
    """Tests for management command sync_lan_settings."""

    def setUp(self):
        self._tmpdir = None
        import tempfile
        self._tmpdir = tempfile.mkdtemp()
        import os
        self._old_db_path = os.environ.get("DATABASE_PATH")
        os.environ["DATABASE_PATH"] = f"{self._tmpdir}/db.sqlite3"

    def tearDown(self):
        import os
        if self._old_db_path is not None:
            os.environ["DATABASE_PATH"] = self._old_db_path
        else:
            os.environ.pop("DATABASE_PATH", None)
        import shutil
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)

    def test_command_syncs_lan_host_and_port(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        call_command("sync_lan_settings", "--lan-host=192.168.0.101", "--lan-port=8011", stdout=out)
        output = out.getvalue()
        self.assertIn("LAN settings synced", output)
        self.assertIn("http://192.168.0.101:8011/", output)

    def test_command_rejects_public_ip(self):
        from django.core.management import call_command, CommandError
        from io import StringIO
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("sync_lan_settings", "--lan-host=8.8.8.8", "--lan-port=8011", stdout=out)

    def test_command_rejects_localhost(self):
        from django.core.management import call_command, CommandError
        from io import StringIO
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("sync_lan_settings", "--lan-host=127.0.0.1", "--lan-port=8011", stdout=out)

    def test_command_rejects_invalid_port(self):
        from django.core.management import call_command, CommandError
        from io import StringIO
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("sync_lan_settings", "--lan-host=192.168.0.101", "--lan-port=80", stdout=out)

    def test_command_rejects_invalid_ip_format(self):
        from django.core.management import call_command, CommandError
        from io import StringIO
        out = StringIO()
        with self.assertRaises(CommandError):
            call_command("sync_lan_settings", "--lan-host=not-an-ip", "--lan-port=8011", stdout=out)


class F023ScriptExistenceTests(TestCase):
    """Test Windows scripts exist and have expected content."""

    def test_taf_lan_sync_script_exists(self):
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "windows", "taf-lan-sync.ps1")
        self.assertTrue(os.path.exists(path), f"Missing: {path}")

    def _read_script(self, name):
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "windows", name)
        with open(path) as f:
            return f.read()

    def test_taf_lan_sync_uses_8011(self):
        content = self._read_script("taf-lan-sync.ps1")
        self.assertIn("8011", content)
        self.assertIn("127.0.0.1", content)
        self.assertNotIn("SECRET_KEY", content)

    def test_taf_lan_sync_no_secrets(self):
        content = self._read_script("taf-lan-sync.ps1")
        self.assertNotIn("SECRET_KEY", content)
        self.assertNotIn(".env", content)

    def test_taf_lan_install_auto_sync_exists(self):
        import os
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "windows", "taf-lan-install-auto-sync.ps1")
        self.assertTrue(os.path.exists(path), f"Missing: {path}")

    def test_taf_lan_install_mentions_scheduled_task(self):
        content = self._read_script("taf-lan-install-auto-sync.ps1")
        self.assertIn("Register-ScheduledTask", content) or self.assertIn("New-ScheduledTask", content)


class F023SecretSafetyTests(TestCase):
    """Tests that SECRET_KEY is never exposed."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser(
            username="secadmin", password="secadmin", email="sec@example.com"
        )
        self.client.login(username="secadmin", password="secadmin")

    def test_secret_key_not_in_dashboard_network(self):
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertNotContains(response, "SECRET_KEY")


class SeedModule5CommandTests(TestCase):
    def test_seed_module5_creates_expected_module_and_active_session(self):
        call_command("seed_module5")
        module = TrainingModule.objects.get(code="MODULE_5")
        session = TrainingSession.objects.get(session_code="M5-ANDO-001")
        self.assertEqual(module.title, "Module 5 - Email et outils de communication")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module5_is_idempotent(self):
        call_command("seed_module5")
        call_command("seed_module5")
        self.assertEqual(TrainingModule.objects.filter(code="MODULE_5").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M5-ANDO-001").count(), 1)

    def test_seed_module5_does_not_overwrite_existing_session_details(self):
        call_command("seed_module5")
        session = TrainingSession.objects.get(session_code="M5-ANDO-001")
        session.location = "Autre lieu"
        session.trainer_name = "Autre formateur"
        session.is_active = False
        session.save()
        call_command("seed_module5")
        session.refresh_from_db()
        self.assertEqual(session.location, "Autre lieu")
        self.assertEqual(session.trainer_name, "Autre formateur")
        self.assertFalse(session.is_active)

    def test_seed_module5_creates_accepting_responses_true(self):
        call_command("seed_module5")
        session = TrainingSession.objects.get(session_code="M5-ANDO-001")
        self.assertTrue(session.accepting_responses)


class Module5SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_5",
            title="Module 5 - Email et outils de communication",
            description="Comprendre les usages academiques de l'email.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M5-ANDO-001",
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
        return Module5Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_email_purpose="bien",
            auto_eval_write_email="un_peu",
            auto_eval_attach_file="tres_bien",
            todo_spotted_recipient=True,
            todo_written_clear_subject=True,
            todo_started_greeting=True,
            todo_written_short_message=True,
            todo_added_politeness=True,
            todo_signed_name=True,
            todo_checked_attachment=True,
            todo_reread_before_sending=True,
            quiz_q1="vrai",
            quiz_q2="vrai",
            quiz_q3="faux",
            quiz_q4="faux",
            quiz_q5="demande_information_devoir_mathematiques",
            quiz_q6="bonjour_monsieur_madame",
            quiz_q7_selected=list(Module5Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_who_writing_to="Professeur de mathematiques",
            practical_email_subject="Demande d'information sur le devoir",
            practical_email_message="Bonjour Monsieur, je voudrais des informations sur le devoir.",
            practical_needs_attachment="oui",
            practical_attachment_file="devoir.pdf",
            practical_best_tool="email",
            feedback_understood_today="J'ai compris comment ecrire un email.",
            feedback_still_difficult="",
            feedback_confidence_email="oui",
        )

    def test_duplicate_school_id_snapshot_is_blocked_for_same_session(self):
        self.make_submission(self.student)
        with self.assertRaises(IntegrityError):
            self.make_submission(self.other_student)

    def test_score_is_computed_on_save(self):
        submission = self.make_submission(self.student)
        self.assertEqual(submission.computed_score, 7)

    def test_score_zero_for_wrong_answers(self):
        submission = Module5Submission.objects.create(
            student=Student.objects.create(school_id_number="02", full_name="Test", class_level=Student.CLASS_LEVEL_SECONDE),
            session=self.session,
            school_id_number_snapshot="02",
            auto_eval_email_purpose="pas_encore",
            auto_eval_write_email="pas_encore",
            auto_eval_attach_file="pas_encore",
            quiz_q1="faux",
            quiz_q2="faux",
            quiz_q3="vrai",
            quiz_q4="vrai",
            quiz_q5="salut",
            quiz_q6="yo_prof",
            quiz_q7_selected=["mot_de_passe_compte"],
            practical_who_writing_to="Test",
            practical_email_subject="Test",
            practical_email_message="Test",
            practical_needs_attachment="non",
            practical_best_tool="tiktok",
            feedback_understood_today="Test",
            feedback_confidence_email="pas_encore",
        )
        self.assertEqual(submission.computed_score, 0)


class Module5FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_5",
            title="Module 5 - Email et outils de communication",
            description="Comprendre les usages academiques de l'email.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 18),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M5-ANDO-001",
            is_active=True,
        )
        self.module2 = TrainingModule.objects.create(code="MODULE_2", title="Module 2", description="Test")
        TrainingSession.objects.create(
            module=self.module2, date=date(2026, 6, 18),
            location="Lycee Andohalo", trainer_name="Formateur",
            session_code="M2-ANDO-001", is_active=True,
        )
        self.module3 = TrainingModule.objects.create(code="MODULE_3", title="Module 3", description="Test")
        TrainingSession.objects.create(
            module=self.module3, date=date(2026, 6, 18),
            location="Lycee Andohalo", trainer_name="Formateur",
            session_code="M3-ANDO-001", is_active=True,
        )
        self.module4 = TrainingModule.objects.create(code="MODULE_4", title="Module 4", description="Test")
        TrainingSession.objects.create(
            module=self.module4, date=date(2026, 6, 18),
            location="Lycee Andohalo", trainer_name="Formateur",
            session_code="M4-ANDO-001", is_active=True,
        )

    def valid_payload(self):
        return {
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_email_purpose": "bien",
            "auto_eval_write_email": "un_peu",
            "auto_eval_attach_file": "tres_bien",
            "todo_spotted_recipient": "on",
            "todo_written_clear_subject": "on",
            "todo_started_greeting": "on",
            "todo_written_short_message": "on",
            "todo_added_politeness": "on",
            "todo_signed_name": "on",
            "todo_checked_attachment": "on",
            "todo_reread_before_sending": "on",
            "quiz_q1": "vrai",
            "quiz_q2": "vrai",
            "quiz_q3": "faux",
            "quiz_q4": "faux",
            "quiz_q5": "demande_information_devoir_mathematiques",
            "quiz_q6": "bonjour_monsieur_madame",
            "quiz_q7_selected": list(Module5Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_who_writing_to": "Professeur de mathematiques",
            "practical_email_subject": "Demande d'information sur le devoir",
            "practical_email_message": "Bonjour Monsieur, je voudrais des informations.",
            "practical_needs_attachment": "oui",
            "practical_attachment_file": "devoir.pdf",
            "practical_best_tool": "email",
            "feedback_understood_today": "J'ai compris comment ecrire un email.",
            "feedback_still_difficult": "",
            "feedback_confidence_email": "oui",
        }

    def test_module_5_form_get(self):
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 5 - Email et outils de communication")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_5"), data=self.valid_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Module5Submission.objects.count(), 1)
        submission = Module5Submission.objects.get()
        self.assertEqual(submission.school_id_number_snapshot, "01")
        self.assertEqual(submission.computed_score, 7)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"
        response = self.client.post(reverse("surveys:module_5"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre exactement 2 chiffres")
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Module5Submission.objects.count(), 0)

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_5"), data=self.valid_payload())
        payload = self.valid_payload()
        payload["full_name"] = "Autre eleve"
        response = self.client.post(reverse("surveys:module_5"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Une réponse existe déjà pour ce numéro")
        self.assertEqual(Module5Submission.objects.count(), 1)

    def test_same_school_id_can_submit_all_modules_separately(self):
        m2_payload = {
            "school_id_number": "01", "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "auto_eval_internet_explained": "un_peu", "auto_eval_learning_usage": "parfois",
            "auto_eval_open_browser": "oui", "quiz_q1": "faux", "quiz_q2": "vrai",
            "quiz_q3": "vrai", "quiz_q4_selected": ["chercher_une_explication"],
            "quiz_q5": "cours_equation_seconde_exemple",
            "practical_search_text": "test", "practical_site_text": "",
            "practical_subject": "mathematiques",
            "feedback_understood_today": "test", "feedback_still_difficult": "",
            "feedback_confidence": "oui",
        }
        self.assertEqual(self.client.post(reverse("surveys:module_2"), data=m2_payload).status_code, 302)
        self.assertEqual(self.client.post(reverse("surveys:module_5"), data=self.valid_payload()).status_code, 302)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(Module5Submission.objects.count(), 1)

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_5"), data=self.valid_payload())
        submission = Module5Submission.objects.get()
        other_client = self.client_class()
        response = other_client.get(reverse("surveys:module_5_success", args=[submission.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_5"))

    def test_module_5_form_returns_503_when_no_active_session_exists(self):
        self.session.is_active = False
        self.session.save()
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Le formulaire n'est pas disponible maintenant.", status_code=503)

    def test_practical_email_message_saved(self):
        self.client.post(reverse("surveys:module_5"), data=self.valid_payload())
        submission = Module5Submission.objects.get()
        self.assertEqual(submission.practical_email_message, "Bonjour Monsieur, je voudrais des informations.")

    def test_todo_8_items(self):
        self.client.post(reverse("surveys:module_5"), data=self.valid_payload())
        submission = Module5Submission.objects.get()
        self.assertTrue(submission.todo_spotted_recipient)
        self.assertTrue(submission.todo_written_clear_subject)
        self.assertTrue(submission.todo_started_greeting)
        self.assertTrue(submission.todo_written_short_message)
        self.assertTrue(submission.todo_added_politeness)
        self.assertTrue(submission.todo_signed_name)
        self.assertTrue(submission.todo_checked_attachment)
        self.assertTrue(submission.todo_reread_before_sending)

    def test_quiz_score_max_7(self):
        self.client.post(reverse("surveys:module_5"), data=self.valid_payload())
        submission = Module5Submission.objects.get()
        self.assertEqual(submission.computed_score, 7)


class Module5PedagogyContentTests(TestCase):
    def setUp(self):
        call_command("seed_module5")

    def test_student_modules_shows_module_5(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 5 - Email et outils de communication")

    def test_student_module_5_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_5_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_5_detail_contains_email_content(self):
        response = self.client.get(reverse("surveys:student_module_5_detail"))
        self.assertContains(response, "Email")
        self.assertContains(response, "Objet")
        self.assertContains(response, "Pièce jointe")

    def test_student_module_5_detail_contains_5_lines_method(self):
        response = self.client.get(reverse("surveys:student_module_5_detail"))
        self.assertContains(response, "méthode en 5 lignes")

    def test_student_module_5_detail_contains_security(self):
        response = self.client.get(reverse("surveys:student_module_5_detail"))
        self.assertContains(response, "mot de passe")


class Module5DashboardAndCockpitTests(TestCase):
    def setUp(self):
        call_command("seed_module5")
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )

    def test_module_5_form_200(self):
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_module_5_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_5"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_module_5_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_5_csv"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_module_5_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_5"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Score moyen")
        self.assertContains(response, "Module 5")

    def test_csv_export_module_5_contains_submission_data(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_5_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("computed_score", response.content.decode())

    def test_csv_export_sanitizes_formula_like_cells(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        submission = Module5Submission.objects.create(
            student=Student.objects.create(
                school_id_number="99", full_name="=cmd", class_level="seconde",
            ),
            session=TrainingSession.objects.get(session_code="M5-ANDO-001"),
            school_id_number_snapshot="99",
            auto_eval_email_purpose="bien", auto_eval_write_email="bien",
            auto_eval_attach_file="bien",
            quiz_q1="vrai", quiz_q2="vrai", quiz_q3="faux", quiz_q4="faux",
            quiz_q5="demande_information_devoir_mathematiques",
            quiz_q6="bonjour_monsieur_madame",
            quiz_q7_selected=list(Module5Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_who_writing_to="Test", practical_email_subject="Test",
            practical_email_message="Test", practical_needs_attachment="non",
            practical_best_tool="email",
            feedback_understood_today="Test", feedback_confidence_email="oui",
        )
        response = self.client.get(reverse("surveys:export_module_5_csv"))
        content = response.content.decode()
        self.assertIn("'=cmd", content)

    def test_cockpit_shows_module_5_when_logged_in(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 5 - Email et outils de communication")
        self.assertContains(response, "Export CSV")


class Module5ClosedSubmissionTests(TestCase):
    def setUp(self):
        call_command("seed_module5")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        session = TrainingSession.objects.get(module__code="MODULE_5", is_active=True)
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])

    def test_module_5_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermées")

    def test_module_5_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_5"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_5_reopened_accepts_submission(self):
        session = TrainingSession.objects.get(module__code="MODULE_5", is_active=True)
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        payload = {
            "school_id_number": "99", "full_name": "Test Student",
            "class_level": "seconde", "group_name": "",
            "auto_eval_email_purpose": "bien", "auto_eval_write_email": "bien",
            "auto_eval_attach_file": "bien",
            "quiz_q1": "vrai", "quiz_q2": "vrai", "quiz_q3": "faux", "quiz_q4": "faux",
            "quiz_q5": "demande_information_devoir_mathematiques",
            "quiz_q6": "bonjour_monsieur_madame",
            "quiz_q7_selected": list(Module5Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_who_writing_to": "Prof", "practical_email_subject": "Info",
            "practical_email_message": "Test", "practical_needs_attachment": "non",
            "practical_best_tool": "email",
            "feedback_understood_today": "Ok", "feedback_confidence_email": "oui",
        }
        response = self.client.post(reverse("surveys:module_5"), data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Module5Submission.objects.filter(school_id_number_snapshot="99").exists())


class Module5ToggleResponsesTests(TestCase):
    def setUp(self):
        call_command("seed_module5")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        self.url = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_5"})

    def test_toggle_requires_login(self):
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_requires_staff(self):
        user = get_user_model().objects.create_user(username="regular", password="test")
        self.client.login(username="regular", password="test")
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 403))

    def test_toggle_closes_module_5(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_5", is_active=True)
        self.assertFalse(session.accepting_responses)

    def test_toggle_reopens_module_5(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url)
        self.client.post(self.url, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_5", is_active=True)
        self.assertTrue(session.accepting_responses)


class Module5AdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.superuser = User.objects.create_superuser(
            username="super", password="super", email="super@example.com",
        )
        self.client.login(username="super", password="super")

    def test_admin_module5submission_accessible(self):
        response = self.client.get(reverse("admin:surveys_module5submission_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_admin_no_secret_exposed(self):
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, "SECRET_KEY")


class Module5RegressionTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        call_command("seed_module5")

    def test_module_2_still_200(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)

    def test_module_3_still_200(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)

    def test_module_4_still_200(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)

    def test_student_modules_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Cockpit formateur")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "/admin/")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertIn(response.status_code, (302, 401, 403))


class SeedModule6CommandTests(TestCase):
    def test_seed_module6_creates_expected_module_and_active_session(self):
        call_command("seed_module6")
        module = TrainingModule.objects.get(code="MODULE_6")
        session = TrainingSession.objects.get(session_code="M6-ANDO-001")
        self.assertEqual(module.title, "Module 6 - Ressources educatives en ligne")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module6_is_idempotent(self):
        call_command("seed_module6")
        call_command("seed_module6")
        self.assertEqual(TrainingModule.objects.filter(code="MODULE_6").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M6-ANDO-001").count(), 1)

    def test_seed_module6_does_not_overwrite_existing_session_details(self):
        call_command("seed_module6")
        session = TrainingSession.objects.get(session_code="M6-ANDO-001")
        session.location = "Autre lieu"
        session.trainer_name = "Autre formateur"
        session.is_active = False
        session.save()
        call_command("seed_module6")
        session.refresh_from_db()
        self.assertEqual(session.location, "Autre lieu")
        self.assertEqual(session.trainer_name, "Autre formateur")
        self.assertFalse(session.is_active)

    def test_seed_module6_creates_accepting_responses_true(self):
        call_command("seed_module6")
        session = TrainingSession.objects.get(session_code="M6-ANDO-001")
        self.assertTrue(session.accepting_responses)


class Module6SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_6",
            title="Module 6 - Ressources éducatives en ligne",
            description="Savoir trouver, choisir et utiliser des ressources éducatives en ligne.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 23),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M6-ANDO-001",
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
        return Module6Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_find_resource="bien",
            auto_eval_choose_resource="tres_bien",
            auto_eval_keep_link="un_peu",
            todo_chose_subject=True,
            todo_searched_resource=True,
            todo_opened_video_pdf_exercise=True,
            todo_checked_level=True,
            todo_noted_resource_title=True,
            todo_noted_link_or_site=True,
            todo_written_what_learned=True,
            todo_kept_for_later=True,
            quiz_q1="vrai",
            quiz_q2="vrai",
            quiz_q3="faux",
            quiz_q4="exercice_corrige",
            quiz_q5="photosynthese_cours_lycee_pdf",
            quiz_q6_selected=list(Module6Submission.QUIZ_Q6_CORRECT_ANSWERS),
            quiz_q7_selected=list(Module6Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_subject="mathematiques",
            practical_what_to_revise="Équations du second degré",
            practical_resource_type="video",
            practical_resource_name_or_link="YouTube - Maths et Tiques",
            practical_adapted_level="oui",
            practical_what_learned="J'ai compris comment résoudre des équations.",
            feedback_understood_today="J'ai compris comment trouver des ressources en ligne.",
            feedback_still_difficult="",
            feedback_confidence_resources="oui",
        )

    def test_duplicate_school_id_snapshot_is_blocked_for_same_session(self):
        self.make_submission(self.student)
        with self.assertRaises(IntegrityError):
            self.make_submission(self.other_student)

    def test_score_is_computed_on_save(self):
        submission = self.make_submission(self.student)
        self.assertEqual(submission.computed_score, 7)

    def test_score_zero_for_wrong_answers(self):
        submission = Module6Submission.objects.create(
            student=Student.objects.create(school_id_number="02", full_name="Test", class_level=Student.CLASS_LEVEL_SECONDE),
            session=self.session,
            school_id_number_snapshot="02",
            auto_eval_find_resource="pas_encore",
            auto_eval_choose_resource="pas_encore",
            auto_eval_keep_link="pas_encore",
            quiz_q1="faux",
            quiz_q2="faux",
            quiz_q3="vrai",
            quiz_q4="publicite",
            quiz_q5="video_drole",
            quiz_q6_selected=["demande_mot_de_passe"],
            quiz_q7_selected=["partager_mot_de_passe"],
            practical_subject="francais",
            practical_what_to_revise="Test",
            practical_resource_type="autre",
            practical_resource_name_or_link="Test",
            practical_adapted_level="non",
            practical_what_learned="Test",
            feedback_understood_today="Test",
            feedback_confidence_resources="pas_encore",
        )
        self.assertEqual(submission.computed_score, 0)


class Module6FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_6",
            title="Module 6 - Ressources éducatives en ligne",
            description="Savoir trouver, choisir et utiliser des ressources éducatives en ligne.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 23),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M6-ANDO-001",
            is_active=True,
        )

    def valid_payload(self):
        return {
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_find_resource": "bien",
            "auto_eval_choose_resource": "tres_bien",
            "auto_eval_keep_link": "un_peu",
            "todo_chose_subject": "on",
            "todo_searched_resource": "on",
            "todo_opened_video_pdf_exercise": "on",
            "todo_checked_level": "on",
            "todo_noted_resource_title": "on",
            "todo_noted_link_or_site": "on",
            "todo_written_what_learned": "on",
            "todo_kept_for_later": "on",
            "quiz_q1": "vrai",
            "quiz_q2": "vrai",
            "quiz_q3": "faux",
            "quiz_q4": "exercice_corrige",
            "quiz_q5": "photosynthese_cours_lycee_pdf",
            "quiz_q6_selected": list(Module6Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7_selected": list(Module6Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_subject": "mathematiques",
            "practical_what_to_revise": "Équations du second degré",
            "practical_resource_type": "video",
            "practical_resource_name_or_link": "YouTube - Maths et Tiques",
            "practical_adapted_level": "oui",
            "practical_what_learned": "J'ai compris comment résoudre des équations.",
            "feedback_understood_today": "J'ai compris comment trouver des ressources en ligne.",
            "feedback_still_difficult": "",
            "feedback_confidence_resources": "oui",
        }

    def test_module_6_form_get(self):
        response = self.client.get(reverse("surveys:module_6"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 6 - Ressources educatives en ligne")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_6"), data=self.valid_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(Module6Submission.objects.count(), 1)
        submission = Module6Submission.objects.get()
        self.assertEqual(submission.school_id_number_snapshot, "01")
        self.assertEqual(submission.computed_score, 7)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"
        response = self.client.post(reverse("surveys:module_6"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Entre exactement 2 chiffres")
        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(Module6Submission.objects.count(), 0)

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_6"), data=self.valid_payload())
        payload = self.valid_payload()
        payload["full_name"] = "Autre eleve"
        response = self.client.post(reverse("surveys:module_6"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Une réponse existe déjà pour ce numéro")
        self.assertEqual(Module6Submission.objects.count(), 1)

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_6"), data=self.valid_payload())
        submission = Module6Submission.objects.get()
        other_client = self.client_class()
        response = other_client.get(reverse("surveys:module_6_success", args=[submission.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_6"))

    def test_module_6_form_returns_503_when_no_active_session_exists(self):
        self.session.is_active = False
        self.session.save()
        response = self.client.get(reverse("surveys:module_6"))
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Le formulaire n'est pas disponible maintenant.", status_code=503)

    def test_practical_what_learned_saved(self):
        self.client.post(reverse("surveys:module_6"), data=self.valid_payload())
        submission = Module6Submission.objects.get()
        self.assertEqual(submission.practical_what_learned, "J'ai compris comment résoudre des équations.")

    def test_todo_8_items(self):
        self.client.post(reverse("surveys:module_6"), data=self.valid_payload())
        submission = Module6Submission.objects.get()
        self.assertTrue(submission.todo_chose_subject)
        self.assertTrue(submission.todo_searched_resource)
        self.assertTrue(submission.todo_opened_video_pdf_exercise)
        self.assertTrue(submission.todo_checked_level)
        self.assertTrue(submission.todo_noted_resource_title)
        self.assertTrue(submission.todo_noted_link_or_site)
        self.assertTrue(submission.todo_written_what_learned)
        self.assertTrue(submission.todo_kept_for_later)

    def test_quiz_score_max_7(self):
        self.client.post(reverse("surveys:module_6"), data=self.valid_payload())
        submission = Module6Submission.objects.get()
        self.assertEqual(submission.computed_score, 7)


class Module6PedagogyContentTests(TestCase):
    def setUp(self):
        call_command("seed_module6")

    def test_student_modules_shows_module_6(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 6 - Ressources educatives en ligne")

    def test_student_module_6_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_6_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_6_detail_contains_resource_content(self):
        response = self.client.get(reverse("surveys:student_module_6_detail"))
        self.assertContains(response, "ressource educative")
        self.assertContains(response, "niveau")
        self.assertContains(response, "lien")

    def test_student_module_6_detail_contains_6_steps_method(self):
        response = self.client.get(reverse("surveys:student_module_6_detail"))
        self.assertContains(response, "etapes")


class Module6DashboardAndCockpitTests(TestCase):
    def setUp(self):
        call_command("seed_module6")
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )

    def test_module_6_form_200(self):
        response = self.client.get(reverse("surveys:module_6"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_module_6_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_6"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_module_6_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_6_csv"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_module_6_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_6"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Score moyen")
        self.assertContains(response, "Module 6")

    def test_csv_export_module_6_contains_submission_data(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_6_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("computed_score", response.content.decode())

    def test_csv_export_sanitizes_formula_like_cells(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        submission = Module6Submission.objects.create(
            student=Student.objects.create(
                school_id_number="99", full_name="=cmd", class_level="seconde",
            ),
            session=TrainingSession.objects.get(session_code="M6-ANDO-001"),
            school_id_number_snapshot="99",
            auto_eval_find_resource="bien",
            auto_eval_choose_resource="bien",
            auto_eval_keep_link="bien",
            quiz_q1="vrai", quiz_q2="vrai", quiz_q3="faux",
            quiz_q4="exercice_corrige", quiz_q5="photosynthese_cours_lycee_pdf",
            quiz_q6_selected=list(Module6Submission.QUIZ_Q6_CORRECT_ANSWERS),
            quiz_q7_selected=list(Module6Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_subject="mathematiques",
            practical_what_to_revise="Test",
            practical_resource_type="video",
            practical_resource_name_or_link="Test",
            practical_adapted_level="oui",
            practical_what_learned="Test",
            feedback_understood_today="Test",
            feedback_confidence_resources="oui",
        )
        response = self.client.get(reverse("surveys:export_module_6_csv"))
        content = response.content.decode()
        self.assertIn("'=cmd", content)

    def test_cockpit_shows_module_6_when_logged_in(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 6 - Ressources educatives en ligne")
        self.assertContains(response, "Export CSV")


class Module6ClosedSubmissionTests(TestCase):
    def setUp(self):
        call_command("seed_module6")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        session = TrainingSession.objects.get(module__code="MODULE_6", is_active=True)
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])

    def test_module_6_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_6"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermees")

    def test_module_6_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_6"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_6_reopened_accepts_submission(self):
        session = TrainingSession.objects.get(module__code="MODULE_6", is_active=True)
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        payload = {
            "school_id_number": "99", "full_name": "Test Student",
            "class_level": "seconde", "group_name": "",
            "auto_eval_find_resource": "bien",
            "auto_eval_choose_resource": "bien",
            "auto_eval_keep_link": "bien",
            "quiz_q1": "vrai", "quiz_q2": "vrai", "quiz_q3": "faux",
            "quiz_q4": "exercice_corrige", "quiz_q5": "photosynthese_cours_lycee_pdf",
            "quiz_q6_selected": list(Module6Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7_selected": list(Module6Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_subject": "mathematiques",
            "practical_what_to_revise": "Test",
            "practical_resource_type": "video",
            "practical_resource_name_or_link": "Test",
            "practical_adapted_level": "oui",
            "practical_what_learned": "Test",
            "feedback_understood_today": "Test",
            "feedback_confidence_resources": "oui",
        }
        response = self.client.post(reverse("surveys:module_6"), data=payload)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Module6Submission.objects.filter(school_id_number_snapshot="99").exists())


class Module6ToggleResponsesTests(TestCase):
    def setUp(self):
        call_command("seed_module6")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        self.url = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_6"})

    def test_toggle_requires_login(self):
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_requires_staff(self):
        user = get_user_model().objects.create_user(username="regular", password="test")
        self.client.login(username="regular", password="test")
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 403))

    def test_toggle_closes_module_6(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_6", is_active=True)
        self.assertFalse(session.accepting_responses)

    def test_toggle_reopens_module_6(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url)
        self.client.post(self.url, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_6", is_active=True)
        self.assertTrue(session.accepting_responses)


class Module6AdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.superuser = User.objects.create_superuser(
            username="super", password="super", email="super@example.com",
        )
        self.client.login(username="super", password="super")

    def test_admin_module6submission_accessible(self):
        response = self.client.get(reverse("admin:surveys_module6submission_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_admin_no_secret_exposed(self):
        response = self.client.get(reverse("admin:index"))
        self.assertNotContains(response, "SECRET_KEY")


class Module6RegressionTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        call_command("seed_module5")
        call_command("seed_module6")

    def test_module_2_still_200(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)

    def test_module_3_still_200(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)

    def test_module_4_still_200(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)

    def test_module_5_still_200(self):
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 200)

    def test_student_modules_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Cockpit formateur")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "/admin/")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertIn(response.status_code, (302, 401, 403))


class SeedModule7CommandTests(TestCase):
    def test_seed_module7_creates_expected_module_and_active_session(self):
        call_command("seed_module7")
        module = TrainingModule.objects.get(code="MODULE_7")
        session = TrainingSession.objects.get(session_code="M7-ANDO-001")
        self.assertEqual(module.title, "Module 7 - Securite en ligne")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module7_is_idempotent(self):
        call_command("seed_module7")
        call_command("seed_module7")
        self.assertEqual(TrainingModule.objects.filter(code="MODULE_7").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M7-ANDO-001").count(), 1)

    def test_seed_module7_does_not_overwrite_existing_session_details(self):
        call_command("seed_module7")
        session = TrainingSession.objects.get(session_code="M7-ANDO-001")
        session.location = "Autre lieu modifie"
        session.save(update_fields=["location"])
        call_command("seed_module7")
        session.refresh_from_db()
        self.assertEqual(session.location, "Autre lieu modifie")

    def test_seed_module7_creates_accepting_responses_true(self):
        call_command("seed_module7")
        session = TrainingSession.objects.get(session_code="M7-ANDO-001")
        self.assertTrue(session.accepting_responses)


class Module7SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_7",
            title="Module 7 - Securite en ligne",
            description="Savoir se proteger en ligne.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 23),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M7-ANDO-001",
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
        return Module7Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_password="oui",
            auto_eval_suspect="pas_encore",
            auto_eval_personal_info="oui_facilement",
            todo_identified_weak_password=True,
            todo_written_password_rules=True,
            todo_understood_no_code_sharing=True,
            todo_observed_suspect_message=True,
            todo_spotted_danger_signs=True,
            todo_applied_stop_method=True,
            todo_listed_personal_info=True,
            todo_ask_help=True,
            quiz_q1="faux",
            quiz_q2="vrai",
            quiz_q3="vrai",
            quiz_q4="verifier_demander_aide",
            quiz_q5_selected=list(Module7Submission.QUIZ_Q5_CORRECT_ANSWERS),
            quiz_q6_selected=list(Module7Submission.QUIZ_Q6_CORRECT_ANSWERS),
            quiz_q7_selected=list(Module7Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_situation="lien_suspect",
            practical_describe="Message avec un lien bizarre.",
            practical_danger_signs="Lien suspect et urgence.",
            practical_protect_selected=["mot_de_passe", "adresse"],
            practical_good_reaction_selected=["ne_pas_cliquer", "demander_aide"],
            practical_explain="Il ne faut pas cliquer et demander de l'aide.",
            feedback_understood_today="J'ai compris comment me proteger.",
            feedback_still_difficult="",
            feedback_confidence_security="oui",
        )

    def test_duplicate_school_id_snapshot_is_blocked_for_same_session(self):
        self.make_submission(self.student)
        with self.assertRaises(IntegrityError):
            self.make_submission(self.other_student)

    def test_score_is_computed_on_save(self):
        sub = self.make_submission(self.student)
        self.assertEqual(sub.computed_score, 7)

    def test_score_zero_for_wrong_answers(self):
        sub = Module7Submission.objects.create(
            student=self.student,
            session=self.session,
            school_id_number_snapshot=self.student.school_id_number,
            auto_eval_password="pas_encore",
            auto_eval_suspect="pas_encore",
            auto_eval_personal_info="pas_encore",
            quiz_q1="vrai",
            quiz_q2="faux",
            quiz_q3="faux",
            quiz_q4="cliquer_tout_de_suite",
            quiz_q5_selected=["message_prof"],
            quiz_q6_selected=["lecon_publique"],
            quiz_q7_selected=["garder_secret", "donner_code"],
            practical_situation="autre",
            practical_describe="Test",
            practical_danger_signs="Test",
            practical_protect_selected=[],
            practical_good_reaction_selected=["partager_vite"],
            practical_explain="Test",
            feedback_understood_today="Test",
            feedback_confidence_security="pas_encore",
        )
        self.assertEqual(sub.computed_score, 0)


class Module7FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_7",
            title="Module 7 - Securite en ligne",
            description="Savoir se proteger en ligne.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 23),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M7-ANDO-001",
            is_active=True,
        )

    def valid_payload(self):
        return {
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_password": "oui",
            "auto_eval_suspect": "pas_encore",
            "auto_eval_personal_info": "oui_facilement",
            "todo_identified_weak_password": "on",
            "todo_written_password_rules": "on",
            "todo_understood_no_code_sharing": "on",
            "todo_observed_suspect_message": "on",
            "todo_spotted_danger_signs": "on",
            "todo_applied_stop_method": "on",
            "todo_listed_personal_info": "on",
            "todo_ask_help": "on",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4": "verifier_demander_aide",
            "quiz_q5_selected": list(Module7Submission.QUIZ_Q5_CORRECT_ANSWERS),
            "quiz_q6_selected": list(Module7Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7_selected": list(Module7Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_situation": "lien_suspect",
            "practical_describe": "Message avec un lien bizarre.",
            "practical_danger_signs": "Lien suspect et urgence.",
            "practical_protect_selected": ["mot_de_passe", "adresse"],
            "practical_good_reaction_selected": ["ne_pas_cliquer", "demander_aide"],
            "practical_explain": "Il ne faut pas cliquer et demander de l'aide.",
            "feedback_understood_today": "J'ai compris comment me proteger.",
            "feedback_still_difficult": "",
            "feedback_confidence_security": "oui",
        }

    def test_module_7_form_get(self):
        response = self.client.get(reverse("surveys:module_7"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 7")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_7"), data=self.valid_payload(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merci")
        self.assertEqual(Module7Submission.objects.count(), 1)
        self.assertEqual(Student.objects.count(), 1)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"
        response = self.client.post(reverse("surveys:module_7"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 chiffres")

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_7"), data=self.valid_payload())
        response = self.client.post(reverse("surveys:module_7"), data=self.valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "déjà")

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_7"), data=self.valid_payload())
        submission = Module7Submission.objects.get()
        other_client = self.client_class()
        response = other_client.get(reverse("surveys:module_7_success", args=[submission.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_7"))

    def test_module_7_form_returns_200_when_responses_closed(self):
        self.session.accepting_responses = False
        self.session.save(update_fields=["accepting_responses"])
        response = self.client.get(reverse("surveys:module_7"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermees")

    def test_practical_explain_saved(self):
        self.client.post(reverse("surveys:module_7"), data=self.valid_payload())
        sub = Module7Submission.objects.first()
        self.assertEqual(sub.practical_explain, "Il ne faut pas cliquer et demander de l'aide.")

    def test_todo_8_items(self):
        self.client.post(reverse("surveys:module_7"), data=self.valid_payload())
        sub = Module7Submission.objects.first()
        for field in [
            "todo_identified_weak_password",
            "todo_written_password_rules",
            "todo_understood_no_code_sharing",
            "todo_observed_suspect_message",
            "todo_spotted_danger_signs",
            "todo_applied_stop_method",
            "todo_listed_personal_info",
            "todo_ask_help",
        ]:
            self.assertTrue(getattr(sub, field), f"{field} should be True")

    def test_quiz_score_max_7(self):
        self.client.post(reverse("surveys:module_7"), data=self.valid_payload())
        sub = Module7Submission.objects.first()
        self.assertEqual(sub.computed_score, 7)


class Module7PedagogyContentTests(TestCase):
    def setUp(self):
        call_command("seed_module7")

    def test_student_modules_shows_module_7(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 7 - Securite en ligne")

    def test_student_module_7_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_7_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_7_detail_contains_title(self):
        response = self.client.get(reverse("surveys:student_module_7_detail"))
        self.assertContains(response, "Module 7 - Securite en ligne")

    def test_student_module_7_detail_contains_form_link(self):
        response = self.client.get(reverse("surveys:student_module_7_detail"))
        self.assertContains(response, "Commencer le questionnaire")


class Module7DashboardAndCockpitTests(TestCase):
    def setUp(self):
        call_command("seed_module7")
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )

    def test_module_7_form_200(self):
        response = self.client.get(reverse("surveys:module_7"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_module_7_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_7"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_module_7_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_7_csv"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_module_7_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_7"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 7")

    def test_csv_export_module_7_contains_submission_data(self):
        self.client.post(reverse("surveys:module_7"), data={
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_password": "oui",
            "auto_eval_suspect": "pas_encore",
            "auto_eval_personal_info": "oui_facilement",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4": "verifier_demander_aide",
            "quiz_q5_selected": list(Module7Submission.QUIZ_Q5_CORRECT_ANSWERS),
            "quiz_q6_selected": list(Module7Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7_selected": list(Module7Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_situation": "lien_suspect",
            "practical_describe": "Message suspect.",
            "practical_danger_signs": "Urgence et lien.",
            "practical_protect_selected": ["mot_de_passe"],
            "practical_good_reaction_selected": ["ne_pas_cliquer"],
            "practical_explain": "Ne pas cliquer.",
            "feedback_understood_today": "Compris.",
            "feedback_still_difficult": "",
            "feedback_confidence_security": "oui",
        })
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_7_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rakoto Aina")

    def test_csv_export_sanitizes_formula_like_cells(self):
        self.client.post(reverse("surveys:module_7"), data={
            "school_id_number": "02",
            "full_name": "=SUM(1,1)",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_password": "oui",
            "auto_eval_suspect": "pas_encore",
            "auto_eval_personal_info": "oui_facilement",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4": "verifier_demander_aide",
            "quiz_q5_selected": list(Module7Submission.QUIZ_Q5_CORRECT_ANSWERS),
            "quiz_q6_selected": list(Module7Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7_selected": list(Module7Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_situation": "lien_suspect",
            "practical_describe": "Test",
            "practical_danger_signs": "Test",
            "practical_protect_selected": ["mot_de_passe"],
            "practical_good_reaction_selected": ["ne_pas_cliquer"],
            "practical_explain": "Test",
            "feedback_understood_today": "Test",
            "feedback_still_difficult": "",
            "feedback_confidence_security": "oui",
        })
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_7_csv"))
        content = response.content.decode()
        self.assertIn("'=SUM(1,1)", content)

    def test_cockpit_shows_module_7_when_logged_in(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 7 - Securite en ligne")


class Module7ClosedSubmissionTests(TestCase):
    def setUp(self):
        call_command("seed_module7")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        session = TrainingSession.objects.get(module__code="MODULE_7", is_active=True)
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])

    def test_module_7_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_7"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermees")

    def test_module_7_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_7"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_7_reopened_accepts_submission(self):
        session = TrainingSession.objects.get(module__code="MODULE_7", is_active=True)
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        response = self.client.post(reverse("surveys:module_7"), data={
            "school_id_number": "01",
            "full_name": "Rakoto",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_password": "oui",
            "auto_eval_suspect": "pas_encore",
            "auto_eval_personal_info": "oui_facilement",
            "quiz_q1": "faux",
            "quiz_q2": "vrai",
            "quiz_q3": "vrai",
            "quiz_q4": "verifier_demander_aide",
            "quiz_q5_selected": list(Module7Submission.QUIZ_Q5_CORRECT_ANSWERS),
            "quiz_q6_selected": list(Module7Submission.QUIZ_Q6_CORRECT_ANSWERS),
            "quiz_q7_selected": list(Module7Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_situation": "lien_suspect",
            "practical_describe": "Test",
            "practical_danger_signs": "Test",
            "practical_protect_selected": ["mot_de_passe"],
            "practical_good_reaction_selected": ["ne_pas_cliquer"],
            "practical_explain": "Test",
            "feedback_understood_today": "Test",
            "feedback_still_difficult": "",
            "feedback_confidence_security": "oui",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merci")


class Module7ToggleResponsesTests(TestCase):
    def setUp(self):
        call_command("seed_module7")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        self.url = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_7"})

    def test_toggle_requires_login(self):
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_requires_staff(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_closes_module_7(self):
        self.client.login(username="staff", password="secret")
        response = self.client.post(self.url, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_7", is_active=True)
        self.assertFalse(session.accepting_responses)

    def test_toggle_reopens_module_7(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url)
        self.client.post(self.url)
        session = TrainingSession.objects.get(module__code="MODULE_7", is_active=True)
        self.assertTrue(session.accepting_responses)


class Module7AdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.superuser = User.objects.create_superuser(
            username="super", password="super", email="super@example.com",
        )
        self.client.login(username="super", password="super")

    def test_admin_module7submission_accessible(self):
        response = self.client.get(reverse("admin:surveys_module7submission_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_admin_no_secret_exposed(self):
        response = self.client.get(reverse("admin:surveys_module7submission_changelist"))
        self.assertNotContains(response, "SECRET_KEY")


class Module7RegressionTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        call_command("seed_module5")
        call_command("seed_module6")
        call_command("seed_module7")

    def test_module_2_still_200(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)

    def test_module_3_still_200(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)

    def test_module_4_still_200(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)

    def test_module_5_still_200(self):
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 200)

    def test_module_6_still_200(self):
        response = self.client.get(reverse("surveys:module_6"))
        self.assertEqual(response.status_code, 200)

    def test_module_7_still_200(self):
        response = self.client.get(reverse("surveys:module_7"))
        self.assertEqual(response.status_code, 200)

    def test_student_modules_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Cockpit formateur")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "/admin/")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertIn(response.status_code, (302, 401, 403))


class InfrastructureConfigTests(TestCase):
    """Tests pour la configuration d'infrastructure F029 (PostgreSQL, Gunicorn, presence)."""

    @override_settings(DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}})
    def test_sqlite_fallback_works(self):
        self.assertEqual(
            self.client.get(reverse("surveys:student_modules")).status_code,
            200,
        )

    def test_psycopg_in_requirements(self):
        req_path = Path(__file__).resolve().parent.parent / "requirements.txt"
        content = req_path.read_text()
        self.assertIn("psycopg", content)

    def test_gunicorn_env_vars_have_defaults(self):
        concurrency = os.getenv("WEB_CONCURRENCY", "2")
        threads = os.getenv("WEB_THREADS", "4")
        timeout = os.getenv("GUNICORN_TIMEOUT", "60")
        self.assertTrue(int(concurrency) >= 1)
        self.assertTrue(int(threads) >= 1)
        self.assertTrue(int(timeout) >= 10)

    def test_presence_heartbeat_interval_is_30s(self):
        heartbeat_path = Path(__file__).resolve().parent.parent / "templates" / "surveys" / "partials" / "presence_heartbeat.html"
        content = heartbeat_path.read_text()
        self.assertIn("setInterval(heartbeat, 30000)", content)

    def test_dashboard_polling_interval_is_15s(self):
        dashboard_path = Path(__file__).resolve().parent.parent / "templates" / "surveys" / "dashboard_home.html"
        content = dashboard_path.read_text()
        self.assertIn("setInterval(poll, 15000)", content)

    def test_docker_compose_has_postgres_service(self):
        compose_path = Path(__file__).resolve().parent.parent / "docker-compose.yml"
        content = compose_path.read_text()
        self.assertIn("db:", content)
        self.assertIn("postgres:16-alpine", content)
        self.assertIn("taf_local_forms_pgdata", content)

    def test_docker_compose_has_no_down_v(self):
        compose_path = Path(__file__).resolve().parent.parent / "docker-compose.yml"
        content = compose_path.read_text()
        self.assertNotIn("down -v", content)

    def test_docker_file_has_gunicorn_env_vars(self):
        dockerfile_path = Path(__file__).resolve().parent.parent / "Dockerfile"
        content = dockerfile_path.read_text()
        self.assertIn("WEB_CONCURRENCY", content)
        self.assertIn("WEB_THREADS", content)
        self.assertIn("GUNICORN_TIMEOUT", content)

    def test_backup_script_exists(self):
        backup_path = Path(__file__).resolve().parent.parent / "scripts" / "dev" / "taf-db-backup"
        self.assertTrue(backup_path.exists(), "taf-db-backup script manquant")
        self.assertTrue(backup_path.stat().st_mode & 0o111, "taf-db-backup doit etre executable")

    def test_load_smoke_script_exists(self):
        smoke_path = Path(__file__).resolve().parent.parent / "scripts" / "dev" / "taf-load-smoke"
        self.assertTrue(smoke_path.exists(), "taf-load-smoke script manquant")
        self.assertTrue(smoke_path.stat().st_mode & 0o111, "taf-load-smoke doit etre executable")

    def test_load_smoke_script_no_post(self):
        smoke_path = Path(__file__).resolve().parent.parent / "scripts" / "dev" / "taf-load-smoke"
        content = smoke_path.read_text()
        self.assertNotIn("POST", content, "taf-load-smoke ne doit pas contenir de POST")

    def test_windows_lan_scripts_no_secrets(self):
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts" / "windows"
        for ps1 in scripts_dir.glob("*.ps1"):
            content = ps1.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("SECRET_KEY", content, f"{ps1.name} ne doit pas contenir SECRET_KEY")

    def test_windows_lan_scripts_no_down_v(self):
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts" / "windows"
        for ps1 in scripts_dir.glob("*.ps1"):
            content = ps1.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("down -v", content, f"{ps1.name} ne doit pas contenir down -v")


class F030NetworkControlTests(TestCase):
    """Tests for the LAN Control Center (F030)."""

    def setUp(self):
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(username="ctrlstaff", password="secret", is_staff=True)
        self.non_staff = User.objects.create_user(username="ctrluser", password="secret")
        self.url = reverse("surveys:dashboard_network_control")

    def test_page_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_page_requires_staff(self):
        self.client.login(username="ctrluser", password="secret")
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 403))

    def test_page_renders_for_staff(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Controle reseau local")
        self.assertContains(response, "127.0.0.1:8019")
        self.assertContains(response, "Configurer et rendre accessible")
        self.assertContains(response, "Redémarrer l'application")
        self.assertContains(response, "Tester l'URL")
        self.assertContains(response, "Copier l'URL")
        self.assertContains(response, "Désactiver l'accès LAN")

    @override_settings(ALLOWED_HOSTS=["*"])
    def test_shows_helper_not_found_when_not_localhost(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url, HTTP_HOST="192.168.0.100")
        self.assertContains(response, "n'écoute que sur")
        self.assertContains(response, "127.0.0.1")

    def test_shows_helper_endpoint_in_page(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "http://127.0.0.1:8019")
        self.assertContains(response, "taf-lan-helper-start.ps1")
        self.assertContains(response, "taf-lan-sync.ps1")
        self.assertContains(response, "taf-lan-show-status.ps1")

    def test_no_helper_link_in_student_space(self):
        self.client.logout()
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Controle reseau local")
        self.assertNotContains(response, "network-control")

    def test_helper_scripts_exist(self):
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts" / "windows"
        self.assertTrue((scripts_dir / "taf-lan-helper.ps1").exists())
        self.assertTrue((scripts_dir / "taf-lan-helper-start.ps1").exists())
        self.assertTrue((scripts_dir / "taf-lan-helper-stop.ps1").exists())

    def test_helper_script_listens_on_127_0_0_1(self):
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("127.0.0.1", content)

    def test_helper_script_does_not_listen_on_0_0_0_0(self):
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertNotIn("0.0.0.0:8019", content)

    def test_helper_script_has_allowed_endpoints(self):
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        for endpoint in ("/status", "/sync", "/restart-app", "/test", "/disable"):
            self.assertIn(endpoint, content, f"Endpoint manquant : {endpoint}")

    def test_helper_scripts_no_secrets(self):
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts" / "windows"
        for ps1 in scripts_dir.glob("taf-lan-helper*"):
            content = ps1.read_text(encoding="utf-8", errors="replace")
            self.assertNotIn("SECRET_KEY", content, f"{ps1.name} ne doit pas contenir SECRET_KEY")
            self.assertNotIn(".env", content, f"{ps1.name} ne doit pas contenir .env")
            self.assertNotIn("docker compose down -v", content, f"{ps1.name} ne doit pas contenir down -v")
            self.assertNotIn("docker system prune", content, f"{ps1.name} ne doit pas contenir prune")

    def test_helper_script_has_cors_headers(self):
        """Helper doit envoyer des en-tetes CORS."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("Access-Control-Allow-Origin", content)
        self.assertIn("Access-Control-Allow-Methods", content)
        self.assertIn("Access-Control-Allow-Headers", content)
        self.assertIn("Add-CorsHeaders", content)

    def test_helper_script_has_options_handler(self):
        """Helper doit gerer les requetes OPTIONS avec un 204."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("OPTIONS", content)
        self.assertIn("204", content)

    def test_helper_script_has_cors_allowlist(self):
        """Helper ne doit autoriser que localhost:8010 et 127.0.0.1:8010."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("http://localhost:8010", content)
        self.assertIn("http://127.0.0.1:8010", content)

    def test_helper_script_no_wildcard_cors(self):
        """Helper ne doit pas utiliser le wildcard '*' pour CORS."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        cors_lines = [l for l in content.splitlines() if "Access-Control" in l or "CORS" in l]
        for line in cors_lines:
            self.assertNotIn("*", line, f"Wildcard CORS interdit: {line.strip()}")

    def test_helper_script_has_vary_origin(self):
        """Helper doit inclure Vary: Origin."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("Vary", content)
        self.assertIn("Origin", content)

    def test_helper_script_no_forbidden_docker_commands(self):
        """Helper ne doit pas contenir de commandes destructives Docker."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertNotIn("down -v", content)
        self.assertNotIn("prune --volumes", content)
        self.assertNotIn("system prune", content)

    def test_page_shows_helper_not_found_on_load(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "Helper LAN non disponible")
        self.assertContains(response, "taf-lan-helper-start.ps1")

    def test_page_has_abort_controller_in_js(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "AbortController")
        self.assertContains(response, "abort")

    def test_page_has_timeout_in_js(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "8000")

    def test_page_buttons_have_click_handlers(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "addEventListener('click'")
        for btn_id in ("btn-check-status", "btn-sync", "btn-restart", "btn-test", "btn-copy-url", "btn-disable"):
            self.assertContains(response, btn_id)

    def test_page_buttons_set_loading_state(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "setButtonLoading")
        self.assertContains(response, "En cours...")

    def test_page_copies_student_url(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "navigator.clipboard")
        self.assertContains(response, "execCommand('copy')")

    def test_page_disable_has_confirm(self):
        self.client.login(username="ctrlstaff", password="secret")
        response = self.client.get(self.url)
        self.assertContains(response, "confirm(")
        self.assertContains(response, "Desactiver")

    # ---- F030B: LAN Helper reliability ----

    def test_helper_script_has_output_stream_close(self):
        """Helper doit fermer OutputStream apres chaque reponse."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("OutputStream.Close()", content)
        self.assertIn("OutputStream.Close()", content)

    def test_helper_script_has_try_catch(self):
        """Helper doit avoir une gestion try/catch globale et par requete."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("try {", content)
        self.assertIn("catch {", content)
        self.assertIn("finally {", content)

    def test_helper_script_has_logs(self):
        """Helper doit ecrire des logs dans logs/windows/."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("taf-lan-helper.log", content)
        self.assertIn("Write-Log", content)

    def test_helper_script_has_pid_file(self):
        """Helper doit ecrire un fichier PID."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("taf-lan-helper.pid", content)
        self.assertIn("| Out-File -FilePath", content)

    def test_helper_script_status_returns_required_fields(self):
        """La fonction Get-Status doit retourner les champs obligatoires."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("helper_pid", content)
        self.assertIn("timestamp", content)
        self.assertIn("version", content)
        self.assertIn("message", content)
        self.assertIn('"Helper actif"', content)

    def test_helper_script_has_version_variable(self):
        """Helper doit definir une variable de version."""
        helper_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper.ps1"
        content = helper_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("helperVersion", content)
        self.assertIn("1.1.0", content)

    def test_start_script_tests_status(self):
        """start.ps1 doit tester /status avant d'annoncer le demarrage."""
        start_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-start.ps1"
        content = start_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("/status", content)
        self.assertIn("StatusCode -eq 200", content)
        self.assertIn("demarre avec succes", content)

    def test_start_script_shows_log_path(self):
        """start.ps1 doit afficher le chemin du log."""
        start_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-start.ps1"
        content = start_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("taf-lan-helper.log", content)
        self.assertIn("ERREUR", content)

    def test_start_script_kills_on_failure(self):
        """start.ps1 doit tuer le processus si /status ne repond pas."""
        start_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-start.ps1"
        content = start_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("Kill()", content)
        self.assertIn("exit 1", content)

    def test_stop_script_uses_pid_file(self):
        """stop.ps1 doit lire le PID file puis tuer le processus."""
        stop_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-stop.ps1"
        content = stop_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("taf-lan-helper.pid", content)
        self.assertIn("Kill()", content)
        self.assertIn("PID file", content)

    def test_stop_script_fallback_commandline(self):
        """stop.ps1 doit chercher par CommandLine si pas de PID file."""
        stop_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-stop.ps1"
        content = stop_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("CommandLine", content)
        self.assertIn("taf-lan-helper", content)

    def test_stop_script_checks_port_freed(self):
        """stop.ps1 doit verifier que le port 8019 est libere."""
        stop_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-stop.ps1"
        content = stop_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("8019", content)
        self.assertIn("libere", content)

    def test_diagnose_script_exists(self):
        """Le script de diagnostic doit exister."""
        diag_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-diagnose.ps1"
        self.assertTrue(diag_path.exists())

    def test_diagnose_script_tests_status(self):
        """diagnose.ps1 doit tester /status."""
        diag_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-diagnose.ps1"
        content = diag_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("/status", content)
        self.assertIn("Diagnostic", content)

    def test_diagnose_script_shows_log(self):
        """diagnose.ps1 doit afficher le log."""
        diag_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-diagnose.ps1"
        content = diag_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("taf-lan-helper.log", content)
        self.assertIn("dernieres", content)

    def test_diagnose_script_shows_process(self):
        """diagnose.ps1 doit afficher les processus helper."""
        diag_path = Path(__file__).resolve().parent.parent / "scripts" / "windows" / "taf-lan-helper-diagnose.ps1"
        content = diag_path.read_text(encoding="utf-8", errors="replace")
        self.assertIn("Processus", content)
        self.assertIn("Port 8019", content)


class SeedModule8CommandTests(TestCase):
    def test_seed_module8_creates_expected_module_and_active_session(self):
        call_command("seed_module8")
        module = TrainingModule.objects.get(code="MODULE_8")
        session = TrainingSession.objects.get(session_code="M8-ANDO-001")
        self.assertEqual(module.title, "Module 8 - Synthese et exercices pratiques")
        self.assertEqual(session.module, module)
        self.assertEqual(session.location, "Lycee Andohalo Antananarivo")
        self.assertEqual(session.trainer_name, "Formateur TAfHSSiM")
        self.assertTrue(session.is_active)

    def test_seed_module8_is_idempotent(self):
        call_command("seed_module8")
        call_command("seed_module8")
        self.assertEqual(TrainingModule.objects.filter(code="MODULE_8").count(), 1)
        self.assertEqual(TrainingSession.objects.filter(session_code="M8-ANDO-001").count(), 1)

    def test_seed_module8_does_not_overwrite_existing_session_details(self):
        call_command("seed_module8")
        session = TrainingSession.objects.get(session_code="M8-ANDO-001")
        session.trainer_name = "Autre Formateur"
        session.save(update_fields=["trainer_name"])
        call_command("seed_module8")
        session.refresh_from_db()
        self.assertEqual(session.trainer_name, "Autre Formateur")


class Module8SubmissionConstraintTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_8",
            title="Module 8 - Synthese",
            description="Mettre en pratique les competences de recherche documentaire.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 23),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M8-ANDO-001",
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
        return Module8Submission.objects.create(
            student=student,
            session=self.session,
            school_id_number_snapshot=student.school_id_number,
            auto_eval_search="bien",
            auto_eval_source="bien",
            auto_eval_summarize="bien",
            todo_chose_subject=True,
            todo_written_question=True,
            todo_transformed_keywords=True,
            todo_found_first_source=True,
            todo_found_second_source=True,
            todo_checked_source_quality=True,
            todo_chose_most_useful=True,
            todo_noted_three_ideas=True,
            todo_prepared_synthesis=True,
            todo_presented_explained=True,
            quiz_q1="vrai",
            quiz_q2="vrai",
            quiz_q3="faux",
            quiz_q4="vrai",
            quiz_q5="vrai",
            quiz_q6="faux",
            quiz_q7_selected=list(Module8Submission.QUIZ_Q7_CORRECT_ANSWERS),
            practical_subject="informatique",
            practical_topic="L intelligence artificielle",
            practical_starting_question="Comment l IA peut elle aider les eleves ?",
            practical_keywords_used="IA, intelligence artificielle, education",
            practical_first_source="Article Wikipedia sur l IA",
            practical_second_source="Video Youtube explicative",
            practical_verified_elements=["auteur_identifie", "site_connu"],
            practical_three_ideas="L IA peut aider a apprendre",
            practical_synthesis="L IA est un outil puissant pour l education.",
            practical_academic_message="L IA peut revolutionner l apprentissage.",
            feedback_best_success="J ai compris comment chercher.",
            feedback_still_difficult="",
            feedback_confidence="oui",
            feedback_one_thing_to_practice="Verifier les sources",
        )

    def test_duplicate_school_id_snapshot_is_blocked_for_same_session(self):
        self.make_submission(self.student)
        with self.assertRaises(IntegrityError):
            self.make_submission(self.other_student)

    def test_score_is_computed_on_save(self):
        sub = self.make_submission(self.student)
        self.assertEqual(sub.computed_score, 7)

    def test_score_zero_for_wrong_answers(self):
        sub = Module8Submission.objects.create(
            student=self.student,
            session=self.session,
            school_id_number_snapshot=self.student.school_id_number,
            auto_eval_search="pas_encore",
            auto_eval_source="pas_encore",
            auto_eval_summarize="pas_encore",
            quiz_q1="faux",
            quiz_q2="faux",
            quiz_q3="vrai",
            quiz_q4="faux",
            quiz_q5="faux",
            quiz_q6="vrai",
            quiz_q7_selected=["copier_sans_comprendre"],
            practical_subject="autre",
            practical_topic="Test",
            practical_starting_question="Test",
            practical_keywords_used="Test",
            practical_first_source="Test",
            practical_verified_elements=[],
            practical_three_ideas="Test",
            practical_synthesis="Test",
            feedback_best_success="Test",
            feedback_confidence="pas_encore",
        )
        self.assertEqual(sub.computed_score, 0)

    def test_has_seven_quiz_questions(self):
        sub = self.make_submission(self.student)
        self.assertIsNotNone(sub.quiz_q1)
        self.assertIsNotNone(sub.quiz_q6)
        self.assertIsNotNone(sub.quiz_q7_selected)

    def test_has_ten_todo_fields(self):
        sub = self.make_submission(self.student)
        todo_fields = [
            sub.todo_chose_subject,
            sub.todo_written_question,
            sub.todo_transformed_keywords,
            sub.todo_found_first_source,
            sub.todo_found_second_source,
            sub.todo_checked_source_quality,
            sub.todo_chose_most_useful,
            sub.todo_noted_three_ideas,
            sub.todo_prepared_synthesis,
            sub.todo_presented_explained,
        ]
        self.assertTrue(all(todo_fields))
        self.assertEqual(len(todo_fields), 10)


class Module8FormViewTests(TestCase):
    def setUp(self):
        self.module = TrainingModule.objects.create(
            code="MODULE_8",
            title="Module 8 - Synthese",
            description="Mettre en pratique les competences de recherche documentaire.",
        )
        self.session = TrainingSession.objects.create(
            module=self.module,
            date=date(2026, 6, 23),
            location="Lycee Andohalo Antananarivo",
            trainer_name="Formateur TAfHSSiM",
            session_code="M8-ANDO-001",
            is_active=True,
        )

    def valid_payload(self):
        return {
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_search": "bien",
            "auto_eval_source": "bien",
            "auto_eval_summarize": "bien",
            "todo_chose_subject": "on",
            "todo_written_question": "on",
            "todo_transformed_keywords": "on",
            "todo_found_first_source": "on",
            "todo_found_second_source": "on",
            "todo_checked_source_quality": "on",
            "todo_chose_most_useful": "on",
            "todo_noted_three_ideas": "on",
            "todo_prepared_synthesis": "on",
            "todo_presented_explained": "on",
            "quiz_q1": "vrai",
            "quiz_q2": "vrai",
            "quiz_q3": "faux",
            "quiz_q4": "vrai",
            "quiz_q5": "vrai",
            "quiz_q6": "faux",
            "quiz_q7_selected": list(Module8Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_subject": "informatique",
            "practical_topic": "L intelligence artificielle",
            "practical_starting_question": "Comment l IA peut elle aider les eleves ?",
            "practical_keywords_used": "IA, intelligence artificielle, education",
            "practical_first_source": "Article Wikipedia sur l IA",
            "practical_second_source": "Video Youtube explicative",
            "practical_verified_elements": ["auteur_identifie", "site_connu"],
            "practical_three_ideas": "L IA peut aider a apprendre",
            "practical_synthesis": "L IA est un outil puissant pour l education.",
            "practical_academic_message": "L IA peut revolutionner l apprentissage.",
            "feedback_best_success": "J ai compris comment chercher.",
            "feedback_still_difficult": "",
            "feedback_confidence": "oui",
            "feedback_one_thing_to_practice": "Verifier les sources",
        }

    def test_module_8_form_get(self):
        response = self.client.get(reverse("surveys:module_8"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 8")
        self.assertContains(response, "Envoyer")

    def test_valid_submission_creates_student_and_submission(self):
        response = self.client.post(reverse("surveys:module_8"), data=self.valid_payload(), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merci")
        self.assertEqual(Module8Submission.objects.count(), 1)
        self.assertEqual(Student.objects.count(), 1)

    def test_invalid_school_id_is_rejected(self):
        payload = self.valid_payload()
        payload["school_id_number"] = "1"
        response = self.client.post(reverse("surveys:module_8"), data=payload)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2 chiffres")

    def test_duplicate_school_id_is_rejected_for_same_active_session(self):
        self.client.post(reverse("surveys:module_8"), data=self.valid_payload())
        response = self.client.post(reverse("surveys:module_8"), data=self.valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "déjà")

    def test_success_page_requires_matching_session_submission_id(self):
        self.client.post(reverse("surveys:module_8"), data=self.valid_payload())
        submission = Module8Submission.objects.get()
        other_client = self.client_class()
        response = other_client.get(reverse("surveys:module_8_success", args=[submission.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("surveys:module_8"))

    def test_module_8_form_returns_200_when_responses_closed(self):
        self.session.accepting_responses = False
        self.session.save(update_fields=["accepting_responses"])
        response = self.client.get(reverse("surveys:module_8"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermees")

    def test_practical_synthesis_saved(self):
        self.client.post(reverse("surveys:module_8"), data=self.valid_payload())
        sub = Module8Submission.objects.first()
        self.assertEqual(sub.practical_synthesis, "L IA est un outil puissant pour l education.")

    def test_todo_10_items(self):
        self.client.post(reverse("surveys:module_8"), data=self.valid_payload())
        sub = Module8Submission.objects.first()
        for field in [
            "todo_chose_subject",
            "todo_written_question",
            "todo_transformed_keywords",
            "todo_found_first_source",
            "todo_found_second_source",
            "todo_checked_source_quality",
            "todo_chose_most_useful",
            "todo_noted_three_ideas",
            "todo_prepared_synthesis",
            "todo_presented_explained",
        ]:
            self.assertTrue(getattr(sub, field), f"{field} should be True")

    def test_quiz_score_max_7(self):
        self.client.post(reverse("surveys:module_8"), data=self.valid_payload())
        sub = Module8Submission.objects.first()
        self.assertEqual(sub.computed_score, 7)


class Module8PedagogyContentTests(TestCase):
    def setUp(self):
        call_command("seed_module8")

    def test_student_modules_shows_module_8(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 8 - Synthese et exercices pratiques")

    def test_student_module_8_detail_status_200(self):
        response = self.client.get(reverse("surveys:student_module_8_detail"))
        self.assertEqual(response.status_code, 200)

    def test_student_module_8_detail_contains_title(self):
        response = self.client.get(reverse("surveys:student_module_8_detail"))
        self.assertContains(response, "Module 8 - Synthese et exercices pratiques")

    def test_student_module_8_detail_contains_form_link(self):
        response = self.client.get(reverse("surveys:student_module_8_detail"))
        self.assertContains(response, "Commencer le questionnaire")


class Module8DashboardAndCockpitTests(TestCase):
    def setUp(self):
        call_command("seed_module8")
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(
            username="formateur", password="motdepasse-solide-123",
        )

    def test_module_8_form_200(self):
        response = self.client.get(reverse("surveys:module_8"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_module_8_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_module_8"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_csv_export_module_8_requires_login(self):
        response = self.client.get(reverse("surveys:export_module_8_csv"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_module_8_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_8"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 8")

    def test_csv_export_module_8_contains_submission_data(self):
        self.client.post(reverse("surveys:module_8"), data={
            "school_id_number": "01",
            "full_name": "Rakoto Aina",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_search": "bien",
            "auto_eval_source": "bien",
            "auto_eval_summarize": "bien",
            "quiz_q1": "vrai",
            "quiz_q2": "vrai",
            "quiz_q3": "faux",
            "quiz_q4": "vrai",
            "quiz_q5": "vrai",
            "quiz_q6": "faux",
            "quiz_q7_selected": list(Module8Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_subject": "informatique",
            "practical_topic": "IA",
            "practical_starting_question": "Test?",
            "practical_keywords_used": "IA, test",
            "practical_first_source": "Wiki",
            "practical_verified_elements": ["auteur_identifie"],
            "practical_three_ideas": "Idee 1, Idee 2, Idee 3",
            "practical_synthesis": "Synthese de test.",
            "practical_academic_message": "Message academique.",
            "feedback_best_success": "J ai reussi.",
            "feedback_still_difficult": "",
            "feedback_confidence": "oui",
            "feedback_one_thing_to_practice": "Plus de pratique.",
        })
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_8_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Rakoto Aina")

    def test_csv_export_sanitizes_formula_like_cells(self):
        self.client.post(reverse("surveys:module_8"), data={
            "school_id_number": "02",
            "full_name": "=SUM(1,1)",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_search": "bien",
            "auto_eval_source": "bien",
            "auto_eval_summarize": "bien",
            "quiz_q1": "vrai",
            "quiz_q2": "vrai",
            "quiz_q3": "faux",
            "quiz_q4": "vrai",
            "quiz_q5": "vrai",
            "quiz_q6": "faux",
            "quiz_q7_selected": list(Module8Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_subject": "informatique",
            "practical_topic": "Test",
            "practical_starting_question": "Test?",
            "practical_keywords_used": "Test",
            "practical_first_source": "Test",
            "practical_verified_elements": ["auteur_identifie"],
            "practical_three_ideas": "Test",
            "practical_synthesis": "Test",
            "feedback_best_success": "Test",
            "feedback_confidence": "oui",
        })
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:export_module_8_csv"))
        content = response.content.decode()
        self.assertIn("'=SUM(1,1)", content)

    def test_cockpit_shows_module_8_when_logged_in(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Module 8 - Synthese et exercices pratiques")


class Module8ClosedSubmissionTests(TestCase):
    def setUp(self):
        call_command("seed_module8")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        session = TrainingSession.objects.get(module__code="MODULE_8", is_active=True)
        session.accepting_responses = False
        session.save(update_fields=["accepting_responses"])

    def test_module_8_get_200_when_closed(self):
        response = self.client.get(reverse("surveys:module_8"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "fermees")

    def test_module_8_post_rejected_when_closed(self):
        response = self.client.post(
            reverse("surveys:module_8"),
            {"school_id_number": "99", "full_name": "Test", "class_level": "seconde", "group_name": ""},
        )
        self.assertNotEqual(response.status_code, 302)
        self.assertEqual(Student.objects.filter(school_id_number="99").count(), 0)

    def test_module_8_reopened_accepts_submission(self):
        session = TrainingSession.objects.get(module__code="MODULE_8", is_active=True)
        session.accepting_responses = True
        session.save(update_fields=["accepting_responses"])
        response = self.client.post(reverse("surveys:module_8"), data={
            "school_id_number": "01",
            "full_name": "Rakoto",
            "class_level": Student.CLASS_LEVEL_SECONDE,
            "group_name": "Salle A",
            "auto_eval_search": "bien",
            "auto_eval_source": "bien",
            "auto_eval_summarize": "bien",
            "quiz_q1": "vrai",
            "quiz_q2": "vrai",
            "quiz_q3": "faux",
            "quiz_q4": "vrai",
            "quiz_q5": "vrai",
            "quiz_q6": "faux",
            "quiz_q7_selected": list(Module8Submission.QUIZ_Q7_CORRECT_ANSWERS),
            "practical_subject": "informatique",
            "practical_topic": "Test",
            "practical_starting_question": "Test?",
            "practical_keywords_used": "Test",
            "practical_first_source": "Test",
            "practical_verified_elements": ["auteur_identifie"],
            "practical_three_ideas": "Test",
            "practical_synthesis": "Test",
            "feedback_best_success": "Test",
            "feedback_confidence": "oui",
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Merci")


class Module8ToggleResponsesTests(TestCase):
    def setUp(self):
        call_command("seed_module8")
        from django.contrib.auth.models import User
        self.staff = User.objects.create_user(
            username="staff", password="secret", is_staff=True,
        )
        self.url = reverse("surveys:toggle_module_responses", kwargs={"module_code": "MODULE_8"})

    def test_toggle_requires_login(self):
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_requires_staff(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.post(self.url)
        self.assertIn(response.status_code, (302, 401, 403))

    def test_toggle_closes_module_8(self):
        self.client.login(username="staff", password="secret")
        response = self.client.post(self.url, follow=True)
        session = TrainingSession.objects.get(module__code="MODULE_8", is_active=True)
        self.assertFalse(session.accepting_responses)

    def test_toggle_reopens_module_8(self):
        self.client.login(username="staff", password="secret")
        self.client.post(self.url)
        self.client.post(self.url)
        session = TrainingSession.objects.get(module__code="MODULE_8", is_active=True)
        self.assertTrue(session.accepting_responses)


class Module8AdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        self.superuser = User.objects.create_superuser(
            username="super", password="super", email="super@example.com",
        )
        self.client.login(username="super", password="super")

    def test_admin_module8submission_accessible(self):
        response = self.client.get(reverse("admin:surveys_module8submission_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_admin_no_secret_exposed(self):
        response = self.client.get(reverse("admin:surveys_module8submission_changelist"))
        self.assertNotContains(response, "SECRET_KEY")


class Module8RegressionTests(TestCase):
    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        call_command("seed_module5")
        call_command("seed_module6")
        call_command("seed_module7")
        call_command("seed_module8")

    def test_module_2_still_200(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertEqual(response.status_code, 200)

    def test_module_3_still_200(self):
        response = self.client.get(reverse("surveys:module_3"))
        self.assertEqual(response.status_code, 200)

    def test_module_4_still_200(self):
        response = self.client.get(reverse("surveys:module_4"))
        self.assertEqual(response.status_code, 200)

    def test_module_5_still_200(self):
        response = self.client.get(reverse("surveys:module_5"))
        self.assertEqual(response.status_code, 200)

    def test_module_6_still_200(self):
        response = self.client.get(reverse("surveys:module_6"))
        self.assertEqual(response.status_code, 200)

    def test_module_7_still_200(self):
        response = self.client.get(reverse("surveys:module_7"))
        self.assertEqual(response.status_code, 200)

    def test_module_8_still_200(self):
        response = self.client.get(reverse("surveys:module_8"))
        self.assertEqual(response.status_code, 200)

    def test_student_modules_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertNotContains(response, "Cockpit formateur")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "/admin/")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertIn(response.status_code, (302, 401, 403))


class RedesignUITests(TestCase):
    """Tests for F033 global UI redesign."""

    def setUp(self):
        call_command("seed_module2")
        call_command("seed_module3")
        call_command("seed_module4")
        call_command("seed_module5")
        call_command("seed_module6")
        call_command("seed_module7")
        call_command("seed_module8")
        self.user = get_user_model().objects.create_user(
            username="formateur", password="motdepasse-solide-123", is_staff=True
        )

    def test_public_pages_respond_200(self):
        for url_name in ["surveys:home", "surveys:student_modules"]:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

    def test_dashboard_pages_require_login(self):
        for url_name in [
            "surveys:dashboard_home",
            "surveys:dashboard_network",
            "surveys:dashboard_network_control",
            "surveys:dashboard_settings",
            "surveys:dashboard_backup",
            "surveys:dashboard_module_2",
            "surveys:dashboard_module_8",
            "surveys:export_module_2_csv",
            "surveys:export_module_8_csv",
        ]:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertIn(response.status_code, (302, 401, 403))

    def test_trainer_navigation_visible_when_logged_in(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Cockpit")
        self.assertContains(response, "Réseau")
        self.assertContains(response, "Contrôle LAN")
        self.assertContains(response, "Configuration")
        self.assertContains(response, "Sauvegarde")
        self.assertContains(response, "Admin avancé")

    def test_student_navigation_has_no_trainer_links(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertContains(response, "Modules")
        self.assertNotContains(response, "Cockpit")
        self.assertNotContains(response, "Export CSV")
        self.assertNotContains(response, "/admin/")
        self.assertNotContains(response, "dashboard/")

    def test_student_module_links_present(self):
        response = self.client.get(reverse("surveys:student_modules"))
        for num in range(2, 9):
            with self.subTest(module=num):
                self.assertContains(response, f"Module {num}")

    def test_trainer_sees_all_modules_in_dashboard(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        for num in range(2, 9):
            with self.subTest(module=num):
                self.assertContains(response, f"Module {num}")

    def test_cockpit_has_network_control_steps(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_network_control"))
        steps = [
            "Helper local",
            "Application locale",
            "IP Wi-Fi",
            "Portproxy",
            "Pare-feu",
            "Django autorise l'IP",
            "URL élèves accessible",
        ]
        for step in steps:
            with self.subTest(step=step):
                self.assertContains(response, step)
        self.assertContains(response, "Configurer et rendre accessible")

    def test_dashboard_results_page_exists(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_backup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sauvegarder les données")
        self.assertContains(response, "Ne jamais supprimer")
        self.assertContains(response, "Commandes interdites")

    def test_dashboard_has_breadcrumbs(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_2"))
        self.assertContains(response, 'class="breadcrumbs"')
        self.assertContains(response, "Cockpit")

    def test_no_cdn_in_templates(self):
        for template_name in [
            "surveys/home.html",
            "surveys/student_modules.html",
            "surveys/dashboard_home.html",
            "surveys/dashboard_network_control.html",
            "surveys/dashboard_backup.html",
            "surveys/base.html",
        ]:
            path = Path(__file__).resolve().parent.parent / "templates" / template_name
            if not path.exists():
                continue
            content = path.read_text()
            with self.subTest(template=template_name):
                self.assertNotIn("cdnjs", content)
                self.assertNotIn("jsdelivr", content)
                self.assertNotIn("unpkg", content)
                self.assertNotIn("bootstrapcdn", content)

    def test_no_secret_key_in_templates(self):
        for path in (Path(__file__).resolve().parent.parent / "templates").rglob("*.html"):
            content = path.read_text()
            with self.subTest(template=str(path)):
                self.assertNotIn("SECRET_KEY", content)

    def test_no_destructive_commands_in_templates_or_scripts(self):
        from pathlib import Path
        project_root = Path(__file__).resolve().parent.parent
        checked_paths = list((project_root / "templates").rglob("*.html"))
        for path in checked_paths:
            content = path.read_text()
            with self.subTest(template=str(path)):
                self.assertNotIn("down -v", content)
                self.assertNotIn("system prune --volumes", content)
                self.assertNotIn("manage.py flush", content)

    def test_skip_link_present(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, 'class="skip-link"')
        self.assertContains(response, 'href="#content"')

    def test_aria_labels_present(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertContains(response, 'aria-labelledby')

    def test_progress_bars_use_css_var(self):
        """The dashboard_module_2 should render progress bars via --w var."""
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_module_2"))
        self.assertContains(response, "--w:")
        self.assertContains(response, "progress-bar")

    def test_student_navigation_shows_supports_public_link(self):
        response = self.client.get(reverse("surveys:student_modules"))
        self.assertContains(response, "Supports")
        self.assertContains(response, 'href="/supports/"')
        self.assertNotContains(response, "Admin avancé")

    def test_student_module_detail_has_breadcrumbs(self):
        response = self.client.get(reverse("surveys:student_module_2_detail"))
        self.assertContains(response, 'class="breadcrumbs"')
        self.assertContains(response, reverse("surveys:home"))
        self.assertContains(response, reverse("surveys:student_modules"))
        self.assertContains(response, "Module 2")

    def test_student_questionnaire_has_breadcrumbs(self):
        response = self.client.get(reverse("surveys:module_2"))
        self.assertContains(response, 'class="breadcrumbs"')
        self.assertContains(response, "Questionnaire")

    def test_trainer_navigation_includes_modules_and_exports(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, reverse("surveys:dashboard_home") + "#modules")
        self.assertContains(response, reverse("surveys:dashboard_home") + "#exports")
        self.assertContains(response, "Admin avancé")

    def test_dashboard_home_has_breadcrumbs(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, 'class="breadcrumbs"')
        self.assertContains(response, "Cockpit")


@override_settings(ALLOWED_HOSTS=["*"], MEDIA_ROOT=Path(mkdtemp()))
class LearningResourceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="formateur",
            password="motdepasse-solide-123",
        )
        self.math_subject = Subject.objects.create(
            name="Mathématiques",
            slug="mathematiques",
            class_level=Student.CLASS_LEVEL_SECONDE,
            sort_order=1,
            is_active=True,
        )
        self.geometry_chapter = Chapter.objects.create(
            subject=self.math_subject,
            title="Géométrie",
            slug="geometrie",
            sort_order=1,
            is_active=True,
        )
        self.history_subject = Subject.objects.create(
            name="Histoire-Géographie",
            slug="histoire-geographie",
            class_level=Student.CLASS_LEVEL_PREMIERE,
            sort_order=2,
            is_active=True,
        )
        self.published = LearningResource.objects.create(
            title="Guide PDF Module 2",
            slug="guide-pdf-module-2",
            description="Support public pour les élèves.",
            resource_type=LearningResource.RESOURCE_TYPE_DOCUMENT,
            module_number=2,
            subject=self.math_subject,
            chapter=self.geometry_chapter,
            file=SimpleUploadedFile("guide-module-2.pdf", b"%PDF-1.4 test content", content_type="application/pdf"),
            source="TAfHSSiM",
            license_label="Usage classe",
            is_published=True,
        )
        self.draft = LearningResource.objects.create(
            title="Brouillon interne",
            slug="brouillon-interne",
            description="Ne doit pas sortir en public.",
            resource_type=LearningResource.RESOURCE_TYPE_DOCUMENT,
            module_number=3,
            file=SimpleUploadedFile("brouillon.pdf", b"%PDF-1.4 draft content", content_type="application/pdf"),
            is_published=False,
        )
        self.video_published = LearningResource.objects.create(
            title="Vidéo module 2",
            slug="video-module-2",
            description="Capsule vidéo locale.",
            resource_type="video",
            module_number=2,
            subject=self.history_subject,
            file=SimpleUploadedFile("video-module-2.mp4", b"\x00\x00\x00\x18ftypmp42video", content_type="video/mp4"),
            source="TAfHSSiM",
            license_label="Usage classe",
            is_published=True,
        )
        self.video_draft = LearningResource.objects.create(
            title="Vidéo brouillon",
            slug="video-brouillon",
            description="Ne doit pas sortir en public.",
            resource_type="video",
            module_number=3,
            file=SimpleUploadedFile("video-brouillon.mp4", b"\x00\x00\x00\x18ftypmp42draft", content_type="video/mp4"),
            is_published=False,
        )

    def test_support_list_returns_200(self):
        response = self.client.get(reverse("surveys:support_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Catalogue public")

    def test_support_list_shows_only_published_resources(self):
        response = self.client.get(reverse("surveys:support_list"))

        self.assertContains(response, self.published.title)
        self.assertContains(response, self.video_published.title)
        self.assertNotContains(response, self.draft.title)
        self.assertNotContains(response, self.video_draft.title)

    def test_support_detail_published_returns_200(self):
        response = self.client.get(reverse("surveys:support_detail", args=[self.published.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertContains(response, "Mathématiques")
        self.assertContains(response, "Géométrie")

    def test_support_detail_draft_returns_404(self):
        response = self.client.get(reverse("surveys:support_detail", args=[self.draft.slug]))

        self.assertEqual(response.status_code, 404)

    def test_support_watch_published_video_returns_200(self):
        response = self.client.get(reverse("surveys:support_watch", args=[self.video_published.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<video", html=False)
        self.assertContains(response, 'preload="metadata"', html=False)

    def test_support_watch_draft_video_returns_404(self):
        response = self.client.get(reverse("surveys:support_watch", args=[self.video_draft.slug]))

        self.assertEqual(response.status_code, 404)

    def test_support_watch_document_returns_404(self):
        response = self.client.get(reverse("surveys:support_watch", args=[self.published.slug]))

        self.assertEqual(response.status_code, 404)

    def test_support_download_published_returns_file(self):
        response = self.client.get(reverse("surveys:support_download", args=[self.published.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment;", response["Content-Disposition"])

    def test_support_download_draft_returns_404(self):
        response = self.client.get(reverse("surveys:support_download", args=[self.draft.slug]))

        self.assertEqual(response.status_code, 404)

    def test_support_download_published_video_returns_file(self):
        response = self.client.get(reverse("surveys:support_download", args=[self.video_published.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "video/mp4")

    def test_dashboard_supports_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_supports"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_supports_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_supports"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard supports")
        self.assertContains(response, self.published.title)
        self.assertContains(response, self.draft.title)
        self.assertContains(response, "Publié")
        self.assertContains(response, "Brouillon")
        self.assertContains(response, "Mathématiques")
        self.assertContains(response, "Géométrie")

    def test_student_navigation_contains_supports_without_dashboard_links(self):
        response = self.client.get(reverse("surveys:support_list"))

        self.assertContains(response, 'href="/supports/"')
        self.assertNotContains(response, "/dashboard/supports/")
        self.assertNotContains(response, "Admin avancé")

    def test_trainer_navigation_contains_dashboard_supports(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_supports"))

        self.assertContains(response, reverse("surveys:dashboard_supports"))

    def test_dashboard_support_upload_requires_login(self):
        response = self.client.get(reverse("surveys:dashboard_support_upload"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_dashboard_support_upload_get_renders_for_logged_in_trainer(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_support_upload"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ajouter un support")
        self.assertContains(response, "20 MB")
        self.assertContains(response, "80 MB")
        self.assertContains(response, "Matière")
        self.assertContains(response, "Chapitre")

    def test_dashboard_support_upload_valid_pdf_creates_draft_resource(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Nouveau guide module 4",
                "description": "Support de test.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "module_number": 4,
                "subject": self.math_subject.pk,
                "chapter": self.geometry_chapter.pk,
                "file": SimpleUploadedFile("guide-module-4.pdf", b"%PDF-1.4 upload content", content_type="application/pdf"),
                "source": "TAfHSSiM",
                "license_label": "Usage classe",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("surveys:dashboard_supports"))
        resource = LearningResource.objects.get(title="Nouveau guide module 4")
        self.assertFalse(resource.is_published)
        self.assertEqual(resource.slug, "nouveau-guide-module-4")
        self.assertEqual(resource.subject, self.math_subject)
        self.assertEqual(resource.chapter, self.geometry_chapter)

    def test_upload_created_as_draft_does_not_appear_in_public_catalog(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Support privé module 5",
                "description": "Brouillon interne.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "module_number": 5,
                "file": SimpleUploadedFile("support-prive.pdf", b"%PDF-1.4 private content", content_type="application/pdf"),
                "source": "TAfHSSiM",
                "license_label": "Usage classe",
            },
        )

        response = self.client_class().get(reverse("surveys:support_list"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Support privé module 5")

    def test_upload_created_as_published_appears_in_public_catalog(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")
        self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Support publié module 6",
                "description": "Visible côté élèves.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "module_number": 6,
                "file": SimpleUploadedFile("support-publie.pdf", b"%PDF-1.4 public content", content_type="application/pdf"),
                "source": "TAfHSSiM",
                "license_label": "Usage classe",
                "is_published": "on",
            },
        )

        response = self.client.get(reverse("surveys:support_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Support publié module 6")

    def test_support_list_can_filter_by_subject(self):
        response = self.client.get(reverse("surveys:support_list"), {"subject": self.math_subject.slug})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertNotContains(response, self.video_published.title)

    def test_support_list_can_filter_by_level(self):
        response = self.client.get(reverse("surveys:support_list"), {"level": Student.CLASS_LEVEL_PREMIERE})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.video_published.title)
        self.assertNotContains(response, self.published.title)

    def test_support_list_can_filter_by_module(self):
        response = self.client.get(reverse("surveys:support_list"), {"module": "2"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published.title)
        self.assertContains(response, self.video_published.title)

    def test_dashboard_support_upload_valid_mp4_creates_video_resource(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Vidéo locale module 4",
                "description": "Capsule vidéo.",
                "resource_type": "video",
                "module_number": 4,
                "file": SimpleUploadedFile("module-4.mp4", b"\x00\x00\x00\x18ftypmp42upload", content_type="video/mp4"),
                "source": "TAfHSSiM",
                "license_label": "Usage classe",
                "is_published": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        resource = LearningResource.objects.get(title="Vidéo locale module 4")
        self.assertEqual(resource.resource_type, "video")
        self.assertTrue(resource.is_published)

    def test_dashboard_support_upload_rejects_chapter_from_other_subject(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Support incohérent",
                "description": "Doit échouer.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "subject": self.history_subject.pk,
                "chapter": self.geometry_chapter.pk,
                "file": SimpleUploadedFile("incoherent.pdf", b"%PDF-1.4 invalid", content_type="application/pdf"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choisis un chapitre de la matière sélectionnée.")
        self.assertFalse(LearningResource.objects.filter(title="Support incohérent").exists())

    def test_dashboard_support_upload_rejects_oversized_mp4(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Vidéo trop lourde",
                "description": "Doit échouer.",
                "resource_type": "video",
                "file": SimpleUploadedFile(
                    "trop-lourd.mp4",
                    b"x" * (80 * 1024 * 1024 + 1),
                    content_type="video/mp4",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "80 MB")
        self.assertFalse(LearningResource.objects.filter(title="Vidéo trop lourde").exists())

    def test_dashboard_support_upload_rejects_non_mvp_video_extensions(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        for filename in ["video.mov", "video.avi", "video.mkv", "video.webm"]:
            response = self.client.post(
                reverse("surveys:dashboard_support_upload"),
                data={
                    "title": f"Vidéo interdite {filename}",
                    "description": "Doit échouer.",
                    "resource_type": "video",
                    "file": SimpleUploadedFile(filename, b"fake-video", content_type="video/quicktime"),
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Format non autorisé")

    def test_support_detail_shows_watch_link_for_published_video(self):
        response = self.client.get(reverse("surveys:support_detail", args=[self.video_published.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("surveys:support_watch", args=[self.video_published.slug]))
        self.assertContains(response, "Regarder la vidéo")

    def test_support_list_shows_watch_link_for_published_video(self):
        response = self.client.get(reverse("surveys:support_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("surveys:support_watch", args=[self.video_published.slug]))
        self.assertContains(response, "Regarder")

    def test_dashboard_support_upload_rejects_forbidden_extension(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Exécutable interdit",
                "description": "Doit échouer.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "file": SimpleUploadedFile("danger.exe", b"MZfake", content_type="application/octet-stream"),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Format non autorisé")
        self.assertFalse(LearningResource.objects.filter(title="Exécutable interdit").exists())

    def test_dashboard_support_upload_rejects_too_large_file(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Fichier trop volumineux",
                "description": "Doit échouer.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "file": SimpleUploadedFile(
                    "trop-lourd.pdf",
                    b"x" * (20 * 1024 * 1024 + 1),
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "20 MB")
        self.assertFalse(LearningResource.objects.filter(title="Fichier trop volumineux").exists())

    def test_dashboard_support_upload_rejects_missing_file(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": "Sans fichier",
                "description": "Doit échouer.",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ce champ est obligatoire.")
        self.assertFalse(LearningResource.objects.filter(title="Sans fichier").exists())

    def test_dashboard_support_upload_generates_unique_slug_for_duplicate_titles(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": self.published.title,
                "description": "Variante 1",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "file": SimpleUploadedFile("variante-1.pdf", b"%PDF-1.4 one", content_type="application/pdf"),
            },
        )
        self.client.post(
            reverse("surveys:dashboard_support_upload"),
            data={
                "title": self.published.title,
                "description": "Variante 2",
                "resource_type": LearningResource.RESOURCE_TYPE_DOCUMENT,
                "file": SimpleUploadedFile("variante-2.pdf", b"%PDF-1.4 two", content_type="application/pdf"),
            },
        )

        slugs = set(LearningResource.objects.filter(title=self.published.title).values_list("slug", flat=True))
        self.assertIn("guide-pdf-module-2", slugs)
        self.assertIn("guide-pdf-module-2-2", slugs)
        self.assertIn("guide-pdf-module-2-3", slugs)

    def test_dashboard_supports_contains_add_upload_link(self):
        self.client.login(username="formateur", password="motdepasse-solide-123")

        response = self.client.get(reverse("surveys:dashboard_supports"))

        self.assertContains(response, reverse("surveys:dashboard_support_upload"))
        self.assertContains(response, "Ajouter un support")
