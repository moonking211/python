from rest_framework import serializers
from restapi.models.twitter.TwitterTweet import TwitterTweet
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TwitterTweetSerializer(serializers.ModelSerializer):
    tw_twitter_user_id = serializers.IntegerField()
    text = serializers.CharField()
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)

    class Meta:
        model = TwitterTweet
        fields = ('tw_tweet_id',
                  'tw_twitter_user_id',
                  'text',
                  'created_at',
                  'last_update')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterTweet.objects_raw.all(),
                fields=('tw_tweet_id',)
            )
        ]