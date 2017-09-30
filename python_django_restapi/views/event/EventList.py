from collections import OrderedDict

from restapi.models.Event import Event
from restapi.serializers.EventSerializer import EventSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class EventList(BaseListCreate):
    # List all events, or create a new event.
#    queryset = Event.objects.all()
    serializer_class = EventSerializer
    contains_filter_fields = ('event',)
    query_filter_fields = ('event', 'description')
    order_fields = ('event', '-event')
    list_filter_fields = ('status', 'event_id', 'base_event_id', 'deleted', 'campaign_id')

    def get_queryset(self):
        queryset = super(EventList, self).get_queryset()
        # reorder result as a tree
        result = []
        events = OrderedDict()
        for event in queryset.order_by('base_event_id', 'event_id'):
            events[event.event_id] = event
        def get_event_by_id(event_id):
            event = events[event_id]
            del events[event_id]
            result.append(event)
            related_event_ids = [event.event_id for event in events.values() if event.base_event_id == event_id]
            for event_id in related_event_ids:
                get_event_by_id(event_id)
        while events:
            event_id = events.keys()[0]
            get_event_by_id(event_id)
        return result

    @property
    def queryset(self):
        return Event.objects.all()
