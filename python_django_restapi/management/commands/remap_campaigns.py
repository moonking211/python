# encoding: utf-8

from __future__ import unicode_literals

import datetime
import logging
import optparse
import six

from django.db import connections
from django.core.management import base as management_base

from restapi.models import Event
from restapi.models import Advertiser
from restapi.models.twitter import TwitterCampaign

logger = logging.getLogger('management-command')
TWITTER_SOURCE_TYPE = 2
TARGET_CAMPAIGNS = {'Android': 1296, 'iPhone': 1297, 'iPad': 1298}
TARGET_BY_ID = {v: k for k, v in six.iteritems(TARGET_CAMPAIGNS)}
EVENTS_BY_CAMPAIGN_ID = {
    campaign_id: dict(
        Event.Event.objects_raw.filter(campaign_id=campaign_id).values_list('event', 'event_id')
    ) for campaign_id in TARGET_BY_ID}
LINE_ITEMS_STATS_TABLES = (
    's_tw_licd',
    's_tw_lich',
    's_tw_lid',
    's_tw_lih',
    's_tw_lihd',
    's_tw_lihh',
    's_tw_likd',
    's_tw_likh',
)
PROMOTED_TWEETS_STATS_TABLES = (
    's_tw_ptcd',
    's_tw_ptch',
    's_tw_ptd',
    's_tw_pth',
    's_tw_pthd',
    's_tw_pthh',
    's_tw_ptkd',
    's_tw_ptkh'
)


def get_target_campaign_id(name):
    target = None
    for s, campaign_id in six.iteritems(TARGET_CAMPAIGNS):
        if s in name:
            if target:
                raise ValueError('Found multiple targets for %r' % name)
            logger.debug('Using target (%d, %s) for %r', campaign_id, s, name)
            target = campaign_id
    if not target:
        raise ValueError('Cannot find a target campaign for %r' % name)
    return target


class Command(management_base.BaseCommand):
    help = 'Remap Twitter campaigns.'
    option_list = management_base.BaseCommand.option_list + (
        optparse.make_option('--update', dest='update', action='store_true', default=False, help='Update data.'),
        optparse.make_option('--tw-campaign-id', dest='tw_campaign_id', action='store', default=None, type=int,
                             help='Twitter campaign id.')
    )

    def handle(self, *args, **options):
        update = options.get('update') or False
        if not update:
            logger.info('Dry run mode. No updates.')
        advertiser = Advertiser.Advertiser.objects_raw.get(advertiser='Zynga')
        campaign_id__campaign__tw_campaign_id__name = TwitterCampaign.TwitterCampaign.objects_raw.filter(
            campaign_id__advertiser_id=advertiser.pk,
            campaign_id__source_type=TWITTER_SOURCE_TYPE
        ).exclude(
            campaign_id__campaign__startswith='TW'
        ).values_list(
            'campaign_id__campaign_id',
            'campaign_id__campaign',
            'tw_campaign_id',
            'name'
        ).order_by(
            'campaign_id__campaign_id'
        )
        if options.get('tw_campaign_id'):
            campaign_id__campaign__tw_campaign_id__name = campaign_id__campaign__tw_campaign_id__name.filter(
                tw_campaign_id=options['tw_campaign_id']
            )
        for campaign_id, campaign, tw_campaign_id, name in campaign_id__campaign__tw_campaign_id__name:
            target_campaign_id = get_target_campaign_id(name)
            if name.endswith('{%d}' % target_campaign_id):
                logger.debug('Campaign %r was already migrated', name)
                continue
            if not name.endswith('{%d}' % campaign_id):
                logger.error('Cannot migrate campaign %r because it does not match campaign %d', name, campaign_id)
                continue

            ts = [datetime.datetime.utcnow()]
            target_events = EVENTS_BY_CAMPAIGN_ID[target_campaign_id]
            events = dict(Event.Event.objects_raw.filter(campaign_id=campaign_id).values_list('event', 'event_id'))
            event_id__target_event_id = []
            for event, event_id in six.iteritems(events):
                event_id__target_event_id.append((event_id, target_events[event]))

            for table in (LINE_ITEMS_STATS_TABLES + PROMOTED_TWEETS_STATS_TABLES):
                ts.append(datetime.datetime.utcnow())
                sql = '''
                    UPDATE {table}
                    SET event_id = CASE {case} END
                    WHERE event_id IN ({event_ids})
                '''.format(
                    table=table,
                    case=' '.join(['WHEN event_id = {} THEN {}'.format(event_id, target_event_id)
                                   for event_id, target_event_id in event_id__target_event_id]),
                    event_ids=', '.join(map(str, [f for f, _ in event_id__target_event_id]))
                )
                logger.debug(sql)
                if update:
                    with connections['app_db'].cursor() as cursor:
                        cursor.execute(sql)
                logger.debug('tw_campaign_id: %d table %s %.2f', tw_campaign_id, table,
                             (datetime.datetime.utcnow() - ts.pop()).total_seconds())

            new_name = name[:name.rindex('{%d}' % campaign_id)] + '{%d}' % target_campaign_id
            if update:
                TwitterCampaign.TwitterCampaign.update({
                    'tw_campaign_id': tw_campaign_id,
                    'campaign_id': target_campaign_id,
                    'name': new_name
                })
            logger.debug('tw_campaign_id: %d set campaign_id: %d => %d name: %r => %r %.2f', tw_campaign_id,
                         campaign_id, target_campaign_id, name, new_name,
                         (datetime.datetime.utcnow() - ts.pop()).total_seconds())
