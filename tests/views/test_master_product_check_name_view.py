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


class MasterProductCheckNameViewTest(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = 'v1:master_product_check_name'
        self.category = CategoryFactory()
        self.brand = BrandFactory(categories=self.category)
        self.color = ColorFactory()
        self.feature_group = FeatureGroupFactory(categories=self.category)
        self.variation_features = FeatureFactory(group=self.feature_group)
        self.variation_features = FeatureFactory(group=self.feature_group, position=1, is_multichoice=True)
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
    def test_check_master_product_name_is_not_duplicated(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        expected_response = {'is_duplicated': False, 'common_name': None}
        response = self.client.get(reverse(self.url), {'common_name': 'Test name unique'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_check_master_product_name_is_duplicated(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        expected_response = {'is_duplicated': True, 'common_name': self.master_product.common_name}
        response = self.client.get(reverse(self.url), {'common_name': self.master_product.common_name}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.master_product.common_name)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_check_master_product_name_is_duplicated_diff_case(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        expected_response = {'is_duplicated': True, 'common_name': self.master_product.common_name}
        response = self.client.get(
            reverse(self.url), {'common_name': str(self.master_product.common_name).upper()}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.master_product.common_name)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_check_master_product_name_is_duplicated_empty_query(self, mock_user):
        mock_user.return_value = self.mock_content_manager
        expected_response = {'message': 'Invalid input', 'errors': {'common_name': ['This field is required.']}}
        response = self.client.get(reverse(self.url), format='json')

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.json(), expected_response)

    @mock.patch('authorizations.user_service.UserService.get_user_by_phone_number')
    def test_failure_check_master_product_name_permission_denied(self, mock_user):
        mock_user.return_value = self.mock_account_manager

        response = self.client.get(reverse(self.url), {'common_name': 'Test name unique'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()['detail'], 'You do not have permission to perform this action.')
