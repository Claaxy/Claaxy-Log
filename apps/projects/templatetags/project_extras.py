from django import template

from apps.projects.services.financials import format_money, get_profit

register = template.Library()


@register.filter
def money(value):
    return format_money(value)


@register.filter
def profit(financials):
    return format_money(get_profit(financials))
