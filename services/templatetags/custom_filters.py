from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replaces all instances of a substring with another substring.
    Usage: {{ text|replace:"old_text":"new_text" }}
    """
    if ':' in arg:
        old_text, new_text = arg.split(':', 1)
        return str(value).replace(old_text, new_text)
    return value
