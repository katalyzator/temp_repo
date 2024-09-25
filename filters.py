from django_filters import rest_framework as filters

from common.filters import MultipleListFilter
from products.models import Product


class MasterProductFilter(filters.FilterSet):
    category_names = MultipleListFilter(field_name='category__name', lookup_expr='icontains')
    brand_names = MultipleListFilter(field_name='brand__name', lookup_expr='icontains')

    class Meta:
        model = Product
        fields = ['brand_names', 'category_names', 'is_visible']
