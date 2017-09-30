from rest_framework import serializers
from restapi.models.Currency import Currency
from restapi.models.choices import STATUS_CHOICES
from restapi.models.Agency import Agency
from restapi.models.TradingDesk import TradingDesk, MANAGE_TRADING_DESK_ID
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.PKRelatedField import PKRelatedField
from restapi.serializers.fields.EmailField import EmailField


class AgencySerializer(BaseModelSerializer):
    trading_desk_id = PKRelatedField(queryset=TradingDesk.objects_raw.all())
    trading_desk = serializers.CharField(read_only=True)
    agency_key = serializers.CharField(read_only=True)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=True)
    created_at = DateTimeField(read_only=True)
    email = EmailField(max_length=255, required=False, allow_blank=True)
    currency = ChoiceCaseInsensitiveField(choices=[(x.currency_code, x.currency_code) for x in Currency.objects.all()],
                                          required=True)
    account_manager = serializers.IntegerField(required=False)
    last_update = DateTimeField(read_only=True)

    # pylint: disable=old-style-class
    class Meta:
        model = Agency
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Agency.objects_raw.all(),
                fields=('trading_desk_id', 'agency')
            )
        ]

    def is_valid(self, *args, **kwargs):
        valid = super(AgencySerializer, self).is_valid(*args, **kwargs)
        trading_desk = self.validated_data.get('trading_desk_id', False)
        account_manager = self.validated_data.get('account_manager', False)
        status = self.validated_data.get('status')
        if trading_desk and trading_desk.pk == MANAGE_TRADING_DESK_ID and not account_manager:
            raise serializers.ValidationError('account_manager field is required.')

        # Manage Agency
        if self.instance and self.instance.pk == 1:
            if self.instance.status != status:
                raise serializers.ValidationError('Forbidden to change status of the Manage agency.')

        return valid
