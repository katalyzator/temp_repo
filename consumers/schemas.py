from decimal import Decimal
from typing import Optional

import faust


class OfferCountPriceSchema(faust.Record, serializer='json'):
    product_id: int
    count: int
    price: Optional[Decimal]
    old_price: Optional[Decimal]


class ProductReviewCountRatingSchema(faust.Record, serializer='json'):
    product_id: int
    reviews_count: int
    rating: float
