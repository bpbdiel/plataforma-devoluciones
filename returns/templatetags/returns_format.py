from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def clp(value):
    if value in (None, ''):
        return ''
    try:
        amount = int(Decimal(str(value)))
    except (InvalidOperation, ValueError):
        return value
    return f'${amount:,}'.replace(',', '.') + ' CLP'
