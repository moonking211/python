import sys
import json
import argparse
import pandas as pd
import _mysql_exceptions
from itertools import groupby
from datetime import *
from optparse import make_option

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.utils import OperationalError
from django.db import connections
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError

from restapi.models.choices import CREATIVE_PRUNING_STATUS_CHOICES
from restapi.models.Ad import Ad
from restapi.models.CreativePruning import CreativePruning

class Command(BaseCommand):

    debug = False
    config = {}
    config['monarch_stats_db'] = 'monarch_stats'
    cursor_app_db = connections['app_db'].cursor()

    option_list = BaseCommand.option_list  + (
                        make_option('--start_date',
                            dest='start_date',
                            default="",
                            help='Start Date (default: + 60 days)'),
                        make_option('--end_date',
                            dest='end_date',
                            default="",
                            help='Start Date (default: yesterday)'),
                        make_option('--start',
                            dest='start_date',
                            default="",
                            help='Start Date (default: + 60 days)'),
                        make_option('--end',
                            dest='end_date',
                            default="",
                            help='Start Date (default: yesterday)'),
                        make_option('--days',
                            dest='days',
                            default="",
                            help='Days Back (default: 60)'),
                        make_option('--debug', action='store_true',
                            dest='debug',
                            default=False,
                            help=''),
                        )

    def handle(self, *args, **options):
        settings.SYSTEM_USER = True
        start_time = datetime.utcnow()

        days = 60
        if 'days' in options and options['days'] != "":
            days = int(float(options['days']))

        self.config['start_date']       = self.add_to_date(self.yesterday(), - days)
        self.config['end_date']         = self.yesterday()

        if 'start_date' in options and options['start_date'] != "":
            self.config['start_date'] = options['start_date']
        elif 'start' in options and options['start'] != "":
            self.config['start_date'] = options['start']

        if 'end_date' in options and options['start_date'] != "":
            self.config['end_date'] = options['end_date']
        elif 'end' in options and options['end'] != "":
            self.config['end_date'] = options['end']

        self._log("Fetching Ads from: %s to %s" % (self.config['start_date'], self.config['end_date']))

        last_day_dk                     = self.get_dk(self.config['end_date'])
        table_suffix                    = last_day_dk

        self.config['ads_table']        = 'all_ads_%s' % (table_suffix)
        self.config['ag_size_table']    = 'ag_size_stats_%s' % (table_suffix)
        self.config['ads_ranked_table'] = 'ads_ranked_%s' % (table_suffix)
        self.config['ads_delete_table'] = 'ads_delete_%s' % (table_suffix)
        self.config['ads_pause_table']  = 'ads_pause_%s' % (table_suffix)

        if 'debug' in options:
            debug = options['debug']

        try:
            self.delete_temp_tables()
        except _mysql_exceptions.Warning, e:
            pass

        if self.get_ad_data():
            self._log("====================> Fetching Ads ====================")

            if self.get_ad_group_by_size():
                self._log("====================> Fetching Ad Group by Size ====================")

                if self.load_dataframe():
                    self._log("====================> Adding ads to Pause ====================")
                    self.filter_ads_to_pause()
                    self._log("====================> Adding ads to Delete ====================")
                    self.filter_ads_to_delete()

                try:
                    self.delete_temp_tables()
                    self.update_job_status()
                except _mysql_exceptions.Warning, e:
                    pass


        end_time = datetime.utcnow()
        self._log('Script Duration: {}'.format(end_time - start_time))

    def today(self):
        return date.today().isoformat()

    def yesterday(self):
        return self.add_to_date(self.today(),-1)

    def str_to_date(self, date_string):
        return datetime.strptime(date_string, '%Y-%m-%d').date()

    def add_to_date(self, date_string, increment):
        return (self.str_to_date(date_string) + timedelta(increment)).isoformat()

    # Returns array ref of all dates from $start to $end inclusive
    def get_dates(self, start, end):
        date_array = []
        current = start

        while( current <= end ):
            date_array.append(current)
            current = self.add_to_date( current, 1 )

        return date_array

    def get_dk( self, date_string ):
        return date_string.replace( '-', '' )

    def _log(self, s):
        print datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(s)

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def get_ad_data(self):
        start_date = self.config['start_date']
        end_date   = self.config['end_date']

        try:
            query = """
                CREATE TABLE %s.%s (index (ad_id)) as
                SELECT
                    c.campaign_id,
                    c.campaign,
                    ag.ad_group,
                    ad.size,
                    t.ad_id,
                    ad.ad,
                    ad.ad_group_id,
                    ad.ad_type,

                    SUM(ibid) ibid,
                    SUM(impression) impression,
                    ROUND(SUM(impression)/SUM(ibid),4) win_rate,

                    SUM(click) click,
                    ROUND(SUM(click)/SUM(impression),4) ctr,

                    SUM(install) install,
                    ROUND(SUM(install)/SUM(click),4) ir,
                    ROUND(SUM(install)/SUM(impression)*1000, 2) ipm,

                    ROUND(SUM(cost)/SUM(impression)*1000, 4) cpm,
                    ROUND(SUM(revenue)/SUM(impression)*1000, 4) rpm,
                    ROUND(SUM(revenue-cost)/SUM(impression)*1000, 4) ppm,

                    ROUND(SUM(cost)/SUM(install), 2) cpi,
                    ROUND(SUM(revenue)/SUM(install), 2) rpi,

                    ROUND(SUM(cost),4) cost,
                    ROUND(SUM(revenue),4) revenue,
                    ROUND(SUM(revenue)-SUM(cost),4) profit,
                    ROUND((SUM(revenue)-SUM(cost))/SUM(revenue),4) margin,

                    MIN(date) first_activity,
                    MAX(date) last_activity,
                    COUNT(DISTINCT date) days,

                    COUNT(DISTINCT IF(impression > 0, date, null)) days_w_impression,
                    MAX(CASE WHEN ad.status != 'enabled' THEN CONCAT('ad-', ad.status) WHEN ag.status != 'enabled' THEN CONCAT('ag-', ag.status) WHEN c.status != 'enabled' THEN CONCAT('c-', c.status) ELSE 'live' END) status

                FROM
                    stats.a_ad_by_country_daily t
                INNER JOIN
                    stats.ad
                ON
                    ad.ad_id = t.ad_id
                INNER JOIN
                    stats.ad_group ag
                ON
                    ad.ad_group_id = ag.ad_group_id
                INNER JOIN
                    stats.campaign c
                ON
                    ag.campaign_id = c.campaign_id
                WHERE
                    t.source_id != 0
                    AND
                    date BETWEEN '%s' AND '%s'
                GROUP BY
                    t.ad_id, ad.ad_group_id, ag.campaign_id
                HAVING
                    status = 'live'
            """ % (self.config['monarch_stats_db'], self.config['ads_table'], self.config['start_date'], self.config['end_date'])

            self._log(query)
            self.cursor_app_db.execute(query)
            return True

        except _mysql_exceptions.Warning, e:
            self._log(e)
            return True

        except OperationalError, e:
            self._log(e)
            return False

    def get_ad_group_by_size(self):
        start_date = self.config['start_date']
        end_date   = self.config['end_date']

        try:
            query = """
                CREATE table %s.%s
                SELECT
                    campaign,
                    ad_group_id,
                    size,
                    COUNT(*) ads,
                    SUM(install)/SUM(impression) * 1000 ipm,
                    LOG(0.01)/LOG(1-SUM(install)/SUM(impression)) ss_1,
                    LOG(0.05)/LOG(1-SUM(install)/SUM(impression)) ss_5,

                    SUM(impression) impression,

                    SUM(click) click,
                    SUM(install) install,
                    SUM(cost) cost,
                    SUM(revenue) revenue,

                    SUM(cost)/SUM(impression) * 1000 cpm,
                    SUM(revenue)/SUM(impression) * 1000 rpm,

                    SUM(cost)/SUM(install) cpi,
                    SUM(revenue)/SUM(install) rpi,

                    LOG(0.01)/LOG(1-SUM(install)/SUM(impression))*SUM(cost)/SUM(impression) ss_1_cost,
                    LOG(0.05)/LOG(1-SUM(install)/SUM(impression))*SUM(cost)/SUM(impression) ss_5_cost

                FROM %s.%s
                GROUP BY
                    ad_group_id, size
                """ % (self.config['monarch_stats_db'], self.config['ag_size_table'], self.config['monarch_stats_db'], self.config['ads_table'])

            self._log(query)
            self.cursor_app_db.execute(query)
            return True

        except _mysql_exceptions.Warning, e:
            self._log(e)
            return True

        except OperationalError, e:
            self._log(e)
            return False

    def load_dataframe(self):
        try:
            query = """
                SELECT * FROM %s.%s
                """ % (self.config['monarch_stats_db'], self.config['ads_table'])

            self._log(query)

            self.cursor_app_db.execute(query)
            ads = pd.read_sql(query, con=connections['app_db'])

            to_rank = ['install', 'ir', 'rpm', 'ctr', 'ibid', 'ipm', 'revenue', 'profit', 'impression']

            for field in to_rank:
                ads[str(field + '_rank')] = ads.groupby(['campaign_id', 'ad_group', 'size'])[field].rank(method='first', ascending=False)

            self.cursor_app_db.execute('use %s' % (self.config['monarch_stats_db']))
            ads.to_sql(con=connections['app_db'], name=self.config['ads_ranked_table'], if_exists='replace', flavor='mysql', index=False)

            return True

        except _mysql_exceptions.Warning, e:
            self._log(e)
            return True

        except OperationalError, e:
            self._log(e)
            return False

    def filter_ads_to_delete(self):
        try:
            query = """
            SELECT
                    a.ad_id,
                    a.ibid,
                    a.impression,
                    a.win_rate,
                    a.click,
                    a.ctr,
                    a.install,
                    a.ir,
                    a.ipm,
                    a.rpm,
                    a.ppm,
                    a.cpi,
                    a.rpi,
                    a.cost,
                    a.revenue,
                    a.profit,
                    a.margin,
                    a.status,
                    a.install_rank,
                    a.ir_rank,
                    a.rpm_rank,
                    a.ctr_rank,
                    a.ibid_rank,
                    a.ipm_rank,
                    a.revenue_rank,
                    a.profit_rank,
                    a.impression_rank,
                    a.days,
                    a.days_w_impression
                FROM
                    %s.%s a
                LEFT JOIN
                    %s.%s s
                ON
                    a.ad_group_id = s.ad_group_id
                AND
                    a.size = s.size
                WHERE
                    a.impression > s.ss_1
                AND
                    a.install_rank > 2
                AND
                    a.ipm_rank > 3
            """ % (self.config['monarch_stats_db'], self.config['ads_ranked_table'], self.config['monarch_stats_db'], self.config['ag_size_table'])

            self._log(query)
            self.cursor_app_db.execute(query)
            data = self.dictfetchall(self.cursor_app_db)
            reason = "install_rank > 2, ipm_rank > 3"

            for ad_data in data:
                try:
                    ad = Ad.objects_raw.get(ad_id=ad_data['ad_id'])
                    ad_data['action'] = "delete"
                    self._log(json.dumps(ad_data))
                    del ad_data['ad_id']

                    try:
                        ad_creative = CreativePruning.objects_raw.get(ad_id=ad)
                        ad_creative.last_update = timezone.now()
                        ad_creative.__dict__.update(**ad_data)
                        ad_creative.save_raw()

                    except CreativePruning.DoesNotExist:
                        ad_creative = CreativePruning.objects_raw.create(ad_id=ad, **ad_data)

                except Ad.DoesNotExist:
                    continue

            return True

        except _mysql_exceptions.Warning, e:
            self._log(e)
            return True

        except OperationalError, e:
            self._log(e)
            return False

    def filter_ads_to_pause(self):
        try:
            query = """
            SELECT
                    ad_id,
                    ibid,
                    impression,
                    win_rate,
                    click,
                    ctr,
                    install,
                    ir,
                    ipm,
                    rpm,
                    ppm,
                    cpi,
                    rpi,
                    cost,
                    revenue,
                    profit,
                    margin,
                    status,
                    install_rank,
                    ir_rank,
                    rpm_rank,
                    ctr_rank,
                    ibid_rank,
                    ipm_rank,
                    revenue_rank,
                    profit_rank,
                    impression_rank,
                    a.days,
                    a.days_w_impression
                FROM
                    %s.%s a
                WHERE
                    a.ipm_rank > 1
                AND
                    a.install_rank > 2
                AND
                    a.impression_rank > 5
                """ % (self.config['monarch_stats_db'], self.config['ads_ranked_table'])

            self._log(query)
            self.cursor_app_db.execute(query)
            data = self.dictfetchall(self.cursor_app_db)
            reason = "ipm_rank > 1, install_rank > 2, impression_rank > 5"

            for ad_data in data:
                try:
                    ad = Ad.objects_raw.get(ad_id=ad_data['ad_id'])
                    ad_data['action'] = "pause"
                    self._log(json.dumps(ad_data))
                    del ad_data['ad_id']

                    try:
                        ad_creative = CreativePruning.objects_raw.get(ad_id=ad)
                        ad_creative.last_update = timezone.now()
                        ad_creative.__dict__.update(**ad_data)
                        ad_creative.save_raw()

                    except CreativePruning.DoesNotExist:
                        ad_creative = CreativePruning.objects_raw.create(ad_id=ad, **ad_data)

                except Ad.DoesNotExist:
                    continue

            return True

        except _mysql_exceptions.Warning, e:
            self._log(e)
            return True

        except OperationalError, e:
            self._log(e)
            return False

    def update_job_status(self):
        sql = "REPLACE INTO job_status SET job_name='creative_pruning', job_type='rtb', last_finished=NOW(), threshold=1440"
        cursor = connections['default'].cursor()
        try:
            cursor.execute(sql)
        except:
            return False
        finally:
            cursor.close()
            return True

    def delete_temp_tables(self):
        self._log("Deleting tables %s, %s, %s" % (self.config['ads_table'], self.config['ag_size_table'], self.config['ads_ranked_table']))
        self.cursor_app_db.execute('DROP TABLE IF EXISTS %s.%s' % (self.config['monarch_stats_db'], self.config['ads_table']))
        self.cursor_app_db.execute('DROP TABLE IF EXISTS %s.%s' % (self.config['monarch_stats_db'], self.config['ag_size_table']))
        self.cursor_app_db.execute('DROP TABLE IF EXISTS %s.%s' % (self.config['monarch_stats_db'], self.config['ads_ranked_table']))
