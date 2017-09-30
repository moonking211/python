from restapi.models.Agency import Agency
from restapi.serializers.AgencySerializer import AgencySerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class AgencyList(BaseListCreate):
    serializer_class = AgencySerializer
    list_filter_fields = ('status', 'agency_id', 'trading_desk_id')
    contains_filter_fields = ('agency',)
    contains_filter_include_pk = True
    order_fields = ('agency', '-agency',
                    'agency_id', '-agency_id')
    query_filter_fields = ('agency', 'agency_id')

    @property
    def queryset(self):
        return Agency.objects.all()
