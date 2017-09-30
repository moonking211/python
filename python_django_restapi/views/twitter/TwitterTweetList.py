from restapi.models.twitter.TwitterTweet import TwitterTweet
from restapi.serializers.twitter.TwitterTweetSerializer import TwitterTweetSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class TwitterTweetList(BaseListCreate):
    serializer_class = TwitterTweetSerializer
    contains_filter_include_pk = True
    query_filter_fields = ('tw_tweet', 'tw_tweet_id')
    order_fields = ('tw_tweet', '-tw_tweet',
                    'tw_tweet_id', '-tw_tweet_id')

    @property
    def queryset(self):
        return TwitterTweet.objects.all()
