from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from products.models import ProductVariant

from .cart import Cart
from .forms import CheckoutForm
from .models import Order, OrderItem
from .telegram import order_message, send_message


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
        return redirect("orders:success", pk=order.pk)

    return render(request, "orders/checkout.html", {"form": form, "items": items, "total": cart.total()})


def success(request, pk):
    if request.session.get("last_order") != pk:
        return redirect("pages:home")
    order = get_object_or_404(Order, pk=pk)
    return render(request, "orders/success.html", {"order": order})
