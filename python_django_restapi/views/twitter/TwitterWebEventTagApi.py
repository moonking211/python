
from twitter_ads.client import Client
from twitter_ads.http import Request
from django.utils.http import int_to_base36

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from restapi.models.twitter.TwitterAccount import TwitterAccount

class TwitterWebEventTagApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        account_id = request.query_params.get('account_id')

        account = TwitterAccount.objects_raw.get(pk=account_id)
        oauth_token = account.tw_twitter_user_id.oauth_token or settings.TW_ACCESS_TOKEN
        oauth_secret = account.tw_twitter_user_id.oauth_secret or settings.TW_ACCESS_SECRET
        if not account_id:
            return Response([])
        account_id = long(account_id)
        if isinstance(account_id,(int,long)):
            account_id = int_to_base36(account_id)

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token,
                            oauth_secret)
        if settings.TW_SANDBOX:
            client.sandbox = settings.TW_SANDBOX
        resource = '/{api_version}/accounts/{account_id}/web_event_tags'.format(api_version=settings.TW_API_VERSION, account_id=account_id)
        response = Request(client, 'get', resource).perform()
        json = response.body['data']
        
        return Response(json)
