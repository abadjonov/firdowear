from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeNumericFilter, RelatedDropdownFilter
from unfold.decorators import display

from .models import AgeGroup, Brand, Category, Color, Product, ProductImage, ProductVariant, Size, SizeType


@admin.register(Brand)
class BrandAdmin(ModelAdmin):
    list_display = ("name", "country", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "country")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AgeGroup)
class AgeGroupAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("name", "min_age_months", "max_age_months", "height_from_cm", "height_to_cm", "is_active")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("__str__", "parent", "default_size_type", "is_active", "sort_order")
    list_filter_submit = True
    list_filter = (("parent", RelatedDropdownFilter), "is_active")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "parent" in form.base_fields:
            parents = Category.objects.filter(parent__isnull=True)
            if obj is not None:
                parents = parents.exclude(pk=obj.pk)
            form.base_fields["parent"].queryset = parents
        return form


class SizeInline(TabularInline, TranslationTabularInline):
    model = Size
    extra = 0


@admin.register(SizeType)
class SizeTypeAdmin(ModelAdmin):
    list_display = ("name", "code")
    inlines = [SizeInline]


@admin.register(Color)
class ColorAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("swatch", "name", "hex_code", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}

    @display(description="")
    def swatch(self, obj):
        return format_html(
            '<span style="display:inline-block;width:20px;height:20px;border-radius:50%;border:1px solid #ccc;background:{}"></span>',
            obj.hex_code,
        )


class ProductImageInline(TabularInline, TranslationTabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "color", "alt", "is_primary", "sort_order")
    readonly_fields = ("preview",)

    @display(description="")
    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="height:60px;width:60px;border-radius:6px;object-fit:cover;" class="shadow-xs">',
                obj.image.url,
            )
        return ""


class ProductVariantInline(TabularInline):
    """Kunlik ish: qoldiqni shu yerda yangilash."""

    model = ProductVariant
    extra = 0
    fields = ("color", "size", "stock", "price_override", "sku", "is_active")
    readonly_fields = ("sku",)
    autocomplete_fields = ("size",)


@admin.register(Size)
class SizeAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = ("label", "size_type", "code", "age_from_years", "age_to_years", "sort_order")
    list_filter_submit = True
    list_filter = (("size_type", RelatedDropdownFilter),)
    search_fields = ("code", "label")


@admin.register(Product)
class ProductAdmin(ModelAdmin, TabbedTranslationAdmin):
    list_display = (
        "thumb",
        "name",
        "category",
        "brand",
        "price",
        "sale_price",
        "stock_badge",
        "is_new",
        "is_featured",
        "is_active",
    )
    list_display_links = ("thumb", "name")
    list_filter_submit = True
    list_filter = (
        "is_active",
        "is_new",
        "is_featured",
        ("season", ChoicesDropdownFilter),
        ("category__parent", RelatedDropdownFilter),
        ("brand", RelatedDropdownFilter),
        ("price", RangeNumericFilter),
    )
    list_editable = ("price", "sale_price", "is_new", "is_featured", "is_active")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("age_groups",)
    inlines = [ProductVariantInline, ProductImageInline]
    list_per_page = 40
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "brand", "age_groups", "size_type", "season")}),
        (_("Narx"), {"fields": ("price", "sale_price")}),
        (_("Tavsif"), {"fields": ("description", "material", "care_notes")}),
        (_("Ko'rinish"), {"fields": ("is_new", "is_featured", "is_active")}),
        (_("SEO"), {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("category", "brand")
            .prefetch_related("images", "variants")
        )

    @display(description="")
    def thumb(self, obj):
        img = obj.primary_image
        return (
            format_html(
                '<img src="{}" style="height:44px;width:44px;border-radius:6px;object-fit:cover;" class="shadow-xs">',
                img.image.url,
            )
            if img
            else "—"
        )

    @display(
        description=_("Qoldiq"),
        label={
            "danger": "danger",
            "warning": "warning",
            "success": "success",
        },
    )
    def stock_badge(self, obj):
        total = sum(v.stock for v in obj.variants.all())
        if total == 0:
            return "danger", "Tugagan (0)"
        if total <= 5:
            return "warning", f"Kam ({total})"
        return "success", f"{total} dona"
