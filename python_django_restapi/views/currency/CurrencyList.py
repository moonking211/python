from restapi.models.Currency import Currency
from restapi.serializers.CurrencySerializer import CurrencySerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class CurrencyList(BaseListCreate):
    serializer_class = CurrencySerializer
    list_filter_fields = ('currency_id',)
    contains_filter_fields = ('currency_code',)
    contains_filter_include_pk = True
    query_filter_fields = ('currency_id', )
    order_fields = ('currency_id', '-currency_id')

    @property
    def queryset(self):
        return Currency.objects.all()
