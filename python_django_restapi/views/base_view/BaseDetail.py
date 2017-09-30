import copy

from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response


class BaseDetail(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

#    def update(self, request, *args, **kwargs):
#        # pylint: disable=not-callable
#        serializer = self.serializer_class(data=request.data, instance=self.get_object())
#        validate_only = self.request.query_params.get('validate_only', False)
#        if validate_only and serializer.is_valid():
#            validated_data = copy.copy(serializer.validated_data)
#            for name, value in validated_data.items():
#                if isinstance(value, models.Model):
#                    validated_data[name] = value.pk
#            return Response(validated_data, status.HTTP_202_ACCEPTED)
#        return super(BaseDetail, self).update(request, *args, **kwargs)
