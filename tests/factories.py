import factory
from factory import RelatedFactoryList

from ..models import Product
from ..models import ProductFeature
from ..models import ProductFeatureValue
from brands.tests.factories import BrandFactory
from categories.tests.factories import CategoryFactory
from colors.tests.factories import ColorFactory
from features.tests.factories import FeatureFactory
from features.tests.factories import FeatureValueFactory


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    common_name = factory.Sequence(lambda n: f'Common name_{n}')
    variant_name = factory.Sequence(lambda n: f'Variant name_{n}')
    slug = factory.Sequence(lambda n: f'Slug_{n}')
    color = factory.SubFactory(ColorFactory)
    main_photo = {
        'id': 187,
        'url': 'http://10.120.200.243:9000/market-test/Screenshot2022-09-26195410-16661925855799956.png',
        'filename': 'Screenshot2022-09-26195410-16661925855799956.png',
        'file_size': 7,
    }
    photos = {
        'id': 188,
        'url': 'http://10.120.200.243:9000/market-test/Screenshot2022-09-26195410-16661925855799956.png',
        'filename': 'Screenshot2022-09-26195410-16661925855799956.png',
        'file_size': 7,
    }
    video_urls = {
        'id': 189,
        'url': 'http://10.120.200.243:9000/market-test/Screenshot2022-09-26195410-16661925855799956.png',
        'filename': 'Screenshot2022-09-26195410-16661925855799956.png',
        'file_size': 7,
    }
    is_visible = True
    brand = factory.SubFactory(BrandFactory)
    category = factory.SubFactory(CategoryFactory)
    variation_features = RelatedFactoryList(FeatureFactory, factory_related_name='variation_products')


class MasterProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    common_name = factory.Sequence(lambda n: f'Common name_{n}')
    variant_name = factory.Sequence(lambda n: f'Variant name_{n}')
    slug = factory.Sequence(lambda n: f'Slug_{n}')
    color = factory.SubFactory(ColorFactory)
    brand = factory.SubFactory(BrandFactory)
    category = factory.SubFactory(CategoryFactory)
    main_photo = {
        'id': 187,
        'url': 'http://10.120.200.243:9000/market-test/Screenshot2022-09-26195410-16661925855799956.png',
        'filename': 'Screenshot2022-09-26195410-16661925855799956.png',
        'file_size': 7,
    }
    photos = {
        'id': 188,
        'url': 'http://10.120.200.243:9000/market-test/Screenshot2022-09-26195410-16661925855799956.png',
        'filename': 'Screenshot2022-09-26195410-16661925855799956.png',
        'file_size': 7,
    }
    video_urls = {
        'id': 189,
        'url': 'http://10.120.200.243:9000/market-test/Screenshot2022-09-26195410-16661925855799956.png',
        'filename': 'Screenshot2022-09-26195410-16661925855799956.png',
        'file_size': 7,
    }
    is_visible = True
    variation_features = RelatedFactoryList(FeatureFactory, factory_related_name='variation_products')


class ProductFeatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductFeature

    product = factory.SubFactory(ProductFactory)
    feature = factory.SubFactory(FeatureFactory)


class ProductFeatureValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProductFeatureValue

    product_feature = factory.SubFactory(ProductFeatureFactory)
    feature_value = factory.SubFactory(FeatureValueFactory)
