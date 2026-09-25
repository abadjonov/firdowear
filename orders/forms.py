import re

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Order


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["name", "phone", "delivery", "address", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Ismingiz"), "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67", "inputmode": "tel", "autocomplete": "tel"}),
            "address": forms.TextInput(attrs={"placeholder": _("Tuman, ko'cha, uy")}),
            "comment": forms.Textarea(attrs={"rows": 2, "placeholder": _("Masalan: 16:00 dan keyin qo'ng'iroq qiling")}),
        }

    def clean_phone(self):
        raw = self.cleaned_data["phone"]
        digits = re.sub(r"\D", "", raw)
        if digits.startswith("998") and len(digits) == 12:
            return "+" + digits
        if len(digits) == 9:
            return "+998" + digits
        raise forms.ValidationError(_("Telefon raqamini +998 XX XXX XX XX ko'rinishida kiriting"))

    def clean(self):
        data = super().clean()
        if data.get("delivery") == Order.Delivery.COURIER and not data.get("address"):
            self.add_error("address", _("Yetkazib berish uchun manzil kerak"))
        return data
