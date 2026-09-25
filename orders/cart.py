"""Sessiyaga asoslangan savat: {variant_id: qty}. Ro'yxatdan o'tish shart emas."""
from decimal import Decimal

from products.models import ProductVariant

KEY = "cart"


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.data = self.session.get(KEY, {})

    def _save(self):
        self.session[KEY] = self.data
        self.session.modified = True

    def add(self, variant_id, qty=1):
        k = str(variant_id)
        self.data[k] = self.data.get(k, 0) + int(qty)
        self._save()

    def set(self, variant_id, qty):
        k = str(variant_id)
        if int(qty) <= 0:
            self.data.pop(k, None)
        else:
            self.data[k] = int(qty)
        self._save()

    def remove(self, variant_id):
        self.data.pop(str(variant_id), None)
        self._save()

    def clear(self):
        self.session.pop(KEY, None)
        self.session.modified = True
        self.data = {}

    def __len__(self):
        return sum(self.data.values())

    def items(self):
        if not self.data:
            return []
        variants = (
            ProductVariant.objects.filter(pk__in=self.data.keys(), is_active=True)
            .select_related("product", "color", "size")
            .prefetch_related("product__images")
        )
        out = []
        for v in variants:
            qty = min(self.data[str(v.pk)], max(v.stock, 0)) if v.stock else 0
            out.append({
                "variant": v, "qty": self.data[str(v.pk)], "available": v.stock,
                "qty_ok": qty == self.data[str(v.pk)],
                "price": v.price, "subtotal": v.price * self.data[str(v.pk)],
            })
        return out

    def total(self):
        return sum((i["subtotal"] for i in self.items()), Decimal(0))
