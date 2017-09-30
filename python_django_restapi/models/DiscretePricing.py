from django.db import models

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.models.base import BaseModel
from restapi.models.PlacementHelper import PlacementHelper
from restapi.models.choices import PLACEMENT_TYPE_ALL
from restapi.models.choices import PLACEMENT_TYPE_CHOICES
from restapi.models.choices import SIZE_ALL
from restapi.models.choices import DISCRETE_PRICING_SIZE_CHOICES
from restapi.models.managers import BaseManager
from restapi.models.fields import DateTimeField

AUDIT_TYPE_DISCRETE_PRICING = 11


class DiscretePricingManager(BaseManager):

    def own(self, queryset=None):
        queryset = super(DiscretePricingManager, self).own(queryset)
        return PlacementHelper.own(queryset)

    def checkCounterKey(selr, **kwargs):
        return 'campaign_id'


class DiscretePricing(BaseModel):
    id = models.AutoField(primary_key=True)
    placement_type = models.CharField(max_length=4, choices=PLACEMENT_TYPE_CHOICES, default=PLACEMENT_TYPE_ALL)
    placement_id = models.CharField(max_length=128, default='all')
    tag = models.CharField(max_length=128, blank=True, null=True, default='')
    size = models.CharField(max_length=8, choices=DISCRETE_PRICING_SIZE_CHOICES, default=SIZE_ALL)
    rev_value = models.FloatField()
    created_at = DateTimeField(default=None, auto_now_add=True)
    last_update = DateTimeField(default=None, auto_now=True)
    advertiser_id = models.IntegerField()
    campaign_id = models.IntegerField()
    campaign = models.CharField(max_length=255)
    ad_group_id = models.IntegerField()
    ad_group = models.CharField(max_length=255)
    source_id = models.IntegerField()
    source = models.CharField(max_length=255)

    objects = DiscretePricingManager()
    objects_raw = models.Manager()
    permission_check = False

    def __unicode__(self):
        return self.placement_id

    def is_own(self):
        return PlacementHelper.is_own(self.campaign_id, self.ad_group_id)

    def autopopulate_by_ownership(self):
        pass

    class Meta:
        managed = False
        db_table = 'discrete_pricing_view'
        app_label = 'restapi'
        ordering = ['-last_update']
        unique_together = ('campaign_id', 'ad_group_id', 'source_id', 'placement_type', 'placement_id')


class DiscretePricingIds(BaseModel):
    id = models.AutoField(primary_key=True)
    campaign_id = models.IntegerField(default=0)
    ad_group_id = models.IntegerField(default=0)
    source_id = models.IntegerField(default=0)
    placement_type = models.CharField(max_length=4, choices=PLACEMENT_TYPE_CHOICES, default=PLACEMENT_TYPE_ALL)
    placement_id = models.CharField(max_length=128, default='all')
    tag = models.CharField(max_length=128, blank=True, null=True, default='')
    size = models.CharField(max_length=8, choices=DISCRETE_PRICING_SIZE_CHOICES, default=SIZE_ALL)
    rev_value = models.FloatField()
    created_at = DateTimeField(default=None, auto_now_add=True)
    last_update = DateTimeField(default=None, auto_now=True)

    objects = DiscretePricingManager()
    objects_raw = models.Manager()
    permission_check = False

    def __unicode__(self):
        return self.placement_id

    @classmethod
    def get_perm_model_name(self):
        return DiscretePricing.get_perm_model_name()

    def is_own(self):
        return PlacementHelper.is_own(self.campaign_id, self.ad_group_id)

    class Meta:
        managed = True
        db_table = 'discrete_pricing'
        app_label = 'restapi'
        ordering = ['-last_update']
        unique_together = ('campaign_id', 'ad_group_id', 'source_id', 'placement_type', 'placement_id')

audit.AuditLogger.register(DiscretePricingIds, audit_type=AUDIT_TYPE_DISCRETE_PRICING, check_delete='physical_delete')
http_caching.HTTPCaching.register(DiscretePricingIds)
