from restapi.models.Agency import Agency
from restapi.serializers.AgencySerializer import AgencySerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class AgencyDetail(BaseDetail):
    # Retrieve, update or delete a advertiser instance.
    serializer_class = AgencySerializer

    @property
    def queryset(self):
        return Agency.objects.all()
