import json
from django.db.models import Q
from restapi.models.Ad import Ad, AUDIT_TYPE_AD
from restapi.models.AdGroup import AdGroup, AUDIT_TYPE_AD_GROUP
from restapi.models.Advertiser import Advertiser, AUDIT_TYPE_ADVERTISER
from restapi.models.Agency import Agency, AUDIT_TYPE_AGENCY
from restapi.models.AuditLog import AuditLog
from restapi.models.BidderBlacklist import AUDIT_TYPE_BIDDER_BLACK_LIST, BidderBlacklistIds
from restapi.models.BidderWhitelist import AUDIT_TYPE_BIDDER_WHITE_LIST, BidderWhitelistIds
from restapi.models.Campaign import Campaign, AUDIT_TYPE_CAMPAIGN
from restapi.models.CustomHint import AUDIT_TYPE_CUSTOM_HINT, CustomHintIds
from restapi.models.DiscretePricing import AUDIT_TYPE_DISCRETE_PRICING, DiscretePricingIds
from restapi.models.Event import Event, AUDIT_TYPE_EVENT
from restapi.models.TradingDesk import TradingDesk, AUDIT_TYPE_TRADING_DESK
from restapi.models.twitter.TwitterCampaign import TwitterCampaign, AUDIT_TYPE_TW_CAMPAIGN
from restapi.models.twitter.TwitterLineItem import TwitterLineItem, AUDIT_TYPE_TW_LINE_ITEM
from restapi.serializers.AuditLogSerializer import AuditLogSerializer
from restapi.views.base_view.BaseListCreate import BaseListCreate


class AuditLogList(BaseListCreate):
    # List all audit log, or create a new audit log.
    # queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    list_filter_fields = ('audit_log_id', 'user_id', 'audit_type', 'audit_action', 'item_id')
    contains_filter_fields = ('audit_log_id',)
    query_filter_fields = ('ad_group',)
    order_fields = ('audit_log_id', '-user_id')
    comparison_filter_fields = ('created',)

    @property
    def queryset(self):
        return AuditLog.objects.all()

    def get_queryset(self):
        params = self.request.query_params
        user = params.get('user', None)
        queryset = super(AuditLogList, self).get_queryset()
        audit_type = params.get('audit_type', None)
        audit_type_num = int(audit_type) if audit_type else None
        name = params.get('name', None)

        if name:
            queryset = self._filter_by_name(queryset, name)

        if params.get('name', None) \
                and audit_type_num not in [AUDIT_TYPE_BIDDER_BLACK_LIST,
                                           AUDIT_TYPE_BIDDER_WHITE_LIST,
                                           AUDIT_TYPE_CUSTOM_HINT,
                                           AUDIT_TYPE_DISCRETE_PRICING,
                                           AUDIT_TYPE_EVENT,
                                           AUDIT_TYPE_AD] \
                and json.loads(params.get('get_child', '{}')):
            queryset = self._get_entity_children(audit_type_num,
                                                 int(params.get('name', None)),
                                                 self.queryset)

            # Sort by parent, if needed
            # queryset = queryset.extra(select={'is_parent': "item_id=%s and audit_type=%s"},
            #                           select_params=((int(params.get('item_id', None)),
            #                                           audit_type_num))).order_by('-is_parent',
            #                                                                      '-created')

            if params.get('audit_action', None):
                queryset = queryset.filter(audit_action=params.get('audit_action', None))

            if params.get('created__gte', None) and params.get('created__lte', None):
                queryset = queryset.filter(created__gte=params.get('created__gte', None),
                                           created__lte=params.get('created__lte', None))

        # All Users
        if user in ['0', '1']:
            pass
        # All Except System User
        elif user is None:
            queryset = queryset.filter(user_id__gt=1)
        else:
            queryset = queryset.filter(user_id=int(user))

        return queryset

    def _filter_by_name(self, queryset, name):
        from restapi.models.Io import Io, AUDIT_TYPE_IO
        trading_desks = TradingDesk.objects.filter(trading_desk__icontains=name).values_list('trading_desk_id', flat=True)
        agencies = Agency.objects.filter(agency__icontains=name).values_list('agency_id', flat=True)
        advertisers = Advertiser.objects.filter(advertiser__icontains=name).values_list('advertiser_id', flat=True)
        campaigns = Campaign.objects.filter(campaign__icontains=name).values_list('campaign_id', flat=True)
        events = Event.objects.filter(event__icontains=name).values_list('event_id', flat=True)
        ad_groups = AdGroup.objects.filter(ad_group__icontains=name).values_list('ad_group_id', flat=True)
        ads = Ad.objects.filter(ad__icontains=name).values_list('ad_id', flat=True)
        black_lists = BidderBlacklistIds.objects.filter(placement_id__icontains=name).values_list('id', flat=True)
        white_lists = BidderWhitelistIds.objects.filter(placement_id__icontains=name).values_list('id', flat=True)
        custom_hints = CustomHintIds.objects.filter(placement_id__icontains=name).values_list('id', flat=True)
        discrete_pricings = DiscretePricingIds.objects.filter(placement_id__icontains=name).values_list('id', flat=True)
        tw_campaigns = TwitterCampaign.objects.filter(name__icontains=name).values_list('tw_campaign_id', flat=True)
        tw_line_items = TwitterLineItem.objects.filter(name__icontains=name).values_list('tw_line_item_id', flat=True)
        try:
            ios = Io.objects.filter(io_id=int(name)).values_list('io_id', flat=True)
        except ValueError:
            ios = []

        try:
            item_id = int(name)
        except ValueError:
            item_id = None

        return queryset.filter((Q(item_id=item_id))
                             | (Q(audit_type=AUDIT_TYPE_TRADING_DESK, item_id__in=trading_desks))
                             | (Q(audit_type=AUDIT_TYPE_AGENCY, item_id__in=agencies))
                             | (Q(audit_type=AUDIT_TYPE_ADVERTISER, item_id__in=advertisers))
                             | (Q(audit_type=AUDIT_TYPE_CAMPAIGN, item_id__in=campaigns))
                             | (Q(audit_type=AUDIT_TYPE_EVENT, item_id__in=events))
                             | (Q(audit_type=AUDIT_TYPE_AD_GROUP, item_id__in=ad_groups))
                             | (Q(audit_type=AUDIT_TYPE_AD, item_id__in=ads))
                             | (Q(audit_type=AUDIT_TYPE_BIDDER_BLACK_LIST, item_id__in=black_lists))
                             | (Q(audit_type=AUDIT_TYPE_BIDDER_WHITE_LIST, item_id__in=white_lists))
                             | (Q(audit_type=AUDIT_TYPE_CUSTOM_HINT, item_id__in=custom_hints))
                             | (Q(audit_type=AUDIT_TYPE_DISCRETE_PRICING, item_id__in=discrete_pricings))
                             | (Q(audit_type=AUDIT_TYPE_TW_CAMPAIGN, item_id__in=tw_campaigns))
                             | (Q(audit_type=AUDIT_TYPE_TW_LINE_ITEM, item_id__in=tw_line_items))
                             | (Q(audit_type=AUDIT_TYPE_IO, item_id__in=ios)))

    def _get_entity_children(self, audit_type_number, item_id, queryset):

        """
        This method creates filtered queryset with all childrens of requested entity
        :param: audit type number, id of requested entity, initial queryset
        :return: filtered queryset
        """
        if audit_type_number == AUDIT_TYPE_TRADING_DESK:
            list_of_agency_ids = Agency.objects.filter(trading_desk_id=item_id) \
                .values_list('agency_id', flat=True)
            list_of_advertiser_ids = Advertiser.objects.filter(agency_id__in=list_of_agency_ids) \
                .values_list('advertiser_id', flat=True)
            list_of_campaign_ids = Campaign.objects.filter(advertiser_id__in=list_of_advertiser_ids) \
                .values_list('campaign_id', flat=True)
            list_of_events_ids = Event.objects.filter(campaign_id__in=list_of_campaign_ids) \
                .values_list('event_id', flat=True)
            list_of_ad_group_ids = AdGroup.objects.filter(campaign_id__in=list_of_campaign_ids) \
                .values_list('ad_group_id', flat=True)
            list_of_ad_ids = Ad.objects.filter(ad_group_id__in=list_of_ad_group_ids) \
                .values_list('ad_id', flat=True)
            return queryset.filter((Q(audit_type=audit_type_number, item_id=item_id))
                                   | (Q(audit_type=AUDIT_TYPE_AGENCY, item_id__in=list_of_agency_ids))
                                   | (Q(audit_type=AUDIT_TYPE_ADVERTISER, item_id__in=list_of_advertiser_ids))
                                   | (Q(audit_type=AUDIT_TYPE_CAMPAIGN, item_id__in=list_of_campaign_ids))
                                   | (Q(audit_type=AUDIT_TYPE_EVENT, item_id__in=list_of_events_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD_GROUP, item_id__in=list_of_ad_group_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD, item_id__in=list_of_ad_ids)))

        if audit_type_number == AUDIT_TYPE_AGENCY:
            list_of_advertiser_ids = Advertiser.objects.filter(agency_id=item_id) \
                .values_list('advertiser_id', flat=True)
            list_of_campaign_ids = Campaign.objects.filter(advertiser_id__in=list_of_advertiser_ids) \
                .values_list('campaign_id', flat=True)
            list_of_events_ids = Event.objects.filter(campaign_id__in=list_of_campaign_ids) \
                .values_list('event_id', flat=True)
            list_of_ad_group_ids = AdGroup.objects.filter(campaign_id__in=list_of_campaign_ids) \
                .values_list('ad_group_id', flat=True)
            list_of_ad_ids = Ad.objects.filter(ad_group_id__in=list_of_ad_group_ids) \
                .values_list('ad_id', flat=True)
            return queryset.filter((Q(audit_type=audit_type_number, item_id=item_id))
                                   | (Q(audit_type=AUDIT_TYPE_ADVERTISER, item_id__in=list_of_advertiser_ids))
                                   | (Q(audit_type=AUDIT_TYPE_CAMPAIGN, item_id__in=list_of_campaign_ids))
                                   | (Q(audit_type=AUDIT_TYPE_EVENT, item_id__in=list_of_events_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD_GROUP, item_id__in=list_of_ad_group_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD, item_id__in=list_of_ad_ids)))

        if audit_type_number == AUDIT_TYPE_ADVERTISER:
            list_of_campaign_ids = Campaign.objects.filter(advertiser_id=item_id) \
                .values_list('campaign_id', flat=True)
            list_of_events_ids = Event.objects.filter(campaign_id__in=list_of_campaign_ids) \
                .values_list('event_id', flat=True)
            list_of_ad_group_ids = AdGroup.objects.filter(campaign_id__in=list_of_campaign_ids) \
                .values_list('ad_group_id', flat=True)
            list_of_ad_ids = Ad.objects.filter(ad_group_id__in=list_of_ad_group_ids) \
                .values_list('ad_id', flat=True)
            return queryset.filter((Q(audit_type=audit_type_number, item_id=item_id))
                                   | (Q(audit_type=AUDIT_TYPE_CAMPAIGN, item_id__in=list_of_campaign_ids))
                                   | (Q(audit_type=AUDIT_TYPE_EVENT, item_id__in=list_of_events_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD_GROUP, item_id__in=list_of_ad_group_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD, item_id__in=list_of_ad_ids)))

        if audit_type_number == AUDIT_TYPE_CAMPAIGN:
            list_of_events_ids = Event.objects.filter(campaign_id=item_id) \
                .values_list('event_id', flat=True)
            list_of_ad_group_ids = AdGroup.objects.filter(campaign_id=item_id) \
                .values_list('ad_group_id', flat=True)
            list_of_ad_ids = Ad.objects.filter(ad_group_id__in=list_of_ad_group_ids) \
                .values_list('ad_id', flat=True)
            list_of_black_list_ids = BidderBlacklistIds.objects.filter(campaign_id=item_id) \
                .values_list('id', flat=True)
            list_of_white_list_ids = BidderWhitelistIds.objects.filter(campaign_id=item_id) \
                .values_list('id', flat=True)
            list_of_custom_hint_ids = CustomHintIds.objects.filter(campaign_id=item_id) \
                .values_list('id', flat=True)
            list_of_discrete_pricing_ids = DiscretePricingIds.objects.filter(campaign_id=item_id) \
                .values_list('id', flat=True)
            return queryset.filter((Q(audit_type=audit_type_number, item_id=item_id))
                                   | (Q(audit_type=AUDIT_TYPE_EVENT, item_id__in=list_of_events_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD_GROUP, item_id__in=list_of_ad_group_ids))
                                   | (Q(audit_type=AUDIT_TYPE_AD, item_id__in=list_of_ad_ids))
                                   | (Q(audit_type=AUDIT_TYPE_BIDDER_BLACK_LIST, item_id__in=list_of_black_list_ids))
                                   | (Q(audit_type=AUDIT_TYPE_BIDDER_WHITE_LIST, item_id__in=list_of_white_list_ids))
                                   | (Q(audit_type=AUDIT_TYPE_CUSTOM_HINT, item_id__in=list_of_custom_hint_ids))
                                   | (Q(audit_type=AUDIT_TYPE_DISCRETE_PRICING, item_id__in=list_of_discrete_pricing_ids)))

        if audit_type_number == AUDIT_TYPE_AD_GROUP:
            list_of_black_list_ids = BidderBlacklistIds.objects.filter(ad_group_id=item_id) \
                .values_list('id', flat=True)
            list_of_white_list_ids = BidderWhitelistIds.objects.filter(ad_group_id=item_id) \
                .values_list('id', flat=True)
            list_of_custom_hint_ids = CustomHintIds.objects.filter(ad_group_id=item_id) \
                .values_list('id', flat=True)
            list_of_discrete_pricing_ids = DiscretePricingIds.objects.filter(ad_group_id=item_id) \
                .values_list('id', flat=True)
            list_of_ad_ids = Ad.objects.filter(ad_group_id=item_id).values_list('ad_id', flat=True)
            return queryset.filter((Q(audit_type=audit_type_number, item_id=item_id))
                                   | (Q(audit_type=AUDIT_TYPE_AD, item_id__in=list_of_ad_ids))
                                   | (Q(audit_type=AUDIT_TYPE_BIDDER_BLACK_LIST, item_id__in=list_of_black_list_ids))
                                   | (Q(audit_type=AUDIT_TYPE_BIDDER_WHITE_LIST, item_id__in=list_of_white_list_ids))
                                   | (Q(audit_type=AUDIT_TYPE_CUSTOM_HINT, item_id__in=list_of_custom_hint_ids))
                                   | (Q(audit_type=AUDIT_TYPE_DISCRETE_PRICING, item_id__in=list_of_discrete_pricing_ids)))

        return queryset
