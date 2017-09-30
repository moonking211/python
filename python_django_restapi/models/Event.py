from django.db import models

from restapi import core
from restapi.models.base import BaseModel
from restapi.models.Campaign import Campaign
from restapi.models.fields import DateTimeField
from restapi.models.managers import BaseManager

import restapi.audit_logger as audit
import restapi.http_caching as http_caching
from restapi.registry import REGISTRY

AUDIT_TYPE_EVENT = 6

OWN_KEY__FIELD = (
    ('user_trading_desk_ids', 'campaign_id__advertiser_id__agency_id__trading_desk_id'),
    ('user_agency_ids', 'campaign_id__advertiser_id__agency_id'),
    ('user_advertiser_ids', 'campaign_id__advertiser_id')
)


class EventManager(BaseManager):
    """Event model manager."""

    def own(self, queryset=None):
        """Returns queryset that filters events that belongs to the current user."""
        return super(EventManager, self).own(queryset).filter(**core.own_filter_kwargs(REGISTRY, OWN_KEY__FIELD))


class Event(BaseModel):
    event_id = models.AutoField(primary_key=True)
    campaign_id = models.ForeignKey(Campaign, db_column='campaign_id', related_name='events')
    event = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    default_args = models.TextField(blank=True, default='')
    base_event_id = models.IntegerField(blank=True, default=0)
    deleted = models.BooleanField(default=False, blank=True)
    max_frequency = models.IntegerField(blank=True, null=True)
    show_in_stats = models.BooleanField(default=True)
    frequency_interval = models.IntegerField(blank=True, null=True)
    accept_unencrypted = models.BooleanField(default=False, blank=True)
    last_update = DateTimeField(null=True, default=None, auto_now=True)

    objects = EventManager()
    objects_raw = models.Manager()
    permission_check = True

    def is_own(self):
        """Returns True if event entity belongs to the current user."""
        advertiser_ids = REGISTRY.get('user_advertiser_ids')
        if advertiser_ids and Event.objects.filter(campaign_id__advertiser_id__in=advertiser_ids,
                                                   event_id=self.event_id).exists():
            return True

        agency_ids = REGISTRY.get('user_agency_ids')
        if agency_ids and Event.objects.filter(campaign_id__advertiser_id__agency_id__in=agency_ids,
                                               event_id=self.event_id).exists():
            return True

        trading_desk_ids = REGISTRY.get('user_trading_desk_ids')
        if trading_desk_ids and Event.objects.filter(
                campaign_id__advertiser_id__agency_id__trading_desk_id__in=trading_desk_ids,
                event_id=self.event_id).exists():
            return True

        return False

    def autopopulate_by_ownership(self):
        pass

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

    def __unicode__(self):
        return self.event

    @property
    def encrypted_event_id(self):
        from mng.commons.crypto import encrypt
        return encrypt(self.event_id)

    search_args = ('event_id',)

    @property
    def search_result(self):
        return {
            'level': 'event',
            'event': self.event,
            'event_id': self.event_id,
            'campaign_id': self.campaign_id.pk,
            'advertiser_id': self.campaign_id.advertiser_id.pk,
            'description': self.description,
            'last_update': self.last_update
        }

    class Meta:
        # managed = False
        unique_together = ('campaign_id', 'event')
        db_table = 'event'
        app_label = 'restapi'


audit.AuditLogger.register(Event, audit_type=AUDIT_TYPE_EVENT, check_delete='physical_delete')
http_caching.HTTPCaching.register(Event)
