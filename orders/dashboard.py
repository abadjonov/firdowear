from django.db.models import Sum
from django.utils import timezone

from orders.models import Order
from products.models import Product, ProductVariant


def dashboard_callback(request, context):
    """
    Django Unfold admin bosh sahifasi (dashboard) uchun KPI ko'rsatkichlari.
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total_orders = Order.objects.count()
    new_orders = Order.objects.filter(status=Order.Status.NEW).count()
    today_orders = Order.objects.filter(created_at__gte=today_start).count()

    completed_revenue = (
        Order.objects.filter(
            status__in=[Order.Status.CONFIRMED, Order.Status.READY, Order.Status.DONE]
        ).aggregate(total=Sum("total"))["total"]
        or 0
    )

    active_products = Product.objects.filter(is_active=True).count()
    out_of_stock_variants = ProductVariant.objects.filter(stock=0, is_active=True).count()

    recent_orders = Order.objects.order_by("-created_at")[:5]

    context.update(
        {
            "stats": {
                "total_orders": total_orders,
                "new_orders": new_orders,
                "today_orders": today_orders,
                "completed_revenue": completed_revenue,
                "active_products": active_products,
                "out_of_stock_variants": out_of_stock_variants,
            },
            "recent_orders": recent_orders,
        }
    )
    return context
