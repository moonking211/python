# encoding: utf-8
"""This module defines Ad model."""

from __future__ import unicode_literals

from copy import deepcopy
from django.db import models

from restapi import core
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.AdGroup import AdGroup

from restapi.models.choices import STATUS_CHOICES, STATUS_PAUSED, AD_SIZE_CHOICES, AD_STATUS_CHOICES, A9_STATUS_CHOICES, \
    A9_STATUS_PASSED

from restapi.models.managers import BaseManager
import restapi.audit_logger as audit
import restapi.http_caching as http_caching

from restapi.registry import REGISTRY

AUDIT_TYPE_AD = 5

OWN_KEY__FIELD = (
    ('user_trading_desk_ids', 'ad_group_id__campaign_id__advertiser_id__agency_id__trading_desk_id'),
    ('user_agency_ids', 'ad_group_id__campaign_id__advertiser_id__agency_id'),
    ('user_advertiser_ids', 'ad_group_id__campaign_id__advertiser_id')
)


class AdManager(BaseManager):
    def own(self, queryset=None):
        return super(AdManager, self).own(queryset).filter(**core.own_filter_kwargs(REGISTRY, OWN_KEY__FIELD))

    def checkCounterKey(self, **kwargs):
        return 'ad_group_id__campaign_id'


class Ad(BaseModel):
    ad_id = models.AutoField(primary_key=True)
    ad_group_id = models.ForeignKey(AdGroup, db_column='ad_group_id')
    creative_id = models.IntegerField(blank=True, null=True)
    ad = models.CharField(max_length=255)  # pylint: disable=invalid-name
    size = models.CharField(max_length=10, choices=AD_SIZE_CHOICES)
    html = models.TextField(blank=True)
    preview_html = models.TextField(blank=True)
    bid = models.DecimalField(max_digits=9, decimal_places=6, blank=True, default=0)
    targeting = models.TextField(blank=True)
    categories = models.TextField(blank=True)
    attrs = models.CharField(max_length=255, blank=True)
    inflator_text = models.TextField(blank=True)
    domain = models.CharField(max_length=255, blank=True)
    redirect_url = models.CharField(max_length=1024, blank=True)

    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_CHOICES[1][0])

    adx_status = models.CharField(max_length=11, choices=AD_STATUS_CHOICES, default=AD_STATUS_CHOICES[0][0])

    appnexus_status = models.CharField(max_length=11, choices=AD_STATUS_CHOICES, default=AD_STATUS_CHOICES[0][0])

    a9_status = models.CharField(max_length=11, choices=A9_STATUS_CHOICES, default=A9_STATUS_PASSED)

    external_args = models.TextField(blank=True)
    ad_type = models.IntegerField(default=1)
    adx_sensitive_categories = models.TextField(blank=True)
    adx_product_categories = models.TextField(blank=True)
    i_url = models.CharField(max_length=1024, blank=True, null=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)
    created_time = DateTimeField(auto_now_add=True)

    adx_attrs = models.CharField(max_length=255, default='', blank=True)
    tag = models.CharField(max_length=255, default='', blank=True)

    objects = AdManager()
    objects_raw = models.Manager()
    permission_check = True

    actions = ('bulk', 'bulk_re_submit_to_adx', 'export')

    search_args = ('ad_id',)

    @property
    def search_result(self):
        return {
            'level': 'ad',
            'ad': self.ad,
            'ad_id': self.ad_id,
            'ad_type': self.ad_type,
            'ad_group_id': self.ad_group_id.pk,
            'campaign_id': self.campaign_id,
            'advertiser_id': self.ad_group_id.campaign_id.advertiser_id.pk,
            'creative_id': self.creative_id,
            'bid': self.bid,
            'last_update': self.last_update
        }

    def is_own(self):
        """Returns True if ad entity belongs to the current user."""
        advertiser_ids = REGISTRY.get('user_advertiser_ids')
        if advertiser_ids and Ad.objects.filter(ad_group_id__campaign_id__advertiser_id__in=advertiser_ids,
                                                ad_id=self.ad_id).exists():
            return True

        agency_ids = REGISTRY.get('user_agency_ids')
        if agency_ids and Ad.objects.filter(ad_group_id__campaign_id__advertiser_id__agency_id__in=agency_ids,
                                            ad_id=self.ad_id).exists():
            return True

        trading_desk_ids = REGISTRY.get('user_trading_desk_ids')
        if trading_desk_ids and Ad.objects.filter(
                ad_group_id__campaign_id__advertiser_id__agency_id__trading_desk_id__in=trading_desk_ids,
                ad_id=self.ad_id).exists():
            return True

        return False

    def autopopulate_by_ownership(self):
        pass

    @property
    def ad_group(self):
        return self.ad_group_id.ad_group

    @property
    def campaign_id(self):
        return self.ad_group_id.campaign_id.campaign_id

    @property
    def campaign(self):
        return self.ad_group_id.campaign_id.campaign

    @property
    def advertiser_id(self):
        return self.ad_group_id.campaign_id.advertiser_id.advertiser_id

    @property
    def advertiser(self):
        return self.ad_group_id.campaign_id.advertiser_id.advertiser

    @property
    def agency(self):
        return self.ad_group_id.campaign_id.advertiser_id.agency_id.agency

    @property
    def agency_id(self):
        return self.ad_group_id.campaign_id.advertiser_id.agency_id.agency_id

    @property
    def trading_desk(self):
        return self.ad_group_id.campaign_id.advertiser_id.agency_id.trading_desk_id.trading_desk

    @property
    def trading_desk_id(self):
        return self.ad_group_id.campaign_id.advertiser_id.agency_id.trading_desk_id.trading_desk_id

    @property
    def encrypted_ad_id(self):
        from mng.commons.crypto import encrypt
        return encrypt(self.ad_id)

    def __unicode__(self):
        return self.ad

    def make_copy(self):
        # pylint: disable=invalid-name
        m = deepcopy(self)
        m.pk = None
        m.ad_id = None
        m.creative_id = None
        m.ad_group_id_id = None
        m.domain = ''
        m.targeting = ''
        m.categories = ''
        m.status = STATUS_PAUSED  # 'paused'
        m.adx_status = 'new'
        m.appnexus_status = 'new'
        m.a9_status = 'passed'
        m.adx_attrs = ''
        m.adx_sensitive_categories = ''
        m.adx_product_categories = ''
        return m

    class Meta:
        managed = True
        unique_together = ('ad_group_id', 'ad')
        db_table = 'ad'
        app_label = 'restapi'


audit.AuditLogger.register(Ad, audit_type=AUDIT_TYPE_AD, check_delete='physical_delete')
http_caching.HTTPCaching.register(Ad)
