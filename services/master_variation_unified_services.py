from common.constants import WRONG_LOOKUP
from common.exceptions import ObjectNotFoundException
from common.exceptions import ValidationException
from products.models import Product
from products.services.master_product_services import MasterProductService
from products.services.product_services import ProductService


class MasterVariationUnifiedService:
    @classmethod
    def get(cls, *args, **kwargs) -> Product:
        try:
            return Product.objects.get(*args, **kwargs)
        except Product.DoesNotExist:
            raise ObjectNotFoundException('Product not found')
        except ValueError:
            raise ValidationException(WRONG_LOOKUP)

    @classmethod
    def delete(cls, product: Product):
        if product.master:
            ProductService.delete(product=product)
        else:
            MasterProductService.delete(product=product)

    @classmethod
    def update(cls, product: Product, is_visible: bool):
        if product.master:
            return ProductService.update_variation_product_visibility(variation_product=product, is_visible=is_visible)
        else:
            return MasterProductService.update_master_product_visibility(master_product=product, is_visible=is_visible)
