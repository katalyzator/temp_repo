from unittest import mock

from authorizations.user_service import UserData
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
from products.tests.factories import ProductFactory
from products.tests.factories import ProductFeatureFactory
from products.tests.factories import ProductFeatureValueFactory


class ProductUpdateViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = 'v1:retrieve_update_master_product'
        self.category = CategoryFactory()
        self.color = ColorFactory(name='Color test')
        self.brand = BrandFactory(categories=self.category)
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_features = FeatureFactory(group=self.feature_group, is_variation=True)
        self.variation_feature_2 = FeatureFactory(group=self.feature_group, is_variation=True)
        self.variation_feature_not_variation = FeatureFactory(
            group=self.feature_group,
        )
        self.master_product = ProductFactory(
            color=self.color,
            offers_count=0,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_feature_not_variation,
        )
        self.master_product.variation_features.set([self.variation_feature_not_variation])
        self.master_product_with_offer = ProductFactory(
            color=self.color,
            offers_count=1,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_feature_not_variation,
        )
        self.master_product_with_offer.variation_features.set([self.variation_feature_not_variation])
        self.master_product_feature = ProductFeatureFactory(
            product=self.master_product, feature=self.variation_feature_not_variation
        )

        self.feature_value = FeatureValueFactory(feature=self.variation_feature_not_variation)
        self.master_product_feature_value = ProductFeatureValueFactory(
            product_feature=self.master_product_feature, feature_value=self.feature_value
        )
        self.master_product_feature_2 = ProductFeatureFactory(
            product=self.master_product, feature=self.variation_features
        )

        self.feature_value_2 = FeatureValueFactory(feature=self.variation_features)
        self.master_product_feature_value_2 = ProductFeatureValueFactory(
            product_feature=self.master_product_feature_2, feature_value=self.feature_value_2
        )
        self.master_product_for_variation = ProductFactory(
            color=self.color,
            offers_count=1,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_features,
        )
        self.master_product_for_variation.variation_features.set([self.variation_features])
        self.variation_product_with_offer = ProductFactory(
            master=self.master_product_for_variation,
            color=self.color,
            offers_count=1,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_features,
        )
        self.product_feature = ProductFeatureFactory(
            product=self.variation_product_with_offer, feature=self.variation_features
        )

        self.feature_value_3 = FeatureValueFactory(feature=self.variation_features)
        self.product_feature_value = ProductFeatureValueFactory(
            product_feature=self.product_feature, feature_value=self.feature_value_3
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
    def test_success_update_master_product(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image
        body = {
            'common_name': 'Galaxy Test',
            'is_visible': False,
            'brand': self.brand.id,
            'description': 'Some description test',
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'variation_features': [self.variation_features.id],
            'features': [
                {
                    'feature_id': self.master_product_feature_value.product_feature.feature.id,
                    'value_id': self.master_product_feature_value.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product.id}), data=body, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['brand']['id'], body['brand'])
        self.assertEqual(response.json()['common_name'], body['common_name'])
        self.assertEqual(response.json()['is_visible'], body['is_visible'])
        self.assertEqual(response.json()['description'], body['description'])
        self.assertEqual(response.json()['main_photo'], mocked_image)
        self.assertEqual(response.json()['photos'], [mocked_image])
        self.assertEqual(response.json()['video_urls'], body['video_urls'])
        self.assertEqual(response.json()['variation_features'][0]['id'], body['variation_features'][0])
        self.assertEqual(response.json()['features'][0]['id'], body['features'][0]['feature_id'])

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_success_update_master_product_with_offers(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image

        body = {
            'common_name': 'Galaxy Test',
            'is_visible': False,
            'brand': self.brand.id,
            'description': 'Some description test',
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'variation_features': [self.variation_features.id],
            'features': [
                {
                    'feature_id': self.master_product_feature_value.product_feature.feature.id,
                    'value_id': self.master_product_feature_value.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product_with_offer.id}), data=body, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.json()['message'], 'Мастер карточка не может быть отключена')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_master_product(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        body = {
            'common_name': 'Galaxy Test',
            'is_visible': False,
            'brand': self.brand.id,
            'description': 'Some description test',
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'variation_features': [self.variation_features.id],
            'features': [
                {
                    'feature_id': self.master_product_feature_value.product_feature.feature.id,
                    'value_id': self.master_product_feature_value.feature_value.id,
                }
            ],
            'offers_count': 2,
        }
        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product.id + 100}), data=body, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['message'], 'Master product not found')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_master_product_without_common_name(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        body = {
            'is_visible': False,
            'brand': self.brand.id,
            'description': 'Some description test',
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'variation_features': [self.variation_features.id],
            'features': [
                {
                    'feature_id': self.master_product_feature_value.product_feature.feature.id,
                    'value_id': self.master_product_feature_value.feature_value.id,
                }
            ],
            'offers_count': 2,
        }
        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product.pk}), data=body, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.json()['message'], 'Invalid input')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_failure_update_master_product_has_variation_using_this_feature(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image
        body = {
            'common_name': 'Galaxy Test',
            'is_visible': True,
            'brand': self.brand.id,
            'description': 'Some description test',
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'variation_features': [self.variation_feature_2.id],
            'features': [
                {
                    'feature_id': self.master_product_feature_value.product_feature.feature.id,
                    'value_id': self.master_product_feature_value.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product_for_variation.id}), data=body, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.json()['message'], 'Есть вариант с этим параметром')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_failure_update_master_product_with_variation_feature_feature_similar(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        mocked_image = {
            'id': 11,
            'url': 'http://10.120.200.243:9000/market-test/6kb_pic-16647790287173183.jpg',
            'filename': '6kb_pic-16647790287173183.jpg',
            'file_size': 6,
        }
        mock_get_image.return_value = mocked_image

        body = {
            'common_name': 'Galaxy Test',
            'is_visible': False,
            'brand': self.brand.id,
            'description': 'Some description test',
            'main_photo_id': '11',
            'photo_ids': ['12'],
            'video_urls': ['https://youtube.com/somevideo'],
            'variation_features': [self.variation_features.id],
            'features': [
                {
                    'feature_id': self.master_product_feature_value_2.product_feature.feature.id,
                    'value_id': self.master_product_feature_value_2.feature_value.id,
                }
            ],
        }
        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product.id}), data=body, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(
            response.json()['message'], 'Характеристики вариантов и характеристики мастер карточки не могут совпадать'
        )

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_update_master_product_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager
        body = {}

        response = self.client.put(
            reverse(self.url, kwargs={'slug_or_pk': self.master_product.id}), data=body, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
