from datetime import date

from django.core.management.base import BaseCommand

from surveys.models import TrainingModule, TrainingSession


class Command(BaseCommand):
    help = "Create the default Module 5 training module and active session."

    def handle(self, *args, **options):
        module, _ = TrainingModule.objects.get_or_create(
            code="MODULE_5",
            defaults={
                "title": "Module 5 - Email et outils de communication",
                "description": "Comprendre les usages academiques de l'email et communiquer avec respect.",
            },
        )
        session, created = TrainingSession.objects.get_or_create(
            session_code="M5-ANDO-001",
            defaults={
                "module": module,
                "date": date.today(),
                "location": "Lycee Andohalo Antananarivo",
                "trainer_name": "Formateur TAfHSSiM",
                "is_active": True,
                "accepting_responses": True,
            },
        )

        action = "cree" if created else "conserve"
        self.stdout.write(
            self.style.SUCCESS(
                f"Module {module.code} pret et session {session.session_code} {action}."
            )
        )
