from datetime import date

from django.core.management.base import BaseCommand

from surveys.models import TrainingModule, TrainingSession


class Command(BaseCommand):
    help = "Create the default Module 2 training module and active session."

    def handle(self, *args, **options):
        module, _ = TrainingModule.objects.get_or_create(
            code="MODULE_2",
            defaults={
                "title": "Module 2 - Comprendre Internet",
                "description": "Aider les eleves a comprendre Internet comme outil de recherche et d'apprentissage.",
            },
        )
        session, created = TrainingSession.objects.get_or_create(
            session_code="M2-ANDO-001",
            defaults={
                "module": module,
                "date": date.today(),
                "location": "Lycee Andohalo Antananarivo",
                "trainer_name": "Formateur TAfHSSiM",
                "is_active": True,
            },
        )

        action = "cree" if created else "conserve"
        self.stdout.write(
            self.style.SUCCESS(
                f"Module {module.code} pret et session {session.session_code} {action}."
            )
        )
