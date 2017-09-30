from django.http import QueryDict

from rest_framework import generics

from restapi.models.Advertiser import Advertiser
from restapi.serializers.AdvertiserSerializer import RawAdvertiserSerializer, AdvertiserSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class AdvertiserList(BaseListCreate):
    # List all advertisers, or create a new advertiser.
    serializer_class = AdvertiserSerializer
    list_filter_fields = ('status', 'advertiser_id', 'agency_id', 'agency_id__trading_desk_id')
    contains_filter_fields = ('advertiser',)
    contains_filter_include_pk = True
    query_filter_fields = ('advertiser', 'advertiser_id')
    order_fields = (
        'advertiser', '-advertiser',
        'advertiser_id', '-advertiser_id',
        'twitter_margin', '-twitter_margin'
    )

    @property
    def queryset(self):
        return Advertiser.objects.all().prefetch_related('agency_id')

    def get_queryset(self):
        params = self.request.query_params
        trading_desk_id = params.get('trading_desk_id')

        if trading_desk_id is not None:
            query_params = QueryDict('', mutable=True)
            query_params.update(params)
            query_params['agency_id__trading_desk_id'] = trading_desk_id
            self.query_params = query_params
        return super(AdvertiserList, self).get_queryset()


class RawAdvertiserList(generics.ListAPIView):
    serializer_class = RawAdvertiserSerializer
    filter_fields = ('advertiser_key',)

    def get_queryset(self):
        advertiser_key = self.request.query_params.get('advertiser_key')
        return Advertiser.objects_raw.filter(advertiser_key=advertiser_key)
