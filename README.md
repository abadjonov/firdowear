# Firdowear

O'g'il bolalar kiyimi va poyabzali do'koni (0–18 yosh) uchun onlayn vitrina. Django 5, o'zbek + rus.

## Ishga tushirish

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # SECRET_KEY va do'kon ma'lumotlarini to'ldiring
python manage.py migrate
python manage.py seed_catalog   # o'lchamlar, kategoriyalar, ranglar, yosh guruhlari
python manage.py createsuperuser
python manage.py runserver
```

Ko'rish uchun namunaviy mahsulotlar: `python manage.py demo_products` (faqat lokalda).

## Tuzilma

- `products/` — Brand, AgeGroup, Category, SizeType, Size, Color, Product, ProductImage, ProductVariant
- `pages/` — bosh sahifa, manzil
- `templates/` — `base.html` + `products/_card.html` (include)
- `locale/ru/` — interfeys tarjimasi; kontent tarjimasi `django-modeltranslation` orqali (`name_uz`, `name_ru`)

Batafsil reja: [PLAN.md](PLAN.md).

## Kunlik ish (admin)

`/admin/` → Mahsulotlar → mahsulot → pastdagi **Variantlar** jadvalida `Qoldiq` ni o'zgartiring. Tugaganini o'chirmang — `0` qo'ying.

## Telegram botga buyurtma xabari (3-bosqich)

1. Telegramda **@BotFather** → `/newbot` → token oling.
2. Yaratilgan botga o'z akkauntingizdan `/start` yozing (yoki botni do'kon guruhiga qo'shing).
3. Brauzerda oching: `https://api.telegram.org/bot<TOKEN>/getUpdates` → `"chat":{"id": ...}` qiymatini oling.
4. `.env` ga yozing:
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC...
   TELEGRAM_CHAT_ID=987654321
   ```
5. Serverni qayta ishga tushiring. Har bir buyurtma darhol shu chatga keladi (mahsulot, o'lcham, rang, telefon, admin havolasi).

Token bo'lmasa sayt baribir ishlaydi — buyurtma admin panelda (`/admin/orders/order/`) ko'rinadi, faqat xabar yuborilmaydi.

### Xabar kelmayaptimi? Tekshirish

```bash
python manage.py telegram_check            # sozlama + token + sinov xabari
docker compose exec web python manage.py telegram_check   # Docker'da
python manage.py telegram_check --order 12 # 12-buyurtma xabarini qayta yuborish
```

Buyurtmalar ro'yxatida (`/admin/orders/order/`) **«Telegramga yuborildi»** ustuni bor:
`✗` bo'lsa xabar ketmagan. Bir nechta buyurtmani belgilab
**«Telegram xabarini qayta yuborish»** amalini bajarsangiz kifoya.

Sabablari bo'yicha tartib:

| Alomat | Sabab | Yechim |
|---|---|---|
| Logda `TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID sozlanmagan` | `.env` to'ldirilmagan yoki servis qayta ishga tushmagan | `.env` ni yozing → `docker compose up -d` |
| `Unauthorized` (401) | token noto'g'ri/ketirilgan | @BotFather'dan yangi token |
| `chat not found` / `bot was kicked` (400/403) | botga `/start` yozilmagan, chat_id xato, bot guruhdan chiqarilgan | `getUpdates` dan id oling; guruh uchun id `-100...` |
| `can't parse entities` (400) | mijoz matnida `<`, `>`, `&` bor edi | tuzatilgan: matn escape qilinadi, baribir xato bo'lsa oddiy matnda ketadi |
| `tarmoq xatosi` | serverdan `api.telegram.org` ga chiqish yo'q | firewall/DNS/proksini tekshiring |

`TELEGRAM_CHAT_ID` va token'ni `.env` da **qo'shtirnoqsiz** yozing: `TELEGRAM_CHAT_ID=-1001234567890`.

## Buyurtma oqimi

Mahsulot → rang → o'lcham → **Savatga** → Savat → Ism/telefon/yetkazish → **Tasdiqlash** → Telegram xabar + admin.
Buyurtma berilganda variant qoldig'i avtomatik kamayadi. Bekor qilsangiz, admin'da «omborga qaytarish» amali bor.
