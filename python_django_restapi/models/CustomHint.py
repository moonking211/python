from datetime import datetime
from django.conf import settings
from django.db import models
from pytz import timezone

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.models.base import BaseModel
from restapi.models.PlacementHelper import PlacementHelper
from restapi.models.choices import INFLATOR_TYPE_CHOICES
from restapi.models.choices import PLACEMENT_TYPE_ALL
from restapi.models.choices import PLACEMENT_TYPE_CHOICES
from restapi.models.choices import SIZE_ALL
from restapi.models.choices import CUSTOM_HINT_SIZE_CHOICES
from restapi.models.managers import BaseManager
from restapi.models.fields import DateTimeField
from restapi.models.fields import WideRangeDateTimeField

from restapi.models.Campaign import Campaign
from restapi.models.AdGroup import AdGroup

AUDIT_TYPE_CUSTOM_HINT = 9


class CustomHintManager(BaseManager):

    def own(self, queryset=None):
        queryset = super(CustomHintManager, self).own(queryset)
        return PlacementHelper.own(queryset)

    def filter_by_list(self, params, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        for name in params.keys():
            values = params[name]
            args = dict()

            if name == 'active' and values:
                values_set = {bool(v) for v in values}
                now = datetime.now()
                if True in values_set and False not in values_set:
                    args = {'end_date__gte': now}
                elif False in values_set and True not in values_set:
                    args = {'end_date__lt': now}
            else:
                args = {'%s__in' % name: values}

            if args:
                queryset = queryset.filter(**args)
        return queryset

    def checkCounterKey(selr, **kwargs):
        return 'campaign_id'


class CustomHint(BaseModel):
    id = models.AutoField(primary_key=True)
    size = models.CharField(max_length=8, choices=CUSTOM_HINT_SIZE_CHOICES, default=SIZE_ALL)
    placement_type = models.CharField(max_length=4, choices=PLACEMENT_TYPE_CHOICES, default=PLACEMENT_TYPE_ALL)
    placement_id = models.CharField(max_length=128, default='all')
    inflator_type = models.CharField(max_length=8, choices=INFLATOR_TYPE_CHOICES, null=True, default=None)
    inflator = models.DecimalField(max_digits=9, decimal_places=6, null=True, default=None)
    priority = models.IntegerField(default=0)
    max_frequency = models.IntegerField(default=0)
    frequency_interval = models.IntegerField(default=0)
    start_date = WideRangeDateTimeField(default=timezone(settings.TIME_ZONE).localize(datetime(datetime.now().year, 1, 1)))
    end_date = WideRangeDateTimeField(default=timezone(settings.TIME_ZONE).localize(datetime(datetime.now().year, 12, 31)))
    tag = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_update = DateTimeField(default=None, auto_now=True)
    advertiser_id = models.IntegerField()
    campaign_id = models.ForeignKey(Campaign, db_column='campaign_id', null=True, db_constraint=False, on_delete=models.DO_NOTHING)
    campaign = models.CharField(max_length=255)
    ad_group_id = models.ForeignKey(AdGroup, db_column='ad_group_id', null=True, db_constraint=False, on_delete=models.DO_NOTHING)
    ad_group = models.CharField(max_length=255)
    ad_id = models.IntegerField()
    # pylint: disable=invalid-name
    ad = models.CharField(max_length=255)
    source_id = models.IntegerField()
    source = models.CharField(max_length=255)

    objects = CustomHintManager()
    objects_raw = models.Manager()
    permission_check = True

    def __unicode__(self):
        return self.placement_id

    def is_own(self):
        return PlacementHelper.is_own(self.campaign_id, self.ad_group_id)

    def autopopulate_by_ownership(self):
        pass

    class Meta:
        managed = False
        db_table = 'custom_hint_view'
        app_label = 'restapi'
        ordering = ['-last_update']
        unique_together = ('campaign_id', 'ad_group_id', 'ad_id', 'source_id', 'size', 'placement_type', 'placement_id')


class CustomHintIds(BaseModel):
    id = models.AutoField(primary_key=True)
    size = models.CharField(max_length=8, choices=CUSTOM_HINT_SIZE_CHOICES, default=SIZE_ALL)
    placement_type = models.CharField(max_length=4, choices=PLACEMENT_TYPE_CHOICES, default=PLACEMENT_TYPE_ALL)
    placement_id = models.CharField(max_length=128, default='all')
    inflator_type = models.CharField(max_length=8, choices=INFLATOR_TYPE_CHOICES, null=True, default=None)
    inflator = models.DecimalField(max_digits=9, decimal_places=6, null=True, default=None)
    priority = models.IntegerField(default=0)
    max_frequency = models.IntegerField(default=0)
    frequency_interval = models.IntegerField(default=0)
    start_date = WideRangeDateTimeField(default=timezone(settings.TIME_ZONE).localize(datetime(datetime.now().year, 1, 1)))
    end_date = WideRangeDateTimeField(default=timezone(settings.TIME_ZONE).localize(datetime(datetime.now().year, 12, 31)))
    tag = models.CharField(max_length=128, blank=True, null=True, default=None)
    last_update = DateTimeField(default=None, auto_now=True)
    campaign_id = models.IntegerField(default=0)
    ad_group_id = models.IntegerField(default=0)
    ad_id = models.IntegerField(default=0)
    source_id = models.IntegerField(default=0)

    objects = CustomHintManager()
    objects_raw = models.Manager()
    permission_check = True

    def __unicode__(self):
        return self.placement_id

    @classmethod
    def get_perm_model_name(self):
        return CustomHint.get_perm_model_name()

    def is_own(self):
        return PlacementHelper.is_own(self.campaign_id, self.ad_group_id)

    class Meta:
        managed = True
        db_table = 'custom_hint'
        app_label = 'restapi'
        ordering = ['-last_update']
        unique_together = ('campaign_id', 'ad_group_id', 'ad_id', 'source_id', 'size', 'placement_type', 'placement_id')

audit.AuditLogger.register(CustomHintIds, audit_type=AUDIT_TYPE_CUSTOM_HINT, check_delete='physical_delete')
http_caching.HTTPCaching.register(CustomHintIds)
