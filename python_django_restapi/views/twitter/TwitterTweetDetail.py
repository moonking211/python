from django.conf import settings

from restapi.models.twitter.TwitterTweet import TwitterTweet
from restapi.serializers.twitter.TwitterTweetSerializer import TwitterTweetSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class TwitterTweetDetail(BaseDetail):
    serializer_class = TwitterTweetSerializer

    @property
    def queryset(self):
        return TwitterTweet.objects.all()
