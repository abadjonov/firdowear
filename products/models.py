from django.db import models
from django.db.models import Min, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Brand(models.Model):
    """Do'kon ko'p brendli. Firdowear — do'kon nomi, brend emas."""

    name = models.CharField(_("Nomi"), max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(_("Logo"), upload_to="brands/", blank=True)
    country = models.CharField(_("Mamlakat"), max_length=60, blank=True)
    sort_order = models.PositiveSmallIntegerField(_("Tartib"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Brend")
        verbose_name_plural = _("Brendlar")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:brand", args=[self.slug])


class AgeGroup(models.Model):
    """Yosh guruhi — kiyim turidan alohida (jinsi har yoshda bor)."""

    name = models.CharField(_("Nomi"), max_length=60)
    slug = models.SlugField(unique=True)
    min_age_months = models.PositiveSmallIntegerField(_("Yosh (oy) dan"), default=0)
    max_age_months = models.PositiveSmallIntegerField(_("Yosh (oy) gacha"), default=216)
    height_from_cm = models.PositiveSmallIntegerField(_("Bo'y (sm) dan"), default=50)
    height_to_cm = models.PositiveSmallIntegerField(_("Bo'y (sm) gacha"), default=182)
    sort_order = models.PositiveSmallIntegerField(_("Tartib"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["sort_order"]
        verbose_name = _("Yosh guruhi")
        verbose_name_plural = _("Yosh guruhlari")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:age_group", args=[self.slug])


class Category(models.Model):
    """Ikki darajali daraxt: Ustki kiyim -> Hoodie."""

    name = models.CharField(_("Nomi"), max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE,
        related_name="children", verbose_name=_("Ota kategoriya"),
    )
    image = models.ImageField(_("Rasm"), upload_to="categories/", blank=True)
    default_size_type = models.ForeignKey(
        "SizeType", null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name=_("Standart o'lcham tizimi"),
        help_text=_("Yangi mahsulot qo'shganda avtomatik tanlanadi"),
    )
    sort_order = models.PositiveSmallIntegerField(_("Tartib"), default=0)
    is_active = models.BooleanField(_("Faol"), default=True)
    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Kategoriya")
        verbose_name_plural = _("Kategoriyalar")

    def __str__(self):
        return f"{self.parent} → {self.name}" if self.parent else self.name

    def get_absolute_url(self):
        return reverse("products:category", args=[self.slug])

    def descendant_ids(self):
        ids = [self.pk]
        ids += list(self.children.values_list("pk", flat=True))
        return ids


class SizeType(models.Model):
    """height_cm, age_month, letter, waist, eu_shoe ... aralashmasligi kerak."""

    code = models.SlugField(unique=True)
    name = models.CharField(_("Nomi"), max_length=60)

    class Meta:
        verbose_name = _("O'lcham tizimi")
        verbose_name_plural = _("O'lcham tizimlari")

    def __str__(self):
        return self.name


class Size(models.Model):
    size_type = models.ForeignKey(SizeType, on_delete=models.CASCADE, related_name="sizes")
    code = models.CharField(_("Kod"), max_length=20, help_text="134, 28, 32, XL")
    label = models.CharField(_("Ko'rsatiladigan nom"), max_length=60, help_text="134 sm (8–9 yosh)")
    age_from_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    age_to_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["size_type", "sort_order"]
        unique_together = [("size_type", "code")]
        verbose_name = _("O'lcham")
        verbose_name_plural = _("O'lchamlar")

    def __str__(self):
        return f"{self.label} [{self.size_type.code}]"


class Color(models.Model):
    name = models.CharField(_("Nomi"), max_length=50)
    slug = models.SlugField(unique=True)
    hex_code = models.CharField(max_length=7, default="#000000")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = _("Rang")
        verbose_name_plural = _("Ranglar")

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, category__is_active=True)

    def in_stock(self):
        return self.filter(variants__stock__gt=0, variants__is_active=True).distinct()

    def with_min_price(self):
        return self.annotate(
            min_variant_price=Min("variants__price_override", filter=Q(variants__is_active=True))
        )


class Product(TimeStamped):
    class Season(models.TextChoices):
        ALL = "all", _("Barcha fasl")
        SPRING = "spring", _("Bahor")
        SUMMER = "summer", _("Yoz")
        AUTUMN = "autumn", _("Kuz")
        WINTER = "winter", _("Qish")

    name = models.CharField(_("Nomi"), max_length=200)
    slug = models.SlugField(unique=True, max_length=220)
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products",
        limit_choices_to={"parent__isnull": False}, verbose_name=_("Kategoriya"),
        help_text=_("Faqat eng pastki (2-daraja) kategoriya"),
    )
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="products", verbose_name=_("Brend"),
    )
    age_groups = models.ManyToManyField(AgeGroup, blank=True, related_name="products", verbose_name=_("Yosh guruhlari"))
    size_type = models.ForeignKey(SizeType, on_delete=models.PROTECT, verbose_name=_("O'lcham tizimi"))
    description = models.TextField(_("Tavsif"), blank=True)
    material = models.CharField(_("Material"), max_length=200, blank=True)
    care_notes = models.CharField(_("Parvarish"), max_length=300, blank=True)
    season = models.CharField(_("Fasl"), max_length=10, choices=Season.choices, default=Season.ALL)

    price = models.DecimalField(_("Narx (so'm)"), max_digits=12, decimal_places=0)
    sale_price = models.DecimalField(_("Chegirma narxi"), max_digits=12, decimal_places=0, null=True, blank=True)

    is_new = models.BooleanField(_("Yangi"), default=False)
    is_featured = models.BooleanField(_("Bosh sahifada"), default=False)
    is_active = models.BooleanField(_("Faol"), default=True)

    meta_title = models.CharField(max_length=160, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Mahsulot")
        verbose_name_plural = _("Mahsulotlar")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("products:detail", args=[self.slug])

    # --- narx ---
    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def current_price(self):
        return self.sale_price if self.is_on_sale else self.price

    @property
    def discount_percent(self):
        if not self.is_on_sale:
            return 0
        return round((self.price - self.sale_price) * 100 / self.price)

    # --- rasm & qoldiq ---
    @property
    def primary_image(self):
        imgs = list(self.images.all())
        if not imgs:
            return None
        return next((i for i in imgs if i.is_primary), imgs[0])

    @property
    def in_stock(self):
        return any(v.stock > 0 and v.is_active for v in self.variants.all())

    def available_colors(self):
        seen, out = set(), []
        for v in self.variants.all():
            if v.is_active and v.color_id not in seen:
                seen.add(v.color_id)
                out.append(v.color)
        return out


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    color = models.ForeignKey(Color, null=True, blank=True, on_delete=models.SET_NULL, verbose_name=_("Rang"))
    image = models.ImageField(_("Rasm"), upload_to="products/%Y/%m/")
    thumb = models.ImageField(upload_to="products/%Y/%m/thumb/", blank=True, editable=False)
    large = models.ImageField(upload_to="products/%Y/%m/large/", blank=True, editable=False)
    alt = models.CharField(max_length=160, blank=True)
    is_primary = models.BooleanField(_("Asosiy"), default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "sort_order", "pk"]
        verbose_name = _("Rasm")
        verbose_name_plural = _("Rasmlar")

    def __str__(self):
        return f"{self.product} #{self.pk}"

    @property
    def thumb_url(self):
        return (self.thumb or self.image).url

    @property
    def large_url(self):
        return (self.large or self.image).url

    def save(self, *args, **kwargs):
        regenerate = self.image and (not self.pk or not self.thumb or self._image_changed())
        super().save(*args, **kwargs)
        if regenerate:
            from .images import build_variants
            thumb, large, tn, ln = build_variants(self.image)
            self.thumb.save(tn, thumb, save=False)
            self.large.save(ln, large, save=False)
            super().save(update_fields=["thumb", "large"])

    def _image_changed(self):
        if not self.pk:
            return True
        old = ProductImage.objects.filter(pk=self.pk).values_list("image", flat=True).first()
        return old != self.image.name


class ProductVariant(models.Model):
    """Haqiqiy ombor birligi: '134 sm, qora hoodie — 3 ta'."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    size = models.ForeignKey(Size, on_delete=models.PROTECT, verbose_name=_("O'lcham"))
    color = models.ForeignKey(Color, on_delete=models.PROTECT, verbose_name=_("Rang"))
    sku = models.CharField("SKU", max_length=50, unique=True, blank=True)
    stock = models.PositiveIntegerField(_("Qoldiq"), default=0)
    price_override = models.DecimalField(
        _("Alohida narx"), max_digits=12, decimal_places=0, null=True, blank=True,
        help_text=_("Bo'sh bo'lsa mahsulot narxi"),
    )
    is_active = models.BooleanField(_("Faol"), default=True)

    class Meta:
        ordering = ["color__sort_order", "size__sort_order"]
        unique_together = [("product", "size", "color")]
        verbose_name = _("Variant")
        verbose_name_plural = _("Variantlar")

    def __str__(self):
        return f"{self.product} / {self.color} / {self.size.label}"

    @property
    def price(self):
        return self.price_override if self.price_override is not None else self.product.current_price

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"FW-{self.product_id}-{self.color.slug[:3].upper()}-{self.size.code}"
        super().save(*args, **kwargs)
