from datetime import date

from django.core.management.base import BaseCommand

from surveys.models import TrainingModule, TrainingSession


class Command(BaseCommand):
    help = "Create the default Module 1 first-contact questionnaire and active session."

    def handle(self, *args, **options):
        module, _ = TrainingModule.objects.get_or_create(
            code="MODULE_1",
            defaults={
                "title": "Module 1 - Première prise de contact",
                "description": "Mieux connaître l'accès au numérique, les habitudes et les besoins des élèves.",
            },
        )
        session, created = TrainingSession.objects.get_or_create(
            session_code="M1-ANDO-001",
            defaults={
                "module": module,
                "date": date.today(),
                "location": "Lycée Andohalo Antananarivo",
                "trainer_name": "Formateur TAfHSSiM",
                "is_active": True,
                "accepting_responses": True,
            },
        )
        action = "créée" if created else "conservée"
        self.stdout.write(self.style.SUCCESS(f"Module {module.code} prêt et session {session.session_code} {action}."))
