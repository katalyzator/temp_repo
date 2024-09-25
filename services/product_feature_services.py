from features.models import Feature
from products.models import ProductFeature


class ProductFeatureService:
    @classmethod
    def filter(cls, *args, **kwargs):
        return ProductFeature.objects.filter(*args, **kwargs)

    @classmethod
    def delete(cls, product_id: int):
        delete_product_features = cls.filter(product_id=product_id)
        delete_product_features.delete()

    @classmethod
    def is_feature_used_in_variation_products(cls, feature: Feature) -> bool:
        return ProductFeature.objects.filter(feature=feature, product__master__isnull=False).exists()
