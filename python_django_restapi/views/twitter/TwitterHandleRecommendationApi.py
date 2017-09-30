from twitter_ads.client import Client
from twitter_ads.http import Request
from django.utils.http import int_to_base36

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from restapi.models.twitter.TwitterAccount import TwitterAccount
from rest_framework import status
from .helper import human_format

class TwitterHandleRecommendationApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        account_id = request.query_params.get('account_id')
        handles = request.query_params.get('handles')
        number = request.query_params.get('number', 40)
        if account_id and handles and number:
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

            api_domain = 'https://ads.twitter.com'
            resource = '/accounts/%s/handle_recommendation.json?handles=%s&number=%s' % (account_id, handles, number)
            response = Request(client, 'get', resource, domain=api_domain).perform()
            if not (int(number) == 2):
                res = []
                api_domain = 'https://api.twitter.com'
                i = 0
                while i < len(response.body):
                    temp = response.body[i:i+100]
                    i += 100
                    resource = '/1.1/users/lookup.json?screen_name=%s' % ','.join(temp)
                    resource = resource.replace('@', '')
                    result = Request(client, 'get', resource, domain=api_domain).perform()
                    for r in result.body:
                        r['followers_count_str'] = human_format(r['followers_count'])
                    res = res + result.body
                return Response(res)
            return Response(response.body)
        else:
            return Response({'errors': 'account_id, keywords or number is missing.'}, status=status.HTTP_400_BAD_REQUEST)
