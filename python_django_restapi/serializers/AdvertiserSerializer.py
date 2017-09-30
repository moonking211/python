from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES
from restapi.models.Advertiser import Advertiser
from restapi.models.Agency import Agency
from restapi.models.Currency import Currency
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.fields.ZeroDateField import ZeroDateField
from restapi.serializers.fields.EmailField import EmailField


class RawAdvertiserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertiser
        fields = ('advertiser_id',
                  'advertiser',
                  'advertiser_key',
                  )


class AdvertiserSerializer(BaseModelSerializer):
    agency_id = PKRelatedField(queryset=Agency.objects_raw.all())
    agency = serializers.CharField(read_only=True)
    trading_desk_id = serializers.IntegerField(read_only=True)
    trading_desk = serializers.CharField(read_only=True)
    advertiser_key = serializers.CharField(read_only=True)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=False)
    flight_start_date = ZeroDateField(required=False, allow_null=True)
    email = EmailField(max_length=255, required=False, allow_blank=True)
    contact = serializers.CharField(max_length=100, required=True)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)
    currency = ChoiceCaseInsensitiveField(choices=[(x.currency_code, x.currency_code) for x in Currency.objects.all()], allow_blank=True)

    required_in_schema = ['currency']

    # pylint: disable=old-style-class
    class Meta:
        model = Advertiser
        fields = ('advertiser_id',
                  'advertiser',
                  'advertiser_key',
                  'agency_id',
                  'agency',
                  'trading_desk_id',
                  'trading_desk',
                  'account_manager',
                  'contact',
                  'address1',
                  'address2',
                  'city',
                  'state_prov',
                  'country',
                  'phone',
                  'email',
                  'notes',
                  'zip',
                  'sampling_rate',
                  'throttling_rate',
                  'flight_start_date',
                  'created_at',
                  'last_update',
                  'currency',
                  'twitter_margin',
                  'discount',
                  'status')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Advertiser.objects_raw.all(),
                fields=('agency_id', 'advertiser')
            )
        ]

    def is_valid(self, *args, **kwargs):
        errors = {}
        if not self.initial_data.get('agency_id', None):
            raise serializers.ValidationError({'agency_id': 'agency_id field is required.'})

        currency = self.initial_data.get('currency', None)
        twitter_margin = self.initial_data.get('twitter_margin', None)

        if self.instance and self.instance.currency and not currency:
            raise serializers.ValidationError({'currency': 'agency_id field is required.'})

        if int(str(twitter_margin)[::-1].find('.')) > 2:
            raise serializers.ValidationError({'Twitter Service Fee': 'Incorrect value, must be integer.'})

        if twitter_margin < 0:
            raise serializers.ValidationError({'Twitter Service Fee': 'Twitter Service Fee can not be lower than 0'})
        
        return super(AdvertiserSerializer, self).is_valid(*args, **kwargs)
