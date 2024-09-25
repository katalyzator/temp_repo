from auditlog.registry import auditlog
from django.db import models

from brands.models import Brand
from categories.models import Category
from colors.models import Color
from common.models import SingletonModel
from common.models import TimestampModel
from features.models import Feature
from features.models import FeatureValue


class ProductConfig(SingletonModel):
    days_new = models.PositiveSmallIntegerField(default=30)


class Product(TimestampModel):
    master = models.ForeignKey('self', null=True, blank=True, related_name='variations', on_delete=models.CASCADE)
    common_name = models.CharField(max_length=255, null=True)
    variant_name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True)
    color = models.ForeignKey(Color, on_delete=models.PROTECT, null=True, blank=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    main_photo = models.JSONField()
    miniature_photo = models.JSONField(null=True, blank=True)
    photos = models.JSONField()
    video_urls = models.JSONField(null=True)
    offers_min_price = models.DecimalField(max_digits=20, decimal_places=4, null=True)
    offers_old_price = models.DecimalField(max_digits=20, decimal_places=4, null=True)
    description = models.TextField(max_length=1000, blank=True, null=True)
    is_visible = models.BooleanField()
    offers_count = models.PositiveSmallIntegerField(default=0)
    variation_features = models.ManyToManyField(Feature, related_name='variation_products')
    reviews_count = models.IntegerField(default=0)
    rating = models.FloatField(null=True)

    def __str__(self) -> str:
        return f'{self.common_name} {self.variant_name}'


class ProductFeature(TimestampModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='products')

    def __str__(self) -> str:
        return f'{self.feature.name} - {self.product.variant_name}'


class ProductFeatureValue(TimestampModel):
    product_feature = models.ForeignKey(ProductFeature, on_delete=models.CASCADE, related_name='selected_values')
    feature_value = models.ForeignKey(FeatureValue, on_delete=models.CASCADE, related_name='products')

    def __str__(self) -> str:
        return f'{self.product_feature.product} - {self.feature_value.value}'


auditlog.register(Product, exclude_fields=['updated_at'], serialize_data=True, serialize_auditlog_fields_only=True)
auditlog.register(
    ProductFeature, exclude_fields=['updated_at'], serialize_data=True, serialize_auditlog_fields_only=True
)
auditlog.register(
    ProductFeatureValue, exclude_fields=['updated_at'], serialize_data=True, serialize_auditlog_fields_only=True
)
