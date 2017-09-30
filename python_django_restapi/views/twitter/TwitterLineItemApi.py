import json
from django.conf import settings
from rest_framework.response import Response

from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from restapi.registry import REGISTRY
from restapi.models.twitter.TwitterLineItem import TwitterLineItem

class TwitterLineItemApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        params = request.data if request.method == 'POST' else request.query_params
        account_id = params.get('account_id', None)
        tw_account_id = params.get('tw_account_id', None)

        if account_id is not None and tw_account_id is None:
            tw_account = TwitterLineItem.objects.get(account_id=account_id)
            tw_account_id = tw_account.tw_account_id

        if tw_account_id is not None:
            data = TwitterLineItem.fetch_line_items(dict(tw_account_id=tw_account_id))
            return Response(data=data, status=status.HTTP_200_OK)

        return Response(data=dict(status='error', msg='Missing input tw_account_id ID'), status=status.HTTP_404_NOT_FOUND)
