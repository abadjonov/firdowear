"""Buyurtma kelganda do'kon egasiga Telegram orqali xabar. Token va chat ID .env da.

Muhim: mijoz yozgan matn (ism, izoh, manzil) va mahsulot nomlari `<`, `>`, `&`
belgilarini o'z ichiga olishi mumkin. `parse_mode=HTML` bo'lganda Telegram bunday
xabarni "can't parse entities" bilan qaytaradi — shuning uchun hamma dinamik matn
`html.escape` dan o'tkaziladi. Baribir 400 qaytsa, xabar oddiy matnda qayta yuboriladi.
"""
import html
import json
import logging
import re
import time
import urllib.error
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/{method}"
TIMEOUT = 8          # bitta so'rovga sekund
MAX_LEN = 4096       # Telegram bitta xabar uzunligi chegarasi
MAX_RETRY_WAIT = 3   # 429 bo'lsa kutish chegarasi (checkout'ni bloklab qo'ymaslik uchun)


class TelegramError(Exception):
    """Telegram API qaytargan xato: error_code + description (+ 429 da retry_after)."""

    def __init__(self, description, error_code=0, retry_after=None):
        super().__init__(description)
        self.description = description
        self.error_code = error_code
        self.retry_after = retry_after


def fmt(n) -> str:
    return f"{n:,.0f}".replace(",", " ")


def order_message(order, admin_url: str) -> str:
    """Buyurtma haqida HTML xabar. Dinamik qismlar escape qilinadi."""
    e = html.escape
    lines = [f"🛍 <b>Yangi buyurtma #{order.pk}</b>", ""]
    for i in order.items.all():
        lines.append(
            f"• {e(i.product_name)} — {e(i.color_name)}, {e(i.size_label)} × {i.qty} "
            f"= {fmt(i.subtotal)} so'm"
        )
    lines += [
        "",
        f"💰 <b>Jami: {fmt(order.total)} so'm</b>",
        f"👤 {e(order.name)}",
        f"📞 <a href=\"tel:{e(order.phone, quote=True)}\">{e(order.phone)}</a>",
        f"🚚 {e(order.get_delivery_display())}" + (f": {e(order.address)}" if order.address else ""),
    ]
    if order.comment:
        lines.append(f"💬 {e(order.comment)}")
    lines += ["", f"🔗 {e(admin_url)}"]
    return "\n".join(lines)


def to_plain(text: str) -> str:
    """HTML xabarni oddiy matnga aylantirish (zaxira variant)."""
    return html.unescape(re.sub(r"<[^>]+>", "", text))


def split_message(text: str, limit: int = MAX_LEN) -> list:
    """Uzun xabarni qator chegarasida bo'laklarga ajratish."""
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for line in text.split("\n"):
        # bitta qatorning o'zi ham chegaradan uzun bo'lsa — kesamiz
        while len(line) > limit:
            parts.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) + 1 > limit:
            parts.append(cur.rstrip("\n"))
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
    if cur:
        parts.append(cur)
    return [p for p in parts if p]


def _call(method: str, payload: dict, token: str) -> dict:
    """Bitta API so'rovi. `ok=false` yoki tarmoq xatosi — TelegramError."""
    req = urllib.request.Request(
        API_URL.format(token=token, method=method),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
    except urllib.error.HTTPError as err:
        # Telegram xato tavsifini javob tanasida qaytaradi — uni o'qib olamiz
        try:
            data = json.loads(err.read().decode("utf-8", "replace"))
        except Exception:
            data = {}
        raise TelegramError(
            data.get("description") or f"HTTP {err.code}",
            error_code=data.get("error_code") or err.code,
            retry_after=(data.get("parameters") or {}).get("retry_after"),
        ) from None
    except Exception as err:  # DNS, taymaut, TLS...
        raise TelegramError(f"tarmoq xatosi: {err}") from None

    try:
        data = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        raise TelegramError("Telegram javobini o'qib bo'lmadi") from None
    if not data.get("ok"):
        raise TelegramError(
            data.get("description") or "noma'lum xato",
            error_code=data.get("error_code", 0),
            retry_after=(data.get("parameters") or {}).get("retry_after"),
        )
    return data


def get_me() -> dict:
    """Token tekshiruvi: bot haqidagi ma'lumot yoki TelegramError."""
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    if not token:
        raise TelegramError("TELEGRAM_BOT_TOKEN sozlanmagan")
    return _call("getMe", {}, token)["result"]


def _send_chunk(text: str, token: str, chat_id: str) -> None:
    """Bitta bo'lakni yuborish: 429/5xx da qayta urinish, HTML xatosida oddiy matn."""
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    attempts = 0
    while True:
        attempts += 1
        try:
            _call("sendMessage", payload, token)
            return
        except TelegramError as err:
            # Xabarni HTML deb o'qib bo'lmadi — oddiy matnda qayta yuboramiz (bir marta)
            if err.error_code == 400 and "parse" in err.description.lower() and "parse_mode" in payload:
                log.warning("Telegram HTML parse xatosi (%s) — oddiy matnda yuborilmoqda", err.description)
                payload = {k: v for k, v in payload.items() if k != "parse_mode"}
                payload["text"] = to_plain(payload["text"])
                continue
            retryable = err.error_code == 429 or err.error_code >= 500 or err.error_code == 0
            if retryable and attempts < 3:
                wait = min(int(err.retry_after or 1), MAX_RETRY_WAIT)
                log.warning("Telegram %s — %s s dan keyin qayta urinish", err.description, wait)
                time.sleep(wait)
                continue
            raise


def send_message(text: str) -> bool:
    """Xabarni yuborish. Muvaffaqiyat — True; sozlama yo'q/xato — False."""
    token = (settings.TELEGRAM_BOT_TOKEN or "").strip()
    chat_id = (settings.TELEGRAM_CHAT_ID or "").strip()
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID sozlanmagan — xabar yuborilmadi")
        return False
    ok = True
    for chunk in split_message(text):
        try:
            _send_chunk(chunk, token, chat_id)
        except TelegramError as err:
            log.error("Telegram xato (%s): %s", err.error_code or "tarmoq", err.description)
            ok = False
    return ok


def notify_order(order, admin_url: str) -> bool:
    """Buyurtma xabarini yuborish; natijani order.telegram_sent ga yozish."""
    sent = send_message(order_message(order, admin_url))
    if not sent:
        log.error("Buyurtma #%s Telegram xabari yuborilmadi", order.pk)
    order.telegram_sent = sent
    order.save(update_fields=["telegram_sent"])
    return sent
