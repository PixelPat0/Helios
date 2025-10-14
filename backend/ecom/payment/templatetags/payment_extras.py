from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        return Decimal('0')

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtract the argument from the value"""
    try:
        return Decimal(str(value)) - Decimal(str(arg))
    except (ValueError, TypeError):
        return Decimal('0')


@register.filter
def get_item(dictionary, key):
    """Allows lookup on dicts or similar objects in templates (e.g., dictionary|get_item:key)"""
    return dictionary.get(key, []) # Return an empty list if key not found (safe)