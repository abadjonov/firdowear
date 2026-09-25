from django.db import models
from django.utils.translation import gettext_lazy as _

from products.models import ProductVariant


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", _("Yangi")
        CONFIRMED = "confirmed", _("Tasdiqlandi")
        READY = "ready", _("Tayyor / yetkazilmoqda")
        DONE = "done", _("Bajarildi")
        CANCELLED = "cancelled", _("Bekor qilindi")

    class Delivery(models.TextChoices):
        PICKUP = "pickup", _("Do'kondan olib ketish")
        COURIER = "courier", _("Yetkazib berish")

    name = models.CharField(_("Ism"), max_length=100)
    phone = models.CharField(_("Telefon"), max_length=20)
    delivery = models.CharField(_("Yetkazish"), max_length=10, choices=Delivery.choices, default=Delivery.PICKUP)
    address = models.CharField(_("Manzil"), max_length=300, blank=True)
    comment = models.TextField(_("Izoh"), blank=True)
    status = models.CharField(_("Holat"), max_length=10, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField(_("Jami"), max_digits=12, decimal_places=0, default=0)
    language = models.CharField(max_length=5, default="uz")
    telegram_sent = models.BooleanField(_("Telegramga yuborildi"), default=False)
    admin_note = models.TextField(_("Ichki izoh"), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Buyurtma")
        verbose_name_plural = _("Buyurtmalar")

    def __str__(self):
        return f"#{self.pk} {self.name} {self.phone}"

    def recalc(self):
        self.total = sum(i.price * i.qty for i in self.items.all())
        self.save(update_fields=["total"])


class OrderItem(models.Model):
    """Variantga bog'lanadi (qaysi o'lcham/rang ketgani saqlanadi); narx buyurtma paytidagi nusxa."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT, verbose_name=_("Variant"))
    product_name = models.CharField(max_length=200)
    color_name = models.CharField(max_length=50)
    size_label = models.CharField(max_length=60)
    sku = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=12, decimal_places=0)
    qty = models.PositiveSmallIntegerField(_("Soni"), default=1)

    class Meta:
        verbose_name = _("Buyurtma qatori")
        verbose_name_plural = _("Buyurtma qatorlari")

    def __str__(self):
        return f"{self.product_name} {self.color_name} {self.size_label} ×{self.qty}"

    @property
    def subtotal(self):
        return self.price * self.qty
