"""Telegram: kanal (katalog) va aloqa boti — ikki xil manzil, ikki xil o'rin."""
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings

from products.models import Category, Product, SizeType

from .context_processors import shop_info, telegram_url

SHOP = {
    "name": "Firdo",
    "phone": "+998 90 000 00 00",
    "telegram": "firdowear",          # kanal — katalog
    "telegram_bot": "firdo_shop_bot",  # aloqa boti
    "instagram": "firdowear",
    "address_uz": "Toshkent shahri",
    "address_ru": "г. Ташкент",
    "hours": "09:00 – 21:00",
    "map_embed": "",
}


class TelegramUrlTests(SimpleTestCase):
    def test_username_at_and_full_url_accepted(self):
        """.env da qanday yozilishidan qat'i nazar bitta ko'rinishga keladi."""
        self.assertEqual(telegram_url("firdowear"), "https://t.me/firdowear")
        self.assertEqual(telegram_url("@firdowear"), "https://t.me/firdowear")
        self.assertEqual(telegram_url("https://t.me/firdowear"), "https://t.me/firdowear")
        self.assertEqual(telegram_url("  t.me/firdowear/ "), "https://t.me/firdowear")

    def test_empty_value_has_no_url(self):
        """Bo'sh qoldirilgan bo'lsa shablonda havola chiqmasligi kerak."""
        for value in ("", "   ", None):
            self.assertEqual(telegram_url(value), "")


@override_settings(SHOP=SHOP)
class ShopInfoTelegramTests(SimpleTestCase):
    def test_channel_and_bot_are_separate(self):
        shop = shop_info(RequestFactory().get("/"))["shop"]
        self.assertEqual(shop["telegram"], "firdowear")
        self.assertEqual(shop["telegram_url"], "https://t.me/firdowear")
        self.assertEqual(shop["telegram_bot"], "firdo_shop_bot")
        self.assertEqual(shop["telegram_bot_url"], "https://t.me/firdo_shop_bot")

    def test_bot_falls_back_to_channel(self):
        """SHOP_TELEGRAM_BOT berilmasa, eski sozlash kabi kanal ishlatiladi."""
        with self.settings(SHOP={**SHOP, "telegram_bot": ""}):
            shop = shop_info(RequestFactory().get("/"))["shop"]
        self.assertEqual(shop["telegram_bot_url"], "https://t.me/firdowear")
        self.assertEqual(shop["telegram_bot"], "firdowear")


@override_settings(SHOP=SHOP, LANGUAGE_CODE="uz")
class TelegramLinkTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(
            name="Test futbolka", slug="test-futbolka", price=50000,
            category=Category.objects.create(name="Ustki kiyim", slug="ustki"),
            size_type=SizeType.objects.create(name="Bo'y (sm)", code="height_cm"),
        )

    def test_footer_shows_channel_and_bot(self):
        r = self.client.get("/uz/")
        self.assertContains(r, "Telegram kanal (katalog)")
        self.assertContains(r, 'href="https://t.me/firdowear"')
        self.assertContains(r, 'href="https://t.me/firdo_shop_bot"')

    def test_footer_labels_translated_to_russian(self):
        r = self.client.get("/ru/")
        self.assertContains(r, "Telegram-канал (каталог)")
        self.assertContains(r, "Telegram-бот (связь)")

    def test_contact_button_uses_bot(self):
        r = self.client.get("/uz/contact/")
        self.assertContains(r, 'href="https://t.me/firdo_shop_bot"')
        self.assertContains(r, "https://t.me/firdowear")  # kanal — alohida

    def test_product_order_button_uses_bot(self):
        """«Telegram orqali so'rash» kanalga emas, botga borishi kerak."""
        r = self.client.get(self.product.get_absolute_url())  # /uz/product/test-futbolka/
        self.assertContains(r, 'id="order-btn" href="https://t.me/firdo_shop_bot"')
        self.assertContains(r, 'const tg = "https://t.me/firdo_shop_bot";')
