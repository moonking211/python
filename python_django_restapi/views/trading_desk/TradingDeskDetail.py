from restapi.models.TradingDesk import TradingDesk
from restapi.serializers.TradingDeskSerializer import TradingDeskSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class TradingDeskDetail(BaseDetail):
    # Retrieve, update or delete a trading_desk instance.
    serializer_class = TradingDeskSerializer

    @property
    def queryset(self):
        return TradingDesk.objects.all()
