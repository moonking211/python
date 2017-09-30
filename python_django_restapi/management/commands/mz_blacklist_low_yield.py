import pyhs2
import sys
import json
import argparse
import pickle
import datetime
from datetime import date
from optparse import make_option
from django.conf import settings
from django.db import connections
from django.core.management.base import BaseCommand, CommandError

from restapi.models.BidderBlacklist import BidderBlacklist
from restapi.models.BidderBlacklist import BidderBlacklistIds

class Command(BaseCommand):

    option_list = BaseCommand.option_list  + (
                        make_option('--start_date',
                            dest='start_date',
                            default="",
                            help='Start Date (default: + 90 days)'),
                        make_option('--end_date',
                            dest='end_date',
                            default="",
                            help='Start Date (default: yesterday)'),
                        make_option('--start',
                            dest='start_date',
                            default="",
                            help='Start Date (default: + 90 days)'),
                        make_option('--end',
                            dest='end_date',
                            default="",
                            help='Start Date (default: yesterday)'),
                        make_option('--queue',
                            dest='queue',
                            choices=['p1', 'p2', 'p3'],
                            default='p2',
                            help='Manage Campaign ID'),
                        make_option('--print_bulk', action='store_true',
                            dest='print_bulk',
                            default='',
                            help='Print Tab Delimited Output for Monarch Bulk Uploading'),
                        make_option('--debug', action='store_true',
                            dest='debug',
                            default=False,
                            help=''),
                        )

    def handle(self, *args, **options):
        settings.SYSTEM_USER = True

        start_date = self.add_to_date(self.yesterday(), -90)
        end_date = self.yesterday()
        queue = "p2"
        print_bulk = False
        debug = False

        if 'start_date' in options and options['start_date'] != "":
            start_date = options['start_date']
        elif 'start' in options and options['start'] != "":
            start_date = options['start']

        if 'end_date' in options and options['start_date'] != "":
            end_date = options['end_date']
        elif 'end' in options and options['end'] != "":
            end_date = options['end']

        print "%s to %s" % (start_date, end_date)

        if 'print_bulk' in options:
            print_bulk = options['print_bulk']

        if 'queue' in options:
            queue = options['queue']


        if 'debug' in options:
            debug = options['debug']

        data = self.get_data(start_date, end_date, queue, debug)
        to_blacklist = self.get_mz_blacklist(data)

        if print_bulk:

            for each in to_blacklist:

                # campaign_id, ad_group_id, source_id*, placement_id*, placement_type*, size, tag
                bulk_entry = [each['campaign_id'], '0', each['source_id'], each['placement_id'], 'app', '', each['tag']]

                print '\t'.join(map(str, bulk_entry))

        try:
            for item in to_blacklist:
                try:
                    blacklist_entry = BidderBlacklistIds.objects_raw.get(campaign_id=item['campaign_id'], ad_group_id=0, source_id=item['source_id'], placement_id=item['placement_id'])
                    blacklist_entry.size = None
                    print "Existing entry: " + json.dumps(item)

                except TypeError:
                    pass
                except AttributeError:
                    pass
                except BidderBlacklistIds.DoesNotExist:
                    blacklist_entry = BidderBlacklistIds(campaign_id=item['campaign_id'], ad_group_id=0, source_id=item['source_id'], placement_id=item['placement_id'])
                    print "Adding new entry: " + json.dumps(item)

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

    def get_data(self, start_date, end_date, hive_queue='p1', debug=False):

        host = 'hive-prod.manage.com'
        port = 10000

        data = []

        # Return saved data if available
        if debug:

            try:
                with open('mz-placements.pickle', 'rb') as f:
                    print "reading from pickle file..."
                    data = pickle.load(f)
                return data
            except:
                pass

        with pyhs2.connect(host=host,
                           port=port,
                           authMechanism="PLAIN",
                           user='hdfs',
                           password='',
                           database='default') as conn:

            with conn.cursor() as cur:

                cur.execute("set mapred.job.queue.name=%s" % (hive_queue))
                cur.execute("set mapred.job.name=MZ: Gathering Placements to Blacklist %s to %s" % (start_date, end_date))
                cur.execute('set hive.cli.print.header=true')

                # TODO: Revisit whether which help and which doesn't
                cur.execute('set hive.vectorized.execution.enabled = true')
                cur.execute('set hive.vectorized.execution.reduce.enabled = true')
                cur.execute('set hive.cbo.enable=true')
                cur.execute('set hive.compute.query.using.stats=true')
                cur.execute('set hive.stats.fetch.column.stats=true')
                cur.execute('set hive.stats.fetch.partition.stats=true')

                query = """
                    SELECT
                        campaign_id,
                        source_id,
                        placement_id,
                        min(placement) placement,
                        SUM(ibid) ibid,
                        SUM(impression) impression,

                        SUM(click) click,

                        SUM(install) install,

                        ROUND(SUM(cost),4) cost,
                        ROUND(SUM(revenue),4) revenue,

                        SUM(event_a) event_a,
                        SUM(event_b) event_b,
                        SUM(event_c) event_c,
                        SUM(event_d) event_d,
                        SUM(event_e) event_e
                    FROM
                        summary.mz_daily d
                    WHERE
                        source_id != 0
                    AND
                        date BETWEEN '%s' AND '%s'
                    GROUP BY
                        campaign_id,
                        d.platform,
                        source_id,
                        placement_id
                    HAVING
                        install > 1
                """ % (start_date, end_date)

                cur.execute(query)

                schema = cur.getSchema()
                columns = [i['columnName'].split('.')[-1] for i in schema]

                for row in cur.fetch():

                    row_dict = {}
                    i = 0
                    for r in row:
                        row_dict[columns[i]] = r
                        i += 1

                    data.append(row_dict)

        if debug:
            # Save data
            with open('mz-placements.pickle', 'wb') as f:
                pickle.dump(data, f)

        return data


    def get_mz_blacklist(self, data):

        blacklist = []
        for row in data:

            campaign_id = row['campaign_id']
            source_id = row['source_id']
            placement_id = row['placement_id']
            placement = row['placement']
            install = row['install']
            event_a = row['event_a']
            event_b = row['event_b']
            event_c = row['event_c']

            pa = float(event_a)/float(install)
            pb = float(event_b)/float(install)
            pc = float(event_c)/float(install)

            tag = ''
            entry = {}

            # MOS iOS
            if row['campaign_id'] == 950:

                if install > 20 and pa < 0.4:
                    tag = 'Poor %%A yield (%i installs, %.2f %%A)' % (install, pa*100)

                elif install > 10 and pa < 0.2:
                    tag = 'Poor %%A yield (%i installs, %.2f %%A)' % (install, pa*100)

            # MOS Android
            elif row['campaign_id'] == 951:

                if install > 20 and pa < 0.5:
                    tag = 'Poor %%A yield (%i installs, %.2f %%A)' % (install, pa*100)

                elif install > 10 and pa < 0.2:
                    tag = 'Poor %%A yield (%i installs, %.2f %%A)' % (install, pa*100)

            # GOW iOS
            elif row['campaign_id'] == 328:

                if install > 20 and pa < 0.5:
                    tag = 'Poor %%A yield (%i installs, %.2f %%A)' % (install, pa*100)

                elif install > 10 and pa < 0.2:
                    tag = 'Poor %%A yield (%i installs, %.2f %%A)' % (install, pa*100)

            # To Blacklist
            if tag != '':

                entry['campaign_id'] = campaign_id
                entry['source_id'] = source_id
                entry['placement_id'] = placement_id
                entry['tag'] = tag

                blacklist.append(entry)

                # Debug
                #print "%s|%s-%s:%s|%i|%i|%i|%f|%f|%s" % (platform, source_id, placement_id, placement, install, event_a, event_b, pa, pb, tag)

        return blacklist

    def update_job_status(self):
        sql = "REPLACE INTO job_status SET job_name='mz_blacklist', job_type='rtb', last_finished=NOW(), threshold=1440"
        cursor = connections['default'].cursor()
        try:
            cursor.execute(sql)
        except:
            return False
        finally:
            cursor.close()
            return True
