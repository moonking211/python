from restapi.models.TradingDesk import TradingDesk
from restapi.serializers.TradingDeskSerializer import TradingDeskSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class TradingDeskList(BaseListCreate):
    serializer_class = TradingDeskSerializer
    list_filter_fields = ('status', 'trading_desk_id')
    contains_filter_fields = ('trading_desk',)
    contains_filter_include_pk = True
    query_filter_fields = ('trading_desk', 'trading_desk_id')
    order_fields = ('trading_desk', '-trading_desk', 'trading_desk_id', '-trading_desk_id')

    @property
    def queryset(self):
        return TradingDesk.objects.all()
