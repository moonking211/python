from restapi.models.Currency import Currency
from restapi.serializers.CurrencySerializer import CurrencySerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class CurrencyDetail(BaseDetail):
    serializer_class = CurrencySerializer

    @property
    def queryset(self):
        return Currency.objects.all()
