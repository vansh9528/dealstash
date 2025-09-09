from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Usage: {{ field|add_class:"form-control" }}
    """
    return field.as_widget(attrs={"class": css_class})
