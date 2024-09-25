from django.contrib import admin

from products.models import Product
from products.models import ProductConfig
from products.models import ProductFeature
from products.models import ProductFeatureValue


class VariantInline(admin.TabularInline):
    model = Product
    extra = 0


@admin.register(ProductConfig)
class ProductConfigAdmin(admin.ModelAdmin):
    list_display = ('days_new',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('common_name', 'variant_name', 'is_visible', 'master', 'offers_count')
    list_filter = ('is_visible', 'master', 'category', 'brand')
    inlines = [VariantInline]


@admin.register(ProductFeature)
class ProductFeatureAdmin(admin.ModelAdmin):
    list_display = ('product', 'feature')
    list_filter = ('product', 'feature')


@admin.register(ProductFeatureValue)
class ProductFeatureValueAdmin(admin.ModelAdmin):
    list_display = ('product_feature', 'feature_value')
    list_filter = ('product_feature', 'feature_value')
