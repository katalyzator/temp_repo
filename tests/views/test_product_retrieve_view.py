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
from products.models import Product
from products.tests.factories import ProductFactory


class ProductRetrieveViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = 'v1:retrieve_product'
        self.category = CategoryFactory()
        self.brand = BrandFactory(categories=self.category)
        self.color = ColorFactory()
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_features = FeatureFactory(group=self.feature_group)
        self.master_product = ProductFactory(
            color=self.color, category=self.category, brand=self.brand, variation_features=self.variation_features
        )
        self.product = ProductFactory(
            master=self.master_product,
            color=self.color,
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
    def test_success_get_product(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(reverse(self.url, kwargs={'slug': self.product.slug}), format='json')
        product = Product.objects.get(slug=self.product.slug)
        expected_response = {
            'id': self.product.id,
            'variant_name': self.product.variant_name,
            'slug': self.product.slug,
            'color': {'id': self.product.color.id, 'name': self.product.color.name},
            'main_photo': self.product.main_photo,
            'photos': self.product.photos,
            'miniature_photo': None,
            'features': [],
            'is_visible': self.product.is_visible,
            'offers_count': self.product.offers_count,
            'created_at': self.product.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'updated_at': product.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_product_not_found(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(reverse(self.url, kwargs={'slug': 'slug'}), format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['message'], 'Product not found')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_product_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager

        response = self.client.get(reverse(self.url, kwargs={'slug': self.product.slug}), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
