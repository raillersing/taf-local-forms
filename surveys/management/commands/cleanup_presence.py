from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from surveys.models import FormPresence


class Command(BaseCommand):
    help = "Mark expired presences (no heartbeat > 120s)"

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(seconds=120)
        expired = FormPresence.objects.filter(
            last_seen_at__lt=cutoff, status=FormPresence.STATUS_ACTIVE
        ).update(status=FormPresence.STATUS_EXPIRED)
        self.stdout.write(f"{expired} expired presence(s) cleaned up.")
