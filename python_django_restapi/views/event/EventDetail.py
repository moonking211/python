from restapi.models.Event import Event
from restapi.serializers.EventSerializer import EventSerializer
from restapi.views.base_view.BaseDetail import BaseDetail


class EventDetail(BaseDetail):
    # Retrieve, update or delete a ad instance.
#    queryset = Event.objects.all()
    serializer_class = EventSerializer

    @property
    def queryset(self):
        return Event.objects.all()
