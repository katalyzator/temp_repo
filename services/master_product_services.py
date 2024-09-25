from typing import Optional

from authorizations.authentication import User
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import Sum
from django.db.models.functions import Coalesce
from pytils.translit import slugify

from brands.models import Brand
from categories.models import Category
from common.cdn_services import CDNService
from common.common_producers import ActivityProducer
from common.constants import CREATE_ACTIVITY
from common.constants import PRODUCT_MODEL
from common.constants import UPDATE_ACTIVITY
from common.constants import WRONG_LOOKUP
from common.exceptions import IntegrityException
from common.exceptions import ObjectNotFoundException
from common.exceptions import ValidationException
from features.services.feature_services import FeatureService
from products.models import Product
from products.models import ProductFeature
from products.models import ProductFeatureValue
from products.product_producers import ProductProducer
from products.services.product_feature_services import ProductFeatureService
from products.services.product_services import ProductService


class MasterProductService:
    @classmethod
    def get(cls, *args, **kwargs) -> Product:
        try:
            return Product.objects.get(master__isnull=True, *args, **kwargs)
        except Product.DoesNotExist:
            raise ObjectNotFoundException('Master product not found')
        except ValueError:
            raise ValidationException(WRONG_LOOKUP)

    @classmethod
    def filter(cls, *args, **kwargs):
        return Product.objects.filter(master__isnull=True, *args, **kwargs)

    @classmethod
    def validate_master_product_visibility_turning_off(cls, master_product: Product):
        if master_product.offers_count > 0:
            raise ValidationException(message='Мастер карточка не может быть отключена')

    @classmethod
    def validate_master_product(cls, master_product: Product):
        if master_product.master is not None:
            raise ValidationException(message='Этот продукт не является мастер карточкой')

    @classmethod
    def update_master_product_visibility(cls, master_product: Product, is_visible: bool) -> Product:
        if master_product.is_visible == is_visible:
            return master_product
        try:
            cls.validate_master_product(master_product=master_product)
            if not is_visible and master_product.is_visible:
                cls.validate_master_product_visibility_turning_off(master_product=master_product)
                ProductService.bulk_turn_off_visibility_of_product(master_product=master_product)

            master_product.is_visible = is_visible
            master_product.save()
            master_product.refresh_from_db()
            return master_product
        except IntegrityError as e:
            raise IntegrityException(f'Can not update master product: {str(e)}')

    @classmethod
    def bulk_update_products_brand(cls, master_product: Product, brand: Brand):
        try:
            variation_products = ProductService.filter(master=master_product)
            variation_products.update(brand=brand)

            return master_product
        except IntegrityError as e:
            raise IntegrityException(f'Can not update product variation brands: {str(e)}')

    @classmethod
    def validate_slug(cls, slug: str):
        if Product.objects.filter(slug__exact=slug):
            raise ValidationException(message='Такой товар уже существует')

    @classmethod
    def create(
        cls,
        common_name: str,
        is_visible: bool,
        brand: Brand,
        category: Category,
        description: str,
        main_photo_id: str,
        photo_ids: list,
        video_urls: list,
        variation_features: list,
        features: list,
        creator: User,
        miniature_photo_id: Optional[str] = None,
    ) -> Product:
        try:
            miniature_photo = None
            if miniature_photo_id:
                miniature_photo = CDNService.get_image_dict(image_id=miniature_photo_id)
            main_photo = CDNService.get_image_dict(image_id=main_photo_id)
            photos_list = []
            for photo_id in photo_ids:
                photo_dict = CDNService.get_image_dict(image_id=photo_id)
                photos_list.append(photo_dict)

            generated_slug = slugify(common_name)
            cls.validate_slug(slug=generated_slug)
            master_product = Product.objects.create(
                common_name=common_name,
                slug=generated_slug,
                is_visible=is_visible,
                brand=brand,
                category=category,
                main_photo=main_photo,
                photos=photos_list,
                description=description,
                video_urls=video_urls,
                miniature_photo=miniature_photo,
            )
            master_product.variation_features.set(variation_features)
            for selected_value in features:
                feature = selected_value['feature_id']
                value = selected_value['value_id']
                if not value.feature == feature:
                    raise ValidationException('Can not create master product: wrong values in features list')
                product_feature, _ = ProductFeature.objects.get_or_create(product=master_product, feature=feature)
                ProductFeatureValue.objects.create(product_feature=product_feature, feature_value=value)

            ActivityProducer.activity_create(
                product=master_product,
                object_model=PRODUCT_MODEL,
                user_id=creator.id,
                activity_type=CREATE_ACTIVITY,
                created_or_updated_date=master_product.created_at,
            )

            return master_product
        except IntegrityError as e:
            raise IntegrityException(f'Can not create master product: {str(e)}')

    @classmethod
    def validate_master_has_variation_with_used_feature(cls, master_product_id: int, new_variation_features: set):
        variants_features_ids = set(
            ProductFeature.objects.filter(product__master_id=master_product_id).values_list('feature_id', flat=True)
        )
        if len(variants_features_ids) > 0 and not variants_features_ids.issubset(new_variation_features):
            raise ValidationException(message='Есть вариант с этим параметром')

    @classmethod
    def validate_features_variation_features_interction(cls, variation_features: set, features: set):
        if len(variation_features.intersection(features)) > 0:
            raise ValidationException(
                message='Характеристики вариантов и характеристики мастер карточки не могут совпадать'
            )

    @classmethod
    @transaction.atomic
    def update(
        cls,
        master_product: Product,
        common_name: str,
        brand: Brand,
        main_photo_id: str,
        photo_ids: list,
        video_urls: list,
        description: str,
        variation_features: list,
        features: list,
        is_visible: bool,
        editor: User,
        miniature_photo_id: Optional[str] = None,
    ) -> Product:
        try:
            if miniature_photo_id:
                master_product.miniature_photo = CDNService.get_image_dict(image_id=miniature_photo_id)
            main_photo_dict = CDNService.get_image_dict(image_id=main_photo_id)
            photos_list = []
            for photo_id in photo_ids:
                photo_dict = CDNService.get_image_dict(image_id=photo_id)
                photos_list.append(photo_dict)

            if master_product.common_name != common_name:
                generated_slug = slugify(common_name)
                cls.validate_slug(slug=generated_slug)

                ProductService.bulk_update_products_slug_and_common_name(
                    master=master_product, slug=generated_slug, common_name=common_name
                )
                master_product.slug = slugify(common_name)
            master_product.common_name = common_name
            master_product.brand = brand
            master_product.main_photo = main_photo_dict
            master_product.photos = photos_list
            master_product.video_urls = video_urls
            master_product.description = description

            values_list = set(master_product.variation_features.values_list('id', flat=True))
            variation_features_set = set([x.id for x in variation_features])
            features_set = set([x['feature_id'].id for x in features])

            if variation_features_set != values_list:
                cls.validate_master_has_variation_with_used_feature(
                    master_product_id=master_product.id, new_variation_features=variation_features_set
                )
                cls.validate_features_variation_features_interction(
                    variation_features=variation_features_set, features=features_set
                )
                master_product.variation_features.set(variation_features)

            ProductFeatureService.delete(product_id=master_product.id)

            for selected_value in features:
                feature = selected_value['feature_id']
                value = selected_value['value_id']
                if not value.feature == feature:
                    raise ValidationException('Can not create master product: wrong values in features list')
                product_feature = ProductFeature.objects.create(product=master_product, feature=feature)
                ProductFeatureValue.objects.create(product_feature=product_feature, feature_value=value)

            cls.update_master_product_visibility(master_product=master_product, is_visible=is_visible)
            cls.bulk_update_products_brand(master_product=master_product, brand=brand)
            master_product.save()

            ActivityProducer.activity_create(
                product=master_product,
                object_model=PRODUCT_MODEL,
                user_id=editor.id,
                activity_type=UPDATE_ACTIVITY,
                created_or_updated_date=master_product.updated_at,
            )

            return master_product
        except IntegrityError as e:
            raise IntegrityException(f'Can not update master product: {str(e)}')

    @classmethod
    def delete(cls, product: Product):
        if product.variations.filter(offers_count__gt=0).exists():
            raise ValidationException(
                message='Удаление товара, у вариантов которого имеются ' 'предложения продавцов невозможна'
            )
        master_id = product.id
        product.delete()
        ProductProducer.master_product_delete(master_id=master_id)

    @classmethod
    def check_master_product_name_is_duplicated(cls, name: str) -> dict:
        product = cls.filter(common_name__iexact=name).first()
        return {'is_duplicated': bool(product), 'common_name': product.common_name if product else None}

    @classmethod
    def get_variations_total_offers_count(cls, product: Product) -> int:
        return product.variations.aggregate(variation_offers_count=Coalesce(Sum('offers_count'), 0))[
            'variation_offers_count'
        ]

    @classmethod
    def get_master_product_variation_features_usage(cls, master_product: Product, variation_feature_ids: list):
        variation_features = FeatureService.filter(id__in=variation_feature_ids).annotate(
            is_feature_used=Exists(ProductFeatureService.filter(product__master=master_product, feature=OuterRef('id')))
        )

        return variation_features
