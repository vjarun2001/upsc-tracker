from django import template

from apps.common.utils import format_minutes_hm, format_seconds_hm

register = template.Library()


@register.filter
def get_item(mapping, key):
    return mapping.get(key)


@register.filter
def minutes_to_hm(total_minutes):
    return format_minutes_hm(total_minutes)


@register.filter
def seconds_to_hm(total_seconds):
    return format_seconds_hm(total_seconds)
