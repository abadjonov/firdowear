"""Ko'rish uchun namunaviy mahsulotlar (rasmlar Pillow bilan chiziladi). Ishlab chiqarishda ishlatmang."""
import io, random
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw
from products.models import AgeGroup, Brand, Category, Color, Product, ProductImage, ProductVariant, Size

DEMO = [
    ("Qora klassik hoodie", "Чёрное классическое худи", "hudi", "LC Waikiki", 189000, None, ["qora", "kulrang"], (128, 152), "all", ["maktab", "osmir"], True, True),
    ("Qishki parka, haki", "Зимняя парка хаки", "parka", "Koton", 410000, 320000, ["haki", "toq-kok"], (104, 140), "winter", ["kichkintoy", "maktab"], False, True),
    ("Maktab oq ko'ylagi", "Школьная белая рубашка", "maktab-koylak", None, 95000, None, ["oq"], (122, 164), "all", ["maktab", "osmir"], False, False),
    ("Jinsi, to'q ko'k", "Джинсы тёмно-синие", "jinsi", "DeFacto", 165000, 139000, ["toq-kok", "kok"], (98, 146), "all", ["kichkintoy", "maktab"], True, False),
    ("Sport kostyum", "Спортивный костюм", "sport-kostyum", "Adidas", 520000, None, ["qora", "kok"], (140, 176), "all", ["osmir"], True, True),
    ("Chaqaloq bodisi 3 ta", "Боди для малыша 3 шт", "chaqaloq-toplam", "Carter's", 120000, None, ["oq", "havorang"], (56, 86), "all", ["chaqaloq"], True, False),
]
SHOES = [("Krossovka, oq", "Кроссовки белые", "krossovka", "Nike", 450000, 380000, ["oq", "qora"], (28, 39), ["kichkintoy", "maktab", "osmir"])]

def img(color_hex, text):
    im = Image.new("RGB", (600, 800), color_hex)
    d = ImageDraw.Draw(im); d.rectangle([40, 40, 560, 760], outline="#ffffff", width=6); d.text((60, 60), text, fill="#ffffff")
    b = io.BytesIO(); im.save(b, "JPEG", quality=80); return ContentFile(b.getvalue(), "demo.jpg")

class Command(BaseCommand):
    def handle(self, *a, **o):
        from django.utils.text import slugify
        def brand(n):
            return Brand.objects.get_or_create(slug=slugify(n), defaults={"name": n})[0] if n else None
        def make(uz, ru, cat, br, price, sale, colors, rng, season, ages, new, feat, shoe=False):
            c = Category.objects.get(slug=cat)
            p, created = Product.objects.get_or_create(slug=slugify(uz), defaults=dict(
                name_uz=uz, name_ru=ru, category=c, brand=brand(br), size_type=c.default_size_type,
                price=price, sale_price=sale, season=season, is_new=new, is_featured=feat,
                description_uz="Yumshoq, sifatli material. Kundalik kiyish uchun qulay.",
                description_ru="Мягкий качественный материал. Удобно на каждый день.", material="Paxta 80%, poliester 20%"))
            if not created: return
            p.age_groups.set(AgeGroup.objects.filter(slug__in=ages))
            sizes = Size.objects.filter(size_type=c.default_size_type, sort_order__gte=0)
            sizes = [s for s in sizes if rng[0] <= int(s.code) <= rng[1]]
            for i, cs in enumerate(colors):
                col = Color.objects.get(slug=cs)
                ProductImage.objects.create(product=p, color=col, image=img(col.hex_code if col.hex_code != "#ffffff" else "#d4d4d8", uz), is_primary=(i == 0))
                for s in sizes:
                    ProductVariant.objects.create(product=p, size=s, color=col, stock=random.choice([0, 1, 2, 3, 5, 8]))
        for d in DEMO: make(*d)
        for uz, ru, cat, br, price, sale, colors, rng, ages in SHOES: make(uz, ru, cat, br, price, sale, colors, rng, "all", ages, True, True)
        self.stdout.write(self.style.SUCCESS(f"Mahsulotlar: {Product.objects.count()}"))
