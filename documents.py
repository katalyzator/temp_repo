from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl import fields
from django_elasticsearch_dsl.registries import registry

from colors.models import ColorGroup
from products.models import Feature
from products.models import Product
from products.models import ProductFeatureValue


@registry.register_document
class ProductDocument(Document):
    common_name = fields.TextField()
    main_photo = fields.ObjectField(
        properties={
            'id': fields.TextField(),
            'url': fields.TextField(),
            'filename': fields.TextField(),
            'file_size': fields.TextField(),
        }
    )
    category = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
        }
    )
    color_id = fields.IntegerField()
    brand = fields.ObjectField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
        }
    )
    reviews_count = fields.IntegerField()
    rating = fields.IntegerField()
    color_groups = fields.NestedField(
        properties={
            'id': fields.IntegerField(),
            'name': fields.TextField(),
            'image': fields.ObjectField(properties={
                'id': fields.TextField(),
                'url': fields.TextField(),
                'filename': fields.TextField(),
                'file_size': fields.TextField(),
                'created_at': fields.TextField(),
            })
        }
    )
    feature_values = fields.NestedField(
        properties={
            'feature_name': fields.TextField(),
            'feature_id': fields.TextField(),
            'feature_is_main': fields.BooleanField(),
            'id': fields.IntegerField(),
            'name': fields.TextField(),
        }
    )

    features = fields.NestedField(
        properties={
            'name': fields.TextField(),
            'id': fields.IntegerField(),
        }
    )

    class Index:
        name = 'products'

    class Django:
        model = Product
        fields = [
            'id',
            'variant_name',
            'description',
            'slug',
            'is_visible',
            'offers_count',
            'offers_min_price',
            'offers_old_price',
            'created_at',
        ]

    def prepare_color_id(self, instance):
        if instance.color:
            return instance.color.id
        return None

    def prepare_common_name(self, instance):
        if instance.master:
            return instance.master.common_name
        return instance.common_name

    def prepare_image(self, instance):
        results = instance.image
        id = results['id']
        url = results['url']
        filename = results['filename']
        file_size = results['file_size']
        return {'id': id, 'url': url, 'filename': filename, 'file_size': file_size}

    def prepare_category(self, instance):
        return {'id': instance.category.id, 'name': instance.category.name}

    def prepare_brand(self, instance):
        return {'id': instance.brand.id, 'name': instance.brand.name}

    def prepare_reviews_count(self, instance):
        return instance.reviews_count

    def prepare_rating(self, instance):
        return instance.rating

    def prepare_color_groups(self, instance):
        color_groups = []
        if instance.color:
            color_groups_qs = ColorGroup.objects.filter(colors__in=[instance.color]).distinct()
            for color_group in color_groups_qs:
                color_groups.append({
                    'id': color_group.id,
                    'name': color_group.name,
                    'image': color_group.image,
                })
        return color_groups

    def prepare_features(self, instance):
        features = []
        product_features = Feature.objects.filter(products__product__in=[instance, instance.master])
        for feature in product_features:
            features.append({
                'id': feature.id,
                'name': feature.name
            })
        return features

    def prepare_feature_values(self, instance):
        feature_values = []
        product_feature_values = ProductFeatureValue.objects.filter(
            product_feature__product__in=[instance, instance.master]
        ).distinct().select_related('feature_value__feature')

        for product_feature_value in product_feature_values:
            feature_values.append({
                'feature_name': product_feature_value.feature_value.feature.name,
                'feature_id': product_feature_value.feature_value.feature.id,
                'feature_is_main': product_feature_value.feature_value.feature.is_main,
                'id': product_feature_value.feature_value.id,
                'name': product_feature_value.feature_value.value,
            })

        return feature_values

