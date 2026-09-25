from .cart import Cart


def cart_count(request):
    return {"cart_count": len(Cart(request))}


def favorites(request):
    return {"fav_ids": set(request.session.get("favorites", []))}
