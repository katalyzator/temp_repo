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
from products.tests.factories import ProductFactory


class MasterProductRetrieveViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = 'v1:retrieve_update_master_product'
        self.category = CategoryFactory()
        self.brand = BrandFactory(categories=self.category)
        self.color = ColorFactory()
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_features = FeatureFactory(group=self.feature_group)
        self.master_product = ProductFactory(
            color=self.color, brand=self.brand, category=self.category, variation_features=self.variation_features
        )
        self.variation_features = FeatureFactory(group=self.feature_group, position=1, is_multichoice=True)
        self.color = ColorFactory(name='Test name')
        self.product = ProductFactory(
            category=self.category, brand=self.brand, variation_features=self.variation_features, color=self.color
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
    def test_success_get_master_product(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(reverse(self.url, kwargs={'slug_or_pk': self.master_product.slug}), format='json')

        expected_response = {
            'id': self.master_product.id,
            'common_name': self.master_product.common_name,
            'slug': self.master_product.slug,
            'brand': {'id': self.brand.id, 'name': self.brand.name},
            'category': {'id': self.category.id, 'name': self.category.name},
            'main_photo': self.master_product.main_photo,
            'miniature_photo': None,
            'photos': self.master_product.photos,
            'video_urls': self.master_product.video_urls,
            'description': self.master_product.description,
            'variation_features': [],
            'features': [],
            'is_visible': self.master_product.is_visible,
            'variations': [],
            'offers_count': self.master_product.offers_count,
            'created_at': self.master_product.created_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'updated_at': self.master_product.updated_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_master_product_not_found(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(reverse(self.url, kwargs={'slug_or_pk': 'slug'}), format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['message'], 'Master product not found')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_master_product_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager

        response = self.client.get(reverse(self.url, kwargs={'slug_or_pk': self.master_product.slug}), format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
