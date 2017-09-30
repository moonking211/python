from restapi.models.Revmap import Revmap
from restapi.serializers.RevmapSerializer import RevmapSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class RevmapList(BaseListCreate):
    # List all revmap, or create a new ad group.
#    queryset = Revmap.objects.all()
    serializer_class = RevmapSerializer
    list_filter_fields = ('status', 'ad_group',)
    contains_filter_fields = ('ad_group',)
    query_filter_fields = ('ad_group',)
    order_fields = ('ad_group_id', '-ad_group_id')

    @property
    def queryset(self):
        return Revmap.objects.all()
