from django import template
from dashboard.models import User_Image

register = template.Library()


@register.simple_tag
def user_profile_image(user):
    try:
        user_image = User_Image.objects.get(user=user)
        return user_image.img.url

    except User_Image.DoesNotExist:
        return '/static/images/user.png'


@register.filter
def get_item(dictionary, key):
    """Look up `key` in `dictionary` from a template — used for the CSV import
    column auto-mapping, where the key is itself a template variable."""
    if not dictionary:
        return None
    return dictionary.get(key)