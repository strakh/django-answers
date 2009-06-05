from django import template
register = template.Library()

@register.filter(name='in')
def _in(value, arg):
    return value in arg