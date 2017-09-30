from restapi.models.Advertiser import Advertiser
from restapi.serializers.AdvertiserSerializer import AdvertiserSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class AdvertiserDetail(BaseDetail):
    # Retrieve, update or delete a advertiser instance.
    serializer_class = AdvertiserSerializer

    @property
    def queryset(self):
        return Advertiser.objects.all()
