# encoding: utf-8
"""This module defines Campaign model."""

from __future__ import unicode_literals

from django.db import models

from restapi import core
from restapi.models.base import BaseModel
from restapi.models.base import BasePausedAtModelMixin
from restapi.models.Advertiser import Advertiser
from restapi.models.TrackingProvider import TrackingProvider

from restapi.models.choices import BUDGET_TYPES_CHOICES, AD_STATUS_DISAPPROVED
from restapi.models.choices import STATUS_CHOICES, STATUS_ENABLED
from restapi.models.choices import IAB_CATEGORIES
from restapi.models.choices import MANAGE_CATEGORIES
from restapi.models.choices import OTHER_IAB_CATEGORIES
from restapi.models.choices import A9_STATUS_PENDING, A9_STATUS_FAILED

from restapi.models.fields import OrderedJSONField
from restapi.models.fields import DateTimeField
from restapi.models.fields import ZeroDateTimeField
from restapi.models.fields import cmp_asterisk_last

from restapi.models.managers import BaseManager

from restapi.registry import REGISTRY

import restapi.audit_logger as audit
import restapi.http_caching as http_caching

AUDIT_TYPE_CAMPAIGN = 3

OWN_KEY__FIELD = (
    ('user_trading_desk_ids', 'advertiser_id__agency_id__trading_desk_id'),
    ('user_agency_ids', 'advertiser_id__agency_id'),
    ('user_advertiser_ids', 'advertiser_id')
)


class CampaignManager(BaseManager):
    """Campaign model manager."""

    def own(self, queryset=None):
        """Returns queryset that filters campaigns that belongs to the current user."""
        return super(CampaignManager, self).own(queryset).filter(**core.own_filter_kwargs(REGISTRY, OWN_KEY__FIELD))


class Campaign(BasePausedAtModelMixin, BaseModel):
    campaign_id = models.AutoField(primary_key=True)
    advertiser_id = models.ForeignKey(Advertiser, db_column='advertiser_id')
    campaign = models.CharField(max_length=255)
    notes = models.TextField(blank=True)
    sampling_rate = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    throttling_rate = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    domain = models.CharField(max_length=255)
    redirect_url = models.CharField(max_length=1024, blank=True)
    destination_url = models.CharField(max_length=511)
    viewthrough_url = models.CharField(max_length=1024, blank=True, default='')
    tracking_provider_id = models.ForeignKey(TrackingProvider, db_column='tracking_provider_id', null=True)
    inflator_text = models.CharField(max_length=1024, blank=True)
    frequency_map = OrderedJSONField(blank=True, default='', cmp=cmp_asterisk_last, default_json=str)
    priority = models.IntegerField(blank=True, default=0)
    daily_budget_type = models.CharField(max_length=10,
                                         blank=True,
                                         choices=BUDGET_TYPES_CHOICES,
                                         default=BUDGET_TYPES_CHOICES[0][0])
    daily_budget_value = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    daily_spend = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_CHOICES[1][0])
    distribution_app_sha1_mac = models.BooleanField(default=False, blank=True)
    distribution_app_sha1_udid = models.BooleanField(default=False, blank=True)
    distribution_app_sha1_android_id = models.BooleanField(default=False, blank=True)  # pylint: disable=invalid-name
    distribution_app_ifa = models.BooleanField(default=False, blank=True)
    distribution_app_md5_ifa = models.BooleanField(default=False, blank=True)
    distribution_app_xid = models.BooleanField(default=False, blank=True)
    distribution_web = models.BooleanField(default=False, blank=True)
    flight_start_date = ZeroDateTimeField(default=None, null=True, blank=True)
    flight_end_date = ZeroDateTimeField(default=None, null=True, blank=True)
    flight_budget_type = models.CharField(max_length=10,
                                          blank=True,
                                          choices=BUDGET_TYPES_CHOICES,
                                          default=BUDGET_TYPES_CHOICES[0][0])
    flight_budget_value = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    attribution_window = models.IntegerField(blank=True, null=True)
    genre = models.IntegerField()
    capped = models.IntegerField(blank=True, default=0)
    hourly_capped = models.IntegerField(blank=True, default=0)
    is_test = models.IntegerField(blank=True, default=0)
    bidder_args = models.CharField(max_length=255, blank=True, default='')
    last_update = DateTimeField(null=True, default=None, auto_now=True)
    paused_at = ZeroDateTimeField(default=None, null=True, blank=True)

    external_id = models.CharField(max_length=100, blank=True, null=True)
    categories = models.TextField(blank=True)
    targeting = models.TextField(blank=True, default='')
    os = models.IntegerField(blank=True, default=1)
    overridden = models.BooleanField(default=False, blank=True)

    ignore_fatigue_segment = models.BooleanField(default=False, blank=True)
    ignore_suppression_segment = models.BooleanField(default=False, blank=True)

    total_cost_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    daily_cost_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    total_loss_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    daily_loss_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    app_install = models.BooleanField(default=False, blank=True)

    source_type = models.IntegerField(max_length=3, default=1)

    actions = ('filter_by_trading_desk', 'targeting_json_read', 'targeting_json_update')

    objects = CampaignManager()
    objects_raw = models.Manager()
    permission_check = True

    def is_own(self):
        """Returns True if campaign entity belongs to the current user."""
        advertiser_ids = REGISTRY.get('user_advertiser_ids')
        if advertiser_ids and self.advertiser_id_id in advertiser_ids:
            return True

        agency_ids = REGISTRY.get('user_agency_ids')
        if agency_ids and Campaign.objects.filter(advertiser_id__agency_id__in=agency_ids,
                                                  campaign_id=self.campaign_id).exists():
            return True

        trading_desk_ids = REGISTRY.get('user_trading_desk_ids')
        if trading_desk_ids and Campaign.objects.filter(advertiser_id__agency_id__trading_desk_id__in=trading_desk_ids,
                                                        campaign_id=self.campaign_id).exists():
            return True

        return False

    def autopopulate_by_ownership(self):
        pass

    search_args = ('campaign_id', 'campaign__icontains')

    @property
    def search_result(self):
        advertiser = self.advertiser_id
        agency = self.advertiser_id.agency_id
        result = {'level': 'campaign',
                  'campaign': self.campaign,
                  'campaign_id': self.campaign_id,
                  'advertiser': advertiser.advertiser,
                  'advertiser_id': advertiser.advertiser_id,
                  'agency': agency.agency,
                  'agency_id': agency.agency_id,
                  'last_update': self.last_update}
        return result

    @property
    def other_iab_classification(self):
        classification = []
        if self.categories is not None:
            for category in self.categories.split(" "):
                if category in dict(OTHER_IAB_CATEGORIES):
                    classification.append(category)
        return classification

    @property
    def manage_classification(self):
        classification = []
        if self.categories is not None:
            for category in self.categories.split(" "):
                if category in dict(MANAGE_CATEGORIES):
                    classification.append(category)
        return classification

    @property
    def iab_classification(self):
        classification = []
        if self.categories is not None:
            for category in self.categories.split(" "):
                if category in dict(IAB_CATEGORIES):
                    classification.append(category)
        return classification

    @property
    def parent_name(self):
        return self.advertiser_id.advertiser

    @property
    def agency_name(self):
        return self.advertiser_id.agency_id.agency

    @property
    def trading_desk_name(self):
        return self.advertiser_id.agency_id.trading_desk_id.trading_desk

    @property
    def advertiser(self):
        return self.advertiser_id.advertiser

    @property
    def agency(self):
        return self.advertiser_id.agency_id.agency

    @property
    def agency_id(self):
        return self.advertiser_id.agency_id.agency_id

    @property
    def _advertiser_id(self):
        return self.advertiser_id.advertiser_id

    @property
    def trading_desk(self):
        return self.advertiser_id.agency_id.trading_desk_id.trading_desk

    @property
    def trading_desk_id(self):
        return self.advertiser_id.agency_id.trading_desk_id.trading_desk_id

    @property
    def ad_groups_enabled(self):
        from restapi.models.AdGroup import AdGroup as model
        return model.objects.getCount(campaign_id=self.pk, status=STATUS_ENABLED)

    @property
    def ad_groups_total(self):
        from restapi.models.AdGroup import AdGroup as model
        return model.objects.getCount(campaign_id=self.pk)

    @property
    def ads_enabled(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id__campaign_id=self.pk, status=STATUS_ENABLED)

    @property
    def ads_disapproved(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id__campaign_id=self.pk,
                                      adx_status=AD_STATUS_DISAPPROVED,
                                      status=STATUS_ENABLED)

    @property
    def a9_pending(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id__campaign_id=self.pk,
                                      a9_status=A9_STATUS_PENDING,
                                      status=STATUS_ENABLED)

    @property
    def a9_failed(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id__campaign_id=self.pk,
                                      a9_status=A9_STATUS_FAILED,
                                      status=STATUS_ENABLED)

    @property
    def ads_total(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id__campaign_id=self.pk)

    @property
    def black_lists_total(self):
        from restapi.models.BidderBlacklist import BidderBlacklistIds as model
        return model.objects.getCount(campaign_id=self.pk)

    @property
    def black_lists_campaign(self):
        from restapi.models.BidderBlacklist import BidderBlacklistIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id=0)

    @property
    def black_lists_ad_group(self):
        from restapi.models.BidderBlacklist import BidderBlacklistIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id__gt=0)

    @property
    def white_lists_total(self):
        from restapi.models.BidderWhitelist import BidderWhitelistIds as model
        return model.objects.getCount(campaign_id=self.pk)

    @property
    def white_lists_campaign(self):
        from restapi.models.BidderWhitelist import BidderWhitelistIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id=0)

    @property
    def white_lists_ad_group(self):
        from restapi.models.BidderWhitelist import BidderWhitelistIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id__gt=0)

    @property
    def custom_hints_total(self):
        from restapi.models.CustomHint import CustomHintIds as model
        return model.objects.getCount(campaign_id=self.pk)

    @property
    def custom_hints_campaign(self):
        from restapi.models.CustomHint import CustomHintIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id=0)

    @property
    def custom_hints_ad_group(self):
        from restapi.models.CustomHint import CustomHintIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id__gt=0)

    @property
    def discrete_pricing_total(self):
        from restapi.models.DiscretePricing import DiscretePricingIds as model
        return model.objects.getCount(campaign_id=self.pk)

    @property
    def discrete_pricing_campaign(self):
        from restapi.models.DiscretePricing import DiscretePricingIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id=0)

    @property
    def discrete_pricing_ad_group(self):
        from restapi.models.DiscretePricing import DiscretePricingIds as model
        return model.objects.getCount(campaign_id=self.pk, ad_group_id__gt=0)

    @property
    def ads_to_pause(self):
        """Returns a number of ads recommended to pause."""
        from restapi.models.CreativePruning import CreativePruning
        return CreativePruning.objects.getCount(ad_id__ad_group_id__campaign_id=self.pk, action='pause')

    @property
    def ads_to_delete(self):
        """Returns a number of ads recommended to delete."""
        from restapi.models.CreativePruning import CreativePruning
        return CreativePruning.objects.getCount(ad_id__ad_group_id__campaign_id=self.pk, action='delete')

    def __unicode__(self):
        return self.campaign

    class Meta:
        managed = True
        unique_together = ('advertiser_id', 'campaign')
        db_table = 'campaign'
        app_label = 'restapi'
        ordering = ('campaign',)


audit.AuditLogger.register(Campaign, audit_type=AUDIT_TYPE_CAMPAIGN, check_delete='physical_delete')
http_caching.HTTPCaching.register(Campaign)
