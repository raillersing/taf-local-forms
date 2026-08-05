from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create the eight default TAfHSSiM modules and their classroom sessions."

    def handle(self, *args, **options):
        for number in range(1, 9):
            call_command(f"seed_module{number}")
        self.stdout.write(self.style.SUCCESS("Les 8 modules TAfHSSiM sont prêts."))
