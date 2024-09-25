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


class MasterProductCheckVariationFeatureUsageViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = 'v1:master_product_check_variation_features_usage'
        self.category = CategoryFactory()
        self.brand = BrandFactory(categories=self.category)
        self.color = ColorFactory()
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_feature = FeatureFactory(group=self.feature_group)
        self.variation_feature_2 = FeatureFactory(group=self.feature_group)
        self.master_product = ProductFactory(
            color=self.color, category=self.category, brand=self.brand, variation_features=self.variation_feature
        )
        self.product = ProductFactory(
            master=self.master_product,
            color=self.color,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_feature,
        )
        self.product_feature = ProductFeatureFactory(product=self.product, feature=self.variation_feature)

        self.feature_value = FeatureValueFactory(feature=self.variation_feature)
        self.product_feature_value = ProductFeatureValueFactory(
            product_feature=self.product_feature, feature_value=self.feature_value
        )
        self.product_2 = ProductFactory(
            master=self.master_product,
            color=self.color,
            category=self.category,
            brand=self.brand,
            variation_features=self.variation_feature,
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
    def test_success_get_variation_features_list_with_usage(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(
            reverse(self.url, kwargs={'pk': self.master_product.id}),
            {'variation_feature_ids': [f'{self.variation_feature.id},{self.variation_feature_2.id}']},
            format='json',
        )
        expected_response = [
            {'variation_feature_id': self.variation_feature.id, 'is_feature_used': True},
            {'variation_feature_id': self.variation_feature_2.id, 'is_feature_used': False},
        ]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_variation_features_product_not_found(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(
            reverse(self.url, kwargs={'pk': self.master_product.id + 10}),
            {'variation_feature_ids': [self.variation_feature.id, self.variation_feature_2.id]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['message'], 'Master product not found')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_variation_features_product_incorrect_variation_feature_ids(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        response = self.client.get(
            reverse(self.url, kwargs={'pk': self.master_product.id}), {'variation_feature_ids': 'banana'}, format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.json()['message'], 'Invalid query parameters')

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_get_variation_features_usage_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager

        response = self.client.get(
            reverse(self.url, kwargs={'pk': self.master_product.id}),
            {'variation_feature_ids': [self.variation_feature.id, self.variation_feature_2.id]},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
