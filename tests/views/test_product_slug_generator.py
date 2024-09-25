from django.test import TestCase

from brands.tests.factories import BrandFactory
from categories.tests.factories import CategoryFactory
from colors.tests.factories import ColorFactory
from common.exceptions import ValidationException
from features.tests.factories import FeatureFactory
from features.tests.factories import FeatureGroupFactory
from features.tests.factories import FeatureValueFactory
from products.services.product_services import ProductService
from products.tests.factories import ProductFactory
from products.tests.factories import ProductFeatureFactory


class AnimalTestCase(TestCase):
    def setUp(self):
        self.color = ColorFactory(name='Test color')
        self.category = CategoryFactory(slug='slug', name='Name', level=1, position=1, image={'url': 'example'})
        self.brand = BrandFactory(name='Test brand', slug='slug', categories=self.category)
        self.feature_group = FeatureGroupFactory(name='Name', visual_name='Name', position=1, categories=self.category)
        self.feature = FeatureFactory(
            name='Feature',
            value_type='string',
            group=self.feature_group,
            is_main=True,
            position=1,
            is_variation=False,
            is_multichoice=True,
        )
        self.product = ProductFactory(
            common_name='Test name',
            variant_name='Test variant name',
            slug='test-slug',
            color=self.color,
            brand=self.brand,
            category=self.category,
            main_photo={'url': 'example'},
            photos={'url': 'example'},
            video_urls={'url': 'example'},
            is_visible=True,
            variation_features=self.feature,
        )
        self.product_feature = ProductFeatureFactory(product=self.product, feature=self.feature)
        self.feature_value = FeatureValueFactory(value='Value', feature=self.feature)
        self.product_feature_values = [self.feature_value.value, self.feature_value.value]

    def test_slug_successful_generation(self):
        product_services = ProductService()
        response = product_services.slug_generator(
            common_name='Test name', color=self.color.name, feature_values=self.product_feature_values
        )
        expected_response = 'test-name-test-color-value-value'
        self.assertEqual(response, expected_response)

    def test_slug_failure_validation(self):
        product_services = ProductService()
        expected_response = {'message': 'Такой товар уже существует'}
        with self.assertRaises(ValidationException):
            response = product_services.validate_product_slug(slug='test-slug')

            self.assertRaises(response, expected_response)
