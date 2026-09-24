from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("catalog/", views.catalog, name="catalog"),
    path("catalog/<slug:slug>/", views.category, name="category"),
    path("age/<slug:slug>/", views.age_group, name="age_group"),
    path("brand/<slug:slug>/", views.brand, name="brand"),
    path("product/<slug:slug>/", views.detail, name="detail"),
]
