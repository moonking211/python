# encoding: utf-8

from __future__ import unicode_literals

import datetime
import logging
import multiprocessing
import optparse
import Queue
import threading
import six

from django.conf import settings
from django.utils import timezone
from django.db import connections
from django.core.management import base as management_base

from restapi.models import choices
from restapi.models import JobStatus
from restapi.models.twitter import TwitterLineItem
from restapi.models.twitter import TwitterRevmap

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


class TwitterLineItemOptimiser(object):
    MAX_CPC_BID = 3000000
    MIN_CPC_BID = 100000

    stats_template = ', '.join([
        'CPCBid=${bid:.2f}',
        'Clicks={7_days[click]:.0f}',
        'Installs={7_days[install]:.0f}',
        'MCost=${7_days[mcost]:.2f}',
        'Rev=${7_days[rev]:.2f}',
        'IR={7_days[ir]:.2f}',
        'CPC=${7_days[cpc]:.2f}',
        'CPI=${7_days[cpi]:.2f}',
        'CPIgoal=${7_days[opt_value]:.2f}',
        '%Goal={7_days[goal]:.2f}'
    ])

    action_templates = {
        'pause': 'Pausing line_item {tw_line_item_id}.',
        'boost': 'Boosting line_item {tw_line_item_id} by 1.1 to ${new_bid:.2f}.',
        'skip': 'Skipping line_item {tw_line_item_id}.',
        'deflate': 'Deflating line_item {tw_line_item_id} by 0.8 to ${new_bid:.2f}.',
        'recommend': 'Recommending line_item {tw_line_item_id} bid ${new_bid:.2f}.'
    }

    def __init__(self, update_bid, name, tw_account_id, tw_campaign_id, tw_line_item_id, opt_type, bid, stats):
        self.update_bid = update_bid
        self._data = {
            'name': name,
            'tw_account_id': tw_account_id,
            'tw_campaign_id': tw_campaign_id,
            'tw_line_item_id': tw_line_item_id,
            'opt_type': opt_type,
            'bid': bid,
            'MIN_INSTALLS': MIN_INSTALLS,
            'MIN_SPEND': MIN_SPEND
        }
        for key, value in six.iteritems(stats):
            self._data[key] = value.get(tw_line_item_id) or _get_zero_stats()
        self._action = self._reason = None

    def __getitem__(self, key):
        result = self._data
        for part in key.split('.'):
            result = (result or {}).get(part)
        return result

    def _update(self, action, reason):
        self._data.update({
            'action': self.action_templates[action].format(**self._data),
            'reason': reason.format(**self._data)
        })

    def pause(self, reason):
        """Pauses line item by setting bid to 10k ($0.01).

        :param reason: reason for pausing line item.
        """
        # Bid $0.01 CPC to effectively pause the line item
        self._data['new_bid'] = 10000
        self._update('pause', reason)

    def boost(self, reason):
        """Boosts line item by increasing bid by 10%.

        :param reason: reason for boosting line item.
        """
        self._data['new_bid'] = normalize_bid(round10k(1.1 * self._data['bid']))
        self._update('boost', reason)

    def skip(self, reason):
        """Skips line item.

        :param reason: reason for skipping line item.
        """
        self._update('skip', reason)

    def deflate(self, reason):
        """Deflate line item.

        :param reason: reason for deflating line item.
        """
        self._data['new_bid'] = normalize_bid(round10k(0.8 * self._data['bid']))
        self._update('deflate', reason)

    def recommend(self, reason):
        """Recommendation for line item.

        :param reason: reason for recommendation.
        """
        if self['M.install'] >= MIN_INSTALLS:
            self._data['ir'], self._data['ir_interval'] = self['M.ir'], '1D'
        else:
            self._data['ir'], self._data['ir_interval'] = self['L.ir'], '7D'
        self._data['new_bid'] = normalize_bid(round10k(self['L.opt_value'] * self._data['ir'] * 1000000))
        self._update('recommend', reason)

    @property
    def update_kwargs(self):
        kwargs = {
            'bid_amount_computed_reason': 'ACTION: {action} REASON: {reason} 7D STATS: {stats}'.format(
                action=self._data['action'],
                reason=self._data['reason'],
                stats=self.stats_template.format(**self._data)
            )
        }
        if 'new_bid' in self._data:
            kwargs['bid_amount_computed'] = self._data['new_bid']
        return kwargs

    def optimize(self):
        # Pause if %Goal(1D) < 0.25 AND mcost(1D) > $20
        if self['M'] and self['M.goal'] < 0.25 and self['M.mcost'] > 20:
            self.pause('Goal(1D) {M[goal]:.2f} < 0.25 and mcost ${M[mcost]:.2f} > $20.')
        # Boost if mcost(2H) < $MIN_SPEND
        elif not self['S'] or self['S.mcost'] < MIN_SPEND:
            self.boost('mcost(2H) $%.2f < ${MIN_SPEND}.' % (self['S.mcost'] or 0.0))
        # Skip if installs(7D) < MIN_INSTALLS
        elif self['L.install'] < MIN_INSTALLS:
            self.skip('{L[install]:.0f} installs < {MIN_INSTALLS} min installs.')
        # If %Goal(2H) < 0.25
        elif self['S'] and self['S.goal'] < 0.25:
            self.deflate('Goal(2H) {S[goal]:.2f} < 0.25.')
        else:
            self.recommend('Opt_value ${L[opt_value]:.2f} * IR({ir_interval}) %{ir:.2f}.')

        TwitterLineItem.TwitterLineItem.objects_raw.filter(
            tw_line_item_id=self._data['tw_line_item_id']
        ).update(**self.update_kwargs)

        logger.debug('%(name)s tw_account_id: %(tw_account_id)s tw_campaign_id: %(tw_campaign_id)s tw_line_item_id: '
                     '%(tw_line_item_id)s ACTION: %(action)s REASON: %(reason)s', self._data)
        if self.update_bid and 'new_bid' in self._data and self._data['bid'] != self._data['new_bid']:
            response = TwitterLineItem.TwitterLineItem.update({
                'account_id': self._data['tw_account_id'],
                'line_item_id': self._data['tw_line_item_id'],
                'bid_amount_local_micro': self._data['new_bid']
            })
            if not response.get('success'):
                logger.error('%s tw_account_id: %s tw_campaign_id: %s tw_line_item_id: %s bid update failed: %s',
                             self._data['name'], self._data['tw_account_id'], self._data['tw_campaign_id'],
                             self._data['tw_line_item_id'], response['message'])


class TwitterCampaignOptimizer(threading.Thread):
    RATE_EVENT = 'click'
    DEFAULT_EVENTS = frozenset(('click',))
    STATS_INTERVALS = (
        (Days(7, 'L'), TimeBucket),
        (Hours(24, 'M'), TimeBucket),
        (Hours(12, 'S'), None)
    )
    MIN_FOR_OPT_TYPE = {'install': 3}

    def __init__(self, queue, optimize, line_item_id, optimize_line_item_id, *args, **kwargs):
        super(TwitterCampaignOptimizer, self).__init__(*args, **kwargs)
        self.queue = queue
        self.optimize = optimize
        self.line_item_id = line_item_id
        self.optimize_line_item_id = optimize_line_item_id

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
        ).values_list('opt_type', flat=True)
        if self.line_item_id:
            opt_types_query = opt_types_query.filter(tw_line_item_id__in=self.line_item_id)
        for opt_type in set(opt_types_query):
            stats = {}
            for interval, time_bucket_factory in self.STATS_INTERVALS:
                utcnow = datetime.datetime.utcnow()
                stats[interval.name] = self.get_campaign_interval_stats(tw_campaign_id, opt_type, now, interval)
                if interval.alias:
                    stats[interval.alias] = stats[interval.name]
                logger.debug('%s tw_account_id: %s tw_campaign_id: %s fetched %s stats for %s: %d ad groups %.2fs',
                             self.name, tw_account_id, tw_campaign_id, interval.name, opt_type,
                             len(stats[interval.name]), (datetime.datetime.utcnow() - utcnow).total_seconds())

                if not time_bucket_factory:
                    continue

                time_bucket = time_bucket_factory()
                utcnow = datetime.datetime.utcnow()
                time_bucket_stats = self.get_campaign_interval_stats(tw_campaign_id, opt_type, now, interval,
                                                                     time_bucket=time_bucket)
                logger.debug('%s tw_account_id: %s tw_campaign_id: %s fetched %s stats (time bucket %s) for %s: %d '
                             'ad groups %.2fs', self.name, tw_account_id, tw_campaign_id, interval.name,
                             time_bucket.name, opt_type, len(stats[interval.name]),
                             (datetime.datetime.utcnow() - utcnow).total_seconds())
                for tw_line_item_id, row in six.iteritems(time_bucket_stats):
                    if row[opt_type] > self.MIN_FOR_OPT_TYPE[opt_type]:
                        property_name = '%sr' % opt_type.lower()[0]
                        logger.info(
                            '%(name)s tw_account_id: %(tw_account_id)s tw_campaign_id: %(tw_campaign_id)s '
                            'overriding %(stats_value)s %(property_name)s stats with %(filtered_value)s filtered '
                            '%(property_name)s stats',
                            {
                                'name': self.name,
                                'tw_account_id': tw_account_id,
                                'tw_campaign_id': tw_campaign_id,
                                'stats_value': stats.get(tw_line_item_id, {}).get(property_name),
                                'property_name': property_name.upper(),
                                'filtered_value': row[property_name]
                            }
                        )
                        stats[interval.name][tw_line_item_id][property_name] = row[property_name]

            tw_line_items_query = TwitterRevmap.TwitterRevmap.objects_raw.filter(
                tw_campaign_id=tw_campaign_id,
                opt_type=opt_type,
                tw_line_item_id__status=choices.STATUS_ENABLED
            ).values_list(
                'tw_line_item_id',
                'tw_line_item_id__bid_amount_local_micro'
            )
            if self.line_item_id:
                tw_line_items_query = tw_line_items_query.filter(tw_line_item_id__in=self.line_item_id)
            for tw_line_item_id, bid_amount_local_micro in tw_line_items_query:
                TwitterLineItemOptimiser(
                    self.optimize and any([
                        not self.optimize_line_item_id,
                        tw_line_item_id in self.optimize_line_item_id
                    ]),
                    self.name,
                    tw_account_id,
                    tw_campaign_id,
                    tw_line_item_id,
                    opt_type,
                    bid_amount_local_micro,
                    stats
                ).optimize()

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

    def __init__(self, queue, optimize, campaign_id, line_item_id, optimize_line_item_id, *args, **kwargs):
        super(TwitterAccountOptimizer, self).__init__(*args, **kwargs)
        self.queue = queue
        self.optimize = optimize
        self.campaign_id = campaign_id
        self.line_item_id = line_item_id
        self.optimize_line_item_id = optimize_line_item_id

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
            tw_campaigns_ids_query = tw_campaigns_ids_query.filter(tw_campaign_id__in=self.campaign_id)
        if self.line_item_id:
            tw_campaigns_ids_query = tw_campaigns_ids_query.filter(tw_line_item_id__in=self.line_item_id)
        tw_campaigns_count = tw_campaigns_ids_query.count()
        if not tw_campaigns_count:
            return

        logger.debug('%s optimizing %d campaigns of tw_account_id: %s', self.name, tw_campaigns_count, tw_account_id)
        queue = Queue.Queue()
        threads = []
        for i in xrange(min(2 * multiprocessing.cpu_count(), tw_campaigns_count)):
            thread = TwitterCampaignOptimizer(queue, self.optimize, self.line_item_id, self.optimize_line_item_id,
                                              name='{}-t{}'.format(self.name, i + 1))
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
            dest='account_id',
            type=int,
            help='Twitter account id.'
        ),
        optparse.make_option(
            '--campaign-id',
            action='append',
            dest='campaign_id',
            type=int,
            help='Twitter campaign id.'
        ),
        optparse.make_option(
            '--line-item-id',
            action='append',
            dest='line_item_id',
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
        )
    )

    def handle(self, *args, **options):
        force = options.get('force')
        job_status = None
        try:
            job_status = JobStatus.JobStatus.objects.get(job_type=JobStatus.TWITTER, job_name=SYNC_DATABASE_JOB)
        except JobStatus.JobStatus.DoesNotExist:
            logger.warn('Job status for %s:%s does not exist', JobStatus.TWITTER, SYNC_DATABASE_JOB)
            if not force:
                return
        now = timezone.localtime(timezone.now())
        if job_status and not force and job_status.last_finished < now - datetime.timedelta(hours=STATS_LATENCY):
            # NOTE: If stats were synced more than STATS_LATENCY hours ago we should not optimize unless force is not
            # given.
            logger.warn('Stats where synced more than %s hours ago', STATS_LATENCY)
            return
        optimize = options.get('optimize') or False
        account_id = options.get('account_id') or []
        campaign_id = options.get('campaign_id') or []
        line_item_id = options.get('line_item_id') or []
        optimize_line_item_id = frozenset(options.get('optimize_line_item_id') or []) or TW_AUTO_OPTIMIZE_LINE_ITEMS
        tw_account_id_query = TwitterLineItem.TwitterLineItem.objects_raw.order_by().distinct().filter(
            status=choices.STATUS_ENABLED,
            tw_campaign_id__status=choices.STATUS_ENABLED,
            tw_campaign_id__tw_account_id__status=choices.STATUS_ENABLED
        ).values_list('tw_campaign_id__tw_account_id', flat=True)
        if campaign_id:
            tw_account_id_query = tw_account_id_query.filter(tw_campaign_id__in=campaign_id)
        if account_id:
            tw_account_id_query = tw_account_id_query.filter(tw_campaign_id__tw_account_id__in=account_id)
        if line_item_id:
            tw_account_id_query = tw_account_id_query.filter(tw_line_item_id__in=line_item_id)
        advertisers_count = tw_account_id_query.count()
        if not advertisers_count:
            return

        workers_count = min(options.get('workers') or 2 * multiprocessing.cpu_count(), advertisers_count or 1)
        logger.debug('Using %d workers to process %d advertisers', workers_count, advertisers_count)

        queue = multiprocessing.JoinableQueue(maxsize=workers_count)

        workers = []
        for i in xrange(workers_count):
            worker = TwitterAccountOptimizer(queue, optimize, campaign_id, line_item_id, optimize_line_item_id,
                                             name='worker-{}'.format(i + 1))
            workers.append(worker)
            worker.start()

        for tw_account_id in tw_account_id_query:
            queue.put((now, tw_account_id), block=False)

        queue.close()

        try:
            for worker in workers:
                worker.join()
            logger.debug('optimisation took %.2f s', (timezone.now() - now).total_seconds())
        except KeyboardInterrupt:
            logger.debug('Received keyboard interrupt')
            for worker in workers:
                worker.shutdown = True

        with connections['default'].cursor() as cursor:
            cursor.execute('''
                REPLACE INTO job_status
                SET
                    job_name='twitter_optimizer',
                    job_type='twitter',
                    last_finished=NOW(),
                    threshold=120
            ''')
