from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import AgeGroup, Brand, Category, Product


class I18nSitemap(Sitemap):
    i18n = True
    alternates = True
    x_default = True
    protocol = "https"


class StaticSitemap(I18nSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["pages:home", "products:catalog", "pages:contact"]

    def location(self, item):
        return reverse(item)


class ProductSitemap(I18nSitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.active().order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(I18nSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)


class BrandSitemap(I18nSitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Brand.objects.filter(is_active=True, products__isnull=False).distinct()


class AgeGroupSitemap(I18nSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return AgeGroup.objects.filter(is_active=True)


SITEMAPS = {
    "static": StaticSitemap, "products": ProductSitemap, "categories": CategorySitemap,
    "brands": BrandSitemap, "ages": AgeGroupSitemap,
}
