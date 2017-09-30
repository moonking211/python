from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.serializers.twitter.TwitterPromotedTweetSerializer import TwitterPromotedTweetSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class TwitterPromotedTweetList(BaseListCreate):
    serializer_class = TwitterPromotedTweetSerializer
    contains_filter_include_pk = True
    query_filter_fields = ('tw_promoted_tweet_id', 'status')
    order_fields = ('tw_protmoted_tweet', '-tw_protmoted_tweet',
                    'tw_protmoted_tweet_id', '-tw_protmoted_tweet_id')
    list_filter_fields = ('tw_line_item_id', )
    @property
    def queryset(self):
        return TwitterPromotedTweet.objects.all()
