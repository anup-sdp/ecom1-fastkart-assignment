from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def add_days(value, days):
    """Add/subtract days from a datetime object"""
    return value + timedelta(days=days)
