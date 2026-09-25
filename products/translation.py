from modeltranslation.translator import TranslationOptions, register

from .models import AgeGroup, Category, Color, Product, ProductImage, Size


@register(Category)
class CategoryTR(TranslationOptions):
    fields = ("name", "meta_title", "meta_description")


@register(AgeGroup)
class AgeGroupTR(TranslationOptions):
    fields = ("name",)


@register(Color)
class ColorTR(TranslationOptions):
    fields = ("name",)


@register(Size)
class SizeTR(TranslationOptions):
    fields = ("label",)


@register(Product)
class ProductTR(TranslationOptions):
    fields = ("name", "description", "material", "care_notes", "meta_title", "meta_description")
    required_languages = {"uz": ("name",)}


@register(ProductImage)
class ProductImageTR(TranslationOptions):
    fields = ("alt",)
