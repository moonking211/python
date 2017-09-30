# encoding: utf-8
"""This module defines Advertiser model."""

from __future__ import unicode_literals

from django.db import models

from restapi import core
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.fields import ZeroDateField
from restapi.models.choices import CURRENCY_USD
from restapi.models.choices import STATUS_CHOICES, STATUS_ENABLED, COUNTRIES
from restapi.models.managers import BaseManager
from restapi.models.ApiKeyGenerator import ApiKeyGenerator
from restapi.models.Agency import Agency

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.registry import REGISTRY

AUDIT_TYPE_ADVERTISER = 2

OWN_KEY__FIELD = (
    ('user_trading_desk_ids', 'agency_id__trading_desk_id'),
    ('user_agency_ids', 'agency_id'),
    ('user_advertiser_ids', 'advertiser_id')
)


class AdvertiserManager(BaseManager):
    """Advertiser model manager."""

    def own(self, queryset=None):
        """Returns queryset that filters advertisers that belongs to the current user."""
        return super(AdvertiserManager, self).own(queryset).filter(**core.own_filter_kwargs(REGISTRY, OWN_KEY__FIELD))

    def _exclude_archived(self, queryset):
        return queryset.exclude(deleted=True)


class Advertiser(BaseModel):
    advertiser_id = models.AutoField(primary_key=True)
    advertiser = models.CharField(max_length=255)
    advertiser_key = models.CharField(max_length=40, default=ApiKeyGenerator.key_generator)
    agency_id = models.ForeignKey(Agency, db_column='agency_id', related_name='agency_advertisers')
    account_manager = models.IntegerField(max_length=10, default=0)
    notes = models.TextField(blank=True)
    encryption_key = models.BinaryField(max_length=16, blank=True, null=True, default=ApiKeyGenerator.random_string_16)
    encryption_iv = models.BinaryField(max_length=16, blank=True, null=True, default=ApiKeyGenerator.random_string_16)
    encryption_suffix = models.BinaryField(max_length=4, blank=True, null=True, default=ApiKeyGenerator.random_string_4)
    deleted = models.BooleanField(default=False, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    zip = models.CharField(max_length=10, default='', blank=True)
    contact = models.CharField(max_length=100)
    address1 = models.CharField(max_length=255, default='', blank=True)
    address2 = models.CharField(max_length=255, default='', blank=True)
    city = models.CharField(max_length=100, default='', blank=True)
    state_prov = models.CharField(max_length=100, default='', blank=True)
    country = models.CharField(max_length=3, choices=COUNTRIES, default=COUNTRIES[0][0])
    phone = models.CharField(max_length=20, default='', blank=True)
    email = models.CharField(max_length=255, default='', blank=True)
    flight_start_date = ZeroDateField(default=None, null=True, blank=True)
    flight_budget = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    sampling_rate = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    throttling_rate = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)
    currency = models.CharField(max_length=3, default=CURRENCY_USD)
    twitter_margin = models.FloatField(default=0.15)
    discount = models.DecimalField(max_digits=9, decimal_places=2, default=0)

    objects = AdvertiserManager()
    objects_raw = models.Manager()
    permission_check = True

    actions = ('filter_by_trading_desk',)

    def is_own(self):
        """Returns True if advertiser entity belongs to the current user."""
        user_advertiser_ids = REGISTRY.get('user_advertiser_ids')
        if user_advertiser_ids and self.advertiser_id in user_advertiser_ids:
            return True

        user_agency_ids = REGISTRY.get('user_agency_ids')
        if user_agency_ids and self.agency_id_id in user_agency_ids:
            return True

        user_trading_desk_ids = REGISTRY.get('user_trading_desk_ids')
        if user_trading_desk_ids and Advertiser.objects.filter(agency_id__trading_desk_id__in=user_trading_desk_ids,
                                                               advertiser_id=self.advertiser_id).exists():
            return True

        return False

    def autopopulate_by_ownership(self):
        pass

    search_args = ('advertiser_id', 'advertiser__icontains')

    @property
    def search_result(self):
        return {
            'level': 'advertiser',
            'advertiser': self.advertiser,
            'advertiser_id': self.advertiser_id,
            'agency': self.agency_id.agency,
            'agency_id': self.agency_id.agency_id,
            'last_update': self.last_update
        }

    @property
    def agency(self):
        return self.agency_id.agency

    @property
    def trading_desk_id(self):
        return self.agency_id.trading_desk_id.trading_desk_id

    @property
    def trading_desk(self):
        return self.agency_id.trading_desk_id.trading_desk

    def __unicode__(self):
        return self.advertiser

    class Meta:
        # managed=False
        unique_together = ('agency_id', 'advertiser')
        db_table = 'advertiser'
        app_label = 'restapi'
        ordering = ('advertiser',)


audit.AuditLogger.register(Advertiser, audit_type=AUDIT_TYPE_ADVERTISER, check_delete='physical_delete')
http_caching.HTTPCaching.register(Advertiser)
