from unittest import mock

from authorizations.user_service import UserData
from pytils.translit import slugify
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from brands.tests.factories import BrandFactory
from categories.tests.factories import CategoryFactory
from colors.tests.factories import ColorFactory
from common.constants import ACCOUNT_MANAGER_ROLE
from common.constants import CONTENT_MANAGER_ROLE
from common.utils import generate_test_jwt_token
from features.tests.factories import FeatureFactory
from features.tests.factories import FeatureGroupFactory
from features.tests.factories import FeatureValueFactory
from products.models import Product
from products.tests.factories import ProductFactory
from products.tests.factories import ProductFeatureFactory
from products.tests.factories import ProductFeatureValueFactory


class ProductUpdateViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = 'v1:update_product'
        self.category = CategoryFactory()
        self.color = ColorFactory(name='Color test')
        self.color2 = ColorFactory(name='Another test color')
        self.brand = BrandFactory(categories=self.category)
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_features = FeatureFactory(group=self.feature_group, is_variation=True)
        self.variation_feature_not_variation = FeatureFactory(
            group=self.feature_group,
        )
        self.master_product = ProductFactory(
            color=self.color,
            offers_count=1,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_feature_not_variation,
        )
        self.master_product_feature = ProductFeatureFactory(
            product=self.master_product, feature=self.variation_feature_not_variation
        )

        self.feature_value = FeatureValueFactory(feature=self.variation_features)
        self.master_product_feature_value = ProductFeatureValueFactory(
            product_feature=self.master_product_feature, feature_value=self.feature_value
        )
        self.slug_text = ' '.join([self.master_product.common_name, self.color.name, '11 19'])
        self.variation_product = ProductFactory(
            master=self.master_product,
            color=self.color,
            slug=slugify(self.slug_text),
            offers_count=0,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_features,
        )
        self.mock_content_manager = UserData(
            id=1,
            roles=[CONTENT_MANAGER_ROLE],
            email='content@example.com',
            phone_number='+996777777777',
            is_visible=True,
            dcb_id='1111',
        )
        self.mock_account_manager = UserData(
            id=5,
            roles=[ACCOUNT_MANAGER_ROLE],
            email='account@example.com',
            phone_number='+996555555555',
            is_visible=True,
            dcb_id='5555',
        )
        self.token = generate_test_jwt_token(
            roles=self.mock_content_manager.roles,
            user_id=self.mock_content_manager.id,
            phone_number=self.mock_content_manager.phone_number,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_success_update_product_with_zero_offers_count(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image
        body = {
            'variant_name': 'Galaxy Test',
            'is_visible': False,
            'color': self.color2.id,
            'main_photo_id': '11',
            'miniature_photo_id': '11',
            'photo_ids': ['12'],
            'features': [
                {
                    'feature_id': self.variation_features.id,
                    'value_id': self.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.id}), data=body, format='json'
        )
        self.assertEqual(mock_get_image.called, True)
        product = Product.objects.get(id=self.variation_product.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(product.color.id, self.color2.id)
        self.assertEqual(response.json()['color']['id'], body['color'])
        self.assertEqual(response.json()['variant_name'], body['variant_name'])
        self.assertEqual(response.json()['is_visible'], body['is_visible'])
        self.assertEqual(response.json()['main_photo'], mocked_image)
        self.assertEqual(response.json()['photos'], [mocked_image])
        self.assertEqual(response.json()['slug'], product.slug)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_failure_update_product_with_offers(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        self.variation_product.offers_count = 1
        self.variation_product.save()
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image
        body = {
            'variant_name': 'Galaxy Test',
            'is_visible': False,
            'color': self.color2.id,
            'main_photo_id': '11',
            'miniature_photo_id': '11',
            'photo_ids': ['12'],
            'features': [
                {
                    'feature_id': self.variation_features.id,
                    'value_id': self.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.id}), data=body, format='json'
        )
        self.assertEqual(mock_get_image.called, True)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.json()['message'], 'Выключение вариант карточки у которой имеются предложения невозможно'
        )

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_failure_update_product_with_wrong_feature_value(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        feature_value = FeatureValueFactory(feature=self.variation_feature_not_variation)
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image
        body = {
            'variant_name': 'Galaxy Test',
            'is_visible': False,
            'color': self.color2.id,
            'main_photo_id': '11',
            'miniature_photo_id': '11',
            'photo_ids': ['12'],
            'features': [
                {
                    'feature_id': self.variation_features.id,
                    'value_id': feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.id}), data=body, format='json'
        )
        product = Product.objects.get(id=self.variation_product.id)
        self.assertEqual(product.color.id, self.color.id)
        self.assertEqual(product.is_visible, True)
        self.assertEqual(mock_get_image.called, True)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.json()['message'], 'Can not update product variation: wrong values in features list')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_product_slug_exist(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        feature = FeatureFactory(group=self.feature_group, is_variation=True)
        feature_value = FeatureValueFactory(feature=feature)
        slug_text = ' '.join([self.master_product.common_name, self.color.name, feature_value.value])
        ProductFactory(
            master=self.master_product,
            color=self.color,
            slug=slugify(slug_text),
            offers_count=0,
            category=self.category,
            brand=self.brand,
            variation_features=feature,
        )
        body = {
            'variant_name': 'Galaxy Test',
            'is_visible': False,
            'color': self.color.id,
            'main_photo_id': '11',
            'miniature_photo_id': '11',
            'photo_ids': ['12'],
            'features': [
                {
                    'feature_id': feature.id,
                    'value_id': feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.id}), data=body, format='json'
        )
        product = Product.objects.get(id=self.variation_product.id)
        self.assertEqual(product.is_visible, True)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.json()['message'], 'Такой товар уже существует')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_product(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        body = {
            'variant_name': 'Galaxy Test',
            'is_visible': False,
            'color': self.color2.id,
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'offers_count': 2,
            'features': [
                {
                    'feature_id': self.variation_features.id,
                    'value_id': self.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.id + 1}), data=body, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['message'], 'Product not found')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_product_without_variant_name(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        body = {
            'is_visible': False,
            'color': self.color.id,
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'offers_count': 2,
            'features': [
                {
                    'feature_id': self.variation_features.id,
                    'value_id': self.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.pk}), data=body, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.json()['message'], 'Invalid input')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_product_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager
        body = {}

        response = self.client.put(
            reverse(self.url, kwargs={'pk': self.variation_product.id}), data=body, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
