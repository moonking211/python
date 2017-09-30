from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.serializers.twitter.TwitterCampaignSerializer import TwitterCampaignSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate
from django.http import QueryDict


class TwitterCampaignList(BaseListCreate):
    serializer_class = TwitterCampaignSerializer
    contains_filter_include_pk = True
    query_filter_fields = ('name', 'tw_campaign_id')
    order_fields = ('name', '-name',
                    'tw_campaign_id', '-tw_campaign_id')
    list_filter_fields = \
        ('status', 'campaign_id__advertiser_id', 'campaign_id__advertiser_id__agency_id__trading_desk_id',
         'campaign_id__advertiser_id__agency_id', 'campaign_id', 'tw_account_id', 'tw_campaign_id')

    @property
    def queryset(self):
        return TwitterCampaign.objects.all()

    def get_queryset(self):
        params = self.request.query_params
        trading_desk_id = params.get('trading_desk_id')
        agency_id = params.get('agency_id')
        advertiser_id = params.get('advertiser_id')
        query_params = QueryDict('', mutable=True)
        query_params.update(params)

        if advertiser_id and int(advertiser_id):
            query_params['campaign_id__advertiser_id'] = advertiser_id

        if trading_desk_id and int(trading_desk_id):
            query_params['campaign_id__advertiser_id__agency_id__trading_desk_id'] = trading_desk_id

        if agency_id and int(agency_id):
            query_params['campaign_id__advertiser_id__agency_id'] = agency_id

        self.query_params = query_params

        query_set = super(TwitterCampaignList, self).get_queryset()
        tw_campaign_ids = params.get('tw_campaign_ids')

        if tw_campaign_ids:
            query_set = query_set.filter(tw_campaign_id__in=tw_campaign_ids.split(','))

        return query_set