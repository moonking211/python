from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES
from restapi.models.Advertiser import Advertiser
from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TwitterAccountSerializer(BaseModelSerializer):
    """
    tw_twitter_user_id = PKRelatedField(queryset=TwitterUser.objects_raw.all())
    advertiser_id = PKRelatedField(queryset=Advertiser.objects_raw.all())
    name = serializers.CharField(required=True, allow_blank=False)
    account_id = serializers.CharField(required=True, allow_blank=False)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)
    """
    handle = serializers.SerializerMethodField()

    class Meta:
        model = TwitterAccount
        fields = ('tw_account_id',
                  'tw_twitter_user_id',
                  'advertiser_id',
                  'name',
                  'handle',
                  'promotable_user_id',
                  'is_manage',
                  'created_at',
                  'last_update')
    
    def get_handle(self, instance):
        return instance.promotable_user_id.name