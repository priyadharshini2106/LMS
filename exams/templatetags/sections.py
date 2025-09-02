# exams/templatetags/sections.py
from django import template

register = template.Library()

@register.filter
def parent_level_id(section):
    # Try common attribute names
    for attr in ['class_level', 'level', 'parent', 'grade', 'standard']:
        if hasattr(section, attr) and getattr(section, attr) is not None:
            return getattr(section, attr).pk
    # Fallback: if nothing matched, return None (template will render empty)
    return None
