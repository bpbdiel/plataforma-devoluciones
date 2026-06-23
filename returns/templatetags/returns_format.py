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


@register.filter
def clp_difference(value, arg):
    if value in (None, '') or arg in (None, ''):
        return ''
    try:
        amount = int(Decimal(str(value))) - int(Decimal(str(arg)))
    except (InvalidOperation, ValueError):
        return ''
    sign = '-' if amount < 0 else ''
    return f'{sign}${abs(amount):,}'.replace(',', '.') + ' CLP'
