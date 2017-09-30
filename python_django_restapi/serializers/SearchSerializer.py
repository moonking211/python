from rest_framework import serializers

from restapi.serializers.BaseReadonlySerializer import BaseReadonlySerializer
from restapi.serializers.fields.DateTimeField import DateTimeField


class SearchSerializer(BaseReadonlySerializer):
    level = serializers.CharField(required=False)
    advertiser_id = serializers.IntegerField(required=False)
    advertiser = serializers.CharField(required=False)
    campaign_id = serializers.IntegerField(required=False)
    campaign = serializers.CharField(required=False)
    event_id = serializers.IntegerField(required=False)
    event = serializers.CharField(required=False)
    ad_group_id = serializers.IntegerField(required=False)
    ad_group = serializers.CharField(required=False)
    ad_id = serializers.IntegerField(required=False)
    agency = serializers.CharField(required=False)
    agency_id = serializers.IntegerField(required=False)
    trading_desk_id = serializers.IntegerField(required=False)
    # pylint: disable=invalid-name
    ad = serializers.CharField(required=False)
    last_update = DateTimeField(read_only=True)
