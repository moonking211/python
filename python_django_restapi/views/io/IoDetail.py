from restapi.models.Io import Io
from restapi.serializers.IoSerializer import IoSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class IoDetail(BaseDetail):
    # Retrieve, update or delete a io instance.
    serializer_class = IoSerializer

    @property
    def queryset(self):
        return Io.objects.all()
