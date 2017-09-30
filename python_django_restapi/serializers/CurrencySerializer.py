from rest_framework import serializers
from restapi.serializers.BaseModelSerializer import BaseModelSerializer

from restapi.models.Currency import Currency


class CurrencySerializer(BaseModelSerializer):

    # pylint: disable=old-style-class
    class Meta:
        model = Currency
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Currency.objects_raw.all(),
                fields=('currency_name', 'currency_code')
            )
        ]
