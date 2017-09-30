from rest_framework import serializers
from restapi.models.Event import Event
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.validators.BaseValidator import BaseValidator
from restapi.serializers.fields.DefaultArgsTextField import DefaultArgsTextField


class EventSerializer(BaseModelSerializer):
    campaign = serializers.CharField(read_only=True)
    advertiser_id = serializers.IntegerField(read_only=True)
    advertiser = serializers.CharField(read_only=True)
    agency_id = serializers.IntegerField(read_only=True)
    agency = serializers.CharField(read_only=True)
    trading_desk_id = serializers.IntegerField(read_only=True)
    trading_desk = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)
    default_args = DefaultArgsTextField(required=False, validators=[BaseValidator.JSONValidator], allow_blank=True)
    max_frequency = serializers.IntegerField(required=False, allow_null=True)
    frequency_interval = serializers.IntegerField(required=False, default=None, allow_null=True)
    accept_unencrypted = serializers.BooleanField(required=False)
    encrypted_event_id = serializers.CharField(required=False, read_only=True)
    last_update = DateTimeField(read_only=True)

    # pylint: disable=old-style-class
    class Meta:
        model = Event
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Event.objects_raw.all(),
                fields=('campaign_id', 'event')
            )
        ]
