from rest_framework import serializers

from brands.serializers import BrandShortSerializer
from categories.models import Category
from categories.serializers import CategoryShortSerializer
from features.models import Feature
from features.models import FeatureValue
from features.serializers.feature_serializers import FeatureBriefSerializer
from products.models import Product
from products.models import ProductFeature
from products.models import ProductFeatureValue
from products.serializers.product_serializers import ProductListSerializer
from products.services.master_product_services import MasterProductService


class ProductFeatureValueSerializer(serializers.Serializer):
    feature_id = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.all())
    value_id = serializers.PrimaryKeyRelatedField(queryset=FeatureValue.objects.all())


class MasterProductCreateSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=1000)
    main_photo_id = serializers.CharField(write_only=True)
    miniature_photo_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    photo_ids = serializers.ListField(child=serializers.CharField())
    video_urls = serializers.ListField(child=serializers.CharField())
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(level=3))
    variation_features = serializers.PrimaryKeyRelatedField(
        queryset=Feature.objects.filter(is_variation=True, is_visible=True), many=True
    )
    features = serializers.ListField(child=ProductFeatureValueSerializer())
    common_name = serializers.CharField(allow_null=False, allow_blank=False)

    class Meta:
        model = Product
        fields = (
            'common_name',
            'brand',
            'category',
            'description',
            'main_photo_id',
            'photo_ids',
            'video_urls',
            'is_visible',
            'variation_features',
            'features',
            'miniature_photo_id',
        )


class MasterProductListSerializer(serializers.ModelSerializer):
    variations = ProductListSerializer(many=True)
    brand = BrandShortSerializer()
    category = CategoryShortSerializer()
    offers_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'slug',
            'common_name',
            'main_photo',
            'brand',
            'category',
            'is_visible',
            'variations',
            'offers_count',
            'created_at',
        )

    def get_offers_count(self, master_product: Product) -> int:
        # ToDo: try updating offers_count field when variation offers_count is updated
        return MasterProductService.get_variations_total_offers_count(product=master_product)


class MasterProductFeatureValueSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='feature_value.id')
    name = serializers.CharField(source='feature_value.value')

    class Meta:
        model = ProductFeatureValue
        fields = (
            'id',
            'name',
        )


class MasterProductFeatureSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='feature.id')
    name = serializers.CharField(source='feature.name')
    values = serializers.SerializerMethodField()
    is_multichoice = serializers.BooleanField(source='feature.is_multichoice')

    class Meta:
        model = ProductFeature
        fields = ('id', 'name', 'is_multichoice', 'values')

    def get_values(self, obj):
        values = ProductFeatureValue.objects.filter(
            product_feature__feature=obj.feature, product_feature__product=obj.product
        )
        return MasterProductFeatureValueSerializer(values, many=True).data


class MasterProductDetailSerializer(serializers.ModelSerializer):
    variations = ProductListSerializer(many=True)
    features = serializers.SerializerMethodField()
    brand = BrandShortSerializer()
    category = CategoryShortSerializer()
    variation_features = serializers.SerializerMethodField()

    def get_features(self, obj):
        return MasterProductFeatureSerializer(
            obj.features.filter(feature__is_visible=True).distinct('feature_id'), many=True
        ).data

    def get_variation_features(self, obj):
        if obj.variation_features:
            return FeatureBriefSerializer(
                obj.variation_features.filter(is_visible=True, is_variation=True), many=True
            ).data

        return list()

    class Meta:
        model = Product
        fields = (
            'id',
            'common_name',
            'slug',
            'brand',
            'category',
            'main_photo',
            'photos',
            'video_urls',
            'miniature_photo',
            'description',
            'variation_features',
            'features',
            'is_visible',
            'variations',
            'offers_count',
            'created_at',
            'updated_at',
        )


class MasterProductUpdateSerializer(serializers.ModelSerializer):
    common_name = serializers.CharField(allow_null=False, allow_blank=False)
    miniature_photo_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    main_photo_id = serializers.CharField(write_only=True)
    photo_ids = serializers.ListField(child=serializers.CharField())
    video_urls = serializers.ListField(child=serializers.CharField())
    description = serializers.CharField(max_length=1000)
    variation_features = serializers.PrimaryKeyRelatedField(
        queryset=Feature.objects.filter(is_variation=True, is_visible=True), many=True, allow_empty=True
    )
    features = serializers.ListField(child=ProductFeatureValueSerializer())

    class Meta:
        model = Product
        fields = (
            'common_name',
            'brand',
            'main_photo_id',
            'photo_ids',
            'video_urls',
            'description',
            'variation_features',
            'features',
            'is_visible',
            'miniature_photo_id',
        )


class MasterProductVisibilityUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id',
            'is_visible',
        )


class MasterProductCommonNameSerializer(serializers.Serializer):
    common_name = serializers.CharField()


class MasterProductCommonNameValiditySerializer(serializers.Serializer):
    is_duplicated = serializers.BooleanField(read_only=True)
    common_name = serializers.CharField(allow_null=True)
