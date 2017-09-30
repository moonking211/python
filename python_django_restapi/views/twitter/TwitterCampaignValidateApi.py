import twitter
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from restapi.models.Campaign import Campaign

class TwitterCampaignValidateApi(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request):
        followers = request.data.get('followers')
        followers = [u.strip() for u in followers.split(',') if u]
        api = twitter.Api(consumer_key=settings.TW_CONSUMER_KEY,
                                  consumer_secret=settings.TW_CONSUMER_SECRET,
                                  access_token_key=settings.TW_ACCESS_TOKEN,
                                  access_token_secret=settings.TW_ACCESS_SECRET)

        invalid_followers = list(followers)
        def chunks(l, n):
            """Yield successive n-sized chunks from l."""
            for i in range(0, len(l), n):
                yield l[i:i+n]

        batches = chunks(followers, 100)
        suggested = []
        map = {}
        for batch in batches:
            followers = api.UsersLookup(screen_name=batch)
            for u in followers:
                screen_name = u.screen_name
                if screen_name in invalid_followers:
                    invalid_followers.remove(screen_name)
                    map[screen_name] = u.id
                else:
                    suggested.append(screen_name)
        res = {
            'invalid_followers': ','.join(invalid_followers),
            'suggested_followers': ','.join(suggested),
            'all_valid': len(invalid_followers) == 0,
            'map': map
        }
        return Response(res)