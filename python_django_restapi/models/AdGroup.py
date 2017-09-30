# encoding: utf-8
"""This module defines AdGroup model."""

from __future__ import unicode_literals

from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from restapi import core
import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.models.base import BaseModel
from restapi.models.base import BasePausedAtModelMixin
from restapi.models.Campaign import Campaign
from restapi.models.choices import BUDGET_TYPES_CHOICES, AD_STATUS_DISAPPROVED, A9_STATUS_PENDING, A9_STATUS_FAILED
from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, STATUS_ENABLED
from restapi.models.choices import AD_GROUP_TYPE_CHOICES
from restapi.models.fields import OrderedJSONField
from restapi.models.fields import DateTimeField
from restapi.models.fields import ZeroDateTimeField
from restapi.models.fields import cmp_asterisk_last
from restapi.models.managers import BaseManager

from restapi.registry import REGISTRY

AUDIT_TYPE_AD_GROUP = 4

OWN_KEY__FIELD = (
    ('user_trading_desk_ids', 'campaign_id__advertiser_id__agency_id__trading_desk_id'),
    ('user_agency_ids', 'campaign_id__advertiser_id__agency_id'),
    ('user_advertiser_ids', 'campaign_id__advertiser_id')
)


def revmap_field(field):
    def getter(self):
        value = None
        # pylint: disable=protected-access
        if self._revmap is not None and field in self._revmap:
            value = self._revmap[field]
        else:
            try:
                value = getattr(self.revmap, field)
            except ObjectDoesNotExist:
                pass
        return value

    def setter(self, value):
        # pylint: disable=protected-access
        if self._revmap is None:
            # pylint: disable=protected-access
            self._revmap = {}
        # pylint: disable=protected-access
        self._revmap[field] = value
        return value

    return property(getter, setter)


class AdGroupManager(BaseManager):
    """Ad group model manager."""

    def own(self, queryset=None):
        """Returns queryset that filters ad groups that belongs to the current user."""
        return super(AdGroupManager, self).own(queryset).filter(**core.own_filter_kwargs(REGISTRY, OWN_KEY__FIELD))

    def checkCounterKey(self, **kwargs):
        return 'campaign_id' in kwargs


class AdGroup(BasePausedAtModelMixin, BaseModel):
    ad_group_id = models.AutoField(primary_key=True)
    campaign_id = models.ForeignKey(Campaign, db_column='campaign_id')
    ad_group = models.CharField(max_length=255)
    ad_group_type = models.IntegerField(blank=True, choices=AD_GROUP_TYPE_CHOICES, default=AD_GROUP_TYPE_CHOICES[0][0])
    targeting = models.TextField(blank=True, default='', db_column='targeting')
    categories = models.TextField(blank=True)
    domain = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    redirect_url = models.CharField(max_length=1024, blank=True)
    destination_url = models.CharField(max_length=511, blank=True, default='')
    viewthrough_url = models.CharField(max_length=1024, blank=True, default='')
    inflator_text = models.CharField(max_length=1024, blank=True)
    frequency_map = OrderedJSONField(blank=True, default='', cmp=cmp_asterisk_last, default_json=str)
    priority = models.IntegerField(blank=True, default=0)
    daily_budget_type = models.CharField(max_length=10,
                                         blank=True,
                                         choices=BUDGET_TYPES_CHOICES,
                                         default=BUDGET_TYPES_CHOICES[0][0])
    daily_budget_value = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    daily_spend = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    capped = models.BooleanField(default=False, blank=True)
    hourly_capped = models.BooleanField(default=False, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_CHOICES[1][0])
    tag = models.CharField(max_length=255, blank=True, null=True)
    flight_start_date = ZeroDateTimeField(default=None, null=True, blank=True)
    flight_end_date = ZeroDateTimeField(default=None, null=True, blank=True)
    flight_budget_type = models.CharField(max_length=10,
                                          blank=True,
                                          choices=BUDGET_TYPES_CHOICES,
                                          default=BUDGET_TYPES_CHOICES[0][0])
    flight_budget_value = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    sampling_rate = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    throttling_rate = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    max_frequency = models.IntegerField(blank=True, null=True, default=None)
    frequency_interval = models.IntegerField(blank=True, null=True, default=None)
    event_args = models.TextField(blank=True)
    bidder_args = models.TextField(blank=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)
    paused_at = ZeroDateTimeField(default=None, null=True, blank=True)
    overridden = models.BooleanField(default=False, blank=True)

    ignore_fatigue_segment = models.NullBooleanField(default=None, blank=True, null=True)
    ignore_suppression_segment = models.NullBooleanField(default=None, blank=True, null=True)

    distribution_app_sha1_android_id = models.NullBooleanField(default=None, blank=True, null=True)
    distribution_app_ifa = models.NullBooleanField(default=None, blank=True, null=True)
    distribution_web = models.NullBooleanField(default=None, blank=True, null=True)

    total_cost_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    daily_cost_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    total_loss_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    daily_loss_cap = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    revmap_rev_type = revmap_field('rev_type')
    revmap_rev_value = revmap_field('rev_value')
    revmap_opt_type = revmap_field('opt_type')
    revmap_opt_value = revmap_field('opt_value')
    revmap_target_type = revmap_field('target_type')
    revmap_target_value = revmap_field('target_value')

    _revmap = None

    objects = AdGroupManager()
    objects_raw = models.Manager()
    permission_check = True

    actions = ('bulk', 'import', 'export', 'rates', 'limits', 'targeting_json_read', 'targeting_json_update')

    @property
    def campaign(self):
        return self.campaign_id.campaign

    @property
    def advertiser_id(self):
        return self.campaign_id.advertiser_id.advertiser_id

    @property
    def advertiser(self):
        return self.campaign_id.advertiser_id.advertiser

    @property
    def agency(self):
        return self.campaign_id.advertiser_id.agency_id.agency

    @property
    def agency_id(self):
        return self.campaign_id.advertiser_id.agency_id.agency_id

    @property
    def trading_desk(self):
        return self.campaign_id.advertiser_id.agency_id.trading_desk_id.trading_desk

    @property
    def trading_desk_id(self):
        return self.campaign_id.advertiser_id.agency_id.trading_desk_id.trading_desk_id

    @property
    def app_install(self):
        return self.campaign_id.app_install

    def is_own(self):
        """Returns True if ad group entity belongs to the current user."""
        advertiser_ids = REGISTRY.get('user_advertiser_ids')
        if advertiser_ids and AdGroup.objects.filter(campaign_id__advertiser_id__in=advertiser_ids,
                                                     ad_group_id=self.ad_group_id).exists():
            return True

        agency_ids = REGISTRY.get('user_agency_ids')
        if agency_ids and AdGroup.objects.filter(campaign_id__advertiser_id__agency_id__in=agency_ids,
                                                 ad_group_id=self.ad_group_id).exists():
            return True

        trading_desk_ids = REGISTRY.get('user_trading_desk_ids')
        if trading_desk_ids and AdGroup.objects.filter(
                campaign_id__advertiser_id__agency_id__trading_desk_id__in=trading_desk_ids,
                ad_group_id=self.ad_group_id).exists():
            return True

        return False

    def autopopulate_by_ownership(self):
        pass

    @property
    def ads_enabled(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id=self.pk, status=STATUS_ENABLED)

    @property
    def ads_disapproved(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id=self.pk,
                                      adx_status=AD_STATUS_DISAPPROVED,
                                      status=STATUS_ENABLED)

    @property
    def a9_pending(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id=self.pk,
                                      a9_status=A9_STATUS_PENDING,
                                      status=STATUS_ENABLED)

    @property
    def a9_failed(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id=self.pk,
                                      a9_status=A9_STATUS_FAILED,
                                      status=STATUS_ENABLED)

    @property
    def ads_total(self):
        from restapi.models.Ad import Ad as model
        return model.objects.getCount(ad_group_id=self.pk)

    @property
    def black_lists_total(self):
        from restapi.models.BidderBlacklist import BidderBlacklistIds as model
        return model.objects.getCount(ad_group_id=self.pk)

    @property
    def white_lists_total(self):
        from restapi.models.BidderWhitelist import BidderWhitelistIds as model
        return model.objects.getCount(ad_group_id=self.pk)

    @property
    def custom_hints_total(self):
        from restapi.models.CustomHint import CustomHintIds as model
        return model.objects.getCount(ad_group_id=self.pk)

    @property
    def discrete_pricing_total(self):
        from restapi.models.DiscretePricing import DiscretePricingIds as model
        return model.objects.getCount(ad_group_id=self.pk)

    @property
    def ads_to_pause(self):
        """Returns a number of ads recommended to pause."""
        from restapi.models.CreativePruning import CreativePruning
        return CreativePruning.objects.getCount(ad_id__ad_group_id=self.pk, action='pause')

    @property
    def ads_to_delete(self):
        """Returns a number of ads recommended to delete."""
        from restapi.models.CreativePruning import CreativePruning
        return CreativePruning.objects.getCount(ad_id__ad_group_id=self.pk, action='delete')

    search_args = ('ad_group_id', 'ad_group__icontains')

    @property
    def search_result(self):
        campaign = self.campaign_id
        advertiser = campaign.advertiser_id
        agency = advertiser.agency_id
        result = {'level': 'adgroup',
                  'ad_group': self.ad_group,
                  'ad_group_id': self.ad_group_id,
                  'campaign': campaign.campaign,
                  'campaign_id': campaign.campaign_id,
                  'advertiser': advertiser.advertiser,
                  'advertiser_id': advertiser.advertiser_id,
                  'agency': agency.agency,
                  'agency_id': agency.agency_id,
                  'last_update': self.last_update}
        return result

    def __unicode__(self):
        return self.ad_group

    def get_fields_for_copy(self):
        rejected_fields = lambda x: x.__class__ is models.AutoField or x.name == 'pk'
        extra_fields = ['revmap_rev_type',
                        'revmap_rev_value',
                        'revmap_opt_type',
                        'revmap_opt_value',
                        'revmap_target_type',
                        'revmap_target_value']
        fields = [f.name for f in self._meta.fields if not rejected_fields(f)]
        return fields + extra_fields

    def make_copy(self):
        values = [(f, getattr(self, f)) for f in self.get_fields_for_copy()]

        initials = dict([(k, v) for k, v in values if v is not None])
        # pylint: disable=invalid-name
        m = self.__class__(**initials)
        # pylint: disable=invalid-name
        m.pk = None
        m.ad_group_id = None
        m.status = STATUS_PAUSED  # 'paused'
        return m

    @property
    def parent_name(self):
        return self.campaign_id.campaign

    def save(self, *args, **kwargs):
        from restapi.audit_logger import AuditLogger
        AuditLogger.skip_next_write = True
        super(AdGroup, self).save(*args, **kwargs)

        if self._revmap is not None:
            from restapi.models.Revmap import Revmap
            revmap_qs = Revmap.objects.filter(ad_group_id=self)

            is_updated = False
            if revmap_qs.exists():
                revmap = revmap_qs.first()

            else:
                revmap = Revmap(ad_group_id=self,
                                ad_group=self.ad_group,
                                campaign_id=self.campaign_id.pk,
                                campaign=self.campaign_id.campaign)
                is_updated = True

            for field in self._revmap:
                old_value = getattr(revmap, field)
                new_value = self._revmap[field]
                if isinstance(new_value, Decimal):
                    new_value = float(new_value)

                setattr(revmap, field, self._revmap[field])
                if old_value != new_value:
                    is_updated = True

            if is_updated:
                revmap.save()

        return super(AdGroup, self).save(*args, **kwargs)

    def as_dict(self):
        data = super(AdGroup, self).as_dict()
        for field in ('revmap_rev_type', 'revmap_rev_value', 'revmap_opt_type', 'revmap_opt_value',
                      'revmap_target_type', 'revmap_target_value'):
            data[field] = getattr(self, field)
        return data

    class Meta:
        managed = True
        unique_together = ('campaign_id', 'ad_group')
        db_table = 'ad_group'
        app_label = 'restapi'
        ordering = ('ad_group',)


audit.AuditLogger.register(AdGroup, audit_type=AUDIT_TYPE_AD_GROUP, check_delete='physical_delete')
http_caching.HTTPCaching.register(AdGroup)
