from django.db import models

from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager
from restapi.models.ApiKeyGenerator import ApiKeyGenerator
from restapi.models.choices import STATUS_CHOICES, STATUS_ENABLED, CURRENCY_USD, COUNTRIES
from restapi.registry import REGISTRY

import restapi.audit_logger as audit
import restapi.http_caching as http_caching

AUDIT_TYPE_TRADING_DESK = 13

MANAGE_TRADING_DESK_ID = 1


class TradingDeskManager(BaseManager):
    def own(self, queryset=None):
        return super(TradingDeskManager, self).own(queryset).filter(pk__in=REGISTRY['user_trading_desk_ids'])


class TradingDesk(BaseModel):
    trading_desk_id = models.AutoField(primary_key=True)
    trading_desk = models.CharField(max_length=255)
    trading_desk_key = models.CharField(max_length=40, default=ApiKeyGenerator.key_generator)
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
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_ENABLED)
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = TradingDeskManager()
    objects_raw = models.Manager()
    permission_check = True

    def is_own(self):
        # have no sence for new trading desk
        if self.pk is None:
            return True
        else:
            return bool(self.trading_desk_userprofiles.filter(user=REGISTRY['user']))

    @property
    def is_manage_trading_desk(self):
        return self.pk == MANAGE_TRADING_DESK_ID

    def __unicode__(self):
        return self.trading_desk

    class Meta:
        # managed=False
        db_table = 'trading_desk'
        app_label = 'restapi'
        ordering = ['trading_desk']


audit.AuditLogger.register(TradingDesk, audit_type=AUDIT_TYPE_TRADING_DESK, check_delete='physical_delete')
http_caching.HTTPCaching.register(TradingDesk)
