from django.conf import settings
from django.utils.translation import get_language

TELEGRAM_BASE = "https://t.me/"

# .env da turlicha yozilishi mumkin: "firdowear", "@firdowear", "https://t.me/firdowear"
_TELEGRAM_PREFIXES = (
    "https://t.me/",
    "http://t.me/",
    "https://telegram.me/",
    "http://telegram.me/",
    "t.me/",
    "telegram.me/",
)


def telegram_url(value):
    """Telegram manzilini https://t.me/<username> ko'rinishiga keltirish.

    Bo'sh qiymat uchun "" qaytadi — shablonlarda shunda havola yashiriladi.
    """
    value = (value or "").strip()
    if not value:
        return ""
    lowered = value.lower()
    for prefix in _TELEGRAM_PREFIXES:
        if lowered.startswith(prefix):
            value = value[len(prefix):]
            break
    username = value.strip().lstrip("@").strip("/ ").split("/")[0].split("?")[0].strip()
    if not username:
        return ""
    return TELEGRAM_BASE + username


def shop_info(request):
    shop = dict(settings.SHOP)
    shop["address"] = shop["address_ru"] if get_language() == "ru" else shop["address_uz"]

    # Kanal (katalog) va aloqa boti — ikki xil havola, ikki xil o'rin.
    channel_url = telegram_url(shop.get("telegram"))
    bot_url = telegram_url(shop.get("telegram_bot")) or channel_url
    shop["telegram_url"] = channel_url
    shop["telegram_bot_url"] = bot_url
    # Ko'rsatish uchun @ siz foydalanuvchi nomi ("Telegram: @firdowear").
    shop["telegram"] = channel_url.rsplit("/", 1)[-1]
    shop["telegram_bot"] = bot_url.rsplit("/", 1)[-1]
    return {"shop": shop}
