from django.db import models

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.models.base import BaseModel
from restapi.models.base import BaseReadonlyModelMixin
from restapi.models.PlacementHelper import PlacementHelper
from restapi.models.choices import PLACEMENT_TYPE_CHOICES
from restapi.models.fields import DateTimeField
from restapi.models.fields import SizeCharField
from restapi.models.managers import BaseManager

AUDIT_TYPE_BIDDER_BLACK_LIST = 8


class BidderBlacklistManager(BaseManager):

    def own(self, queryset=None):
        queryset = super(BidderBlacklistManager, self).own(queryset)
        return PlacementHelper.own(queryset)

    def checkCounterKey(selr, **kwargs):
        return 'campaign_id'


# pylint: disable=model-no-explicit-unicode
class BidderBlacklist(BaseModel, BaseReadonlyModelMixin):
    id = models.AutoField(primary_key=True, db_column='id')
    placement_type = models.CharField(max_length=4, choices=PLACEMENT_TYPE_CHOICES)
    placement_id = models.CharField(max_length=128)
    tag = models.CharField(max_length=128, default='', blank=True, null=True)
    last_update = DateTimeField(default=None, auto_now=True)
    advertiser_id = models.IntegerField()
    campaign_id = models.IntegerField()
    campaign = models.CharField(max_length=255)
    ad_group_id = models.IntegerField()
    ad_group = models.CharField(max_length=255)
    source_id = models.IntegerField()
    source = models.CharField(max_length=255)
    size = SizeCharField(max_length=128, null=True, default=None, blank=True)

    objects = BidderBlacklistManager()
    objects_raw = models.Manager()
    permission_check = True

    def is_own(self):
        return PlacementHelper.is_own(self.campaign_id, self.ad_group_id)

    def __unicode__(self):
        return self.placement_id
 
    class Meta:
        managed = False
        app_label = 'restapi'
        db_table = 'bidder_blacklist_view'
        ordering = ['-last_update']
        unique_together = ('campaign_id', 'ad_group_id', 'source_id', 'placement_type', 'placement_id')


# pylint: disable=model-no-explicit-unicode
class BidderBlacklistIds(BaseModel):
    id = models.AutoField(primary_key=True, db_column='id')
    placement_type = models.CharField(max_length=4, choices=PLACEMENT_TYPE_CHOICES)
    placement_id = models.CharField(max_length=128)
    tag = models.CharField(max_length=128, default='', blank=True, null=True)
    last_update = DateTimeField(default=None, auto_now=True)
    campaign_id = models.IntegerField(default=0)
    ad_group_id = models.IntegerField(default=0)
    source_id = models.IntegerField(default=0)
    size = SizeCharField(max_length=128, null=True, default=None, blank=True)

    objects = BidderBlacklistManager()
    objects_raw = models.Manager()
    permission_check = True

    def is_own(self):
        return PlacementHelper.is_own(self.campaign_id, self.ad_group_id)

    def autopopulate_by_ownership(self):
        pass

    @classmethod
    def get_perm_model_name(self):
        return BidderBlacklist.get_perm_model_name()

    def __unicode__(self):
        return self.placement_id

    class Meta:
        managed = True
        app_label = 'restapi'
        db_table = 'bidder_blacklist'
        ordering = ['-last_update']
        unique_together = ('campaign_id', 'ad_group_id', 'source_id', 'placement_type', 'placement_id')

audit.AuditLogger.register(BidderBlacklistIds, audit_type=AUDIT_TYPE_BIDDER_BLACK_LIST, check_delete='physical_delete')
http_caching.HTTPCaching.register(BidderBlacklistIds)
