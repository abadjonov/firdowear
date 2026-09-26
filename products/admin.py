from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin, TranslationTabularInline

from .models import AgeGroup, Brand, Category, Color, Product, ProductImage, ProductVariant, Size, SizeType


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AgeGroup)
class AgeGroupAdmin(TabbedTranslationAdmin):
    list_display = ("name", "min_age_months", "max_age_months", "height_from_cm", "height_to_cm", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Category)
class CategoryAdmin(TabbedTranslationAdmin):
    list_display = ("__str__", "parent", "default_size_type", "is_active", "sort_order")
    list_filter = ("parent",)
    list_editable = ("is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "parent" in form.base_fields:
            parents = Category.objects.filter(parent__isnull=True)
            if obj is not None:
                parents = parents.exclude(pk=obj.pk)
            form.base_fields["parent"].queryset = parents
        return form


class SizeInline(TranslationTabularInline):
    model = Size
    extra = 0


@admin.register(SizeType)
class SizeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    inlines = [SizeInline]


@admin.register(Color)
class ColorAdmin(TabbedTranslationAdmin):
    list_display = ("swatch", "name", "hex_code", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}

    @admin.display(description="")
    def swatch(self, obj):
        return format_html('<span style="display:inline-block;width:18px;height:18px;border-radius:50%;border:1px solid #999;background:{}"></span>', obj.hex_code)


class ProductImageInline(TranslationTabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "image", "color", "alt", "is_primary", "sort_order")
    readonly_fields = ("preview",)

    @admin.display(description="")
    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px">', obj.image.url)
        return ""


class ProductVariantInline(admin.TabularInline):
    """Kunlik ish: qoldiqni shu yerda yangilash."""
    model = ProductVariant
    extra = 0
    fields = ("color", "size", "stock", "price_override", "sku", "is_active")
    readonly_fields = ("sku",)
    autocomplete_fields = ("size",)


@admin.register(Size)
class SizeAdmin(TabbedTranslationAdmin):
    list_display = ("label", "size_type", "code", "age_from_years", "age_to_years", "sort_order")
    list_filter = ("size_type",)
    search_fields = ("code", "label")


@admin.register(Product)
class ProductAdmin(TabbedTranslationAdmin):
    list_display = ("thumb", "name", "category", "brand", "price", "sale_price", "total_stock", "is_new", "is_featured", "is_active")
    list_display_links = ("thumb", "name")
    list_filter = ("is_active", "is_new", "is_featured", "season", "category__parent", "brand", "age_groups")
    list_editable = ("price", "sale_price", "is_new", "is_featured", "is_active")
    search_fields = ("name", "slug", "variants__sku")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("age_groups",)
    inlines = [ProductVariantInline, ProductImageInline]
    list_per_page = 40
    fieldsets = (
        (None, {"fields": ("name", "slug", "category", "brand", "age_groups", "size_type", "season")}),
        ("Narx", {"fields": ("price", "sale_price")}),
        ("Tavsif", {"fields": ("description", "material", "care_notes")}),
        ("Ko'rinish", {"fields": ("is_new", "is_featured", "is_active")}),
        ("SEO", {"fields": ("meta_title", "meta_description"), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category", "brand").prefetch_related("images", "variants")

    @admin.display(description="")
    def thumb(self, obj):
        img = obj.primary_image
        return format_html('<img src="{}" style="height:44px;border-radius:4px">', img.image.url) if img else "—"

    @admin.display(description="Qoldiq")
    def total_stock(self, obj):
        return sum(v.stock for v in obj.variants.all())


admin.site.site_header = "Firdo — boshqaruv"
admin.site.site_title = "Firdo"
admin.site.index_title = "Do'kon boshqaruvi"
