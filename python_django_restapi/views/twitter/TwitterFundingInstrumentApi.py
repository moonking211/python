
import json as json_tool
from twitter_ads.client import Client
from twitter_ads.http import Request
from django.utils.http import int_to_base36, base36_to_int

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from restapi.models.twitter.TwitterAccount import TwitterAccount
from django.core.cache import cache as redis_cache

class TwitterFundingInstrumentApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        account_id = request.query_params.get('account_id')
        _id = request.query_params.get('id')
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
        resource = '/{api_version}/accounts/{account_id}/funding_instruments'.format(api_version=settings.TW_API_VERSION, account_id=account_id)
        response = Request(client, 'get', resource).perform()
        json = response.body['data']
        
        if _id:
            for item in json:
                if _id == item['id']:
                    return Response([item])

        return Response(json)

class TwitterFundingInstrumentListView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        account_id = request.query_params.get('account_id')
        _id = request.query_params.get('id')
        _key = "funding-instrument-%s" % account_id
        json = redis_cache.get(_key)
        if json:
            json = json_tool.loads(json)
        else:
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
            resource = '/{api_version}/accounts/{account_id}/funding_instruments'.format(api_version=settings.TW_API_VERSION, account_id=account_id)
            response = Request(client, 'get', resource).perform()
            json = response.body['data']
            # expire after 10 mins
            redis_cache.set(_key, json_tool.dumps(json), timeout=60*10)
    
        for item in json:
            item['funding_instrument_id'] = base36_to_int(item['id'])
            if _id == item['id']:
                return Response(dict(results=[item]))

        return Response(dict(results=json))
