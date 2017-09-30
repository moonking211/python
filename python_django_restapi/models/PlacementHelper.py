from django.core.exceptions import ObjectDoesNotExist
from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup
from restapi.registry import REGISTRY


class PlacementHelper(object):

    @staticmethod
    def is_own(campaign_id, ad_group_id):
        is_own = False
        advertiser = None
        try:
            if PlacementHelper.__has_value(campaign_id):
                campaign = Campaign.objects.get(campaign_id=campaign_id)
                advertiser = campaign.advertiser_id

            elif PlacementHelper.__has_value(ad_group_id):
                ad_group = AdGroup.objects.get(ad_group_id=ad_group_id)
                advertiser = ad_group.campaign_id.advertiser_id

            if advertiser is not None:
                is_own = bool(advertiser.agency_id.trading_desk_id.trading_desk_userprofiles.filter(user=REGISTRY['user']))
        except ObjectDoesNotExist:
            pass

        return is_own

    @staticmethod
    def own(queryset):
        own_campaigns = Campaign.objects.filter(advertiser_id__agency_id__trading_desk_id_id__in=REGISTRY['user_trading_desk_ids'])
        return queryset.filter(campaign_id__in=[int(x.pk) for x in own_campaigns])

    @staticmethod
    def __has_value(value):
        return value is not None and value != 0
