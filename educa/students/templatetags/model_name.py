from django import template

register = template.Library()


@register.filter
def model_name(instance):
    """
    Return the model name of an instance.
    """
    return instance._meta.model_name
