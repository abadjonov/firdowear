from django.conf import settings
from django.utils.translation import get_language


def shop_info(request):
    shop = dict(settings.SHOP)
    shop["address"] = shop["address_ru"] if get_language() == "ru" else shop["address_uz"]
    return {"shop": shop}
