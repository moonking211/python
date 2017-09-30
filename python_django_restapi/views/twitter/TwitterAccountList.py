from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.serializers.twitter.TwitterAccountSerializer import TwitterAccountSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from rest_framework import filters, generics
from restapi.models.Advertiser import Advertiser
class TwitterAccountList(BaseListCreate):
    serializer_class = TwitterAccountSerializer
    contains_filter_include_pk = True
    list_filter_fields = ('advertiser_id', )
    query_filter_fields = ('name', 'tw_account_id', 'advertiser_id', )
    order_fields = ('tw_account', '-tw_account',
                    'tw_account_id', '-tw_account_id')
    search_fields = ('name', 'tw_account_id', )
    filter_backends = (filters.SearchFilter, )

    def get_queryset(self):
        tw_account_id = self.request.query_params.get('tw_account_id')
        advertiser_id = self.request.query_params.get('advertiser_id')
        qs = TwitterAccount.objects
        if tw_account_id:
            qs = qs.filter(tw_account_id=tw_account_id)
        if advertiser_id:
            qs = qs.filter(advertiser_id=advertiser_id)
        
        return qs.all()


class RawTwitterAccountList(generics.ListCreateAPIView):
    serializer_class = TwitterAccountSerializer

    def get_queryset(self):
        advertiser_key = self.request.query_params.get('key')
        advertiser = Advertiser.objects_raw.filter(advertiser_key=advertiser_key).first()
        if advertiser:
            return TwitterAccount.objects_raw.filter(advertiser_id=advertiser.pk).all()
        else:
            return None