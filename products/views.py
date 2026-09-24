from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import AgeGroup, Brand, Category, Color, Product, Size

SORTS = {
    "new": "-created_at",
    "price_asc": "price",
    "price_desc": "-price",
}


def _base_qs():
    return (
        Product.objects.active()
        .select_related("category", "brand")
        .prefetch_related("images", "variants__color", "variants__size")
    )


def _apply_filters(request, qs):
    g = request.GET
    if g.get("q"):
        q = g["q"].strip()
        qs = qs.filter(
            Q(name_uz__icontains=q) | Q(name_ru__icontains=q)
            | Q(brand__name__icontains=q) | Q(category__name_uz__icontains=q) | Q(category__name_ru__icontains=q)
        )
    if g.get("age"):
        qs = qs.filter(age_groups__slug=g["age"])
    if g.get("brand"):
        qs = qs.filter(brand__slug=g["brand"])
    if g.get("color"):
        qs = qs.filter(variants__color__slug=g["color"], variants__stock__gt=0)
    if g.get("size"):
        qs = qs.filter(variants__size__code=g["size"], variants__stock__gt=0)
    if g.get("season"):
        qs = qs.filter(season=g["season"])
    if g.get("min"):
        qs = qs.filter(price__gte=g["min"])
    if g.get("max"):
        qs = qs.filter(price__lte=g["max"])
    if g.get("sale"):
        qs = qs.filter(sale_price__isnull=False, sale_price__lt=models_F("price"))
    if g.get("new"):
        qs = qs.filter(is_new=True)
    if g.get("stock"):
        qs = qs.in_stock()
    qs = qs.order_by(SORTS.get(g.get("sort"), "-created_at"))
    return qs.distinct()


def models_F(name):
    from django.db.models import F
    return F(name)


def _render_catalog(request, qs, title, **extra):
    qs = _apply_filters(request, qs)
    page = Paginator(qs, 24).get_page(request.GET.get("page"))
    query = request.GET.copy()
    query.pop("page", None)
    ctx = {
        "page": page,
        "title": title,
        "querystring": query.urlencode(),
        "filter_age_groups": AgeGroup.objects.filter(is_active=True),
        "filter_brands": Brand.objects.filter(is_active=True, products__isnull=False).distinct(),
        "filter_colors": Color.objects.all(),
        "filter_sizes": Size.objects.select_related("size_type"),
        "seasons": Product.Season.choices,
        **extra,
    }
    return render(request, "products/catalog.html", ctx)


def catalog(request):
    return _render_catalog(request, _base_qs(), "Katalog")


def category(request, slug):
    cat = get_object_or_404(Category, slug=slug, is_active=True)
    qs = _base_qs().filter(category_id__in=cat.descendant_ids())
    return _render_catalog(request, qs, cat.name, category=cat, children=cat.children.filter(is_active=True))


def age_group(request, slug):
    ag = get_object_or_404(AgeGroup, slug=slug, is_active=True)
    return _render_catalog(request, _base_qs().filter(age_groups=ag), ag.name, age_group=ag)


def brand(request, slug):
    b = get_object_or_404(Brand, slug=slug, is_active=True)
    return _render_catalog(request, _base_qs().filter(brand=b), b.name, brand=b)


def detail(request, slug):
    product = get_object_or_404(_base_qs(), slug=slug)
    variants = [v for v in product.variants.all() if v.is_active]
    matrix = {}  # color_id -> [variant, ...]
    for v in variants:
        matrix.setdefault(v.color_id, []).append(v)
    related = (
        _base_qs().filter(category=product.category).exclude(pk=product.pk)[:8]
    )
    return render(request, "products/detail.html", {
        "product": product,
        "colors": product.available_colors(),
        "matrix": matrix,
        "related": related,
    })
