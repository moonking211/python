import json
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from twitter_ads.http import Request
from twitter_ads.client import Client
from .helper import human_format
import twitter

class TwitterUserSearchApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )
    def get(self, request):
        q = request.query_params.get('q')
        if not q:
            return Response({'error': 'query is required'}, status=status.HTTP_400_BAD_REQUEST)

        q = q.replace('@', '')
        api_domain = 'https://api.twitter.com'
        client = Client(settings.TW_CONSUMER_KEY, settings.TW_CONSUMER_SECRET, settings.TW_ACCESS_TOKEN,
                                settings.TW_ACCESS_SECRET)
        resource = '/1.1/users/search.json?count=20&q=%s' % q
        result = Request(client, 'get', resource, domain=api_domain).perform()
        res = []
        for r in result.body:
            res.append(dict(followers_count_str=human_format(r['followers_count']), targeting_value=r['id_str'], name=r['name'], profile_image_url=r['profile_image_url'], screen_name='@'+r['screen_name']))

        return Response(data=dict(results=res))


class TwitterUsersVerifyApi(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        screen_names = request.query_params.get('screen_names').split(',')
        api = twitter.Api(consumer_key=settings.TW_CONSUMER_KEY,
                                  consumer_secret=settings.TW_CONSUMER_SECRET,
                                  access_token_key=settings.TW_ACCESS_TOKEN,
                                  access_token_secret=settings.TW_ACCESS_SECRET)

        invalid_followers = [n.lower() for n in screen_names]
        def chunks(l, n):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i:i+n]

        batches = chunks(screen_names, 100)

        res = {}
        for batch in batches:
            followers = api.UsersLookup(screen_name=batch)
            for u in followers:
                screen_name = u.screen_name
                if screen_name.lower() in invalid_followers:
                    invalid_followers.remove(screen_name.lower())
                    res[screen_name.lower()] = dict(targeting_value=str(u.id), name=u.name, verified=u.verified,
                                            protected=u.protected, profile_image_url=u.profile_image_url,
                                            followers_count_str=human_format(u.followers_count),
                                            screen_name=u.screen_name)

        for f in invalid_followers:
            res[f] = False

        return Response(data=res)