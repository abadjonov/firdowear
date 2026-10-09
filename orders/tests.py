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


# --- Telegram bildirishnomalari ---
import io
import json
from unittest import mock
from urllib.error import HTTPError

from django.test import SimpleTestCase

from .models import Order
from django.core.management.base import CommandError

from .telegram import get_me, notify_order, order_message, send_message, split_message


def _ok_response(result=None):
    """urlopen o'rniga: muvaffaqiyatli Telegram javobi."""
    payload = {"ok": True, "result": {"message_id": 1} if result is None else result}

    class R:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(payload).encode()

    return R()


def _http_error(code, description, retry_after=None):
    """Telegram xato javobi: tana ichida error_code + description."""
    body = {"ok": False, "error_code": code, "description": description}
    if retry_after is not None:
        body["parameters"] = {"retry_after": retry_after}
    return HTTPError("https://api.telegram.org", code, description, {},
                     io.BytesIO(json.dumps(body).encode()))


class _Item:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    @property
    def subtotal(self):
        return self.price * self.qty


class _Stub:
    """order_message() uchun yengil nusxa (bazaga tegmasdan)."""

    def __init__(self, items=(), **kw):
        self.__dict__.update(kw)

        class _Items:
            def all(self_inner):
                return items

        self.items = _Items()

    def get_delivery_display(self):
        return "Yetkazib berish"


@override_settings(TELEGRAM_BOT_TOKEN="123456:TESTTOKEN", TELEGRAM_CHAT_ID="-100123")
class TelegramMessageTests(SimpleTestCase):
    def test_message_escapes_html(self):
        """Mijoz matnidagi < > & xabarni buzmasligi kerak (parse_mode=HTML)."""
        o = _Stub(
            items=[_Item(product_name='Futbolka "Classic" & short', color_name="Oq/Qora",
                         size_label="5-6 yosh", qty=2, price=75000)],
            pk=7, name="Ali & Vali", phone="+998901234567", address="5-uy <yonga>",
            comment="Iltimos <3 & tezroq", total=150000,
        )
        msg = order_message(o, "https://firdo.uz/admin/orders/order/7/change/")
        self.assertIn("Ali &amp; Vali", msg)
        self.assertIn("Iltimos &lt;3 &amp; tezroq", msg)
        self.assertIn("Futbolka &quot;Classic&quot; &amp; short", msg)
        self.assertIn("5-uy &lt;yonga&gt;", msg)
        # o'z teglarimiz buzilmagan
        self.assertIn("<b>Yangi buyurtma #7</b>", msg)
        self.assertIn('<a href="tel:+998901234567">', msg)

    def test_split_message(self):
        text = "\n".join(f"qator {i}" for i in range(1500))
        parts = split_message(text)
        self.assertGreater(len(parts), 1)
        self.assertTrue(all(len(p) <= 4096 for p in parts))
        self.assertEqual("\n".join(parts), text)

    def test_success_sends_html_payload(self):
        with mock.patch("urllib.request.urlopen", return_value=_ok_response()) as m:
            self.assertTrue(send_message("salom"))
        body = json.loads(m.call_args[0][0].data.decode())
        self.assertEqual(body["chat_id"], "-100123")
        self.assertEqual(body["parse_mode"], "HTML")

    def test_html_parse_error_falls_back_to_plain(self):
        """Telegram 'can't parse entities' desa — xabar oddiy matnda baribir yetib boradi."""
        with mock.patch("urllib.request.urlopen", side_effect=[
            _http_error(400, "Bad Request: can't parse entities: unsupported start tag"),
            _ok_response(),
        ]) as m:
            self.assertTrue(send_message("salom <3 & ok"))
        bodies = [json.loads(c[0][0].data.decode()) for c in m.call_args_list]
        self.assertEqual(bodies[0]["parse_mode"], "HTML")
        self.assertNotIn("parse_mode", bodies[1])
        self.assertEqual(bodies[1]["text"], "salom <3 & ok")

    def test_plain_fallback_is_bounded(self):
        """Oddiy matn ham rad etilsa — cheksiz urinish bo'lmasligi kerak."""
        with mock.patch("urllib.request.urlopen", side_effect=[
            _http_error(400, "Bad Request: can't parse entities"),
            _http_error(400, "Bad Request: can't parse entities"),
        ]) as m:
            with self.assertLogs("orders.telegram", level="ERROR"):
                self.assertFalse(send_message("salom"))
        self.assertEqual(m.call_count, 2)

    def test_unauthorized_logs_description(self):
        """Eski kod faqat 'HTTP Error 401' yozardi — endi sabab ko'rinadi."""
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(401, "Unauthorized")):
            with self.assertLogs("orders.telegram", level="ERROR") as cm:
                self.assertFalse(send_message("salom"))
        self.assertIn("Unauthorized", "".join(cm.output))

    def test_chat_not_found(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=_http_error(400, "Bad Request: chat not found")):
            with self.assertLogs("orders.telegram", level="ERROR"):
                self.assertFalse(send_message("salom"))

    def test_too_many_requests_is_retried(self):
        with mock.patch("urllib.request.urlopen", side_effect=[
            _http_error(429, "Too Many Requests: retry after 1", retry_after=1),
            _ok_response(),
        ]), mock.patch("orders.telegram.time.sleep") as sleep:
            self.assertTrue(send_message("salom"))
        sleep.assert_called_once_with(1)

    def test_network_error_does_not_raise(self):
        with mock.patch("urllib.request.urlopen", side_effect=OSError("timed out")):
            with self.assertLogs("orders.telegram", level="ERROR"):
                self.assertFalse(send_message("salom"))

    def test_get_me(self):
        with mock.patch("urllib.request.urlopen",
                        return_value=_ok_response({"id": 5, "username": "firdo_bot"})):
            self.assertEqual(get_me()["username"], "firdo_bot")

    def test_check_command_happy_path(self):
        out = io.StringIO()
        with mock.patch("urllib.request.urlopen",
                        return_value=_ok_response({"id": 5, "username": "firdo_bot"})):
            call_command("telegram_check", stdout=out)
        self.assertIn("firdo_bot", out.getvalue())
        self.assertIn("Xabar yetib bordi", out.getvalue())

    def test_check_command_without_settings(self):
        with self.settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID=""):
            with self.assertRaises(CommandError):
                call_command("telegram_check", stdout=io.StringIO(), stderr=io.StringIO())

    def test_check_command_bad_token(self):
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(401, "Unauthorized")):
            with self.assertRaises(CommandError) as cm:
                call_command("telegram_check", stdout=io.StringIO(), stderr=io.StringIO())
        self.assertIn("BotFather", str(cm.exception))

    def test_missing_settings(self):
        with self.settings(TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID=""):
            with self.assertLogs("orders.telegram", level="WARNING"):
                self.assertFalse(send_message("salom"))


@override_settings(TELEGRAM_BOT_TOKEN="123456:TESTTOKEN", TELEGRAM_CHAT_ID="-100123", LANGUAGE_CODE="uz")
class TelegramOrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_catalog", verbosity=0)
        cls.order = Order.objects.create(name="Ali & Vali", phone="+998901234567",
                                         comment="<3", total=100000)

    def test_notify_order_marks_sent(self):
        with mock.patch("urllib.request.urlopen", return_value=_ok_response()):
            self.assertTrue(notify_order(self.order, "https://firdo.uz/admin/"))
        self.order.refresh_from_db()
        self.assertTrue(self.order.telegram_sent)

    def test_notify_order_marks_failure(self):
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(401, "Unauthorized")):
            with self.assertLogs("orders.telegram", level="ERROR"):
                self.assertFalse(notify_order(self.order, "https://firdo.uz/admin/"))
        self.order.refresh_from_db()
        self.assertFalse(self.order.telegram_sent)

    def test_checkout_survives_telegram_failure(self):
        """Telegram yotiq bo'lsa ham buyurtma saqlanishi kerak."""
        from products.models import Color, Product, ProductVariant, Size, SizeType

        p = Product.objects.create(name="Test & futbolka", slug="test-tg", price=50000,
                                   category=Category.objects.first(), size_type=SizeType.objects.first())
        v = ProductVariant.objects.create(
            product=p, color=Color.objects.first(), size=Size.objects.first(),
            sku="TG-1", stock=3, is_active=True,
        )
        s = self.client.session
        s["cart"] = {str(v.pk): 1}
        s.save()
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(401, "Unauthorized")):
            with self.assertLogs("orders.telegram", level="ERROR"):
                r = self.client.post("/uz/checkout/", {
                    "name": "Ali", "phone": "+998901234567", "delivery": "pickup",
                    "address": "", "comment": "",
                })
        order = Order.objects.latest("pk")
        self.assertRedirects(r, f"/uz/order/{order.pk}/success/", fetch_redirect_response=False)
        self.assertFalse(order.telegram_sent)
        self.assertEqual(order.items.count(), 1)
