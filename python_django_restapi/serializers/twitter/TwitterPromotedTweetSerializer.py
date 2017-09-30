from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES
from restapi.models.twitter.TwitterPromotedTweet import TwitterPromotedTweet
from restapi.models.twitter.TwitterLineItem import TwitterLineItem
from restapi.models.twitter.TwitterTweet import TwitterTweet
from restapi.models.twitter.TwitterAppCard import TwitterAppCard

from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField

class TwitterPromotedTweetSerializer(serializers.ModelSerializer):
    tw_line_item_id = PKRelatedField(queryset=TwitterLineItem.objects_raw.all())
    tw_tweet_id = serializers.IntegerField()
    tw_app_card_id = serializers.IntegerField()
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)
    preview = serializers.SerializerMethodField()
    app_card = serializers.SerializerMethodField()

    class Meta:
        model = TwitterPromotedTweet
        fields = ('tw_promoted_tweet_id',
                  'tw_line_item_id',
                  'tw_tweet_id',
                  'tw_app_card_id',
                  'preview',
                  'app_card',
                  'status',
                  'created_at',
                  'last_update')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterPromotedTweet.objects_raw.all(),
                fields=('tw_promoted_tweet_id',)
            )
        ]

    def get_preview(self, instance):
        tweet = TwitterTweet.objects.filter(tw_tweet_id=instance.tw_tweet_id).first()
        if tweet:
              return tweet.text

        return ''

    def get_advertiser_id(self, instance):
        return instance._advertiser_id

    def get_app_card(self, instance):
        app_card = TwitterAppCard.objects.filter(tw_app_card_id=instance.tw_app_card_id).first()
        if app_card:
            video_player_url = ''
            if app_card.video_poster_url and app_card.video_url:
                video_player_url = "https://amp.twimg.com/amplify-web-player/prod/source.html?json_rpc=1&square_corners=1&image_src=%s&vmap_url=%s" % (app_card.video_poster_url, app_card.video_url)
            return {
              'type': app_card.card_type,
              'image': app_card.wide_app_image,
              'video_image': app_card.video_poster_url,
              'video_map': app_card.video_url,
              'video_player_url': video_player_url
            }

        return {}