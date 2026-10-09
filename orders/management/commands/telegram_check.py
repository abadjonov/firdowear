"""Telegram bildirishnomalarini tekshirish va qayta yuborish.

Ishlatish:
    python manage.py telegram_check               # sozlama + getMe + test xabar
    python manage.py telegram_check --order 12    # 12-buyurtma xabarini qayta yuborish
    python manage.py telegram_check --no-send     # faqat sozlamani tekshirish (tarmoqsiz)

Docker'da:  docker compose exec web python manage.py telegram_check
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from orders.telegram import TelegramError, get_me, order_message, send_message

HINTS = [
    (401, "Token noto'g'ri yoki bekor qilingan. @BotFather → /mybots → bot → API Token'ni "
          "qayta ko'chiring (yoki /revoke qilingan bo'lsa yangisini yozing)."),
    (404, "Token noto'g'ri: API_URL'da xatolik yoki bot o'chirilgan. @BotFather'dan tekshiring."),
    (403, "Bot bu chatga yozolmaydi. Guruhda bo'lsa — bot guruhdan chiqarilgan yoki "
          "'Send messages' huquqi yo'q. Shaxsiy chat bo'lsa — foydalanuvchi botni bloklagan."),
    (400, "chat_id noto'g'ri yoki bot bu chatda emas. Shaxsiy chat uchun botga avval /start "
          "yozing, keyin https://api.telegram.org/bot<TOKEN>/getUpdates dan id'ni oling. "
          "Guruh uchun id manfiy (-100...) bo'ladi va bot guruhga a'zo bo'lishi shart."),
    (429, "Juda ko'p so'rov. Bir necha sekund kuting."),
    (0, "Server api.telegram.org ga chiqolmadi: chiquvchi internet, DNS yoki firewall. "
        "Konteyner ichidan tekshiring: docker compose exec web python -c "
        "\"import urllib.request;print(urllib.request.urlopen('https://api.telegram.org',timeout=5).status)\""),
]


def hint_for(code: int) -> str:
    for c, text in HINTS:
        if c == code:
            return text
    return ""


def mask(token: str) -> str:
    """Tokenni logda yashirish: faqat boshi va oxiri."""
    if not token:
        return "(bo'sh)"
    return f"{token[:6]}...{token[-4:]}" if len(token) > 14 else "(juda qisqa — noto'g'ri)"


class Command(BaseCommand):
    help = "Telegram bot sozlamasini tekshiradi va sinov xabarini yuboradi"

    def add_arguments(self, parser):
        parser.add_argument("--order", type=int, help="shu buyurtma xabarini qayta yuborish")
        parser.add_argument("--text", default=None, help="o'rniga yuboriladigan matn")
        parser.add_argument("--no-send", action="store_true", help="faqat sozlamani tekshirish")

    def handle(self, *args, **opts):
        token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
        chat_id = (settings.TELEGRAM_CHAT_ID or "").strip()

        self.stdout.write("1) Sozlama (.env):")
        self.stdout.write(f"   TELEGRAM_BOT_TOKEN = {mask(token)}")
        shown_chat = chat_id or "(bo'sh)"
        self.stdout.write(f"   TELEGRAM_CHAT_ID   = {shown_chat}")
        if not token or not chat_id:
            raise CommandError(
                "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID .env da yo'q yoki bo'sh. "
                "Shu sababli xabar yuborilmaydi. .env ni to'ldiring va servisni qayta ishga "
                "tushiring (docker compose up -d)."
            )
        if '"' in token or "'" in token or " " in token:
            self.stdout.write(self.style.WARNING(
                "   ⚠ Tokenda tirnoq/bo'shliq bor — .env da qiymatni qo'shtirnoqsiz yozing."))
        if opts["no_send"]:
            self.stdout.write(self.style.SUCCESS("Sozlama joyida (--no-send: tarmoq tekshirilmadi)."))
            return

        self.stdout.write("2) Token tekshiruvi (getMe):")
        try:
            me = get_me()
            self.stdout.write(f"   ✅ Bot: @{me.get('username')} (id={me.get('id')})")
        except TelegramError as err:
            self._fail(err)

        if opts["order"]:
            self._resend(opts["order"])
            return

        text = opts["text"] or "✅ Firdo do'koni: Telegram bildirishnomasi ishlayapti."
        self.stdout.write(f"3) Sinov xabari chat_id={chat_id} ga yuborilmoqda...")
        if send_message(text):
            self.stdout.write(self.style.SUCCESS("   ✅ Xabar yetib bordi. Telegram'dan tekshiring."))
        else:
            raise CommandError(
                "Xabar yuborilmadi — sababi yuqoridagi logda. "
                "Eng ko'p uchraydigan holat: botga /start yozilmagan yoki chat_id noto'g'ri."
            )

    def _resend(self, pk):
        from django.urls import reverse

        from orders.models import Order

        order = Order.objects.filter(pk=pk).prefetch_related("items").first()
        if not order:
            raise CommandError(f"#{pk} buyurtma topilmadi.")
        base = (settings.SITE_URL or "").rstrip("/")
        path = reverse("admin:orders_order_change", args=[order.pk])
        admin_url = f"{base}{path}" if base else path
        self.stdout.write(f"3) #{pk} buyurtma xabari qayta yuborilmoqda...")
        if send_message(order_message(order, admin_url)):
            order.telegram_sent = True
            order.save(update_fields=["telegram_sent"])
            self.stdout.write(self.style.SUCCESS(f"   ✅ #{pk} xabari yuborildi."))
        else:
            raise CommandError(f"#{pk} xabari yuborilmadi — logni ko'ring.")

    def _fail(self, err):
        hint = hint_for(err.error_code)
        code = err.error_code or "tarmoq"
        msg = f"Telegram xatosi ({code}): {err.description}"
        if hint:
            msg += f"\n   → {hint}"
        raise CommandError(msg)
