from restapi.models.Source import Source
from restapi.serializers.SourceSerializer import SourceSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class SourceList(BaseListCreate):
    # List all source, or create a new ad group.
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    list_filter_fields = ('status', 'source_id',)
    contains_filter_fields = ('source_id',)
    query_filter_fields = ('source_id',)
    order_fields = ('source_id', '-source_id')
