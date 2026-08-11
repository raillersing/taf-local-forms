from django import template
from surveys.models import EditRequest
from surveys.constants import MODULE_METADATA

register = template.Library()


@register.simple_tag
def pending_edit_requests_count():
    return EditRequest.objects.filter(status=EditRequest.STATUS_PENDING).count()


@register.filter
def get_item(dictionary, key):
    """Return dictionary[key] or None."""
    if dictionary is None:
        return None
    return dictionary.get(key)
