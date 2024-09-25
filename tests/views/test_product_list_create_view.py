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
from common.constants import MERCHANT_MANAGER_ROLE
from common.utils import generate_test_jwt_token
from features.tests.factories import FeatureFactory
from features.tests.factories import FeatureGroupFactory
from features.tests.factories import FeatureValueFactory
from products.models import Product
from products.tests.factories import ProductFactory


class ProductListCreateViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = reverse('v1:list_create_product')
        self.category = CategoryFactory()
        self.color = ColorFactory(name='Color test')
        self.brand = BrandFactory(categories=self.category)
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_features = FeatureFactory(
            group=self.feature_group,
            is_variation=True,
        )
        self.feature_value = FeatureValueFactory(feature=self.variation_features)
        self.master_product = ProductFactory(
            color=self.color, category=self.category, brand=self.brand, variation_features=self.variation_features
        )
        self.visible_product = ProductFactory(
            master=self.master_product,
            color=self.color,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_features,
        )

        self.invisible_product = ProductFactory(
            master=self.master_product,
            color=self.color,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_features,
            is_visible=False,
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
        self.mock_merchant_manager = UserData(
            id=3,
            roles=[MERCHANT_MANAGER_ROLE],
            email='merchant@example.com',
            phone_number='+996333333333',
            is_visible=True,
            dcb_id='3333',
        )
        self.token = generate_test_jwt_token(
            roles=self.mock_content_manager.roles,
            user_id=self.mock_content_manager.id,
            phone_number=self.mock_content_manager.phone_number,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    @mock.patch('common.cdn_services.CDNService.get_image_dict')
    def test_success_create(self, mock_get_image, mock_user):
        mock_user.return_value = self.mock_content_manager
        mock_get_image.return_value = {
            'id': 264,
            'url': 'http://10.120.200.243:9000/market-test/Samsung-Logo-2-1667976110464065.png',
            'filename': 'Samsung-Logo-2-1667976110464065.png',
            'file_size': 47,
        }
        body = {
            'master': self.master_product.id,
            'variant_name': 'Galaxy S22',
            'color': self.color.id,
            'is_visible': True,
            'main_photo_id': '264',
            'photo_ids': ['265'],
            'video_urls': ['https://example.com/11/'],
            'features': [
                {
                    'feature_id': self.variation_features.id,
                    'value_id': self.feature_value.id,
                }
            ],
        }

        response = self.client.post(self.url, data=body, format='json')
        product = Product.objects.last()

        self.assertEqual(mock_get_image.called, True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['id'], product.id)
        self.assertEqual(response.json()['variant_name'], product.variant_name)
        self.assertEqual(response.json()['slug'], product.slug)
        self.assertEqual(response.json()['color'], {'id': self.color.id, 'name': self.color.name})
        self.assertEqual(response.json()['is_visible'], product.is_visible)
        self.assertEqual(response.json()['offers_count'], product.offers_count)
        self.assertEqual(response.json()['created_at'], product.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))
        self.assertEqual(response.json()['updated_at'], product.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'))

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_create_product_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager
        body = {}

        response = self.client.post(self.url, data=body, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_create_product_with_nonexistent_features(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        body = {
            'master': self.master_product.id,
            'name': 'Galaxy S22',
            'color': self.color.id,
            'is_visible': True,
            'main_photo_id': '264',
            'photo_ids': ['265'],
            'video_urls': ['https://example.com/11/'],
            'features': [
                {
                    'feature_id': self.variation_features.id + 10,
                    'value_id': self.feature_value.id,
                }
            ],
        }
        response = self.client.post(
            self.url,
            data=body,
            format='json',
        )
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.json()['message'], 'Invalid input')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_create_product_with_empty_body(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        body = {}

        response = self.client.post(
            self.url,
            data=body,
            format='json',
        )
        self.assertEqual(response.status_code, 406)
        self.assertEqual(response.json()['message'], 'Invalid input')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_success_get_products(self, mock_user):
        mock_user.return_value = self.mock_account_manager
        response = self.client.get(self.url, format='json')

        expected_response = [
            {
                'id': self.visible_product.id,
                'slug': self.visible_product.slug,
                'common_name': self.visible_product.master.common_name,
                'variant_name': self.visible_product.variant_name,
                'main_photo': self.visible_product.main_photo,
            }
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_success_get_products_with_search_by_visible_product_name(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(
            self.url,
            {'search': self.visible_product.master.common_name + ' ' + self.visible_product.variant_name},
            format='json',
        )

        expected_response = [
            {
                'id': self.visible_product.id,
                'slug': self.visible_product.slug,
                'common_name': self.visible_product.master.common_name,
                'variant_name': self.visible_product.variant_name,
                'main_photo': self.visible_product.main_photo,
            }
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_success_get_products_with_search_by_invisible_product_name(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(self.url, {'search': self.invisible_product.variant_name}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_products_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_merchant_manager

        response = self.client.get(self.url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
