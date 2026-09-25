from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from products.models import Product, ProductVariant

from .cart import Cart
from .forms import CheckoutForm, TrackForm
from .models import Order, OrderItem
from .telegram import order_message, send_message
from .tracking import ORDERS_KEY, get_favorites, normalize_phone, remember_order, toggle_favorite


def cart_view(request):
    cart = Cart(request)
    return render(request, "orders/cart.html", {"items": cart.items(), "total": cart.total()})


@require_POST
def cart_add(request):
    v = get_object_or_404(ProductVariant, pk=request.POST.get("variant"), is_active=True)
    cart = Cart(request)
    if v.stock <= 0:
        messages.error(request, _("Bu o'lcham tugagan"))
    else:
        cart.add(v.pk, request.POST.get("qty", 1))
        messages.success(request, _("Savatga qo'shildi: %(name)s") % {"name": f"{v.product.name}, {v.color.name}, {v.size.label}"})
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"count": len(cart)})
    return redirect(request.POST.get("next") or "orders:cart")


@require_POST
def cart_update(request):
    cart = Cart(request)
    for k, val in request.POST.items():
        if k.startswith("qty_"):
            cart.set(k[4:], val or 0)
    if request.POST.get("remove"):
        cart.remove(request.POST["remove"])
    return redirect("orders:cart")


def checkout(request):
    cart = Cart(request)
    items = cart.items()
    if not items:
        return redirect("orders:cart")
    if any(not i["qty_ok"] for i in items):
        messages.error(request, _("Ba'zi mahsulotlar yetarli emas, savatni tekshiring"))
        return redirect("orders:cart")

    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            order = form.save(commit=False)
            order.language = get_language() or "uz"
            order.save()
            for i in items:
                v = i["variant"]
                OrderItem.objects.create(
                    order=order, variant=v, product_name=v.product.name, color_name=v.color.name,
                    size_label=v.size.label, sku=v.sku, price=v.price, qty=i["qty"],
                )
                # Qoldiqni kamaytirish: do'kon egasi tasdiqlaguncha bron
                ProductVariant.objects.filter(pk=v.pk).update(stock=max(v.stock - i["qty"], 0))
            order.recalc()
        admin_url = request.build_absolute_uri(reverse("admin:orders_order_change", args=[order.pk]))
        order.telegram_sent = send_message(order_message(order, admin_url))
        order.save(update_fields=["telegram_sent"])
        cart.clear()
        request.session["last_order"] = order.pk
        remember_order(request.session, order.pk)
        return redirect("orders:success", pk=order.pk)

    return render(request, "orders/checkout.html", {"form": form, "items": items, "total": cart.total()})


def success(request, pk):
    if request.session.get("last_order") != pk:
        return redirect("pages:home")
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/success.html", {"order": order})


# --- Sevimlilar (sessiyada) ---
@require_POST
def favorite_toggle(request):
    try:
        pid = int(request.POST.get("product", ""))
    except ValueError:
        return JsonResponse({"error": "bad product"}, status=400)
    if not Product.objects.active().filter(pk=pid).exists() and pid not in get_favorites(request.session):
        return JsonResponse({"error": "not found"}, status=404)
    active, count = toggle_favorite(request.session, pid)
    if request.headers.get("x-requested-with") == "fetch":
        return JsonResponse({"active": active, "count": count})
    return redirect(request.POST.get("next") or "orders:favorites")


def favorites(request):
    ids = get_favorites(request.session)
    qs = Product.objects.active().filter(pk__in=ids).select_related("brand").prefetch_related("images", "variants")
    by_id = {p.pk: p for p in qs}
    products = [by_id[i] for i in ids if i in by_id]
    return render(request, "orders/favorites.html", {"products": products})


# --- Buyurtmani tekshirish ---
def track(request):
    form = TrackForm(request.POST or None)
    found = None
    if request.method == "POST" and form.is_valid():
        order = Order.objects.filter(pk=form.cleaned_data["number"]).prefetch_related("items").first()
        if order and normalize_phone(order.phone) == normalize_phone(form.cleaned_data["phone"]):
            found = order
            remember_order(request.session, order.pk)
        else:
            form.add_error(None, _("Buyurtma topilmadi. Raqam va telefonni tekshiring."))
    history = Order.objects.filter(pk__in=request.session.get(ORDERS_KEY, [])).prefetch_related("items")
    return render(request, "orders/track.html", {"form": form, "found": found, "history": history})
