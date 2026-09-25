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
