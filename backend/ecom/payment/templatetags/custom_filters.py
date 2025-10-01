# payment/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    """
    Subtracts the arg from the value.
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''