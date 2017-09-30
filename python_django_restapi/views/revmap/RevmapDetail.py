from restapi.models.Revmap import Revmap
from restapi.serializers.RevmapSerializer import RevmapSerializer
from restapi.views.base_view.BaseDetail import BaseDetail
from django.shortcuts import get_object_or_404


class RevmapDetail(BaseDetail):
    # Retrieve, update or delete a revmap instance.
#    queryset = Revmap.objects.all()
    serializer_class = RevmapSerializer

    def get_object(self):
        return get_object_or_404(Revmap, ad_group_id=self.kwargs['ad_group_id'])

    @property
    def queryset(self):
        return Revmap.objects.all()
