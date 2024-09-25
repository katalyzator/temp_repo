from typing import Optional

import requests
from authorizations.authentication import User
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import Value
from django.db.models.functions import Replace
from pytils.translit import slugify

from colors.models import Color
from common.cdn_services import CDNService
from common.common_producers import ActivityProducer
from common.constants import CREATE_ACTIVITY
from common.constants import PRODUCT_MODEL
from common.constants import UPDATE_ACTIVITY
from common.constants import WRONG_LOOKUP
from common.exceptions import FailedDependencyException
from common.exceptions import IntegrityException
from common.exceptions import ObjectNotFoundException
from common.exceptions import ValidationException
from products.models import Product
from products.models import ProductFeature
from products.models import ProductFeatureValue
from products.product_producers import ProductProducer
from django.conf import settings


class ProductService:
    @classmethod
    def filter(cls, *args, **kwargs):
        return Product.objects.filter(master__isnull=False, *args, **kwargs)

    @classmethod
    def slug_generator(cls, common_name: str, color: str, feature_values: list) -> str:
        if feature_values:
            feature_values_str = ' '.join(feature_values)
            slug_text = ' '.join([common_name, color, feature_values_str])
        else:
            slug_text = ' '.join([common_name, color])

        slug = slugify(slug_text)
        return slug

    @classmethod
    def get(cls, *args, **kwargs) -> Product:
        try:
            product = Product.objects.get(master__isnull=False, *args, **kwargs)
            return product
        except Product.DoesNotExist:
            raise ObjectNotFoundException('Product not found')
        except ValueError:
            raise ValidationException(WRONG_LOOKUP)

    @classmethod
    def get_variation(cls, *args, **kwargs) -> Product:
        try:
            product = Product.objects.get(master__isnull=False, *args, **kwargs)
            return product
        except Product.DoesNotExist:
            raise ObjectNotFoundException('Product not found')

    @classmethod
    def validate_variation(cls, variation_product: Product):
        if variation_product.master is None:
            raise ValidationException(message='Этот продукт не является вариантом')

    @classmethod
    def delete(cls, product: Product):
        cls.validate_variation(variation_product=product)
        if product.offers_count > 0:
            raise ValidationException(message='Удаление товара, в котором имеются предложения продавцов невозможна')

        product_id = product.id
        product.delete()
        ProductProducer.product_delete(product_id=product_id)

    @classmethod
    def bulk_turn_off_visibility_of_product(cls, master_product: Product):
        try:
            if cls.filter(master=master_product, offers_count__gt=0).exists():
                raise ValidationException(
                    message='Выключение мастер карточки, к вариантам ' 'которой имеются предложения невозможно'
                )
            visible_variants = cls.filter(master=master_product, is_visible=True)
            visible_variant_ids = list(visible_variants.values_list('id', flat=True))
            visible_variants.update(is_visible=False)
            updated_visible_variants = cls.filter(id__in=visible_variant_ids)
            for variant_product in updated_visible_variants:
                ProductProducer.product_update(product=variant_product)
        except IntegrityError as e:
            raise IntegrityException(f'Невозможно оптом изменить видимость продуктов: {str(e)}')

    @classmethod
    def validate_product_slug(cls, slug: str):
        if Product.objects.filter(slug__exact=slug):
            raise ValidationException(message='Такой товар уже существует')

    @classmethod
    def create(
        cls,
        master: Product,
        variant_name: str,
        color: Color,
        is_visible: bool,
        main_photo_id: str,
        photo_ids: list,
        features: list,
        creator: User,
        miniature_photo_id: Optional[str] = None,
    ) -> Product:
        try:
            miniature_photo = None
            if miniature_photo_id:
                miniature_photo = CDNService.get_image_dict(image_id=miniature_photo_id)
            main_photo_dict = CDNService.get_image_dict(image_id=main_photo_id)
            photos_list = []
            for photo_id in photo_ids:
                photo_dict = CDNService.get_image_dict(image_id=photo_id)
                photos_list.append(photo_dict)

            feature_values_list = [value['value_id'].value for value in features]

            generated_slug = cls.slug_generator(master.common_name, color.name, feature_values_list)
            cls.validate_product_slug(slug=generated_slug)

            product = Product.objects.create(
                master=master,
                brand=master.brand,
                category=master.category,
                variant_name=variant_name,
                slug=generated_slug,
                is_visible=is_visible,
                color=color,
                main_photo=main_photo_dict,
                photos=photos_list,
                description=master.description,
                miniature_photo=miniature_photo,
            )
            for selected_value in features:
                feature = selected_value['feature_id']
                value = selected_value['value_id']
                if not value.feature == feature:
                    raise ValidationException('Can not create product variation: wrong values in features list')
                product_feature, _ = ProductFeature.objects.get_or_create(product=product, feature=feature)
                ProductFeatureValue.objects.create(product_feature=product_feature, feature_value=value)

            if is_visible and not master.is_visible:
                master.is_visible = True
                master.save()

            ProductProducer.product_create(product=product)
            ActivityProducer.activity_create(
                product=product,
                object_model=PRODUCT_MODEL,
                user_id=creator.id,
                activity_type=CREATE_ACTIVITY,
                created_or_updated_date=product.created_at,
            )
            return product
        except IntegrityError as e:
            raise IntegrityException(f'Can not create product variation: {str(e)}')

    @classmethod
    @transaction.atomic
    def update(
        cls,
        product: Product,
        variant_name: str,
        color: Color,
        main_photo_id: str,
        photo_ids: list,
        is_visible: bool,
        features: list,
        editor: User,
        miniature_photo_id: Optional[str] = None,
    ) -> Product:
        try:
            feature_values_list = [value['value_id'].value for value in features]

            new_generated_slug = cls.slug_generator(product.master.common_name, color.name, feature_values_list)
            if new_generated_slug != product.slug:
                cls.validate_product_slug(slug=new_generated_slug)

            if miniature_photo_id:
                product.miniature_photo = CDNService.get_image_dict(image_id=miniature_photo_id)
            main_photo_dict = CDNService.get_image_dict(image_id=main_photo_id)
            photos_list = []
            for photo_id in photo_ids:
                photo_dict = CDNService.get_image_dict(image_id=photo_id)
                photos_list.append(photo_dict)

            product.slug = new_generated_slug
            product.variant_name = variant_name
            product.color = color
            product.main_photo = main_photo_dict
            product.photos = photos_list
            cls.update_variation_product_visibility(variation_product=product, is_visible=is_visible)
            product.save()

            ProductFeature.objects.filter(product=product).delete()

            for selected_value in features:
                feature = selected_value['feature_id']
                value = selected_value['value_id']
                if not value.feature == feature:
                    raise ValidationException('Can not update product variation: wrong values in features list')
                product_feature, _ = ProductFeature.objects.get_or_create(product=product, feature=feature)
                ProductFeatureValue.objects.create(product_feature=product_feature, feature_value=value)

            ProductProducer.product_update(product=product)
            ActivityProducer.activity_create(
                product=product,
                object_model=PRODUCT_MODEL,
                user_id=editor.id,
                activity_type=UPDATE_ACTIVITY,
                created_or_updated_date=product.updated_at,
            )
            return product
        except IntegrityError as e:
            raise IntegrityException(f'Can not update product: {str(e)}')

    @classmethod
    def update_min_price_old_price_and_offers_count(
        cls, product: Product, offers_min_price: str, offers_old_price: str, offers_count: int
    ):
        try:
            product.offers_min_price = offers_min_price
            product.offers_old_price = offers_old_price
            product.offers_count = offers_count
            product.save()
            return product
        except IntegrityError as e:
            raise IntegrityException(f'Can not update product: {str(e)}')

    @classmethod
    def validate_variation_product_turning_off_visibility(cls, variation_product: Product):
        if variation_product.offers_count > 0:
            raise ValidationException(message='Выключение вариант карточки у которой имеются предложения невозможно')

    @classmethod
    def turn_on_master_product_visibility_over_variation(cls, master_product: Product, is_visible: bool):
        try:
            master_product.is_visible = is_visible
            master_product.save()
            master_product.refresh_from_db()

        except IntegrityError as e:
            raise IntegrityException(f'Мастер карточка не может быть включена: {str(e)}')

    @classmethod
    def update_variation_product_visibility(cls, variation_product: Product, is_visible: bool) -> Product:
        if variation_product.is_visible == is_visible:
            return variation_product

        try:
            cls.validate_variation(variation_product=variation_product)
            if not is_visible and variation_product.is_visible:
                cls.validate_variation_product_turning_off_visibility(variation_product=variation_product)

            variation_product.is_visible = is_visible
            if variation_product.is_visible:
                cls.turn_on_master_product_visibility_over_variation(
                    master_product=variation_product.master, is_visible=variation_product.is_visible
                )
            variation_product.save()
            variation_product.refresh_from_db()

            ProductProducer.product_update(product=variation_product)

            return variation_product
        except IntegrityError as e:
            raise IntegrityException(f'Can not update feature group: {str(e)}')

    @classmethod
    def check_product_variant_name_for_uniqueness(cls, name: str, master_product: Product) -> dict:
        variant_products = cls.filter(master=master_product, variant_name__iexact=name).first()
        return {'is_duplicated': bool(variant_products), 'variant_name': name if variant_products is not None else None}

    @classmethod
    def bulk_update_products_slug_and_common_name(cls, master: Product, slug: str, common_name: str) -> int:
        try:
            updated = cls.filter(master=master.id).update(
                slug=Replace('slug', Value(master.slug), Value(slug)), common_name=common_name
            )
            ProductProducer.master_product_bulk_update_products_slug_and_common_name(
                master_product=master, slug=slug, common_name=common_name
            )
            return updated
        except IntegrityError as e:
            raise IntegrityException(f'Can not bulk update products slug: {str(e)}')

    @classmethod
    def get_products_with_offers_with_list_of_category_ids(cls, category_ids: list) -> QuerySet[Product]:
        products_with_offers = Product.objects.filter(
            Q(category_id__in=category_ids, offers_count__gt=0)
            | Q(category__parent__parent_id__in=category_ids, offers_count__gt=0)
            | Q(category__parent_id__in=category_ids, offers_count__gt=0)
        )
        return products_with_offers

    @classmethod
    def get_point_of_sale_active_product_variations(
            cls,
            point_of_sale_id: int,
            master_product_id: int,
    ) -> bool:
        try:
            response = requests.get(
                f'{settings.SHOP_HOST}/api/v1/system/point_of_sale/{point_of_sale_id}/active_products/{master_product_id}/',
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FailedDependencyException(message=str(e))
