from .models import AgeGroup, Category


def catalog_menu(request):
    return {
        "menu_categories": Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related("children"),
        "menu_age_groups": AgeGroup.objects.filter(is_active=True),
    }
