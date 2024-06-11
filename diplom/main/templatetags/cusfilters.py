from django import template
import os

register = template.Library()


@register.filter(name='get_attribute')
def get_attribute(value, arg):
    return getattr(value, arg, "")


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, 0)


@register.filter
def basename(value):
    return os.path.basename(value)


@register.filter
def to_range(start, end):
    return range(start, end)