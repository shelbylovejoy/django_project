from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from movies.models import Movie
from .utils import calculate_cart_total
from .models import Order, Item
from django.contrib.auth.decorators import login_required


def _ensure_carts_in_session(request):
    """Ensure session has a `carts` dict with three carts and an `active_cart` key.

    Session structure:
    request.session['carts'] = {
        'cart1': {movie_id: quantity, ...},
        'cart2': {...},
        'cart3': {...},
    }
    request.session['active_cart'] = 'cart1'  # one of 'cart1','cart2','cart3'
    """
    if 'carts' not in request.session:
        request.session['carts'] = {'cart1': {}, 'cart2': {}, 'cart3': {}}
    if 'active_cart' not in request.session:
        request.session['active_cart'] = 'cart1'


def _get_active_cart(request):
    _ensure_carts_in_session(request)
    active = None
    # prefer explicit POST (when adding), then GET (when switching), then session
    if hasattr(request, 'POST') and request.POST.get('active'):
        active = request.POST.get('active')
    if not active:
        active = request.GET.get('active') or request.session.get('active_cart')
    if active not in ('cart1', 'cart2', 'cart3'):
        active = 'cart1'
    # persist selected active cart in session
    request.session['active_cart'] = active
    return request.session['carts'].setdefault(active, {})


def index(request):
    # determine and persist active cart first (so session reflects any ?active or POST)
    cart = _get_active_cart(request)
    carts = request.session.get('carts', {})
    active_cart_key = request.session.get('active_cart', 'cart1')
    cart_total = 0
    movies_in_cart = []
    movie_ids = list(cart.keys())
    if movie_ids:
        movies_in_cart = Movie.objects.filter(id__in=movie_ids)
        cart_total = calculate_cart_total(cart, movies_in_cart)

    # compute per-cart item counts safely
    carts_summary = {}
    for k in ('cart1', 'cart2', 'cart3'):
        total_items = 0
        for val in carts.get(k, {}).values():
            try:
                total_items += int(val)
            except Exception:
                continue
        carts_summary[k] = total_items

    template_data = {
        'title': 'Cart',
        'movies_in_cart': movies_in_cart,
        'cart_total': cart_total,
        'active_cart': active_cart_key,
        'carts_summary': carts_summary,
    }
    return render(request, 'cart/index.html', {'template_data': template_data})


def add(request, id):
    get_object_or_404(Movie, id=id)
    if request.method != 'POST':
        return redirect('cart.index')

    cart = _get_active_cart(request)
    quantity = request.POST.get('quantity', '1')
    # normalize quantity to string stored in session (existing code expects strings)
    try:
        q = int(quantity)
        if q < 1:
            q = 1
    except Exception:
        q = 1
    cart[str(id)] = str(q)
    # write back carts container
    request.session['carts'][request.session['active_cart']] = cart
    request.session.modified = True
    return redirect('cart.index')


def clear(request):
    _ensure_carts_in_session(request)
    active = request.GET.get('active') or request.session.get('active_cart', 'cart1')
    if active not in ('cart1', 'cart2', 'cart3'):
        active = 'cart1'
    request.session['carts'][active] = {}
    request.session['active_cart'] = active
    request.session.modified = True
    return redirect('cart.index')


@login_required
def purchase(request):
    cart = _get_active_cart(request)
    movie_ids = list(cart.keys())

    if not movie_ids:
        return redirect('cart.index')

    movies_in_cart = Movie.objects.filter(id__in=movie_ids)
    cart_total = calculate_cart_total(cart, movies_in_cart)

    order = Order()
    order.user = request.user
    order.total = cart_total
    order.save()

    for movie in movies_in_cart:
        item = Item()
        item.movie = movie
        item.price = movie.price
        item.order = order
        item.quantity = int(cart[str(movie.id)])
        item.save()

    # clear only the active cart
    active = request.session.get('active_cart', 'cart1')
    request.session['carts'][active] = {}
    request.session.modified = True
    template_data = {'title': 'Purchase confirmation', 'order_id': order.id}
    return render(request, 'cart/purchase.html', {'template_data': template_data})