from django.core.management.base import BaseCommand, CommandError

from surveys.settings_config import apply_lan_settings


class Command(BaseCommand):
    help = "Synchronise les paramètres LAN (TAF_LAN_HOST, TAF_HOST_PORT, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS)."

    def add_arguments(self, parser):
        parser.add_argument("--lan-host", required=True, help="Adresse IPv4 LAN (ex: 192.168.0.101)")
        parser.add_argument("--lan-port", required=True, help="Port LAN (ex: 8011)")

    def handle(self, *args, **options):
        ip = options["lan_host"].strip()
        port = options["lan_port"].strip()

        ok, msg = apply_lan_settings(ip, port)
        if not ok:
            raise CommandError(msg)

        self.stdout.write(self.style.SUCCESS(f"LAN settings synced: http://{ip}:{port}/"))
        self.stdout.write(self.style.SUCCESS("TAF_LAN_HOST, TAF_HOST_PORT, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS mis à jour."))
        self.stdout.write(self.style.WARNING("Redémarre l'application (docker compose up --build -d) pour appliquer les changements."))
