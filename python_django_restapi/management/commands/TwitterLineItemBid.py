import json
import re
import time
import datetime
import sys
from django.conf import settings
from django.db import models
from django.db import connections
from django.utils.http import int_to_base36, base36_to_int
from django.core import serializers
from django.http import HttpRequest
from django.core.management.base import BaseCommand
from restapi.models.managers import BaseManager
from restapi.models.twitter.TwitterRevmap import TwitterRevmap
from restapi.models.twitter.TwitterAccount import TwitterAccount
from restapi.models.twitter.TwitterUser import TwitterUser
from restapi.models.twitter.TwitterCampaign import TwitterCampaign
from restapi.models.twitter.TwitterLineItem import TwitterLineItem

from restapi.models.Campaign import Campaign
from restapi.models.Advertiser import Advertiser


class Command(BaseCommand):

    MIN_INSTALLS = 3
    MIN_SPEND = 1
    MAX_CPC_BID = 3000000
    MIN_CPC_BID = 100000

    def handle(self, *args, **options):
        def filter_by_authorized_user(self, queryset):
            return queryset

        self._log("Started optimizer")
        self._twitter_sync_bids()
        self._update_job_status()
        self._log("Ended optimizer")

    def _log(self, s):
        print datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + s

    def _is_weekend(self, now):
        dt = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        # 0=Monday, 6=Sunday
        return dt.weekday() >= 5

    # Divide hour of day into 6x 4-hour buckets from 0-5
    def _get_hour_bucket(self, now):
        dt = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
        return dt.hour / 4

    def _get_enabled_line_items(self):
        sql = """SELECT tw_line_item_id, opt_value
                 FROM tw_line_item li JOIN
                      tw_campaign ca USING (tw_campaign_id) JOIN
                      campaign c USING (campaign_id) JOIN
                      tw_revmap USING (tw_line_item_id)
                 WHERE
                      li.status = 'enabled' AND
                      ca.status = 'enabled' AND
                      c.status = 'enabled' AND
                      opt_type = 'install'
        """
        cursor = connections['app_db'].cursor()
        cursor.execute(sql)

        enabled_line_items = {}
        for row in cursor:
            stats = {}
            stats['opt_value']   = row[1]
            stats['click']   = 0
            stats['install'] = 0
            stats['mcost']   = 0
            stats['rev']     = 0
            stats['ir']      = 0
            stats['cpc']     = 0
            stats['cpi']     = 0
            stats['goal']    = 0
            enabled_line_items[row[0]] = stats

        return enabled_line_items

    def _get_daily_stats_sql(self, now, days):
        sql = """SELECT
                    tw_line_item_id,
                    SUM(IF(event='click',num,0)) click,
                    SUM(IF(event='install',num,0)) install,
                    SUM(mcost) mcost,
                    SUM(rev) rev,
                    COALESCE(ROUND(SUM(IF(event='install',num,0))/SUM(IF(event='click',num,0)), 2), 0) ir,
                    COALESCE(ROUND(SUM(mcost)/SUM(IF(event='click',num,0)), 2), 0) cpc,
                    COALESCE(ROUND(SUM(mcost)/SUM(IF(event='install',num,0)), 2), 0) cpi,
                    COALESCE(ROUND(SUM(IF(event='install',num,0))*opt_value/SUM(mcost), 2), 0) goal,
                    opt_value
               FROM
                    s_tw_lid s JOIN
                    tw_line_item li USING (tw_line_item_id) JOIN
                    tw_campaign ca USING (tw_campaign_id) JOIN
                    campaign c USING (campaign_id) JOIN
                    event USING (event_id) JOIN
                    tw_revmap USING (tw_line_item_id)
               WHERE
                    li.status = 'enabled' AND
                    ca.status = 'enabled' AND
                    c.status = 'enabled' AND
                    opt_type = 'install' AND
                    event IN ('click','install') AND
                    date >= '%s' - INTERVAL %s DAY
               GROUP BY 1""" % (now, days)
        return sql

    def _get_hourly_stats_sql(self, now, hours, filter_datehour=False):
        datehour_clause = ''
        if filter_datehour:
            if self._is_weekend(now):
                datehour_clause += ' AND DAYOFWEEK(date) IN (1,7)'
            else:
                datehour_clause += ' AND DAYOFWEEK(date) NOT IN (1,7)'
            datehour_clause += datehour_clause + " AND FLOOR(hour/4) = %d" % self._get_hour_bucket(now)

        sql = """SELECT
                    tw_line_item_id,
                    SUM(IF(event='click',num,0)) click,
                    SUM(IF(event='install',num,0)) install,
                    SUM(mcost) mcost,
                    SUM(rev) rev,
                    COALESCE(ROUND(SUM(IF(event='install',num,0))/SUM(IF(event='click',num,0)), 2), 0) ir,
                    COALESCE(ROUND(SUM(mcost)/SUM(IF(event='click',num,0)), 2), 0) cpc,
                    COALESCE(ROUND(SUM(mcost)/SUM(IF(event='install',num,0)), 2), 0) cpi,
                    COALESCE(ROUND(SUM(IF(event='install',num,0))*opt_value/SUM(mcost), 2), 0) goal,
                    opt_value
               FROM
                    s_tw_lih s JOIN
                    tw_line_item li USING (tw_line_item_id) JOIN
                    tw_campaign ca USING (tw_campaign_id) JOIN
                    campaign c USING (campaign_id) JOIN
                    event USING (event_id) JOIN
                    tw_revmap USING (tw_line_item_id)
               WHERE
                    li.status = 'enabled' AND
                    ca.status = 'enabled' AND
                    c.status = 'enabled' AND
                    opt_type = 'install' AND
                    event IN ('click','install') AND
                    CONCAT(date, ' ', LPAD(hour, 2, 0)) >=
                    '%s' - INTERVAL %s HOUR
                    %s
               GROUP BY 1""" % (now, hours, datehour_clause)
        return sql

    def _get_stats(self, now, interval, is_daily, filter_datehour=False):
        if is_daily:
            sql = self._get_daily_stats_sql(now, interval)
        else:
            sql = self._get_hourly_stats_sql(now, interval, filter_datehour)
        self._log(sql)
        cursor = connections['app_db'].cursor()
        cursor.execute(sql)

        data = {}
        for row in cursor:
            stats = {}
            line_item_id     = row[0]
            stats['click']   = row[1]
            stats['install'] = row[2]
            stats['mcost']   = row[3]
            stats['rev']     = row[4]
            stats['ir']      = row[5]
            stats['cpc']     = row[6]
            stats['cpi']     = row[7]
            stats['goal']    = row[8]
            stats['opt_value'] = row[9]
            data[line_item_id] = stats
        return data

    def _merge_ir_stats(self, stats, stats_dh):
        for line_item_id, s in stats.iteritems():
            if line_item_id in stats_dh:
                if stats_dh[line_item_id]['install'] > self.MIN_INSTALLS:
                    self._log("Overriding %f IR stats with %f filtered IR stats" % (s['ir'], stats_dh[line_item_id]['ir']))
                    s['ir'] = stats_dh[line_item_id]['ir']

    # Round to 10000 micros
    def _round_micros(self, micros):
        return int(micros/10000) * 10000

    def _update_job_status(self):
        sql = "REPLACE INTO job_status SET job_name='twitter_optimizer', job_type='twitter', last_finished=NOW(), threshold=120"
        cursor = connections['default'].cursor()
        cursor.execute(sql)

    def _update_tw_line_item(self, tw_line_item):
        self._log(tw_line_item.bid_amount_computed_reason)
        tw_line_item.save_raw()

        # Auto-optimize
        if tw_line_item.tw_line_item_id in settings.TW_AUTO_OPTIMIZE_LINE_ITEMS and \
           tw_line_item.bid_amount_local_micro != tw_line_item.bid_amount_computed:

            self._log("Auto-optimizing tw_line_item_id %d to $%.2f" % (tw_line_item.tw_line_item_id, float(tw_line_item.bid_amount_computed)/1000000))
            tw_account_id = tw_line_item.tw_campaign_id.tw_account_id.tw_account_id
            res = TwitterLineItem.update({'account_id': tw_account_id,
                                                    'line_item_id': tw_line_item.tw_line_item_id,
                                                    'bid_amount_local_micro': tw_line_item.bid_amount_computed})
            if not res['success']:
                self._log("ERROR: Failed updating tw_line_item_id bid: " + res['message'])

    def _twitter_sync_bids(self):

        settings.SYSTEM_USER = True

        now = time.strftime("%Y-%m-%d %H:%M:%S")

        # Get 7-day stats
        stats7d = self._get_stats(now, 7, True)
        # Get 7-day stats filtered by current date/hour
        stats7d_datehour = self._get_stats(now, 7, False, True)
        # Override 7-day IR stats with stats filtered by current date/hour if > MIN_INSTALLS
        self._merge_ir_stats(stats7d, stats7d_datehour)

        # Get 1-day stats
        stats1d = self._get_stats(now, 24, False)
        # Get 1-day stats filtered by current date/hour
        stats1d_datehour = self._get_stats(now, 24, False, True)
        # Override 1-day IR stats with stats filtered by current date/hour if > MIN_INSTALLS
        self._merge_ir_stats(stats1d, stats1d_datehour)

        # Get 2-hour stats
        stats2h = self._get_stats(now, 2, False)

        # Include enabled line items without stats
        enabled_line_items = self._get_enabled_line_items()
        for line_item_id, s in enabled_line_items.iteritems():
            if line_item_id not in stats7d:
                stats7d[line_item_id] = s

        for line_item_id, s in stats7d.iteritems():

            tw_line_item = TwitterLineItem.objects_raw.filter(tw_line_item_id=line_item_id).first()

            campaign_id = tw_line_item.tw_campaign_id.campaign_id
            account_id  = tw_line_item.tw_campaign_id.tw_account_id.tw_account_id

            self._log("================================")
            self._log(str(line_item_id) + ', ' + str(s))
            self._log("Account: " + str(account_id))
            self._log("Line Item: " + str(line_item_id))
            stats_out = "CPCBid=$%.2f, Clicks=%d, Installs=%d, MCost=$%.2f, Rev=$%.2f, IR=%.2f, CPC=$%.2f, CPI=$%.2f, CPIgoal=$%.2f, %%Goal=%.2f" % (float(tw_line_item.bid_amount_local_micro)/1000000, s['click'], s['install'], s['mcost'], s['rev'], s['ir'], s['cpc'], s['cpi'], s['opt_value'], s['goal'])

            # Pause if %Goal(1D) < 0.25 AND mcost(1D) > $20
            if line_item_id in stats1d:
                if stats1d[line_item_id]['goal'] < 0.25 and stats1d[line_item_id]['mcost'] > 20:
                    reason = "ACTION: Pausing line_item %d. REASON: Goal(1D) %.2f < 0.25 and mcost $%.2f > $20." % (line_item_id, stats1d[line_item_id]['goal'], stats1d[line_item_id]['mcost'])
                    reason += " 7D STATS: " + stats_out
                    tw_line_item.bid_amount_computed_reason = reason
                    # Bid $0.01 CPC to effectively pause the line item
                    tw_line_item.bid_amount_computed = 10000
                    self._update_tw_line_item(tw_line_item)
                    continue

            # Boost if mcost(2H) < $MIN_SPEND
            if line_item_id not in stats2h or stats2h[line_item_id]['mcost'] < self.MIN_SPEND:
                mcost_2h = 0 if line_item_id not in stats2h else stats2h[line_item_id]['mcost']
                reason = "ACTION: Boosting line_item %d by 1.1 to $%.2f. REASON: mcost(2H) $%.2f < $%d." % (line_item_id, float(tw_line_item.bid_amount_local_micro * 1.1)/1000000, mcost_2h, self.MIN_SPEND)
                reason += " 7D STATS: " + stats_out
                tw_line_item.bid_amount_computed_reason = reason
                tw_line_item.bid_amount_computed = self._round_micros(tw_line_item.bid_amount_local_micro * 1.1)
                tw_line_item.bid_amount_computed = max(min(tw_line_item.bid_amount_computed, self.MAX_CPC_BID), self.MIN_CPC_BID)
                self._update_tw_line_item(tw_line_item)
                continue

            # Skip if installs(7D) < MIN_INSTALLS
            if s['install'] < self.MIN_INSTALLS:
                reason = "ACTION: Skipping line_item %d. REASON: %d installs < %d min installs." % (line_item_id, s['install'], self.MIN_INSTALLS)
                reason += " 7D STATS: " + stats_out
                tw_line_item.bid_amount_computed_reason = reason
                self._update_tw_line_item(tw_line_item)
                continue

            # If %Goal(2H) < 0.25
            if line_item_id in stats2h and stats2h[line_item_id]['goal'] < 0.25:
                bid_amount_computed = self._round_micros(tw_line_item.bid_amount_local_micro * 0.8)
                reason = "ACTION: Deflating line_item %d by 0.8 to $%.2f. REASON: Goal(2H) %.2f < 0.25." % (line_item_id, float(bid_amount_computed)/1000000, stats2h[line_item_id]['goal'])
            # If %Goal(2H) >= 0.25
            else:
                if stats1d[line_item_id]['install'] >= self.MIN_INSTALLS:
                    ir = stats1d[line_item_id]['ir']
                    ir_interval = '1D'
                else:
                    ir = s['ir']
                    ir_interval = '7D'
                bid_amount_computed = self._round_micros(s['opt_value'] * ir * 1000000)
                reason = "ACTION: Recommending line_item %d bid $%.2f. REASON: Opt_value $%.2f * IR(%s) %.2f." % (line_item_id, float(bid_amount_computed)/1000000, s['opt_value'], ir_interval, ir)

            reason += " 7D STATS: " + stats_out
            tw_line_item.bid_amount_computed_reason = reason
            tw_line_item.bid_amount_computed = max(min(bid_amount_computed, self.MAX_CPC_BID), self.MIN_CPC_BID)
            self._update_tw_line_item(tw_line_item)
