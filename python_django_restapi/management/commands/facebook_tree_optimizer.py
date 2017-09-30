# encoding: utf-8

from __future__ import unicode_literals

import datetime
import json
import logging
import multiprocessing
import optparse
import os
import Queue
import threading
import math

from sklearn.externals import joblib

from django.conf import settings
from django.utils import timezone
from django.db import connections
from django.core.management import base as management_base

from restapi.models import choices
from restapi.models import JobStatus
from restapi.models.twitter import TwitterLineItem
from restapi.models.twitter import TwitterRevmap
from restapi.models.twitter import TwitterConfig
from restapi.models.twitter import TwitterTargetingModels

logger = logging.getLogger('management-command')

STATS_LATENCY = 2  # 2 hours
SOURCE_TYPE = 2  # Twitter campaign source type.
MAX_CPC_BID = 3000000
MIN_CPC_BID = 100000
MIN_SPEND = 1
MIN_INSTALLS = 3
QUEUE_GET_RETRIES = 3
QUEUE_GET_TIMEOUT = 1  # 1 second
SYNC_DATABASE_JOB = 'twitter_sync_database'
TW_AUTO_OPTIMIZE_LINE_ITEMS = frozenset(getattr(settings, 'TW_AUTO_OPTIMIZE_LINE_ITEMS', ()))


def _get_zero_stats():
    return {'click': 0, 'install': 0, 'mcost': 0, 'rev': 0, 'ir': 0, 'cpc': 0, 'cpi': 0, 'opt_value': 0, 'goal': 0}


def normalize_bid(bid, min_cpc_bid=MIN_CPC_BID, max_cpc_bid=MAX_CPC_BID):
    """Normalizes BID using min and max cap."""
    return max(min(bid, max_cpc_bid), min_cpc_bid)


def round10k(v):
    """Rounds given value to 10k."""
    return int(v / 10000) * 10000


def dict_fetchall(cursor):
    """"Returns all rows from a cursor as a dict"""
    return (dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall())


class Interval(object):
    """This class represents time interval."""

    def __init__(self, alias=None):
        self._alias = alias

    @property
    def name(self):
        """Returns interval name."""
        cls = self.__class__.__name__.lower()
        return '{}_{}{}'.format(self.value, cls[:-1] if cls.endswith('s') else cls, 's' if self.value > 1 else '')

    @property
    def alias(self):
        """Returns interval alias."""
        return self._alias

    def mysql_type(self):
        """Returns MySQL type."""
        name = self.__class__.__name__.upper()
        return name[:-1] if name.endswith('S') else name

    def value(self):
        """Returns value."""
        raise NotImplemented

    @property
    def delta(self):
        """Returns datetime.delta that corresponds to interval."""
        return datetime.timedelta(**{self.__class__.__name__.lower(): self.value})


class Days(Interval):
    """This class represents days interval."""

    def __init__(self, days, *args, **kwargs):
        super(Days, self).__init__(*args, **kwargs)
        self.days = days

    @property
    def value(self):
        """Returns interval's number of days."""
        return self.days


class Hours(Interval):
    """This class represents hours interval."""

    def __init__(self, hours, *args, **kwargs):
        super(Hours, self).__init__(*args, **kwargs)
        self.hours = hours

    @property
    def value(self):
        """Returns interval's number of hours."""
        return self.hours


class TimeBucket(object):
    """This class represents time bucket."""

    def __init__(self, date=None):
        self._date = date or datetime.datetime.utcnow()

    @property
    def name(self):
        """Returns time bucket name."""
        return '{}[{}]'.format('weekend' if self.is_weekend() else 'weekday', self.bucket)

    def is_weekend(self):
        """Returns True if time bucket is for weekend."""
        # 0=Monday, 6=Sunday
        return self._date.weekday() >= 5

    @property
    def bucket(self):
        """Returns current time bucket."""
        return self._date.hour / 4


class TwitterCampaignOptimizer(threading.Thread):
    RATE_EVENT = 'click'
    DEFAULT_EVENTS = frozenset(('click',))
    STATS_INTERVALS = (Hours(24 * 7, 'L'), Hours(24, 'M'), Hours(12, 'S'))
    MIN_FOR_OPT_TYPE = {'install': 3}

    def __init__(self, queue, optimize, line_item_id, optimize_line_item_id, tree_filename,
                 vector_filename, *args, **kwargs):
        super(TwitterCampaignOptimizer, self).__init__(*args, **kwargs)
        self.queue = queue
        self.optimize = optimize
        self.line_item_id = line_item_id
        self.optimize_line_item_id = optimize_line_item_id
        self.tree = joblib.load(tree_filename)
        self.vector = joblib.load(vector_filename)

    def get_campaign_interval_stats(self, campaign_id, opt_type, now, interval, time_bucket=None):
        select = ['tw_line_item_id', 'SUM(mcost) AS mcost', 'SUM(rev) AS rev', 'opt_value']
        for ot in (opt_type, self.RATE_EVENT,):
            select.extend([
                "SUM(IF(event='{ot}', num, 0)) AS {ot}".format(ot=ot),
                "COALESCE(ROUND(SUM(mcost) / SUM(IF(event='{ot}', num, 0)), 2), 0) AS {alias}".format(
                    ot=ot,
                    alias='cp%s' % ot.lower()[0]
                )
            ])
            if ot != self.RATE_EVENT:
                select.extend([
                    "COALESCE(ROUND(SUM(IF(event='{ot}', num, 0)) / SUM(IF(event='{rate_event}', num, 0)), 2), 0) AS "
                    "{alias}".format(
                        ot=ot,
                        rate_event=self.RATE_EVENT,
                        alias='%sr' % ot.lower()[0]
                    ),
                    "COALESCE(ROUND(SUM(IF(event='{}', num, 0)) * opt_value / SUM(mcost), 2), 0) AS goal".format(ot)
                ])
        where = [
            'event.event IN (%s)' % ', '.join(["'%s'" % e for e in (opt_type, self.RATE_EVENT)]),
            "tw_revmap.opt_type = '{}'".format(opt_type),
            'tw_line_item.tw_campaign_id = {:d}'.format(campaign_id)
        ]
        if self.line_item_id:
            where.append('tw_line_item_id IN (%s)' % ', '.join(map(str, self.line_item_id)))
        if isinstance(interval, Days) and not time_bucket:
            table = 's_tw_lid'
            where.append("%s.date >= '%s'" % (table, str(now.date() - interval.delta)[:len('2016-10-22')]))
        else:
            table = 's_tw_lih'
            where.append("CONCAT({table}.date, ' ', LPAD({table}.hour, 2, 0)) >= '{date}'".format(
                table=table,
                date=str(now - interval.delta)[:len('2016-10-22 00')]
            ))
            if time_bucket:
                where.extend([
                    'FLOOR({table}.hour / 4) = {bucket}'.format(table=table, bucket=time_bucket.bucket),
                    'DAYOFWEEK({table}.date) {condition}'.format(
                        table=table,
                        condition='IN (1, 7)' if time_bucket.is_weekend() else 'NOT IN (1, 7)'
                    )
                ])
        sql = '''
            SELECT
                {select}
            FROM {table}
                JOIN tw_line_item USING (tw_line_item_id)
                JOIN event USING(event_id)
                JOIN tw_revmap USING(tw_line_item_id)
            WHERE
                {where}
            GROUP BY 1
        '''.format(select=', '.join(select), table=table, where=' AND '.join(where))
        stats = {}
        with connections['app_db'].cursor() as cursor:
            selected = cursor.execute(sql)
            if selected:
                for row in dict_fetchall(cursor):
                    stats[row['tw_line_item_id']] = row
        return stats

    def optimize_campaign(self, now, tw_account_id, tw_campaign_id):
        # First we should get all target events for current campaign.
        opt_types_query = TwitterRevmap.TwitterRevmap.objects_raw.order_by().distinct().filter(
            tw_campaign_id=tw_campaign_id,
            tw_line_item_id__status=choices.STATUS_ENABLED
        ).values_list('opt_type', 'opt_value')
        if self.line_item_id:
            opt_types_query = opt_types_query.filter(tw_line_item_id__in=self.line_item_id)
        prediction_time = now + datetime.timedelta(hours=1)
        time_data = {
            'weekday': prediction_time.isoweekday(),
            'weekend': prediction_time.isoweekday() > 5,
            'day': prediction_time.day,
            'month': prediction_time.month,
            'hour': prediction_time.hour
        }
        for opt_type, opt_value in set(opt_types_query):
            stats = {}
            for interval in self.STATS_INTERVALS:
                utcnow = datetime.datetime.utcnow()
                stats[interval.name] = self.get_campaign_interval_stats(tw_campaign_id, opt_type, now, interval)
                if interval.alias:
                    stats[interval.alias] = stats[interval.name]
                logger.debug('%s tw_account_id: %s tw_campaign_id: %s fetched %s stats for %s: %d ad groups %.2fs',
                             self.name, tw_account_id, tw_campaign_id, interval.name, opt_type,
                             len(stats[interval.name]), (datetime.datetime.utcnow() - utcnow).total_seconds())
            tw_line_items_query = TwitterRevmap.TwitterRevmap.objects_raw.filter(
                tw_campaign_id=tw_campaign_id,
                opt_type=opt_type,
                tw_campaign_id__status=choices.STATUS_ENABLED,
                tw_line_item_id__status=choices.STATUS_ENABLED
            ).values_list('tw_line_item_id', flat=True)
            if self.line_item_id:
                tw_line_items_query = tw_line_items_query.filter(tw_line_item_id__in=self.line_item_id)
            for tw_line_item_id in tw_line_items_query:
                tw_line_item_targeting_query = TwitterTargetingModels.TwitterTargeting.objects_raw.filter(
                    tw_line_item_id=tw_line_item_id
                ).values_list(
                    'name',
                    'tw_targeting_type',
                    'tw_targeting_id',
                    'targeting_value'
                )
                row = {}
                row.update(time_data)
                for interval, alias in (('12_hours', '12_hours'), ('24_hours', '24_hours'), ('168_hours', '7_days')):
                    if not stats.get(interval) or not stats[interval].get(tw_line_item_id):
                        row[alias + '_click'] = row[alias + '_install'] = 0.0
                    else:
                        for k in ('click', 'install'):
                            row[alias + '_' + k] = stats[interval][tw_line_item_id].get(k, 0.0)
                js = json.dumps(row)
                for name, tw_targeting_type, tw_targeting_id, targeting_value in tw_line_item_targeting_query:
                    tw_targeting_type_name = TwitterConfig.TW_TARGETING_ID_TO_ENUM[tw_targeting_type]
                    targeting = unicode('{}:{}'.format(tw_targeting_type_name, targeting_value or tw_targeting_id))
                    row[targeting.encode('utf-8')] = 1
                click, install = self.tree.predict(self.vector.transform(row))[0]
                ir = install / click if click != 0 else 0.0
                bid = int(math.ceil(ir * opt_value * 10 ** 6 / 10 ** 4)) * 10 ** 4
                logger.debug('%s tw_line_item_id: %s click: %f install: %f ir: %f bid: %f json: %s',
                             prediction_time.strftime('%Y-%m-%d %H'), tw_line_item_id, click, install, ir, bid, js)

    def run(self):
        queue_get_retries = QUEUE_GET_RETRIES
        try:
            while queue_get_retries:
                now, tw_account_id, tw_campaign_id = self.queue.get(timeout=QUEUE_GET_TIMEOUT)
                # After every successful queue get we should reset queue get retries.
                queue_get_retries = QUEUE_GET_RETRIES
                logger.debug('%s optimizing tw_account_id: %s tw_campaign_id: %s', self.name, tw_account_id,
                             tw_campaign_id)
                self.optimize_campaign(now, tw_account_id, tw_campaign_id)
                self.queue.task_done()
        except Queue.Empty:
            queue_get_retries -= 1


class TwitterAccountOptimizer(multiprocessing.Process):
    """Worker that optimizes Twitter account."""

    def __init__(self, queue, optimize, campaign_id, tw_campaign_id, line_item_id, optimize_line_item_id, tree_filename,
                 vector_filename, *args, **kwargs):
        super(TwitterAccountOptimizer, self).__init__(*args, **kwargs)
        self.queue = queue
        self.optimize = optimize
        self.campaign_id = campaign_id
        self.tw_campaign_id = tw_campaign_id
        self.line_item_id = line_item_id
        self.optimize_line_item_id = optimize_line_item_id
        self.tree_filename = tree_filename
        self.vector_filename = vector_filename

    def optimize_advertiser(self, now, tw_account_id):
        """Starts thread workers to optimize campaigns of advertiser with a given id.

        :param now: timestamp when optimization started.
        :param tw_account_id: Twitter account id.
        """
        tw_campaigns_ids_query = TwitterLineItem.TwitterLineItem.objects_raw.order_by().distinct().filter(
            tw_campaign_id__tw_account_id=tw_account_id,
            status=choices.STATUS_ENABLED
        ).values_list(
            'tw_campaign_id',
            flat=True
        )
        if self.campaign_id:
            tw_campaigns_ids_query = tw_campaigns_ids_query.filter(tw_campaign_id__campaign_id__in=self.campaign_id)
        if self.tw_campaign_id:
            tw_campaigns_ids_query = tw_campaigns_ids_query.filter(tw_campaign_id__in=self.tw_campaign_id)
        if self.line_item_id:
            tw_campaigns_ids_query = tw_campaigns_ids_query.filter(tw_line_item_id__in=self.line_item_id)
        tw_campaigns_count = tw_campaigns_ids_query.count()
        if not tw_campaigns_count:
            return

        logger.debug('%s optimizing %d campaigns of tw_account_id: %s', self.name, tw_campaigns_count, tw_account_id)
        queue = Queue.Queue()
        threads = []
        for i in xrange(min(2 * multiprocessing.cpu_count(), tw_campaigns_count)):
            thread = TwitterCampaignOptimizer(
                queue,
                self.optimize,
                self.line_item_id,
                self.optimize_line_item_id,
                self.tree_filename,
                self.vector_filename,
                name='{}-t{}'.format(self.name, i + 1)
            )
            thread.daemon = True
            thread.start()
            threads.append(thread)

        for tw_campaign_id in tw_campaigns_ids_query:
            queue.put((now, tw_account_id, tw_campaign_id))

        for thread in threads:
            thread.join()

    def run(self):
        queue_get_retries = QUEUE_GET_RETRIES
        try:
            while queue_get_retries:
                now, tw_account_id = self.queue.get(timeout=QUEUE_GET_TIMEOUT)
                # After every successful queue get we should reset queue get retries.
                queue_get_retries = QUEUE_GET_RETRIES
                self.optimize_advertiser(now, tw_account_id)
                self.queue.task_done()
        except Queue.Empty:
            queue_get_retries -= 1


class Command(management_base.BaseCommand):
    help = 'Optimizes facebook ads.'
    option_list = management_base.BaseCommand.option_list + (
        optparse.make_option(
            '--workers',
            dest='workers',
            type=int,
            help='Number of workers to use. Default value is min(2 * <# of CPU cores>, # of advertiser / 2).'
        ),
        optparse.make_option(
            '--account-id',
            action='append',
            dest='tw_account_id',
            type=int,
            help='Twitter account id.'
        ),
        optparse.make_option(
            '--tw-campaign-id',
            action='append',
            dest='tw_campaign_id',
            type=int,
            help='Twitter campaign id.'
        ),
        optparse.make_option(
            '--campaign-id',
            action='append',
            dest='campaign_id',
            type=int,
            help='Campaign id.'
        ),
        optparse.make_option(
            '--line-item-id',
            action='append',
            dest='tw_line_item_id',
            type=int,
            help='Twitter line item id.'
        ),
        optparse.make_option(
            '--optimize-line-item-id',
            action='append',
            dest='optimize_line_item_id',
            type=int,
            help='Twitter line item id to optimize.'
        ),
        optparse.make_option(
            '-o', '--optimize',
            action='store_true',
            dest='optimize',
            default=False,
            help='Enable auto optimization.'
        ),
        optparse.make_option(
            '-f', '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Forces optimization even if database was not synced recently.'
        ),
        optparse.make_option('-t', '--tree', dest='tree', type=str),
        optparse.make_option('--vector', dest='vector', type=str)
    )

    def handle(self, *args, **options):
        if not options.get('tree'):
            raise management_base.CommandError('--tree is required')
        if not os.path.exists(options['tree']):
            raise management_base.CommandError('File %s does not exist' % options['tree'])
        if not options.get('vector'):
            raise management_base.CommandError('--vector is required')
        if not os.path.exists(options['vector']):
            raise management_base.CommandError('File %s does not exist' % options['vector'])
        force = options.get('force')
        job_status = None
        try:
            job_status = JobStatus.JobStatus.objects.get(job_type=JobStatus.TWITTER, job_name=SYNC_DATABASE_JOB)
        except JobStatus.JobStatus.DoesNotExist:
            logger.warn('Job status for %s:%s does not exist', JobStatus.TWITTER, SYNC_DATABASE_JOB)
            if not force:
                return
        now = timezone.localtime(timezone.now())
        # if job_status and not force and job_status.last_finished + datetime.timedelta(hours=STATS_LATENCY) >= now:
        #     # NOTE: If stats were synced more than STATS_LATENCY hours ago we should not optimize unless force is not
        #     # given.
        #     logger.warn('Stats where synced more than %s hours ago', STATS_LATENCY)
        #     return
        optimize = options.get('optimize') or False
        tw_account_id = options.get('tw_account_id') or []
        tw_campaign_id = options.get('tw_campaign_id') or []
        campaign_id = options.get('campaign_id') or []
        tw_line_item_id = options.get('tw_line_item_id') or []
        optimize_line_item_id = frozenset(options.get('optimize_line_item_id') or []) or TW_AUTO_OPTIMIZE_LINE_ITEMS
        tw_account_id_query = TwitterLineItem.TwitterLineItem.objects_raw.order_by().distinct().filter(
            status=choices.STATUS_ENABLED,
            tw_campaign_id__status=choices.STATUS_ENABLED,
            tw_campaign_id__tw_account_id__status=choices.STATUS_ENABLED
        ).values_list('tw_campaign_id__tw_account_id', flat=True)
        if tw_campaign_id:
            tw_account_id_query = tw_account_id_query.filter(tw_campaign_id__in=tw_campaign_id)
        if tw_account_id:
            tw_account_id_query = tw_account_id_query.filter(tw_campaign_id__tw_account_id__in=tw_account_id)
        if tw_line_item_id:
            tw_account_id_query = tw_account_id_query.filter(tw_line_item_id__in=tw_line_item_id)
        if campaign_id:
            tw_account_id_query = tw_account_id_query.filter(tw_campaign_id__campaign_id__in=campaign_id)
        advertisers_count = tw_account_id_query.count()
        if not advertisers_count:
            return
        workers_count = min(options.get('workers') or 2 * multiprocessing.cpu_count(), advertisers_count or 1)
        logger.debug('Using %d workers to process %d advertisers', workers_count, advertisers_count)

        queue = multiprocessing.JoinableQueue(maxsize=workers_count)

        workers = []
        for i in xrange(workers_count):
            worker = TwitterAccountOptimizer(
                queue,
                optimize,
                campaign_id,
                tw_campaign_id,
                tw_line_item_id,
                optimize_line_item_id,
                tree_filename=options['tree'],
                vector_filename=options['vector'],
                name='worker-{}'.format(i + 1)
            )
            workers.append(worker)
            worker.start()

        for tw_account_id in tw_account_id_query:
            queue.put((now, tw_account_id), block=False)

        queue.close()

        try:
            for worker in workers:
                worker.join()
                # logger.debug('optimisation took %.2f s', (timezone.now().replace(tzinfo=None) - now).total_seconds())
        except KeyboardInterrupt:
            logger.debug('Received keyboard interrupt')
            for worker in workers:
                worker.shutdown = True
