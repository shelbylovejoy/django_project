from django import template

register = template.Library()


@register.filter(name='get_quantity')
def get_cart_quantity(cart, movie_id):
    try:
        return cart[str(movie_id)]
    except Exception:
        return 0


@register.filter(name='get_quantity_from_session')
def get_quantity_from_session(session, movie_id):
    """Reads quantity for movie_id from session carts and active_cart key.

    Usage in template: `{{ request.session|get_quantity_from_session:movie.id }}`
    """
    try:
        carts = session.get('carts', {})
        active = session.get('active_cart', 'cart1')
        cart = carts.get(active, {})
        return cart.get(str(movie_id), 0)
    except Exception:
        return 0