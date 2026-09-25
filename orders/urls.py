from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/", views.cart_add, name="cart_add"),
    path("cart/update/", views.cart_update, name="cart_update"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/<int:pk>/success/", views.success, name="success"),
    path("favorites/", views.favorites, name="favorites"),
    path("favorites/toggle/", views.favorite_toggle, name="favorite_toggle"),
    path("orders/track/", views.track, name="track"),
]
