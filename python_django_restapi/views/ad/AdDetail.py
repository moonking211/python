from restapi.models.Ad import Ad
from restapi.serializers.AdSerializer import AdSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class AdDetail(BaseDetail):
    # Retrieve, update or delete a ad instance.
#    queryset = Ad.objects.all()
    serializer_class = AdSerializer

    @property
    def queryset(self):
        return Ad.objects.all()
