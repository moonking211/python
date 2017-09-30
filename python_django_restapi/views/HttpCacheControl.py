from restapi.http_caching import invalidate
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK


class HttpCacheDrop(generics.GenericAPIView):
    def get(self, request, model_name, pks=None):
        if pks:
            pks = [int(v) for v in pks.split(",")]
        invalidate(model_name, pks)
        data = {}
        return Response(data, status=HTTP_200_OK)
