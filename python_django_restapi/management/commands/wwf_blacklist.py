import pyhs2
import sys
import simplejson
import argparse
import pickle
import datetime
from datetime import date
from optparse import make_option
from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError, IntegrityError
from django.core.management.base import BaseCommand, CommandError

from restapi.models.BidderBlacklist import BidderBlacklist
from restapi.models.BidderBlacklist import BidderBlacklistIds

# See https://managewiki.atlassian.net/browse/AMMYM-3343

class Command(BaseCommand):

    cursor_app_db = connections['app_db_ro'].cursor()

    debug = False

    option_list = BaseCommand.option_list  + (
                        make_option('--start_date',
                            dest='start_date',
                            default="",
                            help='Start Date (default: + 22 days)'),
                        make_option('--end_date',
                            dest='end_date',
                            default="",
                            help='Start Date (default: + 8 days)'),
                        make_option('--start',
                            dest='start_date',
                            default="",
                            help='Start Date (default: + 22 days)'),
                        make_option('--end',
                            dest='end_date',
                            default="",
                            help='Start Date (default: + 8 days)'),
                        make_option('--queue',
                            dest='queue',
                            choices=['p1', 'p2', 'p3'],
                            default='p2',
                            help='Queue'),
                        make_option('--debug', action='store_true',
                            dest='debug',
                            default=False,
                            help=''),
                        )

    def handle(self, *args, **options):
        settings.SYSTEM_USER = True

        start_date = self.add_to_date(self.today(), -22)
        end_date = self.add_to_date(self.today(), -8)
        yesterday = self.yesterday()

        if 'start_date' in options and options['start_date'] != "":
            start_date = options['start_date']
        elif 'start' in options and options['start'] != "":
            start_date = options['start']

        if 'end_date' in options and options['end_date'] != "":
            end_date = options['end_date']
        elif 'end' in options and options['end'] != "":
            end_date = options['end']

        print "%s to %s" % (start_date, end_date)

        if 'queue' in options:
            queue = options['queue']

        if 'debug' in options:
            self.debug = options['debug']

        data = self.get_wwf_data(start_date, end_date, yesterday)
        to_blacklist = self.get_wwf_blacklist(data, yesterday)

        try:
            for item in to_blacklist:
                try:
                    blacklist_entry = BidderBlacklistIds.objects_raw.get(campaign_id=item['campaign_id'], ad_group_id=item['ad_group_id'], source_id=item['source_id'], placement_id=item['placement_id'], size=item['size'])
                    print "Existing entry: " + simplejson.dumps(item)

                except TypeError:
                    pass
                except AttributeError:
                    pass
                except BidderBlacklistIds.DoesNotExist:
                    blacklist_entry = BidderBlacklistIds(campaign_id=item['campaign_id'], ad_group_id=item['ad_group_id'], source_id=item['source_id'], placement_id=item['placement_id'], size=item['size'])
                    print "Adding new entry: " + simplejson.dumps(item)

                blacklist_entry.tag = item['tag']
                blacklist_entry.placement_type = "app"
                blacklist_entry.save_raw();

        except IntegrityError:
            pass

        self.update_job_status()

    def today(self):
        return date.today().isoformat()

    def yesterday(self):
        return self.add_to_date(self.today(),-1)

    def str_to_date(self, date_string):
        return datetime.datetime.strptime(date_string, '%Y-%m-%d').date()

    def add_to_date(self, date_string, increment):
        return (self.str_to_date(date_string) + datetime.timedelta(increment)).isoformat()

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

    def get_month(self, date_string):
        return

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def get_wwf_data(self, start_date, end_date, runDate):
        data = []

        # check zynga_wwf_users are up to date
        self.cursor_app_db.execute("SELECT MAX(from_unixtime(install_time,'%Y-%m-%d')) FROM analytics.zynga_wwf_users")
        ans = self.cursor_app_db.fetchone()[0]

        if ans >= runDate:
            pass
        else:
            raise ValueError('analytics.zynga_wwf_users is not up to date')

        # check zynga_wwf_users are up to date
        self.cursor_app_db.execute("SELECT MAX(from_unixtime(install_time,'%Y-%m-%d')) FROM analytics.zynga_wwf_user_moves")
        ans = self.cursor_app_db.fetchone()[0]

        if ans == runDate:
            pass
        else:
            raise ValueError('analytics.zynga_wwf_user_moves is not up to date')

        query = """
            SELECT
              t.country country,
              t.platform platform,
              t.campaign_id campaign_id,
              t.ad_group_id ad_group_id,
              t.size size,
              MIN(placement) placement,
              t.placement_id placement_id,
              t.source_id source_id,
              SUM(impression) impression,
              SUM(click) click,
              SUM(install) install,
              SUM(revenue) revenue,
              SUM(cost) cost,
              SUM(profit) profit,
              SUM(D5) D5
            FROM (SELECT
                    country,
                    platform,
                    campaign_id campaign_id,
                    ad.ad_group_id ad_group_id,
                    ad.size size,
                    MIN(placement) placement,
                    placement_id placement_id,
                    source_id source_id,
                    SUM(ibid) ibid,
                    SUM(impression) impression,
                    SUM(click) click,
                    SUM(install) install,
                    SUM(cost) cost,
                    SUM(revenue) revenue,
                    SUM(revenue) - SUM(cost) profit
                FROM
                    stats.a_app_by_ad_daily t
                INNER JOIN stats.ad ad
                  ON ad.ad_id = t.ad_id
                WHERE
                    date BETWEEN '{0}' AND '{1}'
                AND
                    source_id != 0
                AND
                    campaign_id IN (155,156)
                GROUP BY
                    t.country,
                    campaign_id,
                    source_id,
                    placement_id,
                    ad.ad_group_id,
                    ad.size) t
                LEFT JOIN (
                    SELECT
                      ad.ad_group_id ad_group_id,
                      u.source_id source_id,
                      u.placement_id placement_id,
                      ad.size size,
                      u.campaign_id campaign_id,
                      u.country country,
                      u.platform platform,
                      SUM(m.d5_moves_played) D5
                    FROM analytics.zynga_wwf_users u
                    LEFT JOIN analytics.zynga_wwf_user_moves m ON (u.device_id = m.device_id AND u.device_id_type = m.device_id_type AND u.campaign_id = m.campaign_id)
                    LEFT JOIN stats.ad ad ON ad.ad_id = u.ad_id
                    WHERE
                        from_unixtime(u.install_time ,'%Y-%m-%d') BETWEEN '{0}' AND '{1}'
                    GROUP BY
                        u.source_id,
                        u.placement_id,
                        u.campaign_id,
                        ad.ad_group_id,
                        ad.size,
                        u.platform,
                        country
                  ) u ON u.source_id = t.source_id
                      AND u.placement_id = t.placement_id AND u.size = t.size
                      AND u.country = t.country AND u.ad_group_id = t.ad_group_id
                      AND t.campaign_id = u.campaign_id
                      AND t.platform = u.platform
                    GROUP BY
                    t.source_id,
                    t.placement_id,
                    t.campaign_id,
                    t.ad_group_id,
                    t.size,
                    t.platform,
                    t.country
        """.format(start_date,end_date)

        self.cursor_app_db.execute(query)
        data = self.dictfetchall(self.cursor_app_db)

        if self.debug:
            # Save data
            with open('wwf-placements.pickle', 'wb') as f:
                pickle.dump(data, f)

        return data

    def get_wwf_blacklist(self, data, runDate):

        blacklist = []
        for row in data:

            profit = 0 if row['profit'] is None else row['profit']
            campaign_id = row['campaign_id']
            source_id = row['source_id']
            size = row['size']
            ad_group_id = row['ad_group_id']
            placement_id = row['placement_id']
            placement = row['placement']
            install = row['install']
            d5 = row['D5']
            country = row['country']
            platform = row['platform']
            revenue = 0 if row['revenue'] is None else row['revenue']

            # print 'revenue:'+ str(revenue)
            # print 'profit:'+ str(profit)

            margin = (float(profit)/float(revenue) * 100) if revenue != 0 else float(profit)*100

            # print 'margin:'+ str(margin)

            p5 = 0 if not d5 or not install else float(d5) / float(install)

            tag = ''
            entry = {}

            if install >= 10 and p5 < 0.001:
                tag = 'Zero D5 (%i installs, %.1f D5, %s profit (%.2f%%) - %s' % (install, p5, round(profit, 2), margin, runDate)

            elif platform == 'iPhone':
                if install >= 10 and p5 < 20 and profit < 0:
                    tag = 'Poor D5 and Unprofitable (%i installs, %.1f D5, %s profit (%.2f%%)) - %s' % (install, p5, round(profit,2), margin, runDate)

            elif platform == 'iPad':
                if install >= 10 and p5 < 3 and profit < 0:
                    tag = 'Poor D5 and Unprofitable (%i installs, %.1f D5, %s profit (%.2f %%)) - %s' % (install, p5, round(profit,2), margin, runDate)

            elif platform == 'Android':
                if install >= 10 and p5 < 5 and profit < 0:
                    tag = 'Poor D5 and Unprofitable (%i installs, %.1f D5, %s profit (%.2f %%)) - %s' % (install, p5, round(profit,2), margin, runDate)

            # To Blacklist
            if tag != '':

                entry['campaign_id'] = campaign_id
                entry['source_id'] = source_id
                entry['placement_id'] = placement_id
                entry['size'] = size
                entry['ad_group_id'] = ad_group_id
                entry['tag'] = tag
                entry['platform'] = platform
                entry['placement'] = placement
                entry['profit'] = profit
                entry['install'] = install
                entry['d5'] = p5
                entry['country'] = country

                blacklist.append(entry)

                # Debug
                #print "%s|%s-%s:%s|%i|%i|%i|%f|%f|%s" % (platform, source_id, placement_id, placement, install, event_a, event_b, pa, pb, tag)

        return blacklist

    def update_job_status(self):
        sql = "REPLACE INTO job_status SET job_name='wwf_blacklist', job_type='rtb', last_finished=NOW(), threshold=1440"
        cursor = connections['default'].cursor()
        try:
            cursor.execute(sql)
        except:
            return False
        finally:
            cursor.close()
            return True
