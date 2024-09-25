from authorizations.authentication import JWTAuthentication
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from common.constants import INVALID_INPUT
from common.responses import NotAcceptableExceptionResponse
from permissions.permissions import IsAuthenticated
from permissions.permissions import IsContentManager
from permissions.permissions import IsSuperAdmin
from products.serializers.master_variation_unified_serializers import UnifiedProductIsVisibleUpdateSerializer
from products.services.master_variation_unified_services import MasterVariationUnifiedService


class MasterVariationUpdateDestroyView(GenericAPIView):
    serializer_class = UnifiedProductIsVisibleUpdateSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (
        IsAuthenticated,
        IsSuperAdmin | IsContentManager,
    )

    def delete(self, request, *args, **kwargs):
        product = MasterVariationUnifiedService.get(id=self.kwargs['pk'])
        MasterVariationUnifiedService.delete(product=product)
        return Response(data={'message': 'Success'}, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        self.serializer_class = UnifiedProductIsVisibleUpdateSerializer
        product = MasterVariationUnifiedService.get(id=kwargs['pk'])
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return NotAcceptableExceptionResponse(data={'message': INVALID_INPUT, 'errors': serializer.errors})
        result = MasterVariationUnifiedService.update(
            product=product,
            is_visible=serializer.validated_data['is_visible'],
        )
        data = UnifiedProductIsVisibleUpdateSerializer(result).data
        return Response(data=data, status=status.HTTP_200_OK)
