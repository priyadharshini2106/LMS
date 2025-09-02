from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """
    Safely add a CSS class to a form field widget.
    Usage: {{ form.field|add_class:"form-control" }}
    """
    try:
        return value.as_widget(attrs={'class': arg})
    except AttributeError:
        return value  # fallback: return the value unchanged if it's not a form field
