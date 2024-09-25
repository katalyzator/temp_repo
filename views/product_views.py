from authorizations.authentication import JWTAuthentication
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from common.constants import INVALID_INPUT
from common.responses import NotAcceptableExceptionResponse
from permissions.permissions import CanGetProducts
from permissions.permissions import IsAuthenticated
from permissions.permissions import IsContentManager
from permissions.permissions import IsSuperAdmin
from products.serializers.product_serializers import ProductBriefListSerializer
from products.serializers.product_serializers import ProductCreateSerializer
from products.serializers.product_serializers import ProductDetailSerializer
from products.serializers.product_serializers import ProductUpdateSerializer
from products.services.product_services import ProductService


class ProductListCreateView(ListCreateAPIView):
    serializer_class = ProductBriefListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['master__common_name', 'variant_name']
    ordering = ['master__common_name']
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated, CanGetProducts)

    def get_queryset(self):
        return ProductService.filter(is_visible=True)

    def post(self, request, *args, **kwargs):
        self.permission_classes = (IsAuthenticated, IsSuperAdmin | IsContentManager)
        self.check_permissions(request=request)
        serializer = ProductCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        product = ProductService.create(**serializer.validated_data, creator=request.user)
        data = ProductDetailSerializer(product).data
        return Response(data, status=status.HTTP_201_CREATED)


class ProductRetrieveView(RetrieveAPIView):
    serializer_class = ProductDetailSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def get(self, request, *args, **kwargs):
        product = ProductService.get(slug=self.kwargs['slug'])
        serializer = self.serializer_class(product)
        return Response(serializer.data)


class ProductUpdateView(GenericAPIView):
    serializer_class = ProductDetailSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def put(self, request, *args, **kwargs):
        product = ProductService.get(pk=kwargs['pk'])
        serializer = ProductUpdateSerializer(product, data=request.data)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        product = ProductService.update(product=product, editor=request.user, **serializer.validated_data)
        data = self.get_serializer(product).data
        return Response(data=data, status=status.HTTP_200_OK)
