from django.conf import settings

from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.serializers.twitter.TwitterPromotedTweetSerializer import TwitterPromotedTweetSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class TwitterPromotedTweetDetail(BaseDetail):
    serializer_class = TwitterPromotedTweetSerializer

    @property
    def queryset(self):
        return TwitterPromotedTweet.objects.all()
