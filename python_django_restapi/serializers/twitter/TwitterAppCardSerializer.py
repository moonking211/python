from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES, TW_CARD_TYPE, TW_CUSTOM_CTA
from restapi.models.twitter.TwitterAppCard import TwitterAppCard
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.MultipleChoiceField import MultipleChoiceField
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TwitterAppCardSerializer(serializers.ModelSerializer):
    tw_account_id = PKRelatedField(queryset=TwitterAccount.objects_raw.all())
    name = serializers.CharField(required=True, allow_blank=False)
    card_type = MultipleChoiceField(choices=TW_CARD_TYPE, required=False)
    preview_url = serializers.CharField(required=True, allow_blank=False)
    app_country_code = serializers.CharField(required=False, allow_blank=False)
    iphone_app_id = serializers.CharField(required=False, allow_blank=False)
    ipad_app_id =  serializers.CharField(required=False, allow_blank=False)
    googleplay_app_id = serializers.CharField(required=False, allow_blank=False)
    deep_link = serializers.CharField(required=False, allow_blank=False)
    custom_cta = MultipleChoiceField(choices=TW_CUSTOM_CTA, required=False)
    custom_icon_media_id = serializers.CharField(required=False, allow_blank=False)
    custom_app_description = serializers.CharField(required=False, allow_blank=False)
    image_media_id = serializers.CharField(required=False, allow_blank=False)
    wide_app_image_media_id = serializers.CharField(required=False, allow_blank=False)
    wide_app_image = serializers.CharField(required=False, allow_blank=False)
    video_id = serializers.CharField(required=False, allow_blank=False)
    video_url = serializers.CharField(required=False, allow_blank=False)
    video_poster_url = serializers.CharField(required=False, allow_blank=False)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)

    class Meta:
        model = TwitterAppCard
        fields = ('tw_app_card_id',
                  'tw_account_id',
                  'name',
                  'card_type',
                  'preview_url',
                  'app_country_code',
                  'iphone_app_id',
                  'ipad_app_id',
                  'googleplay_app_id',
                  'deep_link',
                  'custom_cta',
                  'custom_icon_media_id',
                  'custom_app_description',
                  'image_media_id',
                  'wide_app_image',
                  'wide_app_image_media_id',
                  'video_id',
                  'video_url',
                  'video_poster_url',
                  'status',
                  'created_at',
                  'last_update')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterAppCard.objects_raw.all(),
                fields=('tw_tweet_id',)
            )
        ]