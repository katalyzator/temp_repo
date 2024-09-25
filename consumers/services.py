import logging
import os

import django
from asgiref.sync import sync_to_async
from django.db import IntegrityError

from common.constants import OFFER_PRICE_COUNT_UPDATE_TOPIC
from common.constants import PRODUCT_REVIEW_COUNT_RATING_UPDATE_TOPIC
from products.consumers.schemas import ProductReviewCountRatingSchema

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.base')
django.setup()

from products.consumers.schemas import OfferCountPriceSchema
from products.models import Product


@sync_to_async
def persist_offer_count(data: OfferCountPriceSchema):
    logging.info(f'KAFKA.MESSAGE.CONSUMED topic={OFFER_PRICE_COUNT_UPDATE_TOPIC} data={data.asdict()}')
    try:
        product = Product.objects.get(id=data.product_id)
        product.offers_count = data.count
        product.offers_min_price = data.price
        product.offers_old_price = data.old_price
        product.save()
        logging.info(f'Offer count updated successfully {product.id}')

    except Product.DoesNotExist:
        logging.error(f'Product with id {data.product_id} does not exist')
    except IntegrityError as e:
        logging.error(f'Can not update product: {str(e)}')


@sync_to_async
def persist_product_review_count_rating_update_topic(data: ProductReviewCountRatingSchema):
    logging.info(f'KAFKA.MESSAGE.CONSUMED topic={PRODUCT_REVIEW_COUNT_RATING_UPDATE_TOPIC} data={data.asdict()}')
    try:
        product = Product.objects.get(id=data.product_id)
        product.rating = data.rating
        product.reviews_count = data.reviews_count
        product.save()
        logging.info(f'Product review and rating updated successfully {product.id}')

    except Product.DoesNotExist:
        logging.error(f'Product with id {data.product_id} does not exist')
    except IntegrityError as e:
        logging.error(f'Can not update product: {str(e)}')
