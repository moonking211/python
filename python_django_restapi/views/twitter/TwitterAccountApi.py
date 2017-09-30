import json
from django.conf import settings
from rest_framework.response import Response
from django.utils.http import int_to_base36, base36_to_int
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from restapi.registry import REGISTRY
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.models.Advertiser import Advertiser
from django.core.management import call_command
import oauth2 as oauth
import urlparse
import urllib
from twitter_ads.client import Client
import twitter
from django.core.cache import cache as redis_cache
from StringIO import StringIO


request_token_url = 'https://twitter.com/oauth/request_token'
authorize_url = 'https://twitter.com/oauth/authorize'
access_token_url = 'https://twitter.com/oauth/access_token'


class TwitterSyncApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        campaign_id = request.query_params.get('campaign_id')
        tw_campaign_id=request.query_params.get('tw_campaign_id')
        tw_account_id=request.query_params.get('tw_account_id')
        content = StringIO()
        try:
            if campaign_id:
                call_command('TwitterSync', campaign_id=campaign_id, stdout=content)
            elif tw_campaign_id and tw_account_id:
                call_command('TwitterSync', tw_account_id=tw_account_id, tw_campaign_id=tw_campaign_id, stdout=content)
            else:
                call_command('TwitterSync', stdout=content)
        except Exception as e:
            content.seek(0)
            return Response(dict(status='fail', error_msg=str(e), message=content.read()), status=status.HTTP_400_BAD_REQUEST)

        content.seek(0)
        return Response(dict(status='ok', message=content.read()))


class TwitterLiveAccountsApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        q = request.query_params.get('q')
        tw_user_id = request.query_params.get('tw_user_id')
        tw_user = TwitterUser.objects_raw.get(pk=tw_user_id)
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, tw_user.oauth_token, tw_user.oauth_secret)
        accounts = client.accounts()
        results = []
        for a in accounts:
            tw_account = TwitterAccount.objects_raw.filter(tw_account_id=int(a.id, 36)).first()
            if not tw_account and (not q or (q and (q in a.name or q in a.id))):
                results.append(dict(name=a.name, id=a.id))

        return Response(dict(results=results))


class TwitterAddAccountApi(generics.GenericAPIView):
    def post(self, request):
        tw_user_id = request.data.get('tw_user_id')
        tw_user = TwitterUser.objects_raw.get(pk=tw_user_id)
        tw_account_id = request.data.get('tw_account_id')
        advertiser_id = request.data.get('advertiser_id')
        advertiser = Advertiser.objects_raw.get(pk=advertiser_id)
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, tw_user.oauth_token, tw_user.oauth_secret)
        account = client.accounts(tw_account_id)
        users = account.promotable_users()
        user_info = None
        is_manage = False

        for u in users:
            if u.promotable_user_type == 'FULL':
                api = twitter.Api(consumer_key=settings.TW_CONSUMER_KEY,
                                  consumer_secret=settings.TW_CONSUMER_SECRET,
                                  access_token_key=tw_user.oauth_token,
                                  access_token_secret=tw_user.oauth_secret)
                # https://dev.twitter.com/rest/reference/get/users/show
                # https://api.twitter.com/1.1/users/show.json?screen_name=<user_id>
                user_info = api.GetUser(user_id=u.user_id)

        funding_instruments = account.funding_instruments()
        for f in funding_instruments:
            if not f.cancelled and f.id in settings.TW_MANAGE_FUNDING_INSTRUMENT_IDS:
                is_manage = True

        if user_info:
            tw_promotable_user, created = TwitterUser.objects_raw.get_or_create(tw_twitter_user_id=user_info.id, name=user_info.screen_name)
            TwitterAccount(tw_account_id=int(tw_account_id, 36),
                           promotable_user_id=tw_promotable_user,
                           name=account.name,
                           advertiser_id=advertiser,
                           tw_twitter_user_id=tw_user,
                           is_manage=is_manage).save()

        return Response({'status': 'ok'})


class TwitterAccessTokenApi(generics.CreateAPIView):
    def post(self, request, *args, **kwargs):
        callback_url = request.data.get('callback_url')
        consumer = oauth.Consumer(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET)
        client = oauth.Client(consumer)
        resp, content = client.request(request_token_url, "POST", body=urllib.urlencode({"oauth_callback": callback_url}))
        if resp['status'] != '200':
            error_message = "Invalid response %s" % resp['status']
            return Response(dict(status='fail', msg=error_message), status=status.HTTP_400_BAD_REQUEST)
        request_token = dict(urlparse.parse_qsl(content))
        oauth_token = request_token['oauth_token']
        oauth_token_secret = request_token['oauth_token_secret']
        # expire after 10 minutes
        redis_cache.set("tw_token_%s" % oauth_token, oauth_token_secret, timeout=60*10)
        url = "%s?oauth_token=%s" % (authorize_url, oauth_token)
        return Response(dict(status='ok', url=url))


class TWitterCallbackApi(generics.GenericAPIView):
    def get(self, request):
        oauth_token = request.query_params.get('oauth_token')
        oauth_verifier = request.query_params.get('oauth_verifier')
        oauth_denied = request.query_params.get('denied')

        # if the oauth request was denied, delete our local token and show an error message
        if oauth_denied:
            return Response(dict(status='fail', msg='the OAuth request was denied by this user'),
                            status=status.HTTP_400_BAD_REQUEST)

        if not oauth_token or not oauth_verifier:
            return Response(dict(status='fail', msg='callback param(s) missing'),
                            status=status.HTTP_400_BAD_REQUEST)

        # unless oauth_token is still stored locally, return error
        oauth_token_secret = redis_cache.get("tw_token_%s" % oauth_token, False)
        if not oauth_token_secret:
            return Response(dict(status='fail', msg='oauth_token not found locally'),
                            status=status.HTTP_400_BAD_REQUEST)

        # if we got this far, we have both call back params and we have found this token locally

        consumer = oauth.Consumer(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET)
        token = oauth.Token(oauth_token, oauth_token_secret)
        token.set_verifier(oauth_verifier)
        client = oauth.Client(consumer, token)

        resp, content = client.request(access_token_url, "POST")
        access_token = dict(urlparse.parse_qsl(content))
        real_oauth_token = access_token['oauth_token']
        real_oauth_token_secret = access_token['oauth_token_secret']
        screen_name = access_token['screen_name']
        user_id = access_token['user_id']
        twitter_user, created = TwitterUser.objects_raw.get_or_create(tw_twitter_user_id=user_id, name=screen_name)

        updated = False
        if not created and real_oauth_token != twitter_user.oauth_token:
            updated = True

        twitter_user.oauth_token = real_oauth_token
        twitter_user.oauth_secret = real_oauth_token_secret
        twitter_user.save()

        return Response(dict(created=created, updated=updated, screen_name=screen_name))
