from rest_framework import serializers
from restapi.models.choices import STATUS_CHOICES
from restapi.models.Currency import Currency
from restapi.models.TradingDesk import TradingDesk
from restapi.serializers.BaseModelSerializer import BaseModelSerializer
from restapi.serializers.fields.ChoiceCaseInsensitiveField import ChoiceCaseInsensitiveField
from restapi.serializers.fields.DateTimeField import DateTimeField
from restapi.serializers.fields.EmailField import EmailField


class TradingDeskSerializer(BaseModelSerializer):
    trading_desk_key = serializers.CharField(read_only=True)
    account_manager = serializers.IntegerField(required=True)
    status = ChoiceCaseInsensitiveField(choices=STATUS_CHOICES, required=True)
    email = EmailField(max_length=255, required=False, allow_blank=True)
    created_at = DateTimeField(read_only=True)
    last_update = DateTimeField(read_only=True)
    currency = ChoiceCaseInsensitiveField(choices=[(x.currency_code, x.currency_code) for x in Currency.objects.all()],
                                          required=True)

    # pylint: disable=old-style-class
    class Meta:
        model = TradingDesk
