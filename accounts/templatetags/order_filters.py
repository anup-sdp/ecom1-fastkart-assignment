# accounts/templatetags/order_filters.py
# Create this file structure: accounts/templatetags/__init__.py and accounts/templatetags/order_filters.py

# custom template filter for the multiplication calculation since Django templates don't have built-in multiplication

from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)  # product total price = product price * product quantity
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """Format value as currency"""
    try:
        return f"${float(value):.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def order_status_class(status):
    """Return CSS class based on order status"""
    status_classes = {
        'Pending': 'bg-warning',
        'Completed': 'bg-success',
        'Delivered': 'bg-primary',
        'Cancelled': 'bg-danger',
        'Processing': 'bg-info',
    }
    return status_classes.get(status, 'bg-secondary')

# Don't forget to create accounts/templatetags/__init__.py (empty file)