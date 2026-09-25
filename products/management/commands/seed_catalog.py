"""Boshlang'ich ma'lumotlar: o'lchamlar, kategoriyalar, ranglar, yosh guruhlari (uz/ru).
Ishlatish:  python manage.py seed_catalog
Qayta ishga tushirish xavfsiz — mavjudini o'zgartirmaydi.
"""
from django.core.management.base import BaseCommand

from products.models import AgeGroup, Category, Color, Size, SizeType

AGE_GROUPS = [
    ("chaqaloq", "Chaqaloq", "Малыши", 0, 24, 50, 92),
    ("kichkintoy", "Kichkintoy", "Дошкольники", 24, 84, 92, 122),
    ("maktab", "Maktab yoshi", "Школьники", 84, 156, 122, 152),
    ("osmir", "O'smir", "Подростки", 156, 216, 152, 182),
]

# (sm, yosh_dan, yosh_gacha, uz yorliq, ru yorliq)
HEIGHTS = [
    (50, 0, 0.1, "0–1 oy", "0–1 мес"), (56, 0.1, 0.25, "1–3 oy", "1–3 мес"), (62, 0.25, 0.5, "3–6 oy", "3–6 мес"),
    (68, 0.5, 0.75, "6–9 oy", "6–9 мес"), (74, 0.75, 1, "9–12 oy", "9–12 мес"), (80, 1, 1.5, "12–18 oy", "12–18 мес"),
    (86, 1.5, 2, "18–24 oy", "18–24 мес"), (92, 2, 3, "2 yosh", "2 года"), (98, 3, 4, "3 yosh", "3 года"),
    (104, 4, 5, "4 yosh", "4 года"), (110, 5, 6, "5 yosh", "5 лет"), (116, 6, 7, "6 yosh", "6 лет"),
    (122, 7, 8, "7 yosh", "7 лет"), (128, 8, 9, "8 yosh", "8 лет"), (134, 9, 10, "9 yosh", "9 лет"),
    (140, 10, 11, "10 yosh", "10 лет"), (146, 11, 12, "11 yosh", "11 лет"), (152, 12, 13, "12 yosh", "12 лет"),
    (158, 13, 14, "13 yosh", "13 лет"), (164, 14, 15, "14 yosh", "14 лет"), (170, 15, 16, "15–16 yosh", "15–16 лет"),
    (176, 16, 17, "16–17 yosh", "16–17 лет"), (182, 17, 18, "17–18 yosh", "17–18 лет"),
]

COLORS = [
    ("qora", "Qora", "Чёрный", "#111111"), ("oq", "Oq", "Белый", "#ffffff"), ("kulrang", "Kulrang", "Серый", "#9ca3af"),
    ("toq-kok", "To'q ko'k", "Тёмно-синий", "#1e3a8a"), ("kok", "Ko'k", "Синий", "#2563eb"), ("havorang", "Havorang", "Голубой", "#7dd3fc"),
    ("haki", "Haki", "Хаки", "#6b7a4a"), ("bej", "Bej", "Бежевый", "#d6c3a5"), ("jigarrang", "Jigarrang", "Коричневый", "#78350f"),
    ("yashil", "Yashil", "Зелёный", "#16a34a"), ("qizil", "Qizil", "Красный", "#dc2626"), ("sariq", "Sariq", "Жёлтый", "#facc15"),
    ("bordo", "Bordo", "Бордовый", "#7f1d1d"), ("kop-rangli", "Ko'p rangli", "Разноцветный", "#a855f7"),
]

# slug, uz, ru, size_type, children[(slug, uz, ru)]
CATEGORIES = [
    ("ustki-kiyim", "Ustki kiyim", "Верхняя одежда (топы)", "height_cm", [
        ("futbolka", "Futbolka", "Футболка"), ("polo", "Polo", "Поло"), ("koylak", "Ko'ylak", "Рубашка"),
        ("hudi", "Hoodie / tolstovka", "Худи / толстовка"), ("sviter", "Sviter / jemper", "Свитер / джемпер"),
        ("longsliv", "Longsliv", "Лонгслив"), ("termal", "Termal kiyim", "Термобельё"),
    ]),
    ("pastki-kiyim", "Pastki kiyim", "Брюки и шорты", "height_cm", [
        ("jinsi", "Jinsi", "Джинсы"), ("klassik-shim", "Klassik shim", "Классические брюки"),
        ("sport-shim", "Sport shim", "Спортивные штаны"), ("shorti", "Shorti", "Шорты"), ("bridzhi", "Bridji", "Бриджи"),
    ]),
    ("tashqi-kiyim", "Tashqi kiyim", "Куртки и пальто", "height_cm", [
        ("kurtka", "Kurtka", "Куртка"), ("parka", "Parka / pukhovik", "Парка / пуховик"), ("palto", "Palto", "Пальто"),
        ("jilet", "Jilet", "Жилет"), ("vetrovka", "Vetrovka", "Ветровка"), ("kombinezon", "Kombinezon", "Комбинезон"),
    ]),
    ("sport", "Sport", "Спорт", "height_cm", [
        ("sport-kostyum", "Sport kostyum", "Спортивный костюм"), ("sport-futbolka", "Sport futbolka", "Спортивная футболка"),
        ("sport-shorti", "Sport shorti", "Спортивные шорты"),
    ]),
    ("maktab", "Maktab", "Школа", "height_cm", [
        ("maktab-koylak", "Maktab ko'ylagi", "Школьная рубашка"), ("maktab-shim", "Maktab shimi", "Школьные брюки"),
        ("maktab-jilet", "Maktab jileti", "Школьный жилет"), ("maktab-kostyum", "Maktab kostyumi", "Школьный костюм"),
        ("galstuk", "Galstuk / bobochka", "Галстук / бабочка"),
    ]),
    ("ichki-kiyim", "Ichki kiyim", "Бельё и носки", "height_cm", [
        ("trusi", "Trusi", "Трусы"), ("mayka", "Mayka", "Майка"), ("paypoq", "Paypoq", "Носки"), ("pijama", "Pijama", "Пижама"),
    ]),
    ("poyabzal", "Poyabzal", "Обувь", "eu_shoe", [
        ("krossovka", "Krossovka", "Кроссовки"), ("botinka", "Botinka", "Ботинки"), ("tufli", "Tufli", "Туфли"),
        ("sandal", "Sandal", "Сандалии"), ("rezina-etik", "Rezina etik", "Резиновые сапоги"), ("qishki-etik", "Qishki etik", "Зимние сапоги"),
        ("shippak", "Shippak", "Тапочки / сланцы"),
    ]),
    ("aksessuar", "Aksessuarlar", "Аксессуары", "one_size", [
        ("shapka", "Shapka", "Шапка"), ("sharf", "Sharf", "Шарф"), ("qolqop", "Qo'lqop", "Перчатки"),
        ("kamar", "Kamar", "Ремень"), ("ryukzak", "Ryukzak", "Рюкзак"), ("kepka", "Kepka", "Кепка"),
    ]),
    ("komplekt", "Komplektlar", "Комплекты", "height_cm", [
        ("komplekt-2", "2 qismli komplekt", "Комплект 2 предмета"), ("komplekt-3", "3 qismli komplekt", "Комплект 3 предмета"),
        ("chaqaloq-toplam", "Chaqaloq to'plami", "Набор для малыша"),
    ]),
]


class Command(BaseCommand):
    help = "Firdowear: boshlang'ich katalog ma'lumotlari"

    def handle(self, *args, **opts):
        # --- o'lcham tizimlari ---
        st_h, _ = SizeType.objects.get_or_create(code="height_cm", defaults={"name": "Bo'y (sm)"})
        st_shoe, _ = SizeType.objects.get_or_create(code="eu_shoe", defaults={"name": "Poyabzal (EU)"})
        st_letter, _ = SizeType.objects.get_or_create(code="letter", defaults={"name": "Harfli (XS–XL)"})
        st_waist, _ = SizeType.objects.get_or_create(code="waist", defaults={"name": "Bel (dyuym)"})
        st_one, _ = SizeType.objects.get_or_create(code="one_size", defaults={"name": "Yagona o'lcham"})
        types = {"height_cm": st_h, "eu_shoe": st_shoe, "letter": st_letter, "waist": st_waist, "one_size": st_one}

        n = 0
        for i, (cm, a1, a2, uz, ru) in enumerate(HEIGHTS):
            _, c = Size.objects.get_or_create(size_type=st_h, code=str(cm), defaults={
                "label_uz": f"{cm} sm ({uz})", "label_ru": f"{cm} см ({ru})",
                "age_from_years": a1, "age_to_years": a2, "sort_order": i})
            n += c
        for i, eu in enumerate(range(16, 46)):
            _, c = Size.objects.get_or_create(size_type=st_shoe, code=str(eu), defaults={
                "label_uz": f"{eu}", "label_ru": f"{eu}", "sort_order": i})
            n += c
        for i, s in enumerate(["XS", "S", "M", "L", "XL"]):
            _, c = Size.objects.get_or_create(size_type=st_letter, code=s, defaults={"label_uz": s, "label_ru": s, "sort_order": i})
            n += c
        for i, w in enumerate([24, 25, 26, 27, 28, 29, 30, 31, 32, 34]):
            _, c = Size.objects.get_or_create(size_type=st_waist, code=str(w), defaults={"label_uz": f"W{w}", "label_ru": f"W{w}", "sort_order": i})
            n += c
        _, c = Size.objects.get_or_create(size_type=st_one, code="one", defaults={"label_uz": "Yagona", "label_ru": "Единый", "sort_order": 0})
        n += c
        self.stdout.write(f"O'lchamlar: +{n}")

        n = 0
        for i, (slug, uz, ru, m1, m2, h1, h2) in enumerate(AGE_GROUPS):
            _, c = AgeGroup.objects.get_or_create(slug=slug, defaults={
                "name_uz": uz, "name_ru": ru, "min_age_months": m1, "max_age_months": m2,
                "height_from_cm": h1, "height_to_cm": h2, "sort_order": i})
            n += c
        self.stdout.write(f"Yosh guruhlari: +{n}")

        n = 0
        for i, (slug, uz, ru, hx) in enumerate(COLORS):
            _, c = Color.objects.get_or_create(slug=slug, defaults={"name_uz": uz, "name_ru": ru, "hex_code": hx, "sort_order": i})
            n += c
        self.stdout.write(f"Ranglar: +{n}")

        n = 0
        for i, (slug, uz, ru, st, children) in enumerate(CATEGORIES):
            parent, c = Category.objects.get_or_create(slug=slug, defaults={
                "name_uz": uz, "name_ru": ru, "sort_order": i, "default_size_type": types[st]})
            n += c
            for j, (cs, cuz, cru) in enumerate(children):
                _, c = Category.objects.get_or_create(slug=cs, defaults={
                    "name_uz": cuz, "name_ru": cru, "parent": parent, "sort_order": j, "default_size_type": types[st]})
                n += c
        self.stdout.write(f"Kategoriyalar: +{n}")
        self.stdout.write(self.style.SUCCESS("Tayyor."))
