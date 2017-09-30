from restapi.models.AdGroup import AdGroup
from restapi.serializers.AdGroupSerializer import AdGroupSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class AdGroupDetail(BaseDetail):
    # Retrieve, update or delete a ad group instance.
#    queryset = AdGroup.objects.all()
    serializer_class = AdGroupSerializer

    @property
    def queryset(self):
        return AdGroup.objects.all()
