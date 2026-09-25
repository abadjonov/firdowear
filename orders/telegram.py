"""Buyurtma kelganda do'kon egasiga Telegram orqali xabar. Token va chat ID .env da."""
import json
import logging
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)


def send_message(text: str) -> bool:
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID sozlanmagan — xabar yuborilmadi")
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status == 200
    except Exception as e:  # tarmoq xatosi buyurtmani to'xtatmasin
        log.error("Telegram xato: %s", e)
        return False


def fmt(n) -> str:
    return f"{n:,.0f}".replace(",", " ")


def order_message(order, admin_url: str) -> str:
    lines = [f"🛍 <b>Yangi buyurtma #{order.pk}</b>", ""]
    for i in order.items.all():
        lines.append(f"• {i.product_name} — {i.color_name}, {i.size_label} × {i.qty} = {fmt(i.subtotal)} so'm")
    lines += [
        "",
        f"💰 <b>Jami: {fmt(order.total)} so'm</b>",
        f"👤 {order.name}",
        f"📞 <a href=\"tel:{order.phone}\">{order.phone}</a>",
        f"🚚 {order.get_delivery_display()}" + (f": {order.address}" if order.address else ""),
    ]
    if order.comment:
        lines.append(f"💬 {order.comment}")
    lines += ["", f"🔗 {admin_url}"]
    return "\n".join(lines)
