
import twitter
from twitter_ads.client import Client
from twitter_ads.http import Request
from django.utils.http import int_to_base36, base36_to_int
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from restapi.models.twitter.TwitterAccount import TwitterAccount
from bs4 import BeautifulSoup

class TwitterPromotableUserApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        account_id = request.query_params.get('account_id')
        account = TwitterAccount.objects_raw.get(pk=account_id)
        account_id_base36 = int_to_base36(int(account_id))

        oauth_token=account.tw_twitter_user_id.oauth_token
        oauth_secret=account.tw_twitter_user_id.oauth_secret
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token, oauth_secret)
        resource = '/{api_version}/accounts/{account_id}/promotable_users'.format(api_version=settings.TW_API_VERSION, account_id=account_id_base36)
        response = Request(client, 'get', resource).perform()
        response.body['data']
        root_promotable_user_id = ''
        user_ids = []
        for u in response.body['data']:
            if u['promotable_user_type'] == 'FULL':
                root_promotable_user_id = int(u['user_id'])
            user_ids.append(u['user_id'])

        api = twitter.Api(consumer_key=settings.TW_CONSUMER_KEY,
                          consumer_secret=settings.TW_CONSUMER_SECRET,
                          access_token_key=settings.TW_ACCESS_TOKEN,
                          access_token_secret=settings.TW_ACCESS_SECRET)
        res = []
        promotable_users = api.UsersLookup(user_id=user_ids)
        for u in promotable_users:
            _id = u.id
            if root_promotable_user_id == u.id:
                _id = ''
            res.append({'id': _id, 'screen_name': '@%s' % u.screen_name})

        return Response({'results': res})

class TwitterPromotedTweetApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        account_id = request.query_params.get('account_id')
        next_cursor = request.query_params.get('next_cursor')
        objective = request.query_params.get('objective', 'APP_INSTALLS')
        promotable_user_id = request.query_params.get('promotable_user_id')

        if objective == 'APP_INSTALLS':
            objective = 1
        elif objective == 'WEBSITE_CLICKS':
            objective = 5
        else:
            objective = 0

        if not account_id:
            return Response([])

        account = TwitterAccount.objects_raw.get(pk=account_id)
        account_id_base36 = int_to_base36(int(account_id))

        oauth_token=account.tw_twitter_user_id.oauth_token
        oauth_secret=account.tw_twitter_user_id.oauth_secret
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, oauth_token, oauth_secret)
        api_domain = 'https://ads.twitter.com'

        if next_cursor:
            next_cursor = '&cursor=%s' % next_cursor
        else:
            next_cursor = ''
        resource = '/accounts/{account_id}/tweets/dashboard/tweet_rows?' \
            'manage_campaigns=true&objective={objective}&account={account_id}' \
            '&lang=en&promotable_user={promotable_user}{next_cursor}' \
            .format(
                account_id=account_id_base36,
                next_cursor=next_cursor,
                objective=objective,
                promotable_user=promotable_user_id
            )
        response = Request(client, 'get', resource, domain=api_domain).perform()

        results = []
        html = response.body['tweetRows']
        soup = BeautifulSoup(html, 'html.parser')
        checkboxes = soup.find_all("input", {"class": "tweet-checkbox"})
        tweets = soup.find_all("div", {"class": "Tweet--timeline"})
        for i in range(len(tweets)):
            result = {
                'preview': tweets[i].prettify(),
                'tweet_id': str(checkboxes[i]['value'])
            }
            results.append(result)

        return Response(dict(results=results, next_cursor=response.body.get('cursor')))
