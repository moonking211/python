import pytz
from datetime import datetime
from django.db import models
from dateutil.parser import parse
from restapi.models.Advertiser import Advertiser
from restapi.models.base import BaseModel
from restapi.models.Campaign import Campaign
from restapi.models.managers import BaseManager
from restapi.models.fields import ZeroDateField

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.registry import REGISTRY

AUDIT_TYPE_IO = 22


class IoManager(BaseManager):
    def own(self, queryset=None):
        queryset = super(IoManager, self).own(queryset)
        queryset = queryset.filter(
            campaign_id__advertiser_id__agency_id__trading_desk_id_id__in=REGISTRY['user_trading_desk_ids'])
        return queryset


class Io(BaseModel):
    io_id = models.AutoField(primary_key=True)
    advertiser_id = models.ForeignKey(Advertiser, db_column='advertiser_id')
    campaigns = models.ManyToManyField(Campaign, through='Io_campaign')
    start_date = ZeroDateField(default=None, null=True, blank=True)
    end_date = ZeroDateField(default=None, null=True, blank=True)
    io_budget = models.FloatField()
    io_document_link = models.CharField(max_length=1024, blank=True)
    notes = models.TextField(blank=True, default='')

    objects = IoManager()
    objects_raw = models.Manager()
    permission_check = False

    @property
    def advertiser(self):
        return self.advertiser_id.advertiser

    @property
    def agency_id(self):
        return self.advertiser_id.agency_id.agency_id

    @property
    def trading_desk_id(self):
        return self.advertiser_id.agency_id.trading_desk_id.trading_desk_id

    @property
    def days_left(self):
        start_date = parse(self.start_date).date() if type(self.start_date) == unicode else self.start_date
        end_date = parse(self.end_date).date() if type(self.end_date) == unicode else self.end_date

        if start_date > self.today_date or not end_date:
            return '--'

        if end_date and end_date >= self.today_date and start_date <= self.today_date:
            return (end_date - self.today_date).days

        return 'Expired'

    @property
    def today_date(self):
        utc = pytz.UTC
        return utc.localize(datetime.now()).date()

    def is_own(self):
        return bool(self.advertiser_id.agency_id.trading_desk_id.trading_desk_userprofiles.filter(
            user=REGISTRY['user']))

    def __unicode__(self):
        return "{} ({})".format(self.advertiser_id.advertiser, self.advertiser_id.pk)

    class Meta:
        managed = True
        db_table = 'io'
        app_label = 'restapi'


audit.AuditLogger.register(Io, audit_type=AUDIT_TYPE_IO, check_delete='physical_delete')


class Io_campaign(BaseModel):
    io_id = models.ForeignKey(Io, db_column='io_id')
    campaign_id = models.ForeignKey(Campaign, db_column='campaign_id')

    @property
    def campaign(self):
        return self.campaign_id.campaign

    class Meta:
        managed = True
        auto_created = True
        db_table = 'campaign_io'
        app_label = 'restapi'


http_caching.HTTPCaching.register(Io)
http_caching.HTTPCaching.register(Io_campaign)
