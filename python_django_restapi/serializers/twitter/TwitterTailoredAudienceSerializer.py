from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES, TW_PRODUCT_TYPES, TW_PLACEMENTS, TW_OBJECTIVES, TW_BID_TYPES, TW_BID_UNITS, TW_OPTIMIZATIONS, TW_CHARGE_BYS
from restapi.models.fields import ZeroDateTimeField
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterTailoredAudience import TwitterTailoredAudience
from restapi.serializers.validators.BaseValidator import BaseValidator
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.PKRelatedField import PKRelatedField


class TwitterTailoredAudienceSerializer(serializers.ModelSerializer):
    tw_account_id = PKRelatedField(queryset=TwitterAccount.objects_raw.all())
    name = serializers.CharField(required=True, allow_blank=False)
    audience_size = serializers.CharField(required=False, allow_blank=False)
    targetable_types = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    audience_type = serializers.CharField(required=False, allow_blank=False)
    targetable =  serializers.NullBooleanField()
    list_type = serializers.CharField(required=False, allow_blank=False)
    reasons_not_targetable = serializers.CharField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    partner_source = serializers.CharField(required=False, allow_blank=False)
    is_owner = serializers.NullBooleanField()
    permission_level = serializers.CharField(required=False, allow_blank=False)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)


    class Meta:
        model = TwitterTailoredAudience
        fields = ('tw_targeting_id',
                  'tw_account_id',
                  'name',
                  'audience_size',
                  'targetable_types',
                  'audience_type',
                  'targetable',
                  'list_type',
                  'reasons_not_targetable',
                  'partner_source',
                  'is_owner',
                  'permission_level',
                  'status',
                  'created_at',
                  'last_update')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=TwitterTailoredAudience.objects_raw.all(),
                fields=('tw_targeting_id',)
            )
        ]