from django.shortcuts import render

from products.models import Category, Product


def _qs():
    return Product.objects.active().select_related("category", "brand").prefetch_related("images", "variants")


def home(request):
    return render(request, "pages/home.html", {
        "featured": _qs().filter(is_featured=True)[:8],
        "new": _qs().filter(is_new=True)[:8],
        "sale": [p for p in _qs().filter(sale_price__isnull=False)[:16] if p.is_on_sale][:8],
        "top_categories": Category.objects.filter(parent__isnull=True, is_active=True),
    })


def contact(request):
    return render(request, "pages/contact.html")
