# students/templatetags/custom_tags.py
from django import template
register = template.Library()

@register.filter
def dictget(d, key):
    try:
        return d.get(int(key)) if isinstance(key, str) and key.isdigit() else d.get(key)
    except Exception:
        return None
