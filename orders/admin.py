from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateTimeFilter
from unfold.decorators import action, display

from .models import Order, OrderItem
from .telegram import notify_order


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product_name", "color_name", "size_label", "sku", "price", "qty", "subtotal")
    readonly_fields = ("product_name", "color_name", "size_label", "sku", "price", "subtotal")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "name",
        "phone_link",
        "delivery_badge",
        "formatted_total",
        "status",
        "telegram_status",
    )
    list_filter_submit = True
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("delivery", ChoicesDropdownFilter),
        "telegram_sent",
        ("created_at", RangeDateTimeFilter),
    )
    list_editable = ("status",)
    search_fields = ("name", "phone", "items__sku", "items__product_name")
    readonly_fields = ("total", "language", "telegram_sent", "created_at", "updated_at")
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
    fieldsets = (
        (None, {"fields": ("status", "name", "phone", "delivery", "address", "comment")}),
        (
            _("Ichki ma'lumotlar"),
            {"fields": ("admin_note", "total", "language", "telegram_sent", "created_at", "updated_at")},
        ),
    )
    actions = ["restock_cancelled", "resend_telegram"]

    @display(description=_("Telefon"))
    def phone_link(self, obj):
        return format_html(
            '<a href="tel:{0}" class="text-primary-600 font-medium hover:underline">{0}</a>',
            obj.phone,
        )

    @display(
        description=_("Yetkazish"),
        ordering="delivery",
        label={
            Order.Delivery.PICKUP: "info",
            Order.Delivery.COURIER: "success",
        },
    )
    def delivery_badge(self, obj):
        return obj.delivery, obj.get_delivery_display()

    @display(
        description=_("Telegram"),
        boolean=True,
        ordering="telegram_sent",
    )
    def telegram_status(self, obj):
        return obj.telegram_sent

    @display(description=_("Jami"), ordering="total")
    def formatted_total(self, obj):
        return f"{obj.total:,.0f} so'm".replace(",", " ")

    @action(
        description=_("Bekor qilingan buyurtmalar qoldig'ini omborga qaytarish"),
        icon="inventory_2",
    )
    def restock_cancelled(self, request, queryset):
        n = 0
        for order in queryset.filter(status=Order.Status.CANCELLED):
            for i in order.items.select_related("variant"):
                i.variant.stock += i.qty
                i.variant.save(update_fields=["stock"])
                n += 1
        self.message_user(request, f"{n} ta qator omborga qaytarildi")

    @action(
        description=_("Telegram xabarini qayta yuborish"),
        icon="send",
    )
    def resend_telegram(self, request, queryset):
        """Xabari yetib bormagan (telegram_sent=False) buyurtmalar uchun."""
        total, ok = 0, 0
        for order in queryset.prefetch_related("items"):
            total += 1
            admin_url = request.build_absolute_uri(reverse("admin:orders_order_change", args=[order.pk]))
            if notify_order(order, admin_url):
                ok += 1
        self.message_user(
            request,
            f"{ok}/{total} ta xabar Telegramga yuborildi" if ok else "Birorta xabar yuborilmadi — logni tekshiring",
            level="info" if ok else "error",
        )
