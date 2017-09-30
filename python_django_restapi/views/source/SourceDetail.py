from restapi.models.Source import Source
from restapi.serializers.SourceSerializer import SourceSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class SourceDetail(BaseDetail):
    # Retrieve, update or delete a ad instance.
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
