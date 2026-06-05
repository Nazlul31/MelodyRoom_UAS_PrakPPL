from django import template

register = template.Library()

# Foto bertema karaoke (mikrofon, ruang karaoke, bernyanyi bersama)
HERO_IMAGE = (
    'https://images.unsplash.com/photo-1516280440614-37939bbacd81'
    '?auto=format&fit=crop&w=1920&q=80'
)
DEFAULT_ROOM_IMAGE = (
    'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04'
    '?auto=format&fit=crop&w=800&q=80'
)
VIP_ROOM_IMAGE = (
    'https://images.unsplash.com/photo-1558618666-fcd25c85cd64'
    '?auto=format&fit=crop&w=800&q=80'
)
STANDARD_ROOM_IMAGE = (
    'https://images.unsplash.com/photo-1603092772630-298dca794c57'
    '?auto=format&fit=crop&w=800&q=80'
)
LANDING_ABOUT_IMAGE = (
    'https://images.unsplash.com/photo-1576751877629-41144c1e73f4'
    '?auto=format&fit=crop&w=900&q=80'
)


@register.simple_tag
def hero_image():
    return HERO_IMAGE


@register.simple_tag
def about_image():
    return LANDING_ABOUT_IMAGE


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
