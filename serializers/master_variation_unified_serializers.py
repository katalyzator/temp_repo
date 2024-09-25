from rest_framework import serializers

from products.models import Product


class UnifiedProductIsVisibleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            'id',
            'is_visible',
        )
