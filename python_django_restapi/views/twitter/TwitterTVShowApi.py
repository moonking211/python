
from twitter_ads.client import Client
from twitter_ads.http import Request
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from rest_framework import status
from .helper import human_format


class TwitterTVShowApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        q = request.query_params.get('query')
        tv_market_locale = request.query_params.get('locale')
        if not q or not tv_market_locale:
            return Response(dict(errors='tv_market_locale is required'), status=status.HTTP_400_BAD_REQUEST)

        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, settings.TW_ACCESS_TOKEN,
                        settings.TW_ACCESS_SECRET)
        resource = '/%s/targeting_criteria/tv_shows?tv_market_locale=%s&q=%s' % (settings.TW_API_VERSION,
                                                                                 tv_market_locale, q)
        response = Request(client, 'get', resource).perform()
        json = response.body['data']
        for row in json:
            row['id_str'] = 'i%s:%s' % (row['id'], row['name'])
            row['estimated_users'] = human_format(row['estimated_users'])

        return Response(dict(results=json))
