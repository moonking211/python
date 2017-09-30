from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES
from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TwitterUserSerializer(BaseModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False)
    user_id_str = serializers.SerializerMethodField()

    class Meta:
        model = TwitterUser
        fields = ('tw_twitter_user_id', 'name', 'user_id_str')

    def get_user_id_str(self, instance):
        return str(instance.tw_twitter_user_id)