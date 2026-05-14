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

@register.filter
def split(value, arg):
    """
    Splits a string by a delimiter and returns a list.
    Usage: {{ text|split:"," }}
    """
    return str(value).split(arg)

@register.filter
def trim(value):
    """
    Removes leading and trailing whitespace.
    Usage: {{ text|trim }}
    """
    return str(value).strip()
