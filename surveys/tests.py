import os
from datetime import date
from tempfile import mkdtemp
from unittest.mock import patch

import json

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import FormPresence, Module3Submission, Module4Submission, Student, Submission, TrainingModule, TrainingSession


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
        self.assertContains(response, "Répondre au questionnaire")

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
        self.assertContains(response, "Répondre au questionnaire")

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
        self.assertContains(response, "Répondre au questionnaire")

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
        self.assertContains(response, "Modules de formation")

    def test_home_contains_espace_formateur_link_to_dashboard(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_logo_links_to_dashboard(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, reverse("surveys:dashboard_home"))

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
        self.assertContains(response, "Modules de formation")

    def test_home_contains_espace_formateur(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, "l'espace formateur")
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_logo_points_to_dashboard(self):
        response = self.client.get(reverse("surveys:home"))
        self.assertContains(response, reverse("surveys:dashboard_home"))

    def test_dashboard_shows_full_nav(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "Modules de formation")
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Accès réseau")
        self.assertContains(response, "Configuration réseau")
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

    def test_dashboard_shows_ip_alert_when_not_configured(self):
        response = self.client.get(reverse("surveys:dashboard_home"))
        self.assertContains(response, "IP locale non configurée")

    def test_network_page_links_have_target_blank(self):
        response = self.client.get(reverse("surveys:dashboard_network"))
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'rel="noopener noreferrer"')

    def test_network_page_shows_ip_alert(self):
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
        os.environ["TAF_LAN_HOST"] = "192.168.0.100"
        try:
            response = self.client.get(reverse("surveys:dashboard_home"))
            self.assertContains(response, "http://192.168.0.100:8000/")
        finally:
            os.environ.pop("TAF_LAN_HOST", None)

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
