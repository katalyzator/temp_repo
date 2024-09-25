from django.urls import path

from products.views.master_product_views import MasterProductCheckCommonNameView
from products.views.master_product_views import MasterProductCheckVariantNameView
from products.views.master_product_views import MasterProductListCreateView
from products.views.master_product_views import MasterProductRetrieveUpdateView
from products.views.master_product_views import MasterProductVariationFeatureUsageView
from products.views.master_variation_unified_views import MasterVariationUpdateDestroyView
from products.views.product_views import ProductListCreateView
from products.views.product_views import ProductRetrieveView
from products.views.product_views import ProductUpdateView

urlpatterns = [
    path('master_products/check-name/', MasterProductCheckCommonNameView.as_view(), name='master_product_check_name'),
    path('master_products/', MasterProductListCreateView.as_view(), name='list_create_master_product'),
    path(
        'master_products/<slug:slug_or_pk>/',
        MasterProductRetrieveUpdateView.as_view(),
        name='retrieve_update_master_product',
    ),
    path(
        'master_products/<int:pk>/check-variant_name/',
        MasterProductCheckVariantNameView.as_view(),
        name='product_check_variant_name',
    ),
    path(
        'master_products/<int:pk>/check-variation_features-usage/',
        MasterProductVariationFeatureUsageView.as_view(),
        name='master_product_check_variation_features_usage',
    ),
    path('products/', ProductListCreateView.as_view(), name='list_create_product'),
    path('products/<int:pk>/', ProductUpdateView.as_view(), name='update_product'),
    path('products/<slug:slug>/', ProductRetrieveView.as_view(), name='retrieve_product'),
    path(
        'unified_products/<int:pk>/', MasterVariationUpdateDestroyView.as_view(), name='update_destroy_master_variation'
    ),
]
