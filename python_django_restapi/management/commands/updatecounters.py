from copy import copy
import datetime
import logging

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db.models import Count
from restapi.models.managers import BaseManager
from restapi.models.choices import STATUS_ENABLED, AD_STATUS_DISAPPROVED, A9_STATUS_PENDING, A9_STATUS_FAILED

CACHE_TIME = 1200

logger = logging.getLogger('management-command')


class Command(BaseCommand):
    help = 'Updates counters in REDIS'

    def handle(self, *args, **options):
        utcnow = datetime.datetime.utcnow()

        def filter_by_authorized_user(self, queryset):
            return queryset

        BaseManager.filter_by_authorized_user = filter_by_authorized_user

        from restapi.models.Ad import Ad
        from restapi.models.AdGroup import AdGroup
        from restapi.models.BidderBlacklist import BidderBlacklistIds
        from restapi.models.BidderWhitelist import BidderWhitelistIds
        from restapi.models.CustomHint import CustomHintIds
        from restapi.models.DiscretePricing import DiscretePricingIds
        from restapi.models.CreativePruning import CreativePruning

        # AdGroup.ads_total
        self._update_counters(model=Ad, key_field='ad_group_id')

        # AdGroup.ads_enabled
        self._update_counters(model=Ad, key_field='ad_group_id', filters={'status': STATUS_ENABLED})

        # AdGroup.ads_disapproved
        self._update_counters(model=Ad, key_field='ad_group_id', filters={'adx_status': AD_STATUS_DISAPPROVED,
                                                                          'status': STATUS_ENABLED})

        # AdGroup.a9_pending
        self._update_counters(model=Ad, key_field='ad_group_id', filters={'a9_status': A9_STATUS_PENDING,
                                                                          'status': STATUS_ENABLED})

        # AdGroup.a9_failed
        self._update_counters(model=Ad, key_field='ad_group_id', filters={'a9_status': A9_STATUS_FAILED,
                                                                          'status': STATUS_ENABLED})

        # AdGroup.black_lists_total
        self._update_counters(model=BidderBlacklistIds, key_field='ad_group_id')

        # AdGroup.white_lists_total
        self._update_counters(model=BidderWhitelistIds, key_field='ad_group_id')

        # AdGroup.custom_hints
        self._update_counters(model=CustomHintIds, key_field='ad_group_id')

        # AdGroup.discrete_pricing
        self._update_counters(model=DiscretePricingIds, key_field='ad_group_id')

        # Campaign.ads_total
        self._update_counters(model=Ad, key_field='ad_group_id__campaign_id')

        # Campaign.ads_enabled
        self._update_counters(model=Ad, key_field='ad_group_id__campaign_id', filters={'status': STATUS_ENABLED})

        # Campaign.ads_disapproved
        self._update_counters(model=Ad, key_field='ad_group_id__campaign_id',
                              filters={'adx_status': AD_STATUS_DISAPPROVED,
                                       'status': STATUS_ENABLED})

        # Campaign.a9_pending
        self._update_counters(model=Ad, key_field='ad_group_id__campaign_id', filters={'a9_status': A9_STATUS_PENDING,
                                                                                       'status': STATUS_ENABLED})

        # Campaign.a9_failed
        self._update_counters(model=Ad, key_field='ad_group_id__campaign_id', filters={'a9_status': A9_STATUS_FAILED,
                                                                                       'status': STATUS_ENABLED})

        # Campaign.ad_groups_total
        self._update_counters(model=AdGroup, key_field='campaign_id')

        # Campaign.ad_groups_enabled
        self._update_counters(model=AdGroup, key_field='campaign_id', filters={'status': STATUS_ENABLED})

        # Campaign.black_lists_total
        self._update_counters(model=BidderBlacklistIds, key_field='campaign_id')

        # Campaign.black_lists_campaign
        self._update_counters(model=BidderBlacklistIds, key_field='campaign_id', filters={'ad_group_id': 0})

        # Campaign.black_lists_ad_group
        self._update_counters(model=BidderBlacklistIds, key_field='campaign_id', filters={'ad_group_id__gt': 0})

        # Campaign.white_lists_total
        self._update_counters(model=BidderWhitelistIds, key_field='campaign_id')

        # Campaign.white_lists_campaign
        self._update_counters(model=BidderWhitelistIds, key_field='campaign_id', filters={'ad_group_id': 0})

        # Campaign.white_lists_ad_group
        self._update_counters(model=BidderWhitelistIds, key_field='campaign_id', filters={'ad_group_id__gt': 0})

        # Campaign.custom_hints_total
        self._update_counters(model=CustomHintIds, key_field='campaign_id')

        # Campaign.custom_hints_campaign
        self._update_counters(model=CustomHintIds, key_field='campaign_id', filters={'ad_group_id': 0})

        # Campaign.custom_hints_ad_group
        self._update_counters(model=CustomHintIds, key_field='campaign_id', filters={'ad_group_id__gt': 0})

        # Campaign.discrete_pricing_total
        self._update_counters(model=DiscretePricingIds, key_field='campaign_id')

        # Campaign.discrete_pricing_campaign
        self._update_counters(model=DiscretePricingIds, key_field='campaign_id', filters={'ad_group_id': 0})

        # Campaign.discrete_pricing_ad_group
        self._update_counters(model=DiscretePricingIds, key_field='campaign_id', filters={'ad_group_id__gt': 0})

        # Campaign.ads_to_delete
        self._update_counters(
            model=CreativePruning,
            key_field='ad_id__ad_group_id__campaign_id',
            filters={'action': 'delete'}
        )

        # Campaign.ads_to_archive
        self._update_counters(
            model=CreativePruning,
            key_field='ad_id__ad_group_id__campaign_id',
            filters={'action': 'pause'}
        )

        # AdGroup.ads_to_delete
        self._update_counters(model=CreativePruning, key_field='ad_id__ad_group_id', filters={'action': 'delete'})

        # AdGroup.ads_to_pause
        self._update_counters(model=CreativePruning, key_field='ad_id__ad_group_id', filters={'action': 'pause'})

        logger.info('Counters update took %.2fs', (datetime.datetime.utcnow() - utcnow).total_seconds())

    def _update_counters(self, model, key_field, filters=None):
        logger.debug('Updating %s counters for key field %s using filters: %r',
                     model.__class__.__name__, key_field, filters)
        filters = filters or {}
        for r in model.objects.values(key_field).filter(**filters).annotate(value=Count(key_field)):
            attrs = copy(filters)
            attrs[key_field] = r[key_field]
            CACHE_KEY = model.objects.getCountCacheKey(**attrs)
            value = r['value']
            cache.set(CACHE_KEY, value, CACHE_TIME)
