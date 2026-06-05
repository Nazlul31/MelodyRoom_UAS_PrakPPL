from django import template

register = template.Library()

@register.simple_tag
def hero_image():
    # Tidak dipakai di landing baru (section hero pakai CSS gradient)
    return ''


@register.simple_tag
def about_image():
    # Gambar lokal dari static/images/about.jpg
    from django.templatetags.static import static
    return static('images/about.jpg')


@register.filter
def room_image(room_or_type):
    if hasattr(room_or_type, 'photo') and room_or_type.photo:
        return room_or_type.photo.url
    name = getattr(room_or_type, 'name', '') or ''
    if 'vip' in name.lower():
        return VIP_ROOM_IMAGE
    if 'standard' in name.lower():
        return STANDARD_ROOM_IMAGE
    return DEFAULT_ROOM_IMAGE
