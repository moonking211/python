# encoding: utf-8
"""This module defines Agency model."""

from __future__ import unicode_literals

from django.db import models

from restapi import core
from restapi import registry
from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.choices import COUNTRIES
from restapi.models.choices import CURRENCY_USD
from restapi.models.choices import STATUS_CHOICES
from restapi.models.ApiKeyGenerator import ApiKeyGenerator
from restapi.models.TradingDesk import TradingDesk
from restapi.models.managers import BaseManager
from restapi.registry import REGISTRY
import restapi.audit_logger as audit
import restapi.http_caching as http_caching

AUDIT_TYPE_AGENCY = 12

OWN_KEY__FIELD = (
    ('user_trading_desk_ids', 'agency_id__trading_desk_id'),
    ('user_agency_ids', 'agency_id'),
    ('user_advertiser_ids', 'agency_advertisers__advertiser_id')
)


class AgencyManager(BaseManager):
    """Agency model manager."""

    def own(self, queryset=None):
        """Returns queryset that filters agencies that belongs to the current user."""
        return super(AgencyManager, self).own(queryset).filter(
            **core.own_filter_kwargs(registry.REGISTRY, OWN_KEY__FIELD)
        )


class Agency(BaseModel):
    agency_id = models.AutoField(primary_key=True)
    trading_desk_id = models.ForeignKey(TradingDesk, db_column='trading_desk_id', related_name='trading_desk_agencies')
    agency = models.CharField(max_length=255)
    agency_key = models.CharField(max_length=40, default=ApiKeyGenerator.key_generator)
    account_manager = models.IntegerField(max_length=10, default=0)
    currency = models.CharField(max_length=3, default=CURRENCY_USD)
    contact = models.CharField(max_length=100)
    address1 = models.CharField(max_length=255, default='', blank=True)
    address2 = models.CharField(max_length=255, default='', blank=True)
    city = models.CharField(max_length=100, default='', blank=True)
    state_prov = models.CharField(max_length=100, default='', blank=True)
    zip = models.CharField(max_length=10, default='', blank=True)
    country = models.CharField(max_length=3, choices=COUNTRIES, default=COUNTRIES[0][0])
    phone = models.CharField(max_length=20, default='', blank=True)
    email = models.CharField(max_length=255, default='', blank=True)
    notes = models.TextField(blank=True, default='')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_CHOICES[1][0])
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = AgencyManager()
    objects_raw = models.Manager()
    permission_check = True

    actions = ('filter_by_trading_desk',)

    def is_own(self):
        """Returns True if agency entity belongs to the current user."""
        user_advertiser_ids = REGISTRY.get('user_advertiser_ids')
        if user_advertiser_ids and Agency.objects.filter(agency_advertisers__advertiser_id__in=user_advertiser_ids,
                                                         agency_id=self.agency_id).exists():
            return True

        user_agency_ids = REGISTRY.get('user_agency_ids')
        if user_agency_ids and self.agency_id in user_agency_ids:
            return True

        user_trading_desk_ids = REGISTRY.get('user_trading_desk_ids')
        if user_trading_desk_ids and self.trading_desk_id in user_trading_desk_ids:
            return True

        return False

    def autopopulate_by_ownership(self):
        trading_desk = REGISTRY['user'].profile.trading_desk.first()
        self.trading_desk_id = trading_desk
        self.currency = trading_desk.currency

    def __unicode__(self):
        return self.agency

    search_args = ('agency_id', 'agency__icontains')

    @property
    def trading_desk(self):
        return self.trading_desk_id.trading_desk

    @property
    def search_result(self):
        return {
            'level': 'agency',
            'agency': self.agency,
            'agency_id': self.agency_id,
            'trading_desk_id': self.trading_desk_id.pk,
            'last_update': self.last_update
        }

    class Meta:
        # managed=False
        unique_together = ('trading_desk_id', 'agency')
        db_table = 'agency'
        app_label = 'restapi'
        ordering = ('agency',)


audit.AuditLogger.register(Agency, audit_type=AUDIT_TYPE_AGENCY, check_delete='physical_delete')
http_caching.HTTPCaching.register(Agency)
