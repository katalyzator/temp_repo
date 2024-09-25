import datetime

from dateutil.relativedelta import relativedelta
from rest_framework import serializers

from categories.serializers import CategoryShortSerializer
from colors.models import Color
from colors.serializers.color_serializers import ColorIdNameSerializer
from features.models import Feature
from features.models import FeatureValue
from products.models import Product
from products.models import ProductFeature
from products.models import ProductFeatureValue


class ProductCommonNameSerializer(serializers.Serializer):
    common_name = serializers.CharField()


class ProductCommonNameValiditySerializer(serializers.Serializer):
    is_duplicated = serializers.BooleanField(read_only=True)
    common_name = serializers.CharField(allow_null=True)


class VariationFeatureValueSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='feature_value.id')
    name = serializers.CharField(source='feature_value.value')

    class Meta:
        model = ProductFeatureValue
        fields = (
            'id',
            'name',
        )


class VariationProductFeatureSerializer(serializers.ModelSerializer):
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
        return VariationFeatureValueSerializer(values, many=True).data


class VariationProductFeatureValueSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='product_feature.feature.id')
    feature_name = serializers.CharField(source='product_feature.feature.name')
    value_id = serializers.IntegerField(source='feature_value.id')
    value_name = serializers.CharField(source='feature_value.value')

    class Meta:
        model = ProductFeatureValue
        fields = ('id', 'feature_name', 'value_id', 'value_name')


class ProductDetailSerializer(serializers.ModelSerializer):
    features = serializers.SerializerMethodField()
    color = ColorIdNameSerializer()

    class Meta:
        model = Product
        fields = (
            'id',
            'variant_name',
            'slug',
            'color',
            'main_photo',
            'photos',
            'features',
            'miniature_photo',
            'is_visible',
            'offers_count',
            'created_at',
            'updated_at',
        )

    def get_features(self, obj):
        return VariationProductFeatureSerializer(
            obj.features.filter(feature__is_visible=True).distinct('feature_id'), many=True
        ).data


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'variant_name', 'slug', 'main_photo', 'is_visible', 'offers_count', 'created_at')


class VariationFeatureValueIdsSerializer(serializers.Serializer):
    feature_id = serializers.PrimaryKeyRelatedField(queryset=Feature.objects.filter(is_variation=True))
    value_id = serializers.PrimaryKeyRelatedField(queryset=FeatureValue.objects.all())


class ProductCreateSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField()
    master = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(master__isnull=True))
    color = serializers.PrimaryKeyRelatedField(queryset=Color.objects.all())
    main_photo_id = serializers.CharField(write_only=True)
    miniature_photo_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    photo_ids = serializers.ListField(child=serializers.CharField())
    features = serializers.ListField(child=VariationFeatureValueIdsSerializer())

    class Meta:
        model = Product
        fields = (
            'master',
            'variant_name',
            'color',
            'is_visible',
            'miniature_photo_id',
            'main_photo_id',
            'photo_ids',
            'features',
        )


class ProductUpdateSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(allow_null=False, allow_blank=False)
    main_photo_id = serializers.CharField(write_only=True)
    miniature_photo_id = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    photo_ids = serializers.ListField(child=serializers.CharField())
    features = serializers.ListField(child=VariationFeatureValueIdsSerializer())

    class Meta:
        model = Product
        fields = ('variant_name', 'color', 'main_photo_id', 'photo_ids', 'is_visible', 'miniature_photo_id', 'features')


class ProductVariantNameSerializer(serializers.Serializer):
    variant_name = serializers.CharField()


class ProductVariantNameValiditySerializer(serializers.Serializer):
    is_duplicated = serializers.BooleanField(read_only=True)
    variant_name = serializers.CharField(allow_null=True)


class ProductBriefListSerializer(serializers.ModelSerializer):
    common_name = serializers.CharField(source='master.common_name')

    class Meta:
        model = Product
        fields = ('id', 'slug', 'common_name', 'variant_name', 'main_photo')


class ProductOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'variant_name', 'slug', 'offers_count', 'offers_min_price', 'offers_old_price')


class ProductUpdateMinOldPriceAndOffersCountSerializer(serializers.Serializer):
    offers_min_price = serializers.DecimalField(max_digits=20, decimal_places=4)
    offers_old_price = serializers.DecimalField(max_digits=20, decimal_places=4)
    offers_count = serializers.IntegerField(min_value=0)


class ProductInFavoriteListSerializer(serializers.ModelSerializer):
    is_new = serializers.SerializerMethodField()
    common_name = serializers.CharField(source='master.common_name')
    category = CategoryShortSerializer()

    class Meta:
        model = Product
        fields = (
            'id',
            'slug',
            'common_name',
            'variant_name',
            'main_photo',
            'category',
            'is_new',
            'offers_min_price',
            'offers_old_price',
            'offers_count',
            'reviews_count',
            'rating',
        )

    def get_is_new(self, obj):
        return True if datetime.date.today() <= obj.created_at.date() + relativedelta(months=1) else False
