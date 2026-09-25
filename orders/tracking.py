"""Akkauntsiz qulayliklar: sessiyadagi sevimlilar va buyurtmalar tarixi."""
import re

FAV_KEY = "favorites"
ORDERS_KEY = "my_orders"
MAX_FAV = 200
MAX_ORDERS = 50


def get_favorites(session):
    return list(session.get(FAV_KEY, []))


def toggle_favorite(session, product_id):
    favs = get_favorites(session)
    if product_id in favs:
        favs.remove(product_id)
        active = False
    else:
        favs.insert(0, product_id)
        favs = favs[:MAX_FAV]
        active = True
    session[FAV_KEY] = favs
    session.modified = True
    return active, len(favs)


def remember_order(session, order_id):
    ids = [i for i in session.get(ORDERS_KEY, []) if i != order_id]
    session[ORDERS_KEY] = ([order_id] + ids)[:MAX_ORDERS]
    session.modified = True


def normalize_phone(value):
    """Faqat raqamlar; oxirgi 9 ta raqam (998 kodisiz) solishtiriladi."""
    digits = re.sub(r"\D", "", value or "")
    return digits[-9:]
