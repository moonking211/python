"""This module defines model for Ads pruning."""

from __future__ import unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from restapi.models.base import BaseModel
from restapi.models.fields import DateTimeField
from restapi.models.choices import CREATIVE_PRUNING_STATUS_CHOICES
from restapi.models.managers import BaseManager
from restapi.models.Ad import Ad


class CreativePruningManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(CreativePruningManager, self).own(queryset)
        return queryset

    def checkCounterKey(self, **kwargs):
        """Returns True if given kwargs are valid for counter key."""
        return set(kwargs.keys()) in ({'ad_id__ad_group_id__campaign_id', 'action'}, {'ad_id__ad_group_id', 'action'})


class CreativePruning(BaseModel):
    ad_id = models.ForeignKey(Ad, db_column='ad_id', primary_key=True)
    reason = models.CharField(max_length=255)
    action = models.CharField(max_length=40, choices=CREATIVE_PRUNING_STATUS_CHOICES, default='pause')
    ibid = models.FloatField()
    impression = models.FloatField(help_text=_('Number of times an actual ad was served to the publisher.'))
    win_rate = models.FloatField()
    click = models.FloatField()
    ctr = models.FloatField(verbose_name=_('CTR'))
    install = models.FloatField()
    # Install rate.
    ir = models.FloatField(verbose_name=_('IR'), help_text=_('Install rate = (Installs / Impressions) * 100'))
    ipm = models.FloatField()
    cpm = models.FloatField()
    rpm = models.FloatField(verbose_name=_('RPM'))
    ppm = models.FloatField(verbose_name=_('PPM'))
    cpi = models.FloatField()
    rpi = models.FloatField()
    cost = models.FloatField()
    revenue = models.FloatField()
    profit = models.FloatField()
    margin = models.FloatField()
    status = models.CharField(max_length=63)
    # Install rank.
    install_rank = models.FloatField()
    ir_rank = models.FloatField()
    rpm_rank = models.FloatField()
    ctr_rank = models.FloatField()
    ibid_rank = models.FloatField()
    # IPM rank.
    ipm_rank = models.FloatField(help_text='IPM Rank', verbose_name='IPM Rank')
    revenue_rank = models.FloatField()
    profit_rank = models.FloatField()
    # Impression rank.
    impression_rank = models.FloatField(help_text='Impression Rank')
    days = models.BigIntegerField(max_length=20)
    days_w_impression = models.BigIntegerField(max_length=20, verbose_name=_('Days with impression'))
    created_at = DateTimeField(auto_now_add=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = CreativePruningManager()
    objects_raw = models.Manager()

    # permission_check = True

    def __unicode__(self):
        return unicode(self.ad_id)

    class Meta:
        db_table = 'creative_pruning'
        app_label = 'restapi'

    @property
    def ad(self):
        return self.ad_id

    @property
    def ad_group_id(self):
        return self.ad_id.ad_group_id.ad_group_id

    @property
    def ad_group(self):
        return self.ad_id.ad_group_id.ad_group

    @property
    def campaign_id(self):
        return self.ad_id.ad_group_id.campaign_id.campaign_id

    @property
    def campaign(self):
        return self.ad_id.ad_group_id.campaign_id.campaign

    @property
    def advertiser_id(self):
        return self.ad_id.ad_group_id.campaign_id.advertiser_id.advertiser_id

    @property
    def advertiser(self):
        return self.ad_id.ad_group_id.campaign_id.advertiser_id.advertiser
