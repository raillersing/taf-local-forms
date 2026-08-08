from django import template
from surveys.models import EditRequest

register = template.Library()

@register.simple_tag
def pending_edit_requests_count():
    return EditRequest.objects.filter(status=EditRequest.STATUS_PENDING).count()
