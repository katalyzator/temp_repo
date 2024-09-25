import logging

from common.constants import MASTER_PRODUCT_DELETE_TOPIC
from common.constants import PRODUCT_CREATE_TOPIC
from common.constants import PRODUCT_DELETE_TOPIC
from common.constants import PRODUCT_SLUG_AND_COMMON_NAME_BULK_UPDATE_TOPIC
from common.constants import PRODUCT_UPDATE_TOPIC
from products.models import Product
from project.producer import MessagePublisher

kafka_messenger = MessagePublisher()


class ProductProducer:
    @classmethod
    def product_create(cls, product: Product):
        topic = PRODUCT_CREATE_TOPIC

        data = dict(
            product_id=product.id,
            master_id=product.master.id,
            common_name=product.master.common_name,
            variant_name=product.variant_name,
            slug=product.slug,
            brand_id=product.brand.id,
            category_id=product.category.id,
            main_photo=product.main_photo,
            photos=product.photos,
            video_urls=product.video_urls,
            description=product.description,
            is_visible=product.is_visible,
        )
        kafka_messenger.publish(topic=topic, data=data)
        logging.info(f'KAFKA.MESSAGE.PRODUCED topic={topic} data={data}')

    @classmethod
    def product_update(cls, product: Product):
        topic = PRODUCT_UPDATE_TOPIC

        data = dict(
            product_id=product.id,
            master_id=product.master.id,
            common_name=product.master.common_name,
            variant_name=product.variant_name,
            slug=product.slug,
            brand_id=product.brand.id,
            category_id=product.category.id,
            main_photo=product.main_photo,
            photos=product.photos,
            video_urls=product.video_urls,
            description=product.description,
            is_visible=product.is_visible,
        )
        kafka_messenger.publish(topic=topic, data=data)
        logging.info(f'KAFKA.MESSAGE.PRODUCED topic={topic} data={data}')

    @classmethod
    def master_product_bulk_update_products_slug_and_common_name(
        cls, master_product: Product, slug: str, common_name: str
    ):
        topic = PRODUCT_SLUG_AND_COMMON_NAME_BULK_UPDATE_TOPIC

        data = dict(
            master_id=master_product.id, master_product_slug=master_product.slug, new_slug=slug, common_name=common_name
        )
        kafka_messenger.publish(topic=topic, data=data)
        logging.info(f'KAFKA.MESSAGE.PRODUCED topic={topic} data={data}')

    @classmethod
    def product_delete(cls, product_id: int):
        topic = PRODUCT_DELETE_TOPIC

        data = dict(
            product_id=product_id,
        )
        kafka_messenger.publish(topic=topic, data=data)
        logging.info(f'KAFKA.MESSAGE.PRODUCED topic={topic} data={data}')

    @classmethod
    def master_product_delete(cls, master_id: int):
        topic = MASTER_PRODUCT_DELETE_TOPIC

        data = dict(
            master_id=master_id,
        )
        kafka_messenger.publish(topic=topic, data=data)
        logging.info(f'KAFKA.MESSAGE.PRODUCED topic={topic} data={data}')
