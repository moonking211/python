
from twitter_ads.client import Client
from twitter_ads.http import Request


from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings


class TwitterAccountAppList(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, oauth_token=settings.TW_ACCESS_TOKEN, oauth_token_secret=settings.TW_ACCESS_SECRET):
        account_id = request.query_params.get('account_id')
        if not account_id:
            return Response([])

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                            oauth_token_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        resource = '/{api_version}/accounts/{account_id}/app_lists'.format(api_version=settings.TW_API_VERSION, account_id=account_id)
        response = Request(client, 'get', resource).perform()
        json = response.body['data']
        return Response(json)
