from authorizations.authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response

from common.constants import INVALID_INPUT
from common.pagination import GeneralPagination
from common.responses import NotAcceptableExceptionResponse
from common.utils import get_query_params_data
from features.serializers.feature_serializers import VariationFeatureIdsSerializer
from features.serializers.feature_serializers import VariationFeatureIsUsedSerializer
from permissions.permissions import IsAuthenticated
from permissions.permissions import IsContentManager
from permissions.permissions import IsSuperAdmin
from products.filters import MasterProductFilter
from products.serializers.master_product_serializers import MasterProductCommonNameSerializer
from products.serializers.master_product_serializers import MasterProductCommonNameValiditySerializer
from products.serializers.master_product_serializers import MasterProductCreateSerializer
from products.serializers.master_product_serializers import MasterProductDetailSerializer
from products.serializers.master_product_serializers import MasterProductListSerializer
from products.serializers.master_product_serializers import MasterProductUpdateSerializer
from products.serializers.product_serializers import ProductVariantNameSerializer
from products.serializers.product_serializers import ProductVariantNameValiditySerializer
from products.services.master_product_services import MasterProductService
from products.services.product_services import ProductService


class MasterProductListCreateView(ListCreateAPIView):
    serializer_class = MasterProductListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = MasterProductFilter
    search_fields = ['common_name']
    ordering_fields = ['common_name', 'category__name', 'offers_count', 'created_at']
    pagination_class = GeneralPagination
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def get_queryset(self):
        return MasterProductService.filter()

    def post(self, request, *args, **kwargs):
        serializer = MasterProductCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        master_product = MasterProductService.create(**serializer.validated_data, creator=request.user)
        data = MasterProductDetailSerializer(master_product).data
        return Response(data, status=status.HTTP_201_CREATED)


class MasterProductRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = MasterProductDetailSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def get(self, request, *args, **kwargs):
        product = MasterProductService.get(slug=self.kwargs['slug_or_pk'])
        serializer = self.serializer_class(product)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        master_product = MasterProductService.get(pk=kwargs['slug_or_pk'])
        serializer = MasterProductUpdateSerializer(master_product, data=request.data)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        master_product = MasterProductService.update(
            master_product=master_product, editor=request.user, **serializer.validated_data
        )
        data = self.get_serializer(master_product).data
        return Response(data=data, status=status.HTTP_200_OK)


class MasterProductCheckVariantNameView(GenericAPIView):
    serializer_class = ProductVariantNameSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.query_params)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        product = MasterProductService.get(id=kwargs['pk'])
        check_result_dict = ProductService.check_product_variant_name_for_uniqueness(
            name=serializer.validated_data['variant_name'], master_product=product
        )
        data = ProductVariantNameValiditySerializer(check_result_dict).data
        return Response(data=data, status=status.HTTP_200_OK)


class MasterProductCheckCommonNameView(GenericAPIView):
    serializer_class = MasterProductCommonNameSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def get(self, request):
        serializer = self.get_serializer(data=request.query_params)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        check_result_dict = MasterProductService.check_master_product_name_is_duplicated(
            name=serializer.validated_data['common_name']
        )
        data = MasterProductCommonNameValiditySerializer(check_result_dict).data
        return Response(data=data, status=status.HTTP_200_OK)


class MasterProductVariationFeatureUsageView(GenericAPIView):
    serializer_class = VariationFeatureIsUsedSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def get(self, request, *args, **kwargs):
        query_params_data = get_query_params_data(query_params=request.query_params)
        query_param_serializer = VariationFeatureIdsSerializer(data=query_params_data)
        if not query_param_serializer.is_valid():
            return NotAcceptableExceptionResponse(
                data={'message': 'Invalid query parameters', 'errors': query_param_serializer.errors}
            )
        master_product = MasterProductService.get(pk=self.kwargs['pk'])
        queryset = MasterProductService.get_master_product_variation_features_usage(
            master_product=master_product,
            variation_feature_ids=query_param_serializer.validated_data['variation_feature_ids'],
        )
        data = self.get_serializer(queryset, many=True).data
        return Response(data=data, status=status.HTTP_200_OK)
