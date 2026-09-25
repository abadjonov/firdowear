from django.core.management import call_command
from django.test import TestCase, override_settings

from products.models import Category, Product, SizeType

from .models import Order


@override_settings(LANGUAGE_CODE="uz")
class AccountlessFeaturesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        cls.order = Order.objects.create(name="Ali", phone="+998901234567", total=100000)

    def test_favorite_toggle_ajax(self):
        p = Product.objects.create(name="Test futbolka", slug="test-futbolka", price=50000,
                                   category=Category.objects.first(), size_type=SizeType.objects.first())
        r = self.client.post("/uz/favorites/toggle/", {"product": p.pk}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.json(), {"active": True, "count": 1})
        self.assertEqual(self.client.session["favorites"], [p.pk])
        r = self.client.post("/uz/favorites/toggle/", {"product": p.pk}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.json(), {"active": False, "count": 0})
        self.assertEqual(self.client.get("/uz/favorites/").status_code, 200)

    def test_favorite_unknown_product(self):
        r = self.client.post("/uz/favorites/toggle/", {"product": 999999}, HTTP_X_REQUESTED_WITH="fetch")
        self.assertEqual(r.status_code, 404)

    def test_track_ok_and_history(self):
        r = self.client.post("/uz/orders/track/", {"number": self.order.pk, "phone": "90 123-45-67"})
        self.assertContains(r, f"#{self.order.pk}")
        self.assertEqual(self.client.session["my_orders"], [self.order.pk])
        r = self.client.get("/uz/orders/track/")
        self.assertContains(r, f"#{self.order.pk}")

    def test_track_wrong_phone(self):
        r = self.client.post("/uz/orders/track/", {"number": self.order.pk, "phone": "+998 99 999 99 99"})
        self.assertNotIn("my_orders", self.client.session)
        self.assertIsNone(r.context["found"])

    def test_404_branded(self):
        with self.settings(DEBUG=False):
            r = self.client.get("/uz/yoq-sahifa/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Sahifa topilmadi", status_code=404)
