from django import template
from django.urls import translate_url as _translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context, lang_code):
    """Joriy sahifaning boshqa tildagi URL'i (hreflang uchun)."""
    request = context["request"]
    return _translate_url(request.path, lang_code)
