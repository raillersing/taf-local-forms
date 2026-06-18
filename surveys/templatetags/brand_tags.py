from pathlib import Path

from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def brand_logo_exists() -> bool:
    return (Path(settings.BASE_DIR) / "static" / "brand" / "isoc_madagascar_logo.png").exists()
